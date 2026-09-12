from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.models.compliance import DNCEntry, ConsentRecord
from apps.api.repositories.base import BaseRepository

class DNCRepository(BaseRepository[DNCEntry]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | None = None):
        super().__init__(DNCEntry, session, tenant_id)

    async def get_by_phone(self, phone_number: str) -> DNCEntry | None:
        stmt = select(self.model).where(
            self.model.phone_number == phone_number,
            self.model.is_active == True
        )
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

class ConsentRepository(BaseRepository[ConsentRecord]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | None = None):
        super().__init__(ConsentRecord, session, tenant_id)
        
    async def get_consent(self, phone_number: str, consent_type: str) -> ConsentRecord | None:
        stmt = select(self.model).where(
            self.model.phone_number == phone_number,
            self.model.consent_type == consent_type,
            self.model.status == 'granted'
        )
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
