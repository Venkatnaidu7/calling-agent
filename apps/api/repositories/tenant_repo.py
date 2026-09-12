import re
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from apps.api.models import Tenant
from apps.api.schemas.common import PaginationParams
from apps.api.repositories.base import BaseRepository

class TenantRepository(BaseRepository[Tenant]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Tenant, session=session, tenant_id=None)

    def _generate_slug(self, name: str) -> str:
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')
        return slug

    async def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Tenant:
        if "slug" not in kwargs and "name" in kwargs:
            base_slug = self._generate_slug(kwargs["name"])
            slug = base_slug
            # Ensure uniqueness
            counter = 1
            while await self.get_by_slug(slug):
                slug = f"{base_slug}-{counter}"
                counter += 1
            kwargs["slug"] = slug
            
        return await super().create(**kwargs)
        
    async def get_by_status(self, status: str) -> list[Tenant]:
        stmt = select(Tenant).where(Tenant.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, pagination: PaginationParams) -> tuple[list[Tenant], int]:
        return await self.get_all(pagination)
