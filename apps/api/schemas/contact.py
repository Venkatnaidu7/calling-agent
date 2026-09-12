from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class ContactBase(BaseModel):
    phone_number: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    timezone: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    status: str = "active"
    do_not_call: bool = False


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    phone_number: Optional[str] = None
    status: Optional[str] = None
    do_not_call: Optional[bool] = None


class ContactResponse(ContactBase):
    id: UUID
    tenant_id: UUID
    last_contacted_at: Optional[datetime] = None
    total_calls: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactListBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class ContactListCreate(ContactListBase):
    pass


class ContactListUpdate(ContactListBase):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class ContactListResponse(ContactListBase):
    id: UUID
    tenant_id: UUID
    contact_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactListMemberBase(BaseModel):
    contact_id: UUID


class ContactListMemberCreate(ContactListMemberBase):
    pass


class ContactListMemberResponse(ContactListMemberBase):
    id: UUID
    tenant_id: UUID
    contact_list_id: UUID
    added_at: datetime

    class Config:
        from_attributes = True
