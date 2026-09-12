from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from apps.api.models.campaign import Campaign, CampaignCall
from apps.api.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignCallCreate
from apps.api.schemas.common import PaginationParams
from apps.api.repositories.campaign_repo import CampaignRepository, CampaignCallRepository


class CampaignService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.campaign_repo = CampaignRepository(session, tenant_id)
        self.call_repo = CampaignCallRepository(session, tenant_id)

    async def get_campaign(self, campaign_id: UUID) -> Campaign:
        campaign = await self.campaign_repo.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return campaign

    async def create_campaign(self, data: CampaignCreate) -> Campaign:
        return await self.campaign_repo.create(**data.model_dump())

    async def update_campaign(self, campaign_id: UUID, data: CampaignUpdate) -> Campaign:
        campaign = await self.campaign_repo.update(
            campaign_id, **data.model_dump(exclude_unset=True)
        )
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return campaign

    async def list_campaigns(self, pagination: PaginationParams):
        return await self.campaign_repo.get_all(pagination)

    async def create_campaign_call(self, data: CampaignCallCreate) -> CampaignCall:
        return await self.call_repo.create(**data.model_dump())
