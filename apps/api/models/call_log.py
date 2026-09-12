import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from apps.api.database import Base
from apps.api.models.base import TimestampMixin, TenantMixin


class CallLog(Base, TenantMixin, TimestampMixin):
    __tablename__ = "call_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    call_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )  # our internal call ID
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    agent_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    phone_number_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("phone_numbers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # inbound, outbound
    from_number: Mapped[str] = mapped_column(String(20), nullable=False)
    to_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="initiated", server_default="initiated"
    )
    # initiated, ringing, in_progress, completed, failed, busy, no_answer, cancelled
    provider_call_sid: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    recording_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transcript: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # [{"speaker": "customer"|"agent", "text": "...", "timestamp": "..."}, ...]
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # positive, neutral, negative
    cost_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    transfer_to: Mapped[str | None] = mapped_column(String(20), nullable=True)
    transfer_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_calls: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")

    __table_args__ = (
        CheckConstraint("direction IN ('inbound', 'outbound')", name="call_direction_check"),
        CheckConstraint(
            "status IN ('initiated', 'ringing', 'in_progress', 'completed', 'failed', 'busy', 'no_answer', 'cancelled')",
            name="call_status_check",
        ),
    )
