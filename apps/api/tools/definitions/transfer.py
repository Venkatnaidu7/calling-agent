from typing import Any
import structlog
from apps.api.tools.registry import ToolRegistry, ToolDefinition

logger = structlog.get_logger()


async def transfer_call(
    reason: str, department: str = None, phone_number: str = None, _context: dict = None, **kwargs
) -> dict[str, Any]:
    """Transfer the current call to a human agent or department."""
    logger.info(
        "transfer_call_requested", reason=reason, department=department, phone_number=phone_number
    )
    return {"transfer_initiated": True, "reason": reason, "message": "Transfer initiated"}


async def end_call(
    reason: str, summary: str = None, _context: dict = None, **kwargs
) -> dict[str, Any]:
    """End the current call gracefully."""
    logger.info("end_call_requested", reason=reason, summary=summary)
    return {"call_ending": True, "reason": reason, "message": "Call is ending"}


async def send_sms(to_number: str, message: str, _context: dict = None, **kwargs) -> dict[str, Any]:
    """Send an SMS to the caller via Twilio messaging API."""
    import asyncio
    from twilio.rest import Client
    from apps.api.config import settings

    logger.info("send_sms_requested", to_number=to_number, message_preview=message[:20])

    # SECURITY: Prevent toll fraud by only allowing SMS to the active caller
    caller_number = _context.get("from_number") if _context else None
    if caller_number and to_number != caller_number:
        logger.warning("sms_toll_fraud_prevented", attempted_number=to_number, allowed=caller_number)
        return {"sent": False, "error": "Can only send SMS to the active caller's phone number."}

    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        logger.warning("twilio_not_configured_sms_mocked")
        return {"sent": True, "mock": True, "message": "SMS recorded (Twilio credentials not set)"}

    try:
        sender_number = (_context.get("to_number") if _context else None) or "+18005550199"

        def _send():
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            # Send message
            msg = client.messages.create(
                to=to_number,
                from_=sender_number,
                body=message,
            )
            return msg.sid

        msg_sid = await asyncio.to_thread(_send)
        return {
            "sent": True,
            "message_sid": msg_sid,
            "message": "SMS sent successfully to recipient",
        }
    except Exception as e:
        logger.error("send_sms_failed", error=str(e), to=to_number)
        return {"sent": False, "error": str(e)}


async def create_callback(
    phone_number: str,
    preferred_time: str = None,
    reason: str = None,
    _context: dict = None,
    **kwargs,
) -> dict[str, Any]:
    """Schedule a callback."""
    logger.info(
        "create_callback_requested",
        phone_number=phone_number,
        preferred_time=preferred_time,
        reason=reason,
    )

    try:
        from apps.api.database import async_session_factory
        from apps.api.repositories.contact_repo import ContactRepository
        import uuid

        tenant_id = _context.get("tenant_id") if _context else None

        if tenant_id:
            async with async_session_factory() as session:
                repo = ContactRepository(session, uuid.UUID(tenant_id))
                contact = await repo.get_by_phone(phone_number)
                if contact:
                    callbacks = contact.custom_fields.get("callbacks", []) if contact.custom_fields else []
                    callbacks.append({"time": preferred_time, "reason": reason})
                    custom_fields = contact.custom_fields or {}
                    custom_fields["callbacks"] = callbacks
                    await repo.update(contact.id, custom_fields=custom_fields)
                    await session.commit()
    except Exception as e:
        logger.error("create_callback_failed", error=str(e))
        return {"callback_scheduled": False, "error": "Internal error scheduling callback"}

    return {"callback_scheduled": True, "message": "Callback scheduled successfully"}


def register_transfer_tools():
    ToolRegistry.register(
        ToolDefinition(
            name="transfer_call",
            description="Transfer the current call to a human agent or department",
            parameters={
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Reason for the transfer"},
                    "department": {"type": "string", "description": "Target department"},
                    "phone_number": {
                        "type": "string",
                        "description": "Specific phone number to transfer to",
                    },
                },
                "required": ["reason"],
            },
            handler=transfer_call,
            category="transfer",
        )
    )

    ToolRegistry.register(
        ToolDefinition(
            name="end_call",
            description="End the current call gracefully",
            parameters={
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Reason for ending the call"},
                    "summary": {"type": "string", "description": "Brief summary of the call"},
                },
                "required": ["reason"],
            },
            handler=end_call,
            category="transfer",
        )
    )

    ToolRegistry.register(
        ToolDefinition(
            name="send_sms",
            description="Send an SMS to the caller",
            parameters={
                "type": "object",
                "properties": {
                    "to_number": {"type": "string", "description": "Phone number to send SMS to"},
                    "message": {"type": "string", "description": "SMS message content"},
                },
                "required": ["to_number", "message"],
            },
            handler=send_sms,
            category="transfer",
        )
    )

    ToolRegistry.register(
        ToolDefinition(
            name="create_callback",
            description="Schedule a callback",
            parameters={
                "type": "object",
                "properties": {
                    "phone_number": {"type": "string", "description": "Phone number to call back"},
                    "preferred_time": {"type": "string", "description": "Preferred callback time"},
                    "reason": {"type": "string", "description": "Reason for the callback"},
                },
                "required": ["phone_number"],
            },
            handler=create_callback,
            category="transfer",
        )
    )
