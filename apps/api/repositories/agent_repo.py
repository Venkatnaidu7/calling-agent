from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from apps.api.models.agent import Agent, AgentVersion
from apps.api.schemas.common import PaginationParams
from apps.api.repositories.base import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(model=Agent, session=session, tenant_id=tenant_id)

    async def get_with_versions(self, agent_id: UUID) -> Agent | None:
        stmt = select(Agent).options(selectinload(Agent.versions)).where(Agent.id == agent_id)
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_published_for_phone(self, phone_number_tenant_id: UUID, agent_id: UUID) -> Agent | None:
        """Get published agent for a phone number (used in inbound calls)."""
        stmt = select(Agent).where(
            Agent.id == agent_id,
            Agent.tenant_id == phone_number_tenant_id,
            Agent.status == 'published',
            Agent.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class AgentVersionRepository(BaseRepository[AgentVersion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(model=AgentVersion, session=session, tenant_id=tenant_id)

    async def get_latest_version_number(self, agent_id: UUID) -> int:
        stmt = select(func.coalesce(func.max(AgentVersion.version_number), 0)).where(
            AgentVersion.agent_id == agent_id
        )
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_published_version(self, agent_id: UUID) -> AgentVersion | None:
        stmt = select(AgentVersion).where(
            AgentVersion.agent_id == agent_id,
            AgentVersion.status == 'published'
        )
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_versions(self, agent_id: UUID) -> list[AgentVersion]:
        stmt = select(AgentVersion).where(
            AgentVersion.agent_id == agent_id
        ).order_by(AgentVersion.version_number.desc())
        stmt = self._apply_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_version_by_id(self, version_id: UUID) -> AgentVersion | None:
        return await self.get_by_id(version_id)
