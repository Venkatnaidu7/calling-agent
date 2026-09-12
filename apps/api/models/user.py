import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.database import Base
from apps.api.models.base import TenantMixin, TimestampMixin
from apps.api.models.tenant import Tenant

if TYPE_CHECKING:
    from apps.api.models.session import UserSession


class User(Base, TenantMixin, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False, default="READ_ONLY")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uix_tenant_email"),
        CheckConstraint(
            role.in_(
                [
                    "PLATFORM_ADMIN",
                    "TENANT_OWNER",
                    "TENANT_ADMIN",
                    "SUPERVISOR",
                    "AGENT_MANAGER",
                    "ANALYST",
                    "READ_ONLY",
                    "COMPLIANCE_MANAGER",
                    "CONTACT_MANAGER",
                    "CAMPAIGN_MANAGER",
                ]
            ),
            name="user_role_check",
        ),
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    sessions: Mapped[List["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
