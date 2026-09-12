from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class DNCEntryBase(BaseModel):
    phone_number: str
    source: str
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True

class DNCEntryCreate(DNCEntryBase):
    pass

class DNCEntryUpdate(BaseModel):
    is_active: Optional[bool] = None
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None

class DNCEntryResponse(DNCEntryBase):
    id: UUID
    tenant_id: UUID
    added_by: Optional[UUID] = None
    added_at: datetime

    class Config:
        from_attributes = True

class ConsentRecordBase(BaseModel):
    phone_number: str
    consent_type: str
    status: str
    source: str
    contact_id: Optional[UUID] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)

class ConsentRecordCreate(ConsentRecordBase):
    pass

class ConsentRecordUpdate(BaseModel):
    status: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None

class ConsentRecordResponse(ConsentRecordBase):
    id: UUID
    tenant_id: UUID
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    class Config:
        from_attributes = True
