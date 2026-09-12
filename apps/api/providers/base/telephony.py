from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

@dataclass
class CallResult:
    provider_call_id: str
    status: str
    from_number: str
    to_number: str
    metadata: dict[str, Any] = None

@dataclass
class TransferResult:
    success: bool
    provider_call_id: str
    transfer_type: str  # 'cold' or 'warm'
    destination: str
    error: str | None = None


class TelephonyProvider(ABC):
    """Abstract interface for telephony providers. Implement this for each provider (Twilio, etc)."""

    @abstractmethod
    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        status_callback_url: str,
        machine_detection: bool = False,
        custom_parameters: dict[str, str] | None = None,
    ) -> CallResult:
        """Initiate an outbound call."""
        ...

    @abstractmethod
    async def end_call(self, provider_call_id: str) -> bool:
        """End an active call."""
        ...

    @abstractmethod
    async def transfer_call_cold(
        self,
        provider_call_id: str,
        destination_number: str,
        announcement: str | None = None,
    ) -> TransferResult:
        """Cold (blind) transfer - redirect call to destination."""
        ...

    @abstractmethod
    async def transfer_call_warm(
        self,
        provider_call_id: str,
        destination_number: str,
        from_number: str,
        whisper_message: str | None = None,
    ) -> TransferResult:
        """Warm (attended) transfer using a conference bridge."""
        ...

    @abstractmethod
    def generate_stream_twiml(
        self,
        websocket_url: str,
        custom_parameters: dict[str, str] | None = None,
    ) -> str:
        """Generate TwiML for connecting a call to a media stream."""
        ...

    @abstractmethod
    def validate_webhook_signature(
        self,
        url: str,
        params: dict[str, str],
        signature: str,
    ) -> bool:
        """Validate incoming webhook request signature."""
        ...
