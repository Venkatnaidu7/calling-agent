from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from apps.api.database import get_db
from apps.api.dependencies import get_tenant_context, require_roles
from apps.api.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignCallCreate,
    CampaignCallResponse,
)
from apps.api.schemas.common import PaginationParams
from apps.api.services.campaign_service import CampaignService
from apps.api.models.user import User

router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])


def get_campaign_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)],
) -> CampaignService:
    return CampaignService(session, tenant_id)


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    pagination: Annotated[PaginationParams, Depends()],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CAMPAIGN_MANAGER"]))
    ],
):
    items, total = await service.list_campaigns(pagination)
    return items


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CAMPAIGN_MANAGER"]))
    ],
):
    return await service.create_campaign(data)


@router.get("/{id}", response_model=CampaignResponse)
async def get_campaign(
    id: UUID,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CAMPAIGN_MANAGER"]))
    ],
):
    return await service.get_campaign(id)


@router.put("/{id}", response_model=CampaignResponse)
async def update_campaign(
    id: UUID,
    data: CampaignUpdate,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CAMPAIGN_MANAGER"]))
    ],
):
    return await service.update_campaign(id, data)


@router.post("/calls", response_model=CampaignCallResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign_call(
    data: CampaignCallCreate,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CAMPAIGN_MANAGER"]))
    ],
):
    return await service.create_campaign_call(data)
