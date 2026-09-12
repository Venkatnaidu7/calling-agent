"""
Twilio Voice Webhook and WebSocket Routes

These routes handle:
1. Inbound call webhook - Twilio POSTs here when a call arrives
2. WebSocket media stream - Twilio connects here for bidirectional audio
3. Call status callbacks - Twilio POSTs status updates
4. Outbound call initiation - API to trigger outbound calls
"""

import uuid
import json
import structlog
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Request,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from apps.api.config import settings
from apps.api.database import get_db
from apps.api.dependencies import get_tenant_context, require_roles
from apps.api.models.user import User
from apps.api.repositories.agent_repo import AgentRepository, AgentVersionRepository
from apps.api.realtime.voice_bridge import VoiceBridge
from apps.api.realtime.session_manager import SessionManager, CallSession
from apps.api.providers.twilio.voice import TwilioVoiceProvider
from apps.api.tools.definitions.appointment import register_appointment_tools
from apps.api.tools.definitions.transfer import register_transfer_tools
from apps.api.tools.definitions.contact import register_contact_tools
from apps.api.tools.definitions.knowledge import register_knowledge_tools

logger = structlog.get_logger()

router = APIRouter(tags=["Voice"])

# Register all tools at module load
register_appointment_tools()
register_transfer_tools()
register_contact_tools()
register_knowledge_tools()


# === Schemas ===


class OutboundCallRequest(BaseModel):
    agent_id: uuid.UUID
    to_number: str = Field(..., min_length=10)
    from_number: str = Field(..., min_length=10)
    customer_name: Optional[str] = None
    customer_context: Optional[str] = None
    campaign_id: Optional[uuid.UUID] = None


class CallStatusResponse(BaseModel):
    call_id: str
    status: str
    agent_id: Optional[str] = None
    direction: Optional[str] = None


async def _verify_twilio_request(request: Request, form_dict: dict) -> None:
    if not settings.twilio_auth_token:
        return
    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        logger.warning("twilio_missing_signature", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Missing Twilio signature"
        )

    url = str(request.url)
    provider = TwilioVoiceProvider()
    if not provider.validate_webhook_signature(url, form_dict, signature):
        logger.warning("twilio_invalid_signature", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Twilio signature"
        )


# === Inbound Call Webhook ===


