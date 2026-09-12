from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.models.campaign import Campaign, CampaignCall
from apps.api.repositories.base import BaseRepository

class CampaignRepository(BaseRepository[Campaign]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | None = None):
        super().__init__(Campaign, session, tenant_id)

class CampaignCallRepository(BaseRepository[CampaignCall]):
    def __init__(self, session: AsyncSession, tenant_id: UUID | None = None):
        super().__init__(CampaignCall, session, tenant_id)

    async def get_calls_for_campaign(self, campaign_id: UUID):
        stmt = select(self.model).where(self.model.campaign_id == campaign_id)
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
