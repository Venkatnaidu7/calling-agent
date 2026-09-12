from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.agent import Agent, AgentVersion
from apps.api.schemas.agent import (
    AgentCreate, AgentUpdate, AgentVersionCreate, AgentVersionUpdate
)
from apps.api.repositories.agent_repo import AgentRepository, AgentVersionRepository
from apps.api.schemas.common import PaginationParams
from datetime import datetime, timezone

class AgentService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.agent_repo = AgentRepository(session, tenant_id)
        self.version_repo = AgentVersionRepository(session, tenant_id)

    async def create_agent(self, data: AgentCreate) -> Agent:
        agent = Agent(
            tenant_id=self.tenant_id,
            name=data.name,
            description=data.description,
            status="draft"
        )
        self.session.add(agent)
        await self.session.flush()

        version = AgentVersion(
            agent_id=agent.id,
            tenant_id=self.tenant_id,
            version_number=1,
            status="draft",
            name=data.name,
        )
        self.session.add(version)
        await self.session.commit()
        
        return await self.get_agent(agent.id)

    async def get_agent(self, agent_id: UUID) -> Agent:
        agent = await self.agent_repo.get_with_versions(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent

    async def list_agents(self, pagination: PaginationParams) -> list[Agent]:
        items, _ = await self.agent_repo.get_all(pagination)
        return items

    async def update_agent(self, agent_id: UUID, data: AgentUpdate) -> Agent:
        agent = await self.get_agent(agent_id)
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(agent, k, v)
        await self.session.commit()
        return agent

    async def delete_agent(self, agent_id: UUID):
        agent = await self.get_agent(agent_id)
        agent.is_active = False
        agent.status = "archived"
        await self.session.commit()

    async def create_version(self, agent_id: UUID, data: AgentVersionCreate) -> AgentVersion:
        agent = await self.get_agent(agent_id)
        latest_version_num = await self.version_repo.get_latest_version_number(agent_id)
        
        version = AgentVersion(
            agent_id=agent.id,
            tenant_id=self.tenant_id,
            version_number=latest_version_num + 1,
            status="draft",
            **data.model_dump()
        )
        self.session.add(version)
        await self.session.commit()
        return version

    async def list_versions(self, agent_id: UUID) -> list[AgentVersion]:
        agent = await self.get_agent(agent_id) # ensures it exists and belongs to tenant
        return await self.version_repo.list_versions(agent.id)

    async def get_version(self, version_id: UUID) -> AgentVersion:
        version = await self.version_repo.get_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Agent version not found")
        return version

    async def update_version(self, version_id: UUID, data: AgentVersionUpdate) -> AgentVersion:
        version = await self.get_version(version_id)
        if version.status != 'draft':
            raise HTTPException(status_code=400, detail="Only draft versions can be updated")
            
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(version, k, v)
        await self.session.commit()
        return version

    async def set_version_testing(self, version_id: UUID) -> AgentVersion:
        version = await self.get_version(version_id)
        if version.status != 'draft':
            raise HTTPException(status_code=400, detail="Only draft versions can be moved to testing")
        version.status = 'testing'
        await self.session.commit()
        return version

    async def publish_version(self, agent_id: UUID, version_id: UUID, user_id: UUID) -> AgentVersion:
        agent = await self.get_agent(agent_id)
        version = await self.get_version(version_id)
        
        if version.agent_id != agent.id:
            raise HTTPException(status_code=400, detail="Version does not belong to this agent")
            
        if version.status not in ['draft', 'testing']:
            raise HTTPException(status_code=400, detail="Only draft or testing versions can be published")
            
        # Archive currently published version
        current_published = await self.version_repo.get_published_version(agent_id)
        if current_published:
            current_published.status = 'archived'
            
        version.status = 'published'
        version.published_at = datetime.now(timezone.utc)
        version.published_by = user_id
        
        agent.published_version_id = version.id
        agent.status = 'published'
        
        await self.session.commit()
        return version

    async def rollback_version(self, agent_id: UUID, target_version_id: UUID, user_id: UUID) -> AgentVersion:
        agent = await self.get_agent(agent_id)
        version = await self.get_version(target_version_id)
        
        if version.agent_id != agent.id:
            raise HTTPException(status_code=400, detail="Version does not belong to this agent")
            
        if version.status != 'archived':
            raise HTTPException(status_code=400, detail="Can only rollback to archived versions")
            
        current_published = await self.version_repo.get_published_version(agent_id)
        if current_published:
            current_published.status = 'archived'
            
        version.status = 'published'
        version.published_at = datetime.now(timezone.utc)
        version.published_by = user_id
        
        agent.published_version_id = version.id
        agent.status = 'published'
        
        await self.session.commit()
        return version
