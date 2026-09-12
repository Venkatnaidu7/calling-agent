from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.models.phone_number import PhoneNumber
from apps.api.repositories.base import BaseRepository


class PhoneNumberRepository(BaseRepository[PhoneNumber]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(model=PhoneNumber, session=session, tenant_id=tenant_id)

    async def get_by_number(self, number: str) -> Optional[PhoneNumber]:
        stmt = select(PhoneNumber).where(PhoneNumber.number == number)
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_number_global(self, number: str) -> Optional[PhoneNumber]:
        """Look up phone number globally for inbound call routing."""
        stmt = select(PhoneNumber).where(PhoneNumber.number == number, PhoneNumber.is_active)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_agent(self, agent_id: UUID) -> List[PhoneNumber]:
        stmt = select(PhoneNumber).where(PhoneNumber.agent_id == agent_id, PhoneNumber.is_active)
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def assign_agent(self, phone_id: UUID, agent_id: Optional[UUID]) -> Optional[PhoneNumber]:
        return await self.update(phone_id, agent_id=agent_id)

    async def release_number(self, phone_id: UUID) -> Optional[PhoneNumber]:
        return await self.update(phone_id, is_active=False, status="released", agent_id=None)
