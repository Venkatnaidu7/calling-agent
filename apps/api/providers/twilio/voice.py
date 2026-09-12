import asyncio
import structlog
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from apps.api.providers.base.telephony import TelephonyProvider, CallResult, TransferResult
from apps.api.config import settings

logger = structlog.get_logger()


class TwilioVoiceProvider(TelephonyProvider):
    def __init__(self):
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.validator = RequestValidator(settings.twilio_auth_token)

    async def initiate_outbound_call(
        self,
        to_number,
        from_number,
        webhook_url,
        status_callback_url,
        machine_detection=False,
        custom_parameters=None,
    ):
        def _create_call():
            call_params = {
                "to": to_number,
                "from_": from_number,
                "url": webhook_url,
                "status_callback": status_callback_url,
                "status_callback_event": ["initiated", "ringing", "answered", "completed"],
            }
            if machine_detection:
                call_params["machine_detection"] = "Enable"
                call_params["async_amd"] = "true"

            return self.client.calls.create(**call_params)

        try:
            call = await asyncio.to_thread(_create_call)
            return CallResult(
                provider_call_id=call.sid,
                status=call.status,
                from_number=from_number,
                to_number=to_number,
                metadata={"uri": call.uri},
            )
        except Exception as e:
            logger.error("twilio_outbound_call_failed", error=str(e), to=to_number)
            raise

    async def end_call(self, provider_call_id):
        def _update():
            return self.client.calls(provider_call_id).update(status="completed")

        try:
            await asyncio.to_thread(_update)
            return True
        except Exception as e:
            logger.error("twilio_end_call_failed", error=str(e), call_id=provider_call_id)
            return False

    async def transfer_call_cold(self, provider_call_id, destination_number, announcement=None):
        def _update():
            response = VoiceResponse()
            if announcement:
                response.say(announcement)
            response.dial(destination_number)
            return self.client.calls(provider_call_id).update(twiml=str(response))

        try:
            call = await asyncio.to_thread(_update)
            return TransferResult(
                success=True,
                provider_call_id=call.sid,
                transfer_type="cold",
                destination=destination_number,
            )
        except Exception as e:
            logger.error("twilio_cold_transfer_failed", error=str(e), call_id=provider_call_id)
            return TransferResult(
                success=False,
                provider_call_id=provider_call_id,
                transfer_type="cold",
                destination=destination_number,
                error=str(e),
            )

    async def transfer_call_warm(
        self, provider_call_id, destination_number, from_number, whisper_message=None
    ):
        def _warm_transfer():
            conference_name = f"conf_{provider_call_id}"

            # Put original caller in conference
            response = VoiceResponse()
            response.dial().conference(conference_name)
            self.client.calls(provider_call_id).update(twiml=str(response))

            # Dial the agent to the same conference
            agent_response = VoiceResponse()
            if whisper_message:
                agent_response.say(whisper_message)
            agent_response.dial().conference(conference_name)

            twiml_str = str(agent_response)

            agent_call = self.client.calls.create(
                to=destination_number, from_=from_number, twiml=twiml_str
            )
            return agent_call

        try:
            await asyncio.to_thread(_warm_transfer)
            return TransferResult(
                success=True,
                provider_call_id=provider_call_id,
                transfer_type="warm",
                destination=destination_number,
            )
        except Exception as e:
            logger.error("twilio_warm_transfer_failed", error=str(e), call_id=provider_call_id)
            return TransferResult(
                success=False,
                provider_call_id=provider_call_id,
                transfer_type="warm",
                destination=destination_number,
                error=str(e),
            )

    def generate_stream_twiml(self, websocket_url, custom_parameters=None):
        response = VoiceResponse()
        connect = Connect()
        stream = Stream(url=websocket_url)
        if custom_parameters:
            for k, v in custom_parameters.items():
                stream.parameter(name=k, value=str(v))
        connect.append(stream)
        response.append(connect)
        return str(response)

    def validate_webhook_signature(self, url, params, signature):
        return self.validator.validate(url, params, signature)
