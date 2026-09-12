from uuid import UUID
from typing import Annotated, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.database import get_db
from apps.api.dependencies import get_tenant_context, require_roles
from apps.api.models.user import User
from apps.api.schemas.webhook import WebhookEndpointCreate, WebhookEndpointResponse, WebhookEndpointWithSecretResponse
from apps.api.services.webhook_service import WebhookService

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks & Integrations"])


def get_webhook_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)],
) -> WebhookService:
    return WebhookService(session, tenant_id)


@router.get("", response_model=List[WebhookEndpointResponse])
async def list_webhook_endpoints(
    service: Annotated[WebhookService, Depends(get_webhook_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))],
):
    """List configured outgoing webhook destinations."""
    return await service.list_endpoints()


@router.post("", response_model=WebhookEndpointWithSecretResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_endpoint(
    data: WebhookEndpointCreate,
    service: Annotated[WebhookService, Depends(get_webhook_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))],
):
    """Create a new webhook endpoint and receive the signing secret."""
    return await service.create_endpoint(data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_endpoint(
    id: UUID,
    service: Annotated[WebhookService, Depends(get_webhook_service)],
    user: Annotated[User, Depends(require_roles("TENANT_OWNER", "TENANT_ADMIN"))],
):
    """Remove a webhook endpoint."""
    await service.delete_endpoint(id)
