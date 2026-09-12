import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from apps.api.database import Base
from apps.api.models.base import TimestampMixin, TenantMixin

class DNCEntry(Base, TenantMixin):
    __tablename__ = "dnc_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # manual, opt_out, federal, state
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    added_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (
        Index('ix_dnc_phone_tenant', 'tenant_id', 'phone_number', unique=True),
        CheckConstraint("source IN ('manual', 'opt_out', 'federal', 'state', 'imported')", name='dnc_source_check'),
    )

class ConsentRecord(Base, TenantMixin):
    __tablename__ = "consent_records"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    consent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # call, sms, recording, ai_disclosure
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # granted, revoked
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # verbal, written, electronic, imported
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict, server_default='{}')
    # e.g. {"call_id": "...", "timestamp": "...", "recording_url": "..."}
    __table_args__ = (
        CheckConstraint("consent_type IN ('call', 'sms', 'recording', 'ai_disclosure')", name='consent_type_check'),
        CheckConstraint("status IN ('granted', 'revoked')", name='consent_status_check'),
    )
