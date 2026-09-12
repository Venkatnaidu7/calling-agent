from uuid import UUID
from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.database import get_db
from apps.api.dependencies import get_tenant_context, require_roles
from apps.api.models.user import User
from apps.api.schemas.call_log import (
    CallLogFilter,
    CallLogResponse,
    CallTranscriptResponse,
    CallStatsResponse,
)
from apps.api.schemas.common import PaginationParams, PaginatedResponse
from apps.api.services.call_log_service import CallLogService

router = APIRouter(prefix="/api/v1/calls", tags=["Call Logs"])


def get_call_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)],
) -> CallLogService:
    return CallLogService(session, tenant_id)


@router.get("", response_model=PaginatedResponse[CallLogResponse])
async def list_call_logs(
    service: Annotated[CallLogService, Depends(get_call_service)],
    pagination: Annotated[PaginationParams, Depends()],
    user: Annotated[
        User,
        Depends(
            require_roles(
                "TENANT_OWNER",
                "TENANT_ADMIN",
                "SUPERVISOR",
                "AGENT_MANAGER",
                "ANALYST",
                "READ_ONLY",
            )
        ),
    ],
    direction: Optional[str] = None,
    status: Optional[str] = None,
    agent_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
    from_number: Optional[str] = None,
    to_number: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    filters = CallLogFilter(
        direction=direction,
        status=status,
        agent_id=agent_id,
        campaign_id=campaign_id,
        from_number=from_number,
        to_number=to_number,
        date_from=date_from,
        date_to=date_to,
    )
    return await service.list_logs(filters, pagination)


@router.get("/stats", response_model=CallStatsResponse)
async def get_call_statistics(
    service: Annotated[CallLogService, Depends(get_call_service)],
    user: Annotated[
        User,
        Depends(
            require_roles(
                "TENANT_OWNER",
                "TENANT_ADMIN",
                "SUPERVISOR",
                "AGENT_MANAGER",
                "ANALYST",
                "READ_ONLY",
            )
        ),
    ],
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    return await service.get_stats(date_from=date_from, date_to=date_to)


@router.get("/{call_id}", response_model=CallLogResponse)
async def get_call_detail(
    call_id: str,
    service: Annotated[CallLogService, Depends(get_call_service)],
    user: Annotated[
        User,
        Depends(
            require_roles(
                "TENANT_OWNER",
                "TENANT_ADMIN",
                "SUPERVISOR",
                "AGENT_MANAGER",
                "ANALYST",
                "READ_ONLY",
            )
        ),
    ],
):
    return await service.get_log(call_id)


@router.get("/{call_id}/transcript", response_model=CallTranscriptResponse)
async def get_call_transcript(
    call_id: str,
    service: Annotated[CallLogService, Depends(get_call_service)],
    user: Annotated[
        User,
        Depends(
            require_roles(
                "TENANT_OWNER",
                "TENANT_ADMIN",
                "SUPERVISOR",
                "AGENT_MANAGER",
                "ANALYST",
                "READ_ONLY",
            )
        ),
    ],
):
    return await service.get_transcript(call_id)
