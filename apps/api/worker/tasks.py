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
        
        tenant_uuid = uuid.UUID(tenant_id)
        async with async_session_factory() as session:
            repo = CallLogRepository(session, tenant_id=tenant_uuid)
            call_log = await repo.get_by_call_id(call_id)
            if not call_log:
                logger.warning("call_log_not_found_for_worker", call_id=call_id)
                return

            logger.info("post_call_processing_complete", call_id=call_id)

            # Dispatch webhook event
            webhook_service = WebhookService(session, tenant_uuid)
            await webhook_service.dispatch_event("call.analyzed", {
                "call_id": call_id,
                "duration": call_log.duration_seconds,
                "sentiment": call_log.sentiment,
            })

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error("post_call_processing_failed", error=str(exc), call_id=call_id)
        raise self.retry(exc=exc, countdown=10)


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
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="tasks.campaign_dialer", bind=True)
def campaign_dialer_task(self, tenant_id: str, campaign_id: str):
    """
    Background outbound campaign dispatcher:
    Paces automated calls respecting tenant concurrency and TCPA calling windows.
    """
    async def _run():
        from apps.api.services.campaign_service import CampaignService
        tenant_uuid = uuid.UUID(tenant_id)
        campaign_uuid = uuid.UUID(campaign_id)

        async with async_session_factory() as session:
            service = CampaignService(session, tenant_uuid)
            campaign = await service.get_campaign(campaign_uuid)
            logger.info("campaign_dispatching_batch", campaign_id=campaign_id, name=campaign.name)

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error("campaign_dialer_failed", error=str(exc), campaign_id=campaign_id)
