from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from apps.api.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse, TenantDetailResponse
from apps.api.schemas.common import PaginationParams, PaginatedResponse
from apps.api.repositories.tenant_repo import TenantRepository


class TenantService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tenant_repo = TenantRepository(session)

    async def create_tenant(self, data: TenantCreate) -> TenantResponse:
        tenant = await self.tenant_repo.create(**data.model_dump(exclude_unset=True))
        await self.session.commit()
        return TenantResponse.model_validate(tenant)

    async def get_tenant(self, id: UUID) -> TenantDetailResponse:
        tenant = await self.tenant_repo.get_by_id(id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return TenantDetailResponse.model_validate(tenant)

    async def update_tenant(self, id: UUID, data: TenantUpdate) -> TenantResponse:
        tenant = await self.tenant_repo.update(id, **data.model_dump(exclude_unset=True))
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        await self.session.commit()
        return TenantResponse.model_validate(tenant)

    async def suspend_tenant(self, id: UUID) -> None:
        tenant = await self.tenant_repo.update(id, status="suspended")
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        await self.session.commit()

    async def reactivate_tenant(self, id: UUID) -> None:
        tenant = await self.tenant_repo.update(id, status="active")
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        await self.session.commit()

    async def list_tenants(self, pagination: PaginationParams) -> PaginatedResponse[TenantResponse]:
        items, total = await self.tenant_repo.list_all(pagination)
        pages = (total + pagination.per_page - 1) // pagination.per_page if total > 0 else 0
        return PaginatedResponse(
            items=[TenantResponse.model_validate(i) for i in items],
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            pages=pages,
        )
