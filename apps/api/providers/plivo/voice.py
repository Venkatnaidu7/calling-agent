import asyncio
import structlog
import plivo
from plivo.utils import verify_signature
from xml.etree.ElementTree import Element, SubElement, tostring

from apps.api.providers.base.telephony import TelephonyProvider, CallResult, TransferResult
from apps.api.config import settings

logger = structlog.get_logger()


class PlivoVoiceProvider(TelephonyProvider):
    def __init__(self):
        if settings.plivo_auth_id and settings.plivo_auth_token:
            self.client = plivo.RestClient(settings.plivo_auth_id, settings.plivo_auth_token)
        else:
            self.client = None

    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        status_callback_url: str,
        machine_detection: bool = False,
        custom_parameters: dict[str, str] | None = None,
    ) -> CallResult:
        def _create_call():
            call_params = {
                "to_": to_number,
                "from_": from_number,
                "answer_url": webhook_url,
                "answer_method": "POST",
                "fallback_url": status_callback_url,
                "fallback_method": "POST",
            }
            if machine_detection:
                call_params["machine_detection"] = "true"
                call_params["machine_detection_url"] = status_callback_url
                call_params["machine_detection_method"] = "POST"
            
            # Plivo doesn't support custom params directly in the create call method in the same way,
            # but we can pass them in the answer_url as query params.
            if custom_parameters:
                import urllib.parse
                qs = urllib.parse.urlencode(custom_parameters)
                call_params["answer_url"] = f"{webhook_url}?{qs}"

            return self.client.calls.create(**call_params)

        try:
            response = await asyncio.to_thread(_create_call)
            # Plivo returns a response object with request_uuid
            return CallResult(
                provider_call_id=response.request_uuid,
                status="queued",
                from_number=from_number,
                to_number=to_number,
                metadata={"message": response.message},
            )
        except Exception as e:
            logger.error("plivo_outbound_call_failed", error=str(e), to=to_number)
            raise

    async def end_call(self, provider_call_id: str) -> bool:
        def _update():
            return self.client.calls.delete(provider_call_id)

        try:
            await asyncio.to_thread(_update)
            return True
        except Exception as e:
            logger.error("plivo_end_call_failed", error=str(e), call_id=provider_call_id)
            return False

    async def transfer_call_cold(
        self, provider_call_id: str, destination_number: str, announcement: str | None = None
    ) -> TransferResult:
        def _update():
            # Generate XML for transfer
            response = Element("Response")
            if announcement:
                speak = SubElement(response, "Speak")
                speak.text = announcement
            dial = SubElement(response, "Dial")
            number = SubElement(dial, "Number")
            number.text = destination_number
            
            twiml_str = tostring(response, encoding="unicode")
            return self.client.calls.transfer(provider_call_id, aleg_url="", aleg_method="POST", twiml=twiml_str)

        try:
            await asyncio.to_thread(_update)
            return TransferResult(
                success=True,
                provider_call_id=provider_call_id,
                transfer_type="cold",
                destination=destination_number,
            )
        except Exception as e:
            logger.error("plivo_cold_transfer_failed", error=str(e), call_id=provider_call_id)
            return TransferResult(
                success=False,
                provider_call_id=provider_call_id,
                transfer_type="cold",
                destination=destination_number,
                error=str(e),
            )

    async def transfer_call_warm(
        self, provider_call_id: str, destination_number: str, from_number: str, whisper_message: str | None = None
    ) -> TransferResult:
        # Simplified warm transfer (Plivo usually requires complex conference logic)
        # We will fallback to cold transfer logic for now or return error.
        return TransferResult(
            success=False,
            provider_call_id=provider_call_id,
            transfer_type="warm",
            destination=destination_number,
            error="Warm transfer not natively supported in this Plivo abstraction yet."
        )

    def generate_stream_twiml(
        self, websocket_url: str, custom_parameters: dict[str, str] | None = None
    ) -> str:
        """Generate Plivo XML for connecting a call to a media stream."""
        response = Element("Response")
        stream = SubElement(response, "Stream", url=websocket_url, bidirectional="true")
        
        if custom_parameters:
            for k, v in custom_parameters.items():
                param = SubElement(stream, "Parameter", name=k, value=str(v))
                
        return tostring(response, encoding="unicode")

    def validate_webhook_signature(
        self, url: str, params: dict[str, str], signature: str
    ) -> bool:
        if not settings.plivo_auth_token:
            return True
        return verify_signature(url, params, signature, settings.plivo_auth_token)
