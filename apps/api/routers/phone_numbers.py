from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.database import get_db
from apps.api.dependencies import get_tenant_context, require_roles
from apps.api.models.user import User
from apps.api.schemas.phone_number import PhoneNumberCreate, PhoneNumberUpdate, PhoneNumberAssign, PhoneNumberResponse
from apps.api.schemas.common import PaginationParams, PaginatedResponse
from apps.api.services.phone_number_service import PhoneNumberService

router = APIRouter(prefix="/api/v1/phone-numbers", tags=["Phone Numbers"])


def get_phone_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)],
) -> PhoneNumberService:
    return PhoneNumberService(session, tenant_id)


@router.get("", response_model=PaginatedResponse[PhoneNumberResponse])
async def list_phone_numbers(
    service: Annotated[PhoneNumberService, Depends(get_phone_service)],
    pagination: Annotated[PaginationParams, Depends()],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER", "ANALYST", "READ_ONLY"))],
):
    return await service.list_numbers(pagination)


@router.post("", response_model=PhoneNumberResponse, status_code=status.HTTP_201_CREATED)
async def provision_phone_number(
    data: PhoneNumberCreate,
    service: Annotated[PhoneNumberService, Depends(get_phone_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))],
):
    return await service.provision_number(data)


@router.get("/{id}", response_model=PhoneNumberResponse)
async def get_phone_number(
    id: UUID,
    service: Annotated[PhoneNumberService, Depends(get_phone_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER", "ANALYST", "READ_ONLY"))],
):
    return await service.get_number(id)


@router.put("/{id}", response_model=PhoneNumberResponse)
async def update_phone_number(
    id: UUID,
    data: PhoneNumberUpdate,
    service: Annotated[PhoneNumberService, Depends(get_phone_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"))],
):
    return await service.update_number(id, data)


@router.post("/{id}/assign", response_model=PhoneNumberResponse)
async def assign_agent_to_number(
    id: UUID,
    data: PhoneNumberAssign,
    service: Annotated[PhoneNumberService, Depends(get_phone_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"))],
):
    return await service.assign_to_agent(id, data.agent_id)


@router.post("/{id}/release", status_code=status.HTTP_204_NO_CONTENT)
async def release_phone_number(
    id: UUID,
    service: Annotated[PhoneNumberService, Depends(get_phone_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))],
):
    await service.release_number(id)
