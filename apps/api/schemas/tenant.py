from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class TenantCreate(BaseModel):
    name: str
    business_name: Optional[str] = None
    country: Optional[str] = Field(None, max_length=2)
    timezone: str = "UTC"

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    business_name: Optional[str] = None
    timezone: Optional[str] = None
    business_hours: Optional[Dict[str, Any]] = None
    compliance_settings: Optional[Dict[str, Any]] = None

class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    business_name: Optional[str]
    country: Optional[str]
    timezone: str
    status: str
    settings: Dict[str, Any]
    created_at: datetime
    
    model_config = {"from_attributes": True}

class TenantDetailResponse(TenantResponse):
    business_hours: Dict[str, Any]
    compliance_settings: Dict[str, Any]
