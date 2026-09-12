from typing import Optional, List
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime
from apps.api.schemas.tenant import TenantResponse

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    email_verified: bool
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    
    model_config = {"from_attributes": True}

class UserDetailResponse(UserResponse):
    tenant: TenantResponse

class CurrentUserResponse(UserDetailResponse):
    permissions: List[str] = []
