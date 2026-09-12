from uuid import UUID
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.database import get_db
from apps.api.dependencies import get_tenant_context, require_roles
from apps.api.models.user import User
from apps.api.schemas.analytics import AnalyticsDashboardResponse
from apps.api.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


def get_analytics_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)],
) -> AnalyticsService:
    return AnalyticsService(session, tenant_id)


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_dashboard_analytics(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN", "SUPERVISOR", "AGENT_MANAGER", "ANALYST"))],
    days: int = Query(default=30, ge=1, le=365),
    agent_id: Optional[UUID] = None,
):
    """Retrieve comprehensive call metrics, sentiment analysis, daily volume, and agent performance."""
    return await service.get_dashboard_metrics(days=days, agent_id=agent_id)
