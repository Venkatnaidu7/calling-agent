from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from apps.api.database import get_db
from apps.api.dependencies import get_tenant_context, require_roles
from apps.api.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactListCreate,
    ContactListResponse,
    ContactListMemberCreate,
    ContactListMemberResponse,
)
from apps.api.schemas.common import PaginationParams
from apps.api.services.contact_service import ContactService
from apps.api.models.user import User

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


def get_contact_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)],
) -> ContactService:
    return ContactService(session, tenant_id)


@router.get("", response_model=list[ContactResponse])
async def list_contacts(
    service: Annotated[ContactService, Depends(get_contact_service)],
    pagination: Annotated[PaginationParams, Depends()],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CONTACT_MANAGER"]))
    ],
):
    items, total = await service.list_contacts(pagination)
    return items


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    service: Annotated[ContactService, Depends(get_contact_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CONTACT_MANAGER"]))
    ],
):
    return await service.create_contact(data)


@router.get("/{id}", response_model=ContactResponse)
async def get_contact(
    id: UUID,
    service: Annotated[ContactService, Depends(get_contact_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CONTACT_MANAGER"]))
    ],
):
    return await service.get_contact(id)


@router.put("/{id}", response_model=ContactResponse)
async def update_contact(
    id: UUID,
    data: ContactUpdate,
    service: Annotated[ContactService, Depends(get_contact_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CONTACT_MANAGER"]))
    ],
):
    return await service.update_contact(id, data)


@router.post("/lists", response_model=ContactListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    data: ContactListCreate,
    service: Annotated[ContactService, Depends(get_contact_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CONTACT_MANAGER"]))
    ],
):
    return await service.create_list(data)


@router.post(
    "/lists/{list_id}/members",
    response_model=ContactListMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_to_list(
    list_id: UUID,
    data: ContactListMemberCreate,
    service: Annotated[ContactService, Depends(get_contact_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CONTACT_MANAGER"]))
    ],
):
    return await service.add_to_list(list_id, data.contact_id)


@router.delete("/lists/{list_id}/members/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_list(
    list_id: UUID,
    contact_id: UUID,
    service: Annotated[ContactService, Depends(get_contact_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "CONTACT_MANAGER"]))
    ],
):
    success = await service.remove_from_list(list_id, contact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found in list")
