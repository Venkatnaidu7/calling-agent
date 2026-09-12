from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.models.billing import WebhookEndpoint
from apps.api.repositories.base import BaseRepository


class WebhookRepository(BaseRepository[WebhookEndpoint]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(model=WebhookEndpoint, session=session, tenant_id=tenant_id)

    async def get_active_endpoints(self, tenant_id: UUID) -> List[WebhookEndpoint]:
        stmt = select(WebhookEndpoint).where(
            WebhookEndpoint.tenant_id == tenant_id,
            WebhookEndpoint.is_active == True,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
