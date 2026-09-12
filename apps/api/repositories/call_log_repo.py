from uuid import UUID
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from apps.api.models.call_log import CallLog
from apps.api.schemas.call_log import CallLogFilter
from apps.api.schemas.common import PaginationParams
from apps.api.repositories.base import BaseRepository


class CallLogRepository(BaseRepository[CallLog]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(model=CallLog, session=session, tenant_id=tenant_id)

    async def get_by_call_id(self, call_id: str) -> Optional[CallLog]:
        stmt = select(CallLog).where(CallLog.call_id == call_id)
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_provider_call_sid(self, provider_call_sid: str) -> Optional[CallLog]:
        stmt = select(CallLog).where(CallLog.provider_call_sid == provider_call_sid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_filter(
        self,
        filters: CallLogFilter,
        pagination: PaginationParams,
    ) -> Tuple[List[CallLog], int]:
        conditions = []
        if self.tenant_id:
            conditions.append(CallLog.tenant_id == self.tenant_id)
        if filters.direction:
            conditions.append(CallLog.direction == filters.direction)
        if filters.status:
            conditions.append(CallLog.status == filters.status)
        if filters.agent_id:
            conditions.append(CallLog.agent_id == filters.agent_id)
        if filters.campaign_id:
            conditions.append(CallLog.campaign_id == filters.campaign_id)
        if filters.from_number:
            conditions.append(CallLog.from_number == filters.from_number)
        if filters.to_number:
            conditions.append(CallLog.to_number == filters.to_number)
        if filters.date_from:
            conditions.append(CallLog.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(CallLog.created_at <= filters.date_to)

        where_clause = and_(*conditions) if conditions else True

        count_stmt = select(func.count()).select_from(CallLog).where(where_clause)
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar_one()

        stmt = (
            select(CallLog)
            .where(where_clause)
            .order_by(CallLog.created_at.desc())
            .offset(pagination.skip)
            .limit(pagination.limit)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_stats(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        conditions = []
        if self.tenant_id:
            conditions.append(CallLog.tenant_id == self.tenant_id)
        if date_from:
            conditions.append(CallLog.created_at >= date_from)
        if date_to:
            conditions.append(CallLog.created_at <= date_to)

        where_clause = and_(*conditions) if conditions else True

        # Total counts, duration, and costs
        stmt = select(
            func.count(CallLog.id),
            func.coalesce(func.sum(CallLog.duration_seconds), 0),
            func.coalesce(func.avg(CallLog.duration_seconds), 0.0),
            func.coalesce(func.sum(CallLog.cost_cents), 0),
        ).where(where_clause)
        res = await self.session.execute(stmt)
        total_calls, total_dur, avg_dur, total_cost = res.one()

        # Breakdown by status
        status_stmt = (
            select(CallLog.status, func.count(CallLog.id))
            .where(where_clause)
            .group_by(CallLog.status)
        )
        status_res = await self.session.execute(status_stmt)
        by_status = {row[0]: row[1] for row in status_res.all()}

        # Breakdown by direction
        dir_stmt = (
            select(CallLog.direction, func.count(CallLog.id))
            .where(where_clause)
            .group_by(CallLog.direction)
        )
        dir_res = await self.session.execute(dir_stmt)
        by_direction = {row[0]: row[1] for row in dir_res.all()}

        # Breakdown by sentiment
        sent_stmt = (
            select(func.coalesce(CallLog.sentiment, "unknown"), func.count(CallLog.id))
            .where(where_clause)
            .group_by(CallLog.sentiment)
        )
        sent_res = await self.session.execute(sent_stmt)
        by_sentiment = {row[0]: row[1] for row in sent_res.all()}

        return {
            "total_calls": total_calls,
            "total_duration_seconds": int(total_dur),
            "avg_duration_seconds": float(avg_dur),
            "total_cost_cents": int(total_cost),
            "by_status": by_status,
            "by_direction": by_direction,
            "by_sentiment": by_sentiment,
        }
