import uuid
from datetime import datetime
from typing import Any, List

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from apps.api.database import Base
from apps.api.models.base import TimestampMixin, TenantMixin


class Agent(Base, TenantMixin, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    published_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # currently published version

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published', 'archived')", name="agent_status_check"),
    )

    versions: Mapped[List["AgentVersion"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by="AgentVersion.version_number.desc()",
    )


class AgentVersion(Base, TenantMixin, TimestampMixin):
    __tablename__ = "agent_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")

    # Agent Configuration (stored as structured JSONB)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # agent display name for this version
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)  # personality description
    voice: Mapped[str] = mapped_column(
        String(50), default="ash"
    )  # OpenAI voice: alloy, echo, shimmer, ash, ballad, coral, sage, verse
    language: Mapped[str] = mapped_column(String(10), default="en")  # primary language
    languages: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default='["en"]'
    )  # supported languages

    # Instructions & Context
    system_instructions: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # agent-specific instructions
    business_context: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # business info injected into context
    greeting_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # first message on call connect

    # Objectives & Behavior
    objectives: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")
    fallback_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # message when AI fails
    max_call_duration_seconds: Mapped[int] = mapped_column(Integer, default=1800)  # 30 min default

    # Knowledge Configuration
    knowledge_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    # e.g. {"enabled": true, "max_chunks": 5, "relevance_threshold": 0.7}

    # Tool Permissions
    tool_permissions: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    # e.g. {"check_availability": true, "book_appointment": true, "send_sms": false}

    # Transfer Rules
    transfer_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")
    # e.g. {"enabled": true, "conditions": ["customer_requested", "emergency"], "default_number": "+1555..."}

    # Business Hours
    business_hours: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")

    # Compliance
    compliance_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    # e.g. {"ai_disclosure": "always", "recording_policy": "enabled_after_disclosure"}

    # Turn Detection Settings
    turn_detection_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    # e.g. {"type": "server_vad", "threshold": 0.5, "silence_duration_ms": 500, "prefix_padding_ms": 300}

    # Loop Protection
    loop_protection_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    # e.g. {"max_misunderstandings": 3, "max_tool_failures": 3, "action": "transfer"}

    # Publishing metadata
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("agent_id", "version_number", name="uix_agent_version"),
        CheckConstraint(
            "status IN ('draft', 'testing', 'published', 'archived')",
            name="agent_version_status_check",
        ),
    )

    agent: Mapped["Agent"] = relationship(back_populates="versions")
