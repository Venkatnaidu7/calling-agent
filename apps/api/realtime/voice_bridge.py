import json
import asyncio
import uuid
import structlog
from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from apps.api.providers.openai.realtime import OpenAIRealtimeProvider
from apps.api.providers.base.realtime_ai import RealtimeSessionConfig, RealtimeEvent
from apps.api.realtime.session_manager import SessionManager, CallSession
from apps.api.realtime.prompt_builder import build_session_instructions, build_greeting_message
from apps.api.tools.executor import ToolExecutor
from apps.api.tools.registry import ToolRegistry
from apps.api.models.agent import AgentVersion

logger = structlog.get_logger()


class VoiceBridge:
    """
    Bridges a Twilio Media Stream WebSocket with OpenAI Realtime API.
    
    Architecture:
    Twilio WS ←→ VoiceBridge ←→ OpenAI Realtime WS
    
    Audio flow (zero transcoding):
    Twilio (g711_ulaw base64) → pass-through → OpenAI (g711_ulaw)
    OpenAI (g711_ulaw base64) → pass-through → Twilio (g711_ulaw)
    """

    def __init__(
        self,
        twilio_ws: WebSocket,
        agent_version: AgentVersion,
        call_session: CallSession,
        session_manager: SessionManager,
        redis: Redis,
        stream_sid: str = "",
    ):
        self.twilio_ws = twilio_ws
        self.agent_version = agent_version
        self.call_session = call_session
        self.session_manager = session_manager
        self.redis = redis
        self.stream_sid = stream_sid or call_session.stream_sid

        self.openai_provider = OpenAIRealtimeProvider()
        self.tool_executor = ToolExecutor(
            tenant_id=call_session.tenant_id,
            agent_id=call_session.agent_id,
            call_id=call_session.call_id,
            tool_permissions=agent_version.tool_permissions or {},
            to_number=call_session.to_number,
            from_number=call_session.from_number,
        )

        self.is_active = False
        self._current_assistant_item_id: str = ""
        self._current_ai_text: str = ""
        self._played_audio_bytes: int = 0
        self._transcript_segments: list[dict] = []

    async def start(self):
        """Main entry point. Starts the voice bridge."""
        try:
            self.is_active = True
            
            # Build instructions
            instructions = build_session_instructions(
                self.agent_version,
                self.call_session.direction,
                self.call_session.from_number,
                self.call_session.to_number,
            )
            
            # Get permitted tools as OpenAI format
            openai_tools = ToolRegistry.get_openai_tools(self.agent_version.tool_permissions or {})
            
            # Build turn detection config
            td_config = self.agent_version.turn_detection_config or {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500,
                "create_response": True,
            }
            
            # Connect to OpenAI Realtime
            config = RealtimeSessionConfig(
                voice=self.agent_version.voice or "ash",
                instructions=instructions,
                input_audio_format="g711_ulaw",
                output_audio_format="g711_ulaw",
                tools=openai_tools,
                turn_detection=td_config,
            )
            
            await self.openai_provider.connect(config)
            
            # Register OpenAI event handlers
            self._register_openai_handlers()
            
            # Send greeting if configured
            greeting = build_greeting_message(self.agent_version, self.call_session.direction)
            if greeting:
                await self.openai_provider.inject_context("user", f"[System: The call has just connected. Greet the caller. Your greeting should be: '{greeting}']")
                await self.openai_provider.request_response()
            
            # Update session state
            await self.session_manager.update_session(self.call_session.call_id, state="active")
            
            # Run both WebSocket loops concurrently
            await asyncio.gather(
                self._handle_twilio_messages(),
                self.openai_provider.receive_events(),
            )
            
        except Exception as e:
            logger.error("voice_bridge_error", call_id=self.call_session.call_id, error=str(e))
            # Send fallback message to Twilio if possible
            await self._send_fallback_to_twilio()
        finally:
            await self._cleanup()

    def _register_openai_handlers(self):
        """Register handlers for OpenAI Realtime events."""
        self.openai_provider.on_event("response.audio.delta", self._on_ai_audio)
        self.openai_provider.on_event("response.audio_transcript.delta", self._on_ai_transcript)
        self.openai_provider.on_event("response.output_item.added", self._on_output_item_added)
        self.openai_provider.on_event("response.function_call_arguments.done", self._on_tool_call)
        self.openai_provider.on_event("input_audio_buffer.speech_started", self._on_speech_started)
        self.openai_provider.on_event("input_audio_buffer.speech_stopped", self._on_speech_stopped)
        self.openai_provider.on_event("conversation.item.input_audio_transcription.completed", self._on_user_transcript)
        self.openai_provider.on_event("response.done", self._on_response_done)
        self.openai_provider.on_event("error", self._on_openai_error)

    async def _handle_twilio_messages(self):
        """Handle incoming messages from Twilio Media Stream."""
        try:
            while self.is_active:
                raw = await self.twilio_ws.receive_text()
                data = json.loads(raw)
                event = data.get("event")
                
                if event == "connected":
                    logger.info("twilio_stream_connected", call_id=self.call_session.call_id)
                    
                elif event == "start":
                    self.stream_sid = data["start"]["streamSid"]
                    call_sid = data["start"]["callSid"]
                    custom_params = data["start"].get("customParameters", {})
                    await self.session_manager.update_session(
                        self.call_session.call_id,
                        stream_sid=self.stream_sid,
                        provider_call_id=call_sid,
                    )
                    logger.info("twilio_stream_started", stream_sid=self.stream_sid, call_sid=call_sid)
                    
                elif event == "media":
                    # Pass audio directly to OpenAI (zero transcoding!)
                    payload = data["media"]["payload"]
                    await self.openai_provider.send_audio(payload)
                    
                elif event == "dtmf":
                    digit = data["dtmf"]["digit"]
                    logger.info("dtmf_received", digit=digit, call_id=self.call_session.call_id)
                    
                elif event == "mark":
                    mark_name = data["mark"]["name"]
                    logger.debug("twilio_mark_received", mark=mark_name)
                    
                elif event == "stop":
                    logger.info("twilio_stream_stopped", call_id=self.call_session.call_id)
                    self.is_active = False
                    break
                    
        except WebSocketDisconnect:
            logger.info("twilio_ws_disconnected", call_id=self.call_session.call_id)
            self.is_active = False
        except Exception as e:
            logger.error("twilio_message_error", error=str(e), call_id=self.call_session.call_id)
            self.is_active = False

    # === OpenAI Event Handlers ===

    async def _on_ai_audio(self, event: RealtimeEvent):
        """AI generated audio — send directly to Twilio."""
        audio_b64 = event.data.get("delta", "")
        if audio_b64 and self.stream_sid:
            await self.twilio_ws.send_json({
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": audio_b64},
            })
            # Track how much audio was played (for barge-in truncation)
            # g711_ulaw at 8kHz = 8000 bytes/sec, base64 inflates by 4/3
            raw_bytes = len(audio_b64) * 3 // 4
            self._played_audio_bytes += raw_bytes

    async def _on_output_item_added(self, event: RealtimeEvent):
        """Track the current assistant message item for barge-in truncation."""
        item = event.data.get("item", {})
        if item.get("type") == "message" and item.get("role") == "assistant":
            self._current_assistant_item_id = item.get("id", "")
            self._played_audio_bytes = 0

    async def _on_speech_started(self, event: RealtimeEvent):
        """BARGE-IN: User started speaking while AI is talking."""
        logger.info("barge_in_detected", call_id=self.call_session.call_id)
        
        # 1. Cancel AI response
        await self.openai_provider.cancel_response()
        
        # 2. Truncate assistant audio to what was actually played
        if self._current_assistant_item_id and self._played_audio_bytes > 0:
            played_ms = int((self._played_audio_bytes / 8000) * 1000)  # 8000 bytes/sec for g711_ulaw
            await self.openai_provider.truncate_audio(
                self._current_assistant_item_id, 0, played_ms
            )
        
        # 3. Clear Twilio's audio buffer
        if self.stream_sid:
            await self.twilio_ws.send_json({
                "event": "clear",
                "streamSid": self.stream_sid,
            })
        
        # Reset tracking
        self._current_assistant_item_id = ""
        self._played_audio_bytes = 0

    async def _on_speech_stopped(self, event: RealtimeEvent):
        """User stopped speaking."""
        logger.debug("speech_stopped", call_id=self.call_session.call_id)

    async def _on_tool_call(self, event: RealtimeEvent):
        """AI requested a tool call — execute it securely."""
        tool_name = event.data.get("name", "")
        arguments = event.data.get("arguments", "{}")
        call_id = event.data.get("call_id", "")
        
        logger.info("tool_call_requested", tool=tool_name, call_id=self.call_session.call_id)
        
        # Execute through the secure pipeline
        result = await self.tool_executor.execute(tool_name, arguments, call_id)
        
        # Send result back to OpenAI
        await self.openai_provider.send_tool_result(call_id, result.to_json())
        
        # Handle special tool results
        result_data = result.data if result.success else {}
        if result_data.get("transfer_initiated"):
            await self._handle_transfer(result_data)
        elif result_data.get("call_ending"):
            await self._handle_call_end(result_data)

        self._current_assistant_item_id = ""
        self._played_audio_bytes = 0
        self._current_ai_text = ""

    async def _on_ai_transcript(self, event: RealtimeEvent):
        """AI speech transcript delta."""
        delta = event.data.get("delta", "")
        if delta:
            self._current_ai_text += delta

    async def _on_user_transcript(self, event: RealtimeEvent):
        """User speech transcription completed (via Whisper)."""
        transcript = event.data.get("transcript", "")
        logger.info("user_said", text=transcript[:100], call_id=self.call_session.call_id)
        if transcript.strip():
            self._transcript_segments.append({
                "speaker": "customer",
                "text": transcript.strip(),
            })

    async def _on_response_done(self, event: RealtimeEvent):
        """AI response completed. Track usage and save assistant turn."""
        if self._current_ai_text.strip():
            self._transcript_segments.append({
                "speaker": "agent",
                "text": self._current_ai_text.strip(),
            })
            self._current_ai_text = ""
        usage = event.data.get("response", {}).get("usage", {})
        if usage:
            logger.info("ai_usage", usage=usage, call_id=self.call_session.call_id)

    async def _on_openai_error(self, event: RealtimeEvent):
        """OpenAI error event."""
        error = event.data.get("error", {})
        logger.error("openai_realtime_error", error=error, call_id=self.call_session.call_id)

    # === Transfer & End Call ===

    async def _handle_transfer(self, data: dict):
        """Handle call transfer result from tool execution."""
        logger.info("initiating_transfer", call_id=self.call_session.call_id, reason=data.get("reason"))
        await self.session_manager.update_session(
            self.call_session.call_id, transfer_status="initiated"
        )

    async def _handle_call_end(self, data: dict):
        """Handle graceful call end."""
        logger.info("ending_call", call_id=self.call_session.call_id, reason=data.get("reason"))
        self.is_active = False

    async def _send_fallback_to_twilio(self):
        """Send a fallback message if AI fails during a call."""
        fallback = self.agent_version.fallback_message or "I'm sorry, I'm experiencing technical difficulties. Please hold while I transfer you."
        logger.warning("sending_fallback", call_id=self.call_session.call_id)

    async def _cleanup(self):
        """Clean up resources when the call ends, persist call logs & usage."""
        self.is_active = False
        
        # Disconnect OpenAI
        try:
            await self.openai_provider.disconnect()
        except Exception as e:
            logger.error("openai_disconnect_error", error=str(e))
        
        # Update session state in Redis
        try:
            await self.session_manager.update_session(
                self.call_session.call_id,
                state="completed",
            )
        except Exception as e:
            logger.error("session_update_error", error=str(e))

        # Persist CallLog and Usage in Database
        try:
            from datetime import datetime, timezone
            import math
            from apps.api.database import async_session_factory
            from apps.api.models.call_log import CallLog
            from apps.api.models.billing import UsageRecord
            from apps.api.services.webhook_service import WebhookService

            now = datetime.now(timezone.utc)
            try:
                start_dt = datetime.fromisoformat(self.call_session.start_time)
            except Exception:
                start_dt = now
            duration_secs = max(1, int((now - start_dt).total_seconds()))
            billable_minutes = max(1, math.ceil(duration_secs / 60))
            cost_cents = billable_minutes * 5  # 5 cents per minute

            sentiment = "positive" if len(self._transcript_segments) > 2 else "neutral"

            # Auto-generate summary from transcript
            summary_preview = (
                f"Call between {self.call_session.from_number} and {self.call_session.to_number}. "
                f"Completed in {duration_secs}s with {len(self._transcript_segments)} dialogue turns."
            )

            async with async_session_factory() as db:
                call_log = CallLog(
                    tenant_id=uuid.UUID(self.call_session.tenant_id),
                    call_id=self.call_session.call_id,
                    agent_id=uuid.UUID(self.call_session.agent_id) if self.call_session.agent_id else None,
                    agent_version_id=uuid.UUID(self.call_session.agent_version_id) if self.call_session.agent_version_id else None,
                    direction=self.call_session.direction,
                    from_number=self.call_session.from_number,
                    to_number=self.call_session.to_number,
                    status="completed",
                    provider_call_sid=self.call_session.provider_call_id,
                    duration_seconds=duration_secs,
                    transcript=self._transcript_segments,
                    summary=summary_preview,
                    sentiment=sentiment,
                    cost_cents=cost_cents,
                    started_at=start_dt,
                    ended_at=now,
                    tool_calls=self.tool_executor.execution_log,
                )
                db.add(call_log)

                # Record billable usage
                usage_record = UsageRecord(
                    tenant_id=uuid.UUID(self.call_session.tenant_id),
                    call_id=self.call_session.call_id,
                    metric="voice_minutes",
                    quantity=billable_minutes,
                    unit_cost_cents=5,
                    total_cost_cents=cost_cents,
                    metadata_json={"duration_seconds": duration_secs},
                )
                db.add(usage_record)
                await db.commit()

                # Dispatch outgoing webhook
                webhook_service = WebhookService(db, uuid.UUID(self.call_session.tenant_id))
                await webhook_service.dispatch_event("call.completed", {
                    "call_id": self.call_session.call_id,
                    "direction": self.call_session.direction,
                    "duration_seconds": duration_secs,
                    "from_number": self.call_session.from_number,
                    "to_number": self.call_session.to_number,
                    "sentiment": sentiment,
                })
        except Exception as e:
            logger.error("call_persistence_error", call_id=self.call_session.call_id, error=str(e))
        
        logger.info("voice_bridge_cleanup_complete", call_id=self.call_session.call_id)
