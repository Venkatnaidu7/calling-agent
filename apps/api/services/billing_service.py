import secrets
import structlog
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import stripe

from apps.api.config import settings
from apps.api.models.billing import Subscription, UsageRecord
from apps.api.models.tenant import Tenant
from apps.api.schemas.billing import (
    SubscriptionResponse,
    CreateCheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerPortalResponse,
    UsageSummaryResponse,
    PlanTier,
)
from apps.api.repositories.billing_repo import SubscriptionRepository, UsageRecordRepository
from apps.api.repositories.tenant_repo import TenantRepository

logger = structlog.get_logger()

PLANS: Dict[str, PlanTier] = {
    "starter": PlanTier(
        id="starter",
        name="Starter Plan",
        price_monthly_dollars=49,
        monthly_minutes=300,
        concurrency_limit=2,
        features=["1 Phone Number", "300 Included Voice Minutes", "OpenAI Realtime Voice", "Basic Analytics"],
    ),
    "pro": PlanTier(
        id="pro",
        name="Professional Plan",
        price_monthly_dollars=199,
        monthly_minutes=1500,
        concurrency_limit=5,
        features=["5 Phone Numbers", "1500 Included Voice Minutes", "Knowledge Base RAG", "Custom Integrations", "Full Analytics"],
    ),
    "enterprise": PlanTier(
        id="enterprise",
        name="Enterprise Plan",
        price_monthly_dollars=599,
        monthly_minutes=5000,
        concurrency_limit=20,
        features=["Unlimited Phone Numbers", "5000 Included Voice Minutes", "Dedicated Account Manager", "Custom LLM Fine-tuning", "SLA 99.9%"],
    ),
}


class BillingService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.sub_repo = SubscriptionRepository(session, tenant_id=tenant_id)
        self.usage_repo = UsageRecordRepository(session, tenant_id=tenant_id)
        self.tenant_repo = TenantRepository(session)
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key

    async def get_or_create_subscription(self) -> SubscriptionResponse:
        sub = await self.sub_repo.get_by_tenant(self.tenant_id)
        now = datetime.now(timezone.utc)
        if not sub:
            # Create default trialing subscription
            sub = await self.sub_repo.create(
                tenant_id=self.tenant_id,
                plan_tier="starter",
                status="trialing",
                trial_ends_at=now + timedelta(days=14),
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
                monthly_minute_limit=PLANS["starter"].monthly_minutes,
                concurrency_limit=PLANS["starter"].concurrency_limit,
            )
            await self.session.commit()

        start = sub.current_period_start or now - timedelta(days=30)
        end = sub.current_period_end or now + timedelta(days=30)
        minutes_used, _, _ = await self.usage_repo.get_usage_for_period(self.tenant_id, start, end)

        resp = SubscriptionResponse.model_validate(sub)
        resp.minutes_used_this_period = minutes_used
        return resp

    async def create_checkout_session(self, data: CreateCheckoutSessionRequest) -> CheckoutSessionResponse:
        plan = PLANS.get(data.plan_tier)
        if not plan:
            raise HTTPException(status_code=400, detail="Invalid plan tier")

        tenant = await self.tenant_repo.get_by_id(self.tenant_id)
        sub = await self.sub_repo.get_by_tenant(self.tenant_id)

        customer_id = sub.stripe_customer_id if sub and sub.stripe_customer_id else None

        if not settings.stripe_secret_key:
            # Mock checkout session for development
            session_id = f"mock_session_{secrets.token_hex(8)}"
            return CheckoutSessionResponse(
                checkout_url=f"{data.success_url}?session_id={session_id}",
                session_id=session_id,
            )

        try:
            if not customer_id:
                customer = await stripe.Customer.create_async(
                    name=tenant.name if tenant else "Tenant",
                    metadata={"tenant_id": str(self.tenant_id)},
                )
                customer_id = customer.id
                if sub:
                    await self.sub_repo.update(sub.id, stripe_customer_id=customer_id)
                    await self.session.commit()

            checkout = await stripe.checkout.Session.create_async(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": f"AI Calling Platform - {plan.name}"},
                            "unit_amount": plan.price_monthly_dollars * 100,
                            "recurring": {"interval": "month"},
                        },
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=data.success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=data.cancel_url,
                metadata={"tenant_id": str(self.tenant_id), "plan_tier": data.plan_tier},
            )
            return CheckoutSessionResponse(checkout_url=checkout.url, session_id=checkout.id)
        except Exception as e:
            logger.error("stripe_checkout_error", error=str(e))
            raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

    async def create_customer_portal(self, return_url: str) -> CustomerPortalResponse:
        sub = await self.sub_repo.get_by_tenant(self.tenant_id)
        if not sub or not sub.stripe_customer_id:
            raise HTTPException(status_code=400, detail="No active Stripe customer found")

        if not settings.stripe_secret_key:
            return CustomerPortalResponse(portal_url=return_url)

        try:
            portal = await stripe.billing_portal.Session.create_async(
                customer=sub.stripe_customer_id,
                return_url=return_url,
            )
            return CustomerPortalResponse(portal_url=portal.url)
        except Exception as e:
            logger.error("stripe_portal_error", error=str(e))
            raise HTTPException(status_code=500, detail=f"Stripe portal error: {str(e)}")

    async def check_usage_limit(self) -> bool:
        """Check if the tenant has exceeded their monthly voice minute limit."""
        sub = await self.sub_repo.get_by_tenant(self.tenant_id)
        if not sub:
            return False  # Default to allowing calls if no subscription found (trialing)

        now = datetime.now(timezone.utc)
        start = sub.current_period_start or now - timedelta(days=30)
        end = sub.current_period_end or now + timedelta(days=30)

        minutes_used, _, _ = await self.usage_repo.get_usage_for_period(self.tenant_id, start, end)

        if minutes_used >= sub.monthly_minute_limit:
            logger.warning("usage_limit_exceeded", tenant_id=self.tenant_id, used=minutes_used, limit=sub.monthly_minute_limit)
            return True

        return False
        rate_cents = 5  # default 5 cents per minute
        total_cents = rate_cents * quantity if metric == "voice_minutes" else 0

        record = await self.usage_repo.create(
            tenant_id=self.tenant_id,
            call_id=call_id,
            metric=metric,
            quantity=quantity,
            unit_cost_cents=rate_cents,
            total_cost_cents=total_cents,
            metadata_json=metadata or {},
        )
        await self.session.commit()
        return record

    async def get_usage_summary(self) -> UsageSummaryResponse:
        sub = await self.sub_repo.get_by_tenant(self.tenant_id)
        now = datetime.now(timezone.utc)
        start = sub.current_period_start if sub and sub.current_period_start else now - timedelta(days=30)
        end = sub.current_period_end if sub and sub.current_period_end else now + timedelta(days=30)

        total_min, total_cost, breakdown = await self.usage_repo.get_usage_for_period(self.tenant_id, start, end)

        return UsageSummaryResponse(
            tenant_id=self.tenant_id,
            period_start=start,
            period_end=end,
            total_minutes_used=total_min,
            minute_limit=sub.monthly_minute_limit if sub else 300,
            total_cost_cents=total_cost,
            by_metric=breakdown,
        )
