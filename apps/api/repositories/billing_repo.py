from uuid import UUID
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from apps.api.models.billing import Subscription, UsageRecord
from apps.api.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(model=Subscription, session=session, tenant_id=tenant_id)

    async def get_by_tenant(self, tenant_id: UUID) -> Optional[Subscription]:
        stmt = select(Subscription).where(Subscription.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_stripe_customer_id(self, customer_id: str) -> Optional[Subscription]:
        stmt = select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_stripe_subscription_id(self, sub_id: str) -> Optional[Subscription]:
        stmt = select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class UsageRecordRepository(BaseRepository[UsageRecord]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(model=UsageRecord, session=session, tenant_id=tenant_id)

    async def get_usage_for_period(
        self,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> Tuple[int, int, dict]:
        """Returns (total_minutes, total_cost_cents, breakdown_by_metric)."""
        stmt = (
            select(
                UsageRecord.metric,
                func.coalesce(func.sum(UsageRecord.quantity), 0),
                func.coalesce(func.sum(UsageRecord.total_cost_cents), 0),
            )
            .where(
                and_(
                    UsageRecord.tenant_id == tenant_id,
                    UsageRecord.created_at >= period_start,
                    UsageRecord.created_at <= period_end,
                )
            )
            .group_by(UsageRecord.metric)
        )

        result = await self.session.execute(stmt)
        breakdown = {}
        total_cost = 0
        total_minutes = 0

        for metric, qty, cost in result.all():
            breakdown[metric] = int(qty)
            total_cost += int(cost)
            if metric == "voice_minutes":
                total_minutes = int(qty)

        return total_minutes, total_cost, breakdown