@router.post("/api/v1/voice/inbound/{agent_id}")
async def inbound_call_webhook(
    agent_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Twilio calls this webhook when an inbound call arrives.
    Returns TwiML that connects the call to our WebSocket media stream.
    """
    form_data = await request.form()
    form_dict = dict(form_data)
    await _verify_twilio_request(request, form_dict)

    call_sid = form_data.get("CallSid", "")
    from_number = form_data.get("From", "")
    to_number = form_data.get("To", "")

    logger.info(
        "inbound_call_received",
        agent_id=str(agent_id),
        call_sid=call_sid,
        from_number=from_number,
        to_number=to_number,
    )

    # Look up the agent and its published version
    # We need to find the tenant by the phone number mapping
    # For now, search for the agent directly
    agent_repo = AgentRepository(db, tenant_id=None)
    agent = await agent_repo.get_by_id(agent_id)

    if not agent or not agent.is_active or agent.status != "published":
        logger.warning("inbound_call_no_agent", agent_id=str(agent_id))
        return Response(
            content="<Response><Say>We are sorry, this number is not currently accepting calls.</Say><Hangup/></Response>",
            media_type="application/xml",
        )

    # Generate a unique call ID for our session
    call_id = str(uuid.uuid4())

    # Store call_id -> tenant_id mapping in Redis for WebSocket verification
    redis = request.app.state.redis
    if redis:
        from apps.api.realtime.session_manager import SessionManager

        session_manager = SessionManager(redis)
        await session_manager.create_pending_session(call_id, agent.tenant_id)

    # Build the WebSocket URL for the media stream
    ws_scheme = "wss" if settings.twilio_webhook_base_url.startswith("https") else "ws"
    base = settings.twilio_webhook_base_url.replace("https://", "").replace("http://", "")
    ws_url = f"{ws_scheme}://{base}/api/v1/voice/stream/{call_id}"

    # Generate TwiML with <Connect><Stream>
    twilio_provider = TwilioVoiceProvider()
    twiml = twilio_provider.generate_stream_twiml(
        websocket_url=ws_url,
        custom_parameters={
            "call_id": call_id,
            "agent_id": str(agent_id),
            "tenant_id": str(agent.tenant_id),
            "direction": "inbound",
            "from_number": from_number,
            "to_number": to_number,
        },
    )

    logger.info("inbound_call_connecting", call_id=call_id, ws_url=ws_url)
    return Response(content=twiml, media_type="application/xml")


# === WebSocket Media Stream ===


@router.websocket("/api/v1/voice/stream/{call_id}")
async def voice_stream_websocket(
    websocket: WebSocket,
    call_id: str,
):
    """
    WebSocket endpoint that Twilio's Media Stream connects to.
    Bridges Twilio audio with OpenAI Realtime API.
    """
    await websocket.accept()
    logger.info("ws_accepted", call_id=call_id)

    # Initialize Redis from app state at the start
    redis = websocket.app.state.redis
    if not redis:
        logger.error("redis_not_available")
        await websocket.close()
        return

    try:
        # Wait for the 'start' event from Twilio to get custom parameters
        raw = await websocket.receive_text()
        data = json.loads(raw)

        if data.get("event") != "connected":
            logger.warning("ws_unexpected_first_event", event=data.get("event"))

        # Wait for 'start' event with stream parameters
        raw = await websocket.receive_text()
        data = json.loads(raw)

        if data.get("event") != "start":
            logger.error("ws_missing_start_event", event=data.get("event"))
            await websocket.close()
            return

        start_data = data.get("start", {})
        custom_params = start_data.get("customParameters", {})
        stream_sid = start_data.get("streamSid", "")
        twilio_call_sid = start_data.get("callSid", "")

        agent_id = custom_params.get("agent_id", "")
        tenant_id = custom_params.get("tenant_id", "")
        direction = custom_params.get("direction", "inbound")
        from_number = custom_params.get("from_number", "")
        to_number = custom_params.get("to_number", "")

        # SECURITY FIX: Verify tenant_id against the pending session created in the webhook
        session_manager = SessionManager(redis)
        verified_tenant_id = await session_manager.get_pending_tenant(call_id)
        if not verified_tenant_id or verified_tenant_id != tenant_id:
            logger.error(
                "ws_tenant_verification_failed",
                call_id=call_id,
                provided=tenant_id,
                verified=verified_tenant_id,
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Clean up pending session
        await session_manager.delete_pending_session(call_id)

        logger.info(
            "ws_stream_started",
            call_id=call_id,
            stream_sid=stream_sid,
            agent_id=agent_id,
            tenant_id=tenant_id,
        )

        # Get Redis from the app state
        redis = websocket.app.state.redis
        if not redis:
            logger.error("redis_not_available")
            await websocket.close()
            return

        # Load agent version from database
        from apps.api.database import async_session_factory

        async with async_session_factory() as db_session:
            agent_repo = AgentRepository(
                db_session, tenant_id=uuid.UUID(tenant_id) if tenant_id else None
            )
            agent = await agent_repo.get_by_id(uuid.UUID(agent_id) if agent_id else None)

            if not agent or not agent.published_version_id:
                logger.error("ws_no_published_version", agent_id=agent_id)
                await websocket.close()
                return

            version_repo = AgentVersionRepository(
                db_session, tenant_id=uuid.UUID(tenant_id) if tenant_id else None
            )
            agent_version = await version_repo.get_by_id(agent.published_version_id)

            if not agent_version:
                logger.error("ws_version_not_found", version_id=str(agent.published_version_id))
                await websocket.close()
                return

        # Create call session in Redis
        session_manager = SessionManager(redis)

        # Check concurrent call limits
        active_count = await session_manager.get_active_sessions_count(tenant_id)
        if active_count >= settings.call_max_concurrent_per_tenant:
            logger.warning("concurrent_call_limit", tenant_id=tenant_id, count=active_count)
            await websocket.close()
            return

        # SECURITY FIX: Check monthly usage limit before starting the voice bridge
        async with async_session_factory() as db_session:
            from apps.api.services.billing_service import BillingService

            billing_service = BillingService(db_session, uuid.UUID(tenant_id))
            if await billing_service.check_usage_limit():
                logger.warning("monthly_usage_limit_reached", tenant_id=tenant_id)
                await websocket.send_json(
                    {
                        "event": "error",
                        "message": "Monthly voice minute limit reached. Please upgrade your plan.",
                    }
                )
                await websocket.close()
                return

        call_session = CallSession(
            call_id=call_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            agent_version_id=str(agent_version.id),
            direction=direction,
            from_number=from_number,
            to_number=to_number,
            provider_call_id=twilio_call_sid,
            stream_sid=stream_sid,
            language=agent_version.language or "en",
            state="connecting",
        )
        await session_manager.create_session(call_session)

        # Create and start the voice bridge
        bridge = VoiceBridge(
            twilio_ws=websocket,
            agent_version=agent_version,
            call_session=call_session,
            session_manager=session_manager,
            redis=redis,
            stream_sid=stream_sid,
        )

        # The bridge handles all Twilio ↔ OpenAI communication
        # It processes Twilio events internally (it already consumed 'connected' and 'start')
        # We need to "replay" the start event since the bridge expects to handle it
        # Actually, the bridge's _handle_twilio_messages will start fresh from 'media' events
        # The start data was already consumed, so update session with stream_sid
        await session_manager.update_session(
            call_id, stream_sid=stream_sid, provider_call_id=twilio_call_sid
        )

        logger.info("voice_bridge_starting", call_id=call_id)
        await bridge.start()

    except WebSocketDisconnect:
        logger.info("ws_disconnected", call_id=call_id)
    except Exception as e:
        logger.error("ws_error", call_id=call_id, error=str(e))
    finally:
        logger.info("ws_cleanup_complete", call_id=call_id)


# === Call Status Callback ===


@router.post("/api/v1/voice/status/{call_id}")
async def call_status_callback(
    call_id: str,
    request: Request,
):
    """
    Twilio calls this endpoint with call status updates.
    """
    form_data = await request.form()
    await _verify_twilio_request(request, dict(form_data))

    call_status = form_data.get("CallStatus", "")
    call_duration = form_data.get("CallDuration", "0")
    call_sid = form_data.get("CallSid", "")

    logger.info(
        "call_status_update",
        call_id=call_id,
        status=call_status,
        duration=call_duration,
        call_sid=call_sid,
    )

    # Update session if exists
    redis = request.app.state.redis
    if redis:
        session_manager = SessionManager(redis)
        session = await session_manager.get_session(call_id)
        if session:
            if call_status in ("completed", "busy", "no-answer", "failed", "canceled"):
                await session_manager.update_session(call_id, state="completed")

    return {"status": "received"}


# === Outbound Call API ===


@router.post(
    "/api/v1/voice/outbound", response_model=CallStatusResponse, status_code=status.HTTP_201_CREATED
)
async def initiate_outbound_call(
    data: OutboundCallRequest,
    request: Request,
    tenant_id: uuid.UUID = Depends(get_tenant_context),
    current_user: User = Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER")),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate an outbound AI voice call.
    """
    # Verify agent belongs to tenant and is published
    agent_repo = AgentRepository(db, tenant_id=tenant_id)
    agent = await agent_repo.get_by_id(data.agent_id)

    if not agent or not agent.is_active or agent.status != "published":
        raise HTTPException(status_code=404, detail="Published agent not found")

    if not agent.published_version_id:
        raise HTTPException(status_code=400, detail="Agent has no published version")

    # Check concurrent call limits
    redis = request.app.state.redis
    if redis:
        session_manager = SessionManager(redis)
        active_count = await session_manager.get_active_sessions_count(str(tenant_id))
        if active_count >= settings.call_max_concurrent_per_tenant:
            raise HTTPException(status_code=429, detail="Concurrent call limit exceeded")

    # Verify TCPA / DNC Compliance before placing outbound call
    from apps.api.services.compliance_service import ComplianceService

    compliance_service = ComplianceService(db, tenant_id)
    if not await compliance_service.check_can_call(data.to_number, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot call {data.to_number}: Number is on the Do Not Call (DNC) list or consent is revoked.",
        )

    # Generate call ID
    call_id = str(uuid.uuid4())

    # Register pending session in Redis for WebSocket verification
    if redis:
        await session_manager.create_pending_session(call_id, tenant_id)

    # Build webhook URLs
    base = settings.twilio_webhook_base_url.rstrip("/")
    ws_scheme = "wss" if base.startswith("https") else "ws"
    ws_base = base.replace("https://", "").replace("http://", "")
    ws_url = f"{ws_scheme}://{ws_base}/api/v1/voice/stream/{call_id}"
    status_url = f"{base}/api/v1/voice/status/{call_id}"

    # Generate TwiML for the outbound call
    twilio_provider = TwilioVoiceProvider()
    twilio_provider.generate_stream_twiml(
        websocket_url=ws_url,
        custom_parameters={
            "call_id": call_id,
            "agent_id": str(data.agent_id),
            "tenant_id": str(tenant_id),
            "direction": "outbound",
            "from_number": data.from_number,
            "to_number": data.to_number,
        },
    )

    # Initiate the call via Twilio
    try:
        result = await twilio_provider.initiate_outbound_call(
            to_number=data.to_number,
            from_number=data.from_number,
            webhook_url=f"{base}/api/v1/voice/inbound/{data.agent_id}",
            status_callback_url=status_url,
            machine_detection=True,
            custom_parameters={"call_id": call_id},
        )
    except Exception as e:
        logger.error("outbound_call_failed", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to initiate call: {str(e)}") from e

    logger.info(
        "outbound_call_initiated",
        call_id=call_id,
        to=data.to_number,
        provider_call_id=result.provider_call_id,
    )

    return CallStatusResponse(
        call_id=call_id,
        status="initiated",
        agent_id=str(data.agent_id),
        direction="outbound",
    )


# === Active Calls Management ===


@router.get("/api/v1/voice/calls/active", response_model=list[CallStatusResponse])
async def list_active_calls(
    request: Request,
    tenant_id: uuid.UUID = Depends(get_tenant_context),
    current_user: User = Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN", "SUPERVISOR")),
):
    """List active calls for the current tenant."""
    redis = request.app.state.redis
    if not redis:
        return []

    SessionManager(redis)
    active_calls = []

    # Scan for active sessions for this tenant
    async for key in redis.scan_iter("call_session:*"):
        session_data = await redis.hgetall(key)
        if session_data.get("tenant_id") == str(tenant_id) and session_data.get("state") in (
            "connecting",
            "active",
        ):
            active_calls.append(
                CallStatusResponse(
                    call_id=session_data.get("call_id", ""),
                    status=session_data.get("state", ""),
                    agent_id=session_data.get("agent_id"),
                    direction=session_data.get("direction"),
                )
            )

    return active_calls
