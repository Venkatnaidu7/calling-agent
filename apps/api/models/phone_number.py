import uuid
from sqlalchemy import String, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from apps.api.database import Base
from apps.api.models.base import TimestampMixin, TenantMixin


class PhoneNumber(Base, TenantMixin, TimestampMixin):
    __tablename__ = "phone_numbers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)  # E.164 format
    provider: Mapped[str] = mapped_column(String(20), default="twilio", server_default="twilio")
    provider_sid: Mapped[str | None] = mapped_column(String(100), nullable=True)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    friendly_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    capabilities: Mapped[dict] = mapped_column(JSONB, default=dict, server_default='{}')
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    __table_args__ = (
        CheckConstraint("status IN ('active', 'suspended', 'released')", name='phone_number_status_check'),
    )
