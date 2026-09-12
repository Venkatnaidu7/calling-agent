from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.schemas.user import UserCreate, UserUpdate, UserResponse
from apps.api.schemas.common import PaginationParams, PaginatedResponse
from apps.api.services.user_service import UserService
from apps.api.database import get_db
from apps.api.models.user import User
from apps.api.middleware.auth import require_roles, require_permissions
from apps.api.middleware.tenant import get_tenant_context

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(),
    tenant_id: UUID = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_permissions("view_all"))
):
    service = UserService(db, tenant_id)
    return await service.list_users(pagination)

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    tenant_id: UUID = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))
):
    # Prevent privilege escalation
    if data.role == "PLATFORM_ADMIN" and current_user.role != "PLATFORM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign PLATFORM_ADMIN role",
        )
    if data.role == "TENANT_OWNER" and current_user.role not in ("TENANT_OWNER", "PLATFORM_ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owners can assign TENANT_OWNER role",
        )
    service = UserService(db, tenant_id)
    return await service.create_user(data)

@router.get("/{id}", response_model=UserResponse)
async def get_user(
    id: UUID,
    tenant_id: UUID = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_permissions("view_all"))
):
    service = UserService(db, tenant_id)
    return await service.get_user(id)

@router.put("/{id}", response_model=UserResponse)
async def update_user(
    id: UUID,
    data: UserUpdate,
    tenant_id: UUID = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))
):
    service = UserService(db, tenant_id)
    return await service.update_user(id, data)

@router.put("/{id}/role", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_role(
    id: UUID,
    role_data: dict, # Expecting {"role": "TENANT_ADMIN"}
    tenant_id: UUID = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("TENANT_OWNER", "PLATFORM_ADMIN"))
):
    """Update a user's role. Strictly restricted to Owners and Platform Admins."""
    new_role = role_data.get("role")
    if not new_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role is required")
    if new_role == "PLATFORM_ADMIN" and current_user.role != "PLATFORM_ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot assign PLATFORM_ADMIN role")
    service = UserService(db, tenant_id)
    return await service.change_role(id, new_role)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    id: UUID,
    tenant_id: UUID = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))
):
    service = UserService(db, tenant_id)
    await service.deactivate_user(id)
