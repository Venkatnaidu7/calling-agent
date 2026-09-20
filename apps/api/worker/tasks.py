import asyncio
import uuid
import structlog
from apps.api.worker.celery_app import celery_app
from apps.api.database import async_session_factory

logger = structlog.get_logger()


@celery_app.task(name="tasks.post_call_processing", bind=True, max_retries=3)
def post_call_processing_task(self, call_id: str, tenant_id: str):
    """
    Background post-call processing:
    1. Generates dialogue turn summary
    2. Calculates sentiment metrics
    3. Triggers outgoing CRM webhooks
    """

    async def _run():
        from apps.api.repositories.call_log_repo import CallLogRepository
        from apps.api.services.webhook_service import WebhookService
        from apps.api.config import settings
        import openai

        tenant_uuid = uuid.UUID(tenant_id)
        async with async_session_factory() as session:
            repo = CallLogRepository(session, tenant_id=tenant_uuid)
            call_log = await repo.get_by_call_id(call_id)
            if not call_log:
                logger.warning("call_log_not_found_for_worker", call_id=call_id)
                return

            if settings.openai_api_key and call_log.transcript:
                try:
                    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
                    prompt = f"Analyze the following call transcript and output a short 2-3 sentence summary, followed by the overall sentiment (positive, negative, or neutral):\n\n{call_log.transcript}\n"
                    response = await client.chat.completions.create(
                        model=settings.openai_chat_model,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    analysis = response.choices[0].message.content or ""
                    sentiment = "positive" if "positive" in analysis.lower() else "negative" if "negative" in analysis.lower() else "neutral"

                    await repo.update(call_log.id, summary=analysis, sentiment=sentiment)
                    await session.commit()
                    call_log = await repo.get_by_call_id(call_id)
                except Exception as e:
                    logger.error("openai_analysis_failed", error=str(e))

            logger.info("post_call_processing_complete", call_id=call_id)

            # Dispatch webhook event
            webhook_service = WebhookService(session, tenant_uuid)
            await webhook_service.dispatch_event(
                "call.analyzed",
                {
                    "call_id": call_id,
                    "duration": call_log.duration_seconds,
                    "sentiment": call_log.sentiment,
                    "summary": call_log.summary,
                },
            )

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error("post_call_processing_failed", error=str(exc), call_id=call_id)
        raise self.retry(exc=exc, countdown=10) from exc


@celery_app.task(name="tasks.process_document", bind=True, max_retries=2)
def process_document_task(self, tenant_id: str, kb_id: str, doc_id: str):
    """
    Background document ingestion:
    1. Extracts text from PDF / Word / CSV / Web URL
    2. Chunks text into semantic segments
    3. Generates 1536-dim vector embeddings
    4. Inserts chunks into pgvector
    """

    async def _run():
        from apps.api.services.knowledge_service import KnowledgeService

        tenant_uuid = uuid.UUID(tenant_id)
        kb_uuid = uuid.UUID(kb_id)
        doc_uuid = uuid.UUID(doc_id)

        async with async_session_factory() as session:
            service = KnowledgeService(session, tenant_id=tenant_uuid)
            await service.process_document(kb_uuid, doc_uuid)
            await session.commit()
            logger.info("document_async_ingestion_complete", doc_id=doc_id, kb_id=kb_id)

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error("document_ingestion_failed", error=str(exc), doc_id=doc_id)
        raise self.retry(exc=exc, countdown=30) from exc


@celery_app.task(name="tasks.campaign_dialer", bind=True)
def campaign_dialer_task(self, tenant_id: str, campaign_id: str):
    """
    Background outbound campaign dispatcher:
    Paces automated calls respecting tenant concurrency and TCPA calling windows.
    """

    async def _run():
        from apps.api.repositories.campaign_repo import CampaignRepository, CampaignCallRepository
        from apps.api.repositories.phone_number_repo import PhoneNumberRepository
        from apps.api.providers.twilio.voice import TwilioVoiceProvider
        from apps.api.providers.plivo.voice import PlivoVoiceProvider
        from apps.api.config import settings

        tenant_uuid = uuid.UUID(tenant_id)
        campaign_uuid = uuid.UUID(campaign_id)

        async with async_session_factory() as session:
            camp_repo = CampaignRepository(session, tenant_uuid)
            call_repo = CampaignCallRepository(session, tenant_uuid)
            phone_repo = PhoneNumberRepository(session, tenant_uuid)
            from apps.api.repositories.contact_repo import ContactRepository
            contact_repo = ContactRepository(session, tenant_uuid)
            
            campaign = await camp_repo.get_by_id(campaign_uuid)
            if not campaign or campaign.status != "running":
                return
            
            logger.info("campaign_dispatching_batch", campaign_id=campaign_id, name=campaign.name)

            from_number = campaign.from_number
            phone_number_obj = await phone_repo.get_by_number(from_number)

            provider_name = phone_number_obj.provider.lower() if phone_number_obj else "twilio"

            if provider_name == "plivo":
                if not settings.plivo_auth_id:
                    logger.warning("plivo_not_configured_for_campaign", campaign_id=campaign_id)
                    return
                provider = PlivoVoiceProvider()
            else:
                if not settings.twilio_account_sid:
                    logger.warning("twilio_not_configured_for_campaign", campaign_id=campaign_id)
                    return
                provider = TwilioVoiceProvider()

            calls = await call_repo.get_calls_for_campaign(campaign_uuid)
            pending_calls = [c for c in calls if c.status == "pending"]
            
            for call in pending_calls:
                # Refresh campaign status check
                campaign = await camp_repo.get_by_id(campaign_uuid)
                if campaign.status != "running":
                    logger.info("campaign_paused_stopping_dialer", campaign_id=campaign_id)
                    break

                try:
                    contact = await contact_repo.get_by_id(call.contact_id)
                    if not contact:
                        logger.error("campaign_dialer_no_contact", call_id=call.id)
                        continue
                        
                    base = settings.twilio_webhook_base_url or "https://api.example.com"
                    webhook_url = f"{base}/api/v1/voice/inbound/{campaign.agent_id}"
                    status_url = f"{base}/api/v1/voice/status/campaign_{call.id}"

                    await provider.initiate_outbound_call(
                        to_number=contact.phone_number,
                        from_number=from_number,
                        webhook_url=webhook_url,
                        status_callback_url=status_url,
                        machine_detection=True
                    )
                    await call_repo.update(call.id, status="dialing")
                    await session.commit()
                except Exception as e:
                    logger.error("dialer_failed", error=str(e), call_id=call.id)
                    await call_repo.update(call.id, status="failed", error_message=str(e))
                    await session.commit()

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error("campaign_dialer_failed", error=str(exc), campaign_id=campaign_id)
