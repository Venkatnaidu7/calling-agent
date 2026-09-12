import uuid
from typing import Any, List

from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from apps.api.database import Base
from apps.api.models.base import TimestampMixin

class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    business_name: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    timezone: Mapped[str] = mapped_column(String, default="UTC", server_default="UTC")
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="'{}'")
    business_hours: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="'{}'")
    compliance_settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="'{}'")

    __table_args__ = (
        CheckConstraint(status.in_(['active', 'suspended', 'cancelled']), name='tenant_status_check'),
    )

    users: Mapped[List["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    api_keys: Mapped[List["ApiKey"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
