from abc import ABC, abstractmethod
from typing import Any, Callable, Awaitable
from dataclasses import dataclass, field


@dataclass
class RealtimeSessionConfig:
    """Configuration for a realtime AI voice session."""

    model: str = "gpt-4o-mini-realtime-preview"
    voice: str = "ash"
    instructions: str = ""
    input_audio_format: str = "g711_ulaw"
    output_audio_format: str = "g711_ulaw"
    temperature: float = 0.8
    max_response_output_tokens: int = 1024
    turn_detection: dict[str, Any] = field(
        default_factory=lambda: {
            "type": "server_vad",
            "threshold": 0.5,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 500,
            "create_response": True,
        }
    )
    tools: list[dict[str, Any]] = field(default_factory=list)
    input_audio_transcription: dict[str, Any] = field(
        default_factory=lambda: {"model": "whisper-1"}
    )


@dataclass
class RealtimeEvent:
    """An event from the realtime AI provider."""

    type: str
    data: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


class RealtimeAIProvider(ABC):
    """Abstract interface for realtime AI voice providers."""

    @abstractmethod
    async def connect(self, config: RealtimeSessionConfig) -> None:
        """Establish connection to the realtime AI service."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection."""
        ...

    @abstractmethod
    async def send_audio(self, audio_base64: str) -> None:
        """Send audio data to the AI."""
        ...

    @abstractmethod
    async def send_tool_result(self, call_id: str, result: str) -> None:
        """Send tool execution result back to the AI."""
        ...

    @abstractmethod
    async def request_response(self) -> None:
        """Request the AI to generate a response."""
        ...

    @abstractmethod
    async def cancel_response(self) -> None:
        """Cancel an in-progress response (for barge-in)."""
        ...

    @abstractmethod
    async def truncate_audio(self, item_id: str, content_index: int, audio_end_ms: int) -> None:
        """Truncate assistant audio to what was actually played (for barge-in)."""
        ...

    @abstractmethod
    async def update_session(self, config: RealtimeSessionConfig) -> None:
        """Update session configuration mid-call."""
        ...

    @abstractmethod
    async def inject_context(self, role: str, content: str) -> None:
        """Inject a conversation item (for customer context, knowledge, etc)."""
        ...

    @abstractmethod
    async def receive_events(self) -> None:
        """Start receiving events from the AI service. Should call registered handlers."""
        ...

    @abstractmethod
    def on_event(
        self, event_type: str, handler: Callable[[RealtimeEvent], Awaitable[None]]
    ) -> None:
        """Register an event handler for a specific event type."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool: ...
