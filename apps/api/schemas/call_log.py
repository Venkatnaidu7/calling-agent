import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class CallLogFilter(BaseModel):
    direction: Optional[str] = None
    status: Optional[str] = None
    agent_id: Optional[uuid.UUID] = None
    campaign_id: Optional[uuid.UUID] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class CallLogResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    call_id: str
    agent_id: Optional[uuid.UUID] = None
    agent_version_id: Optional[uuid.UUID] = None
    phone_number_id: Optional[uuid.UUID] = None
    direction: str
    from_number: str
    to_number: str
    status: str
    provider_call_sid: Optional[str] = None
    duration_seconds: int
    recording_url: Optional[str] = None
    recording_duration: Optional[int] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    cost_cents: int
    started_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    campaign_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None
    transfer_to: Optional[str] = None
    transfer_reason: Optional[str] = None
    error_message: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class CallLogSummary(BaseModel):
    id: uuid.UUID
    call_id: str
    agent_id: Optional[uuid.UUID] = None
    direction: str
    from_number: str
    to_number: str
    status: str
    duration_seconds: int
    sentiment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CallTranscriptResponse(BaseModel):
    call_id: str
    transcript: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None


class CallStatsResponse(BaseModel):
    total_calls: int
    total_duration_seconds: int
    avg_duration_seconds: float
    total_cost_cents: int
    by_status: Dict[str, int]
    by_direction: Dict[str, int]
    by_sentiment: Dict[str, int]
