import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WebhookEndpointCreate(BaseModel):
    url: str = Field(..., description="Target HTTPS URL to receive webhooks")
    description: Optional[str] = None
    events: List[str] = Field(
        default_factory=lambda: ["*"], description="List of event types or ['*'] for all"
    )


class WebhookEndpointUpdate(BaseModel):
    url: Optional[str] = None
    description: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookEndpointResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    url: str
    description: Optional[str] = None
    events: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookEndpointWithSecretResponse(WebhookEndpointResponse):
    secret: str
