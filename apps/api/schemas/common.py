from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    request_id: Optional[str] = None

class SuccessResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None

class UUIDSchema(BaseModel):
    id: uuid.UUID

class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None
