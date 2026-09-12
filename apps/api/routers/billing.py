from uuid import UUID
from typing import Annotated, Dict
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from urllib.parse import urlparse
from apps.api.config import settings

from apps.api.database import get_db
from apps.api.dependencies import get_tenant_context, require_roles
from apps.api.models.user import User
from apps.api.schemas.billing import (
    SubscriptionResponse,
    CreateCheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerPortalResponse,
    UsageSummaryResponse,
    PlanTier,
)
from apps.api.services.billing_service import BillingService, PLANS

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/billing", tags=["Billing & Subscriptions"])


def get_billing_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)],
) -> BillingService:
    return BillingService(session, tenant_id)


@router.get("/plans", response_model=Dict[str, PlanTier])
async def list_plans():
    """List available subscription plans."""
    return PLANS


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    service: Annotated[BillingService, Depends(get_billing_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))],
):
    """Get active subscription and limits for current tenant."""
    return await service.get_or_create_subscription()


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    data: CreateCheckoutSessionRequest,
    service: Annotated[BillingService, Depends(get_billing_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))],
):
    """Initiate Stripe checkout for plan upgrade."""
    return await service.create_checkout_session(data)


@router.post("/portal", response_model=CustomerPortalResponse)
async def open_customer_portal(
    return_url: str,
    service: Annotated[BillingService, Depends(get_billing_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))],
):
    """Generate Stripe billing portal URL to manage payment methods & invoices."""
    parsed = urlparse(return_url)
    if parsed.netloc and parsed.netloc not in [urlparse(o).netloc for o in settings.cors_origins if o]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid return_url: must match an approved origin or be a relative path."
        )
    return await service.create_customer_portal(return_url)


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    service: Annotated[BillingService, Depends(get_billing_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN", "ANALYST"))],
):
    """Get monthly voice minutes and usage breakdown."""
    return await service.get_usage_summary()


@router.post("/stripe-webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook_handler(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive and process Stripe subscription lifecycle events with cryptographic signature verification."""
    import stripe
    from apps.api.config import settings
    from apps.api.repositories.billing_repo import SubscriptionRepository

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.stripe_webhook_secret or not sig_header:
        logger.error("stripe_webhook_missing_credentials")
        return Response(content="Missing webhook secret or signature", status_code=400)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except Exception as e:
        logger.error("stripe_webhook_signature_failed", error=str(e))
        return Response(content="Invalid signature", status_code=400)

    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {})

    logger.info("stripe_webhook_processing", event_type=event_type)

    sub_repo = SubscriptionRepository(db)

    if event_type == "checkout.session.completed":
        tenant_id = data_object.get("metadata", {}).get("tenant_id")
        plan_tier = data_object.get("metadata", {}).get("plan_tier", "pro")
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("subscription")

        if tenant_id:
            import uuid
            t_uuid = uuid.UUID(tenant_id)
            sub = await sub_repo.get_by_tenant(t_uuid)
            if sub:
                await sub_repo.update(
                    sub.id,
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id,
                    plan_tier=plan_tier,
                    status="active",
                )
                await db.commit()
                logger.info("subscription_activated_from_checkout", tenant_id=tenant_id, plan=plan_tier)

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        subscription_id = data_object.get("id")
        status_val = data_object.get("status")
        cancel_at_end = data_object.get("cancel_at_period_end", False)

        sub = await sub_repo.get_by_stripe_subscription_id(subscription_id)
        if sub:
            await sub_repo.update(
                sub.id,
                status="canceled" if event_type == "customer.subscription.deleted" else status_val,
                cancel_at_period_end=cancel_at_end,
            )
            await db.commit()
            logger.info("subscription_updated", sub_id=subscription_id, status=status_val)

    return {"status": "success"}
