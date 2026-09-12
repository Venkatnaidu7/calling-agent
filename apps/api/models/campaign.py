import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import String, Integer, Boolean, DateTime, Text, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from apps.api.database import Base
from apps.api.models.base import TimestampMixin, TenantMixin

class Campaign(Base, TenantMixin, TimestampMixin):
    __tablename__ = "campaigns"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    contact_list_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contact_lists.id", ondelete="CASCADE"), nullable=False)
    from_number: Mapped[str] = mapped_column(String(20), nullable=False)  # Caller ID
    status: Mapped[str] = mapped_column(String(20), default="draft")
    # draft, scheduled, running, paused, completed, cancelled
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1=highest, 10=lowest
    max_concurrent_calls: Mapped[int] = mapped_column(Integer, default=1)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay_minutes: Mapped[int] = mapped_column(Integer, default=60)
    # Schedule
    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    calling_hours_start: Mapped[str] = mapped_column(String(5), default="09:00")  # HH:MM in contact timezone
    calling_hours_end: Mapped[str] = mapped_column(String(5), default="17:00")
    calling_days: Mapped[list] = mapped_column(JSONB, default=lambda: [1,2,3,4,5], server_default='[1,2,3,4,5]')
    # 1=Mon..7=Sun
    # Stats
    total_contacts: Mapped[int] = mapped_column(Integer, default=0)
    contacted: Mapped[int] = mapped_column(Integer, default=0)
    answered: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default='{}')
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'scheduled', 'running', 'paused', 'completed', 'cancelled')", name='campaign_status_check'),
    )

class CampaignCall(Base, TenantMixin):
    __tablename__ = "campaign_calls"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    call_log_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending, dialing, answered, completed, failed, skipped, dnc
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'dialing', 'answered', 'completed', 'failed', 'skipped', 'dnc')", name='campaign_call_status_check'),
    )
