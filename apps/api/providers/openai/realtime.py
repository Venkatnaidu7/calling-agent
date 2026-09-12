import json
import asyncio
import structlog
import websockets
from typing import Callable, Awaitable
from apps.api.providers.base.realtime_ai import (
    RealtimeAIProvider,
    RealtimeSessionConfig,
    RealtimeEvent,
)
from apps.api.config import settings

logger = structlog.get_logger()

WS_URL = "wss://api.openai.com/v1/realtime"


class OpenAIRealtimeProvider(RealtimeAIProvider):
    def __init__(self):
        self.ws = None
        self._event_handlers: dict[str, list[Callable]] = {}
        self._connected = False
        self._receive_task: asyncio.Task | None = None

    async def connect(self, config: RealtimeSessionConfig):
        url = f"{WS_URL}?model={config.model}"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        self.ws = await websockets.connect(url, additional_headers=headers)
        self._connected = True

        # Wait for session.created event
        raw = await self.ws.recv()
        event = json.loads(raw)
        if event.get("type") != "session.created":
            raise ConnectionError(f"Expected session.created, got {event.get('type')}")

        # Configure session
        await self.update_session(config)
        logger.info("openai_realtime_connected", model=config.model)

    async def disconnect(self):
        self._connected = False
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def send_audio(self, audio_base64: str):
        if not self.ws:
            return
        await self.ws.send(
            json.dumps(
                {
                    "type": "input_audio_buffer.append",
                    "audio": audio_base64,
                }
            )
        )

    async def send_tool_result(self, call_id: str, result: str):
        if not self.ws:
            return
        # Send function_call_output
        await self.ws.send(
            json.dumps(
                {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": result,
                    },
                }
            )
        )
        # Request AI to respond with the result
        await self.request_response()

    async def request_response(self):
        if not self.ws:
            return
        await self.ws.send(json.dumps({"type": "response.create"}))

    async def cancel_response(self):
        if not self.ws:
            return
        await self.ws.send(json.dumps({"type": "response.cancel"}))

    async def truncate_audio(self, item_id: str, content_index: int, audio_end_ms: int):
        if not self.ws:
            return
        await self.ws.send(
            json.dumps(
                {
                    "type": "conversation.item.truncate",
                    "item_id": item_id,
                    "content_index": content_index,
                    "audio_end_ms": audio_end_ms,
                }
            )
        )

    async def update_session(self, config: RealtimeSessionConfig):
        if not self.ws:
            return
        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": config.instructions,
                "voice": config.voice,
                "input_audio_format": config.input_audio_format,
                "output_audio_format": config.output_audio_format,
                "input_audio_transcription": config.input_audio_transcription,
                "turn_detection": config.turn_detection,
                "tools": config.tools,
                "tool_choice": "auto",
                "temperature": config.temperature,
                "max_response_output_tokens": config.max_response_output_tokens,
            },
        }
        await self.ws.send(json.dumps(session_update))

    async def inject_context(self, role: str, content: str):
        if not self.ws:
            return
        await self.ws.send(
            json.dumps(
                {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": role,
                        "content": [{"type": "input_text", "text": content}],
                    },
                }
            )
        )

    async def receive_events(self):
        """Main event loop - receives events from OpenAI and dispatches to handlers."""
        if not self.ws:
            return
        try:
            async for message in self.ws:
                try:
                    event_data = json.loads(message)
                    event_type = event_data.get("type", "")
                    event = RealtimeEvent(type=event_type, data=event_data, raw=event_data)

                    # Dispatch to registered handlers
                    handlers = self._event_handlers.get(event_type, [])
                    wildcard_handlers = self._event_handlers.get("*", [])

                    for handler in handlers + wildcard_handlers:
                        try:
                            await handler(event)
                        except Exception as e:
                            logger.error("event_handler_error", event_type=event_type, error=str(e))
                except json.JSONDecodeError:
                    logger.warning("invalid_json_from_openai")
        except websockets.exceptions.ConnectionClosed:
            logger.info("openai_realtime_connection_closed")
            self._connected = False
        except Exception as e:
            logger.error("openai_realtime_receive_error", error=str(e))
            self._connected = False

    def on_event(self, event_type: str, handler: Callable[[RealtimeEvent], Awaitable[None]]):
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    @property
    def is_connected(self) -> bool:
        return self._connected and self.ws is not None
