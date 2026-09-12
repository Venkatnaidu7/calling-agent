import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from apps.api.database import Base
from apps.api.models.base import TimestampMixin, TenantMixin


class Subscription(Base, TenantMixin, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    plan_tier: Mapped[str] = mapped_column(
        String(50), default="starter", server_default="starter"
    )  # starter, pro, enterprise
    status: Mapped[str] = mapped_column(String(30), default="trialing", server_default="trialing")
    # trialing, active, past_due, canceled, incomplete
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    monthly_minute_limit: Mapped[int] = mapped_column(Integer, default=500, server_default="500")
    concurrency_limit: Mapped[int] = mapped_column(Integer, default=2, server_default="2")

    __table_args__ = (
        CheckConstraint(
            "status IN ('trialing', 'active', 'past_due', 'canceled', 'incomplete')",
            name="subscription_status_check",
        ),
    )


class UsageRecord(Base, TenantMixin):
    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    call_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    metric: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # voice_minutes, llm_tokens, phone_number, tool_call
    quantity: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    unit_cost_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_cost_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, server_default="NOW()", index=True
    )


class WebhookEndpoint(Base, TenantMixin, TimestampMixin):
    __tablename__ = "webhook_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    events: Mapped[list] = mapped_column(JSONB, default=list, server_default='["*"]')
    # e.g. ["call.completed", "contact.created", "appointment.booked"]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
