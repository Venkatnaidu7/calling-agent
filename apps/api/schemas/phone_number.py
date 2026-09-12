import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PhoneNumberBase(BaseModel):
    number: str = Field(..., description="Phone number in E.164 format, e.g. +14155552671")
    friendly_name: Optional[str] = None
    agent_id: Optional[uuid.UUID] = None
    capabilities: Dict[str, Any] = Field(default_factory=lambda: {"voice": True, "sms": True})


class PhoneNumberCreate(PhoneNumberBase):
    provider: str = "twilio"
    provider_sid: Optional[str] = None


class PhoneNumberUpdate(BaseModel):
    friendly_name: Optional[str] = None
    agent_id: Optional[uuid.UUID] = None
    capabilities: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class PhoneNumberAssign(BaseModel):
    agent_id: Optional[uuid.UUID] = None


class PhoneNumberResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    number: str
    provider: str
    provider_sid: Optional[str] = None
    agent_id: Optional[uuid.UUID] = None
    friendly_name: Optional[str] = None
    capabilities: Dict[str, Any]
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
