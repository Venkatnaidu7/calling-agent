from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    agent_id: UUID
    contact_list_id: UUID
    from_number: str
    status: str = "draft"
    priority: int = 5
    max_concurrent_calls: int = 1
    max_attempts: int = 3
    retry_delay_minutes: int = 60
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    calling_hours_start: str = "09:00"
    calling_hours_end: str = "17:00"
    calling_days: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    settings: Dict[str, Any] = Field(default_factory=dict)


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_id: Optional[UUID] = None
    contact_list_id: Optional[UUID] = None
    from_number: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    max_concurrent_calls: Optional[int] = None
    max_attempts: Optional[int] = None
    retry_delay_minutes: Optional[int] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    calling_hours_start: Optional[str] = None
    calling_hours_end: Optional[str] = None
    calling_days: Optional[List[int]] = None
    settings: Optional[Dict[str, Any]] = None


class CampaignResponse(CampaignBase):
    id: UUID
    tenant_id: UUID
    total_contacts: int
    contacted: int
    answered: int
    completed: int
    failed: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignCallBase(BaseModel):
    contact_id: UUID
    attempt_number: int = 1
    status: str = "pending"
    scheduled_at: Optional[datetime] = None


class CampaignCallCreate(CampaignCallBase):
    campaign_id: UUID


class CampaignCallUpdate(BaseModel):
    status: Optional[str] = None
    call_log_id: Optional[UUID] = None
    attempt_number: Optional[int] = None
    attempted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    error_message: Optional[str] = None


class CampaignCallResponse(CampaignCallBase):
    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    call_log_id: Optional[UUID] = None
    attempted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
