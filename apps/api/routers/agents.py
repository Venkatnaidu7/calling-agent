from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from apps.api.database import get_db
from apps.api.dependencies import get_current_user, get_tenant_context, require_roles
from apps.api.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentDetailResponse,
    AgentVersionCreate, AgentVersionUpdate, AgentVersionResponse,
    AgentVersionSummary, PublishAgentRequest, TestAgentRequest
)
from apps.api.schemas.common import PaginationParams
from apps.api.services.agent_service import AgentService
from apps.api.models.user import User

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

def get_agent_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)]
) -> AgentService:
    return AgentService(session, tenant_id)

@router.get("", response_model=list[AgentResponse])
async def list_agents(
    service: Annotated[AgentService, Depends(get_agent_service)],
    pagination: Annotated[PaginationParams, Depends()],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    return await service.list_agents(pagination)

@router.post("", response_model=AgentDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    return await service.create_agent(data)

@router.get("/{id}", response_model=AgentDetailResponse)
async def get_agent(
    id: UUID,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    return await service.get_agent(id)

@router.put("/{id}", response_model=AgentResponse)
async def update_agent(
    id: UUID,
    data: AgentUpdate,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    return await service.update_agent(id, data)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    id: UUID,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    await service.delete_agent(id)

@router.post("/{id}/versions", response_model=AgentVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    id: UUID,
    data: AgentVersionCreate,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    return await service.create_version(id, data)

@router.get("/{id}/versions", response_model=list[AgentVersionSummary])
async def list_versions(
    id: UUID,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    return await service.list_versions(id)

@router.get("/{id}/versions/{version_id}", response_model=AgentVersionResponse)
async def get_version(
    id: UUID,
    version_id: UUID,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    version = await service.get_version(version_id)
    if version.agent_id != id:
        raise HTTPException(status_code=400, detail="Version does not belong to this agent")
    return version

@router.put("/{id}/versions/{version_id}", response_model=AgentVersionResponse)
async def update_version(
    id: UUID,
    version_id: UUID,
    data: AgentVersionUpdate,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    version = await service.get_version(version_id)
    if version.agent_id != id:
        raise HTTPException(status_code=400, detail="Version does not belong to this agent")
    return await service.update_version(version_id, data)

@router.post("/{id}/versions/{version_id}/test", response_model=AgentVersionResponse)
async def set_version_testing(
    id: UUID,
    version_id: UUID,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    version = await service.get_version(version_id)
    if version.agent_id != id:
        raise HTTPException(status_code=400, detail="Version does not belong to this agent")
    return await service.set_version_testing(version_id)

@router.post("/{id}/publish", response_model=AgentVersionResponse)
async def publish_version(
    id: UUID,
    request: PublishAgentRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    return await service.publish_version(id, request.version_id, user.id)

@router.post("/{id}/rollback", response_model=AgentVersionResponse)
async def rollback_version(
    id: UUID,
    request: PublishAgentRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    user: Annotated[User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "AGENT_MANAGER"]))]
):
    # Reusing PublishAgentRequest since it just needs version_id
    return await service.rollback_version(id, request.version_id, user.id)
