from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from apps.api.models.call_log import CallLog
from apps.api.models.agent import Agent
from apps.api.schemas.analytics import (
    AnalyticsDashboardResponse,
    OverviewMetrics,
    SentimentBreakdown,
    DailyCallVolume,
    AgentPerformanceMetrics,
)


class AnalyticsService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def get_dashboard_metrics(
        self,
        days: int = 30,
        agent_id: Optional[UUID] = None,
    ) -> AnalyticsDashboardResponse:
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=days)

        conditions = [CallLog.tenant_id == self.tenant_id, CallLog.created_at >= since]
        if agent_id:
            conditions.append(CallLog.agent_id == agent_id)

        where_clause = and_(*conditions)

        # 1. Overview
        stmt = select(
            func.count(CallLog.id),
            func.coalesce(func.sum(CallLog.duration_seconds), 0),
            func.coalesce(func.avg(CallLog.duration_seconds), 0.0),
            func.coalesce(func.sum(CallLog.cost_cents), 0),
        ).where(where_clause)
        res = await self.session.execute(stmt)
        total_calls, total_dur, avg_dur, total_cost = res.one()

        completed_stmt = select(func.count(CallLog.id)).where(and_(where_clause, CallLog.status == "completed"))
        completed_calls = (await self.session.execute(completed_stmt)).scalar_one()

        failed_stmt = select(func.count(CallLog.id)).where(and_(where_clause, CallLog.status.in_(["failed", "cancelled"])))
        failed_calls = (await self.session.execute(failed_stmt)).scalar_one()

        comp_rate = (completed_calls / total_calls * 100.0) if total_calls > 0 else 0.0

        overview = OverviewMetrics(
            total_calls=total_calls,
            completed_calls=completed_calls,
            failed_calls=failed_calls,
            completion_rate_percent=round(comp_rate, 1),
            total_duration_minutes=round(total_dur / 60.0, 1),
            avg_duration_seconds=round(float(avg_dur), 1),
            estimated_cost_dollars=round(total_cost / 100.0, 2),
        )

        # 2. Sentiment
        sent_stmt = select(CallLog.sentiment, func.count(CallLog.id)).where(where_clause).group_by(CallLog.sentiment)
        sent_res = await self.session.execute(sent_stmt)
        sent_map = {r[0]: r[1] for r in sent_res.all()}

        sentiment = SentimentBreakdown(
            positive=sent_map.get("positive", 0),
            neutral=sent_map.get("neutral", 0),
            negative=sent_map.get("negative", 0),
            unknown=sent_map.get(None, 0) + sent_map.get("unknown", 0),
        )

        # 3. Daily volume
        date_trunc = func.date_trunc('day', CallLog.created_at)
        daily_stmt = select(
            date_trunc,
            CallLog.direction,
            func.count(CallLog.id),
            func.coalesce(func.sum(CallLog.duration_seconds), 0),
        ).where(where_clause).group_by(date_trunc, CallLog.direction).order_by(date_trunc.asc())

        daily_res = await self.session.execute(daily_stmt)
        day_buckets = {}
        for dt, direction, count, dur in daily_res.all():
            day_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)[:10]
            if day_str not in day_buckets:
                day_buckets[day_str] = {"inbound": 0, "outbound": 0, "dur": 0}
            if direction == "inbound":
                day_buckets[day_str]["inbound"] += count
            else:
                day_buckets[day_str]["outbound"] += count
            day_buckets[day_str]["dur"] += dur

        daily_volume = [
            DailyCallVolume(
                date=d,
                inbound_count=v["inbound"],
                outbound_count=v["outbound"],
                total_minutes=round(v["dur"] / 60.0, 1),
            )
            for d, v in sorted(day_buckets.items())
        ]

        # 4. Agent performance
        agent_perf_stmt = select(
            Agent.id,
            Agent.name,
            func.count(CallLog.id),
            func.coalesce(func.avg(CallLog.duration_seconds), 0.0),
        ).join(CallLog, CallLog.agent_id == Agent.id).where(where_clause).group_by(Agent.id, Agent.name)

        agent_perf_res = await self.session.execute(agent_perf_stmt)
        agent_performance = []

        for aid, aname, acalls, aavg in agent_perf_res.all():
            # calculate positive sentiment
            pos_stmt = select(func.count(CallLog.id)).where(
                and_(where_clause, CallLog.agent_id == aid, CallLog.sentiment == "positive")
            )
            pos_count = (await self.session.execute(pos_stmt)).scalar_one()
            pos_pct = (pos_count / acalls * 100.0) if acalls > 0 else 0.0

            agent_performance.append(
                AgentPerformanceMetrics(
                    agent_id=aid,
                    agent_name=aname,
                    total_calls=acalls,
                    avg_duration_seconds=round(float(aavg), 1),
                    positive_sentiment_percent=round(pos_pct, 1),
                    tool_calls_count=0,
                )
            )

        return AnalyticsDashboardResponse(
            overview=overview,
            sentiment=sentiment,
            daily_volume=daily_volume,
            agent_performance=agent_performance,
        )
