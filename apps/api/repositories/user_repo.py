from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from apps.api.models import User
from apps.api.schemas.common import PaginationParams
from apps.api.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | None = None):
        super().__init__(model=User, session=session, tenant_id=tenant_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_global(self, email: str) -> User | None:
        """For login - searches across tenants. Ignores tenant_id context."""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_by_tenant(self, pagination: PaginationParams) -> tuple[list[User], int]:
        return await self.get_all(pagination)

    async def count_by_tenant(self) -> int:
        stmt = select(func.count()).select_from(User)
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one()
