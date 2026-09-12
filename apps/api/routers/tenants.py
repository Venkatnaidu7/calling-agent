from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.schemas.tenant import TenantUpdate, TenantResponse, TenantDetailResponse
from apps.api.schemas.common import PaginationParams, PaginatedResponse
from apps.api.services.tenant_service import TenantService
from apps.api.database import get_db
from apps.api.middleware.auth import require_roles, get_current_user
from apps.api.models import User

router = APIRouter(prefix="/api/v1", tags=["Tenants"])

# === Current tenant routes (must be before /{id} to avoid path conflicts) ===

@router.get("/tenant", response_model=TenantDetailResponse)
async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = TenantService(db)
    return await service.get_tenant(current_user.tenant_id)

@router.put("/tenant", response_model=TenantResponse)
async def update_current_tenant(
    data: TenantUpdate,
    current_user: User = Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    service = TenantService(db)
    return await service.update_tenant(current_user.tenant_id, data)

# === Admin tenant routes ===

@router.get("/tenants", response_model=PaginatedResponse[TenantResponse])
async def list_tenants(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles("PLATFORM_ADMIN"))
):
    service = TenantService(db)
    return await service.list_tenants(pagination)

@router.get("/tenants/{id}", response_model=TenantDetailResponse)
async def get_tenant(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles("PLATFORM_ADMIN"))
):
    service = TenantService(db)
    return await service.get_tenant(id)

@router.put("/tenants/{id}", response_model=TenantResponse)
async def update_tenant(
    id: UUID,
    data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles("PLATFORM_ADMIN"))
):
    service = TenantService(db)
    return await service.update_tenant(id, data)

@router.post("/tenants/{id}/suspend", status_code=status.HTTP_204_NO_CONTENT)
async def suspend_tenant(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles("PLATFORM_ADMIN"))
):
    service = TenantService(db)
    await service.suspend_tenant(id)

@router.post("/tenants/{id}/reactivate", status_code=status.HTTP_204_NO_CONTENT)
async def reactivate_tenant(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles("PLATFORM_ADMIN"))
):
    service = TenantService(db)
    await service.reactivate_tenant(id)
