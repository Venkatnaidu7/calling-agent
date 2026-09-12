"""call_infrastructure

Revision ID: 003
Revises: 002
Create Date: 2026-09-09 16:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create phone_numbers table
    op.create_table(
        "phone_numbers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("number", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=20), server_default="twilio", nullable=False),
        sa.Column("provider_sid", sa.String(length=100), nullable=True),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("friendly_name", sa.String(length=100), nullable=True),
        sa.Column(
            "capabilities",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'released')", name="phone_number_status_check"
        ),
    )
    op.create_index("ix_phone_numbers_tenant_id", "phone_numbers", ["tenant_id"])
    op.create_index("ix_phone_numbers_number", "phone_numbers", ["number"], unique=True)
    op.create_index("ix_phone_numbers_agent_id", "phone_numbers", ["agent_id"])

    # Create call_logs table
    op.create_table(
        "call_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("call_id", sa.String(length=50), nullable=False),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("agent_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "phone_number_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("phone_numbers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("from_number", sa.String(length=20), nullable=False),
        sa.Column("to_number", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="initiated", nullable=False),
        sa.Column("provider_call_sid", sa.String(length=100), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("recording_url", sa.Text(), nullable=True),
        sa.Column("recording_duration", sa.Integer(), nullable=True),
        sa.Column("transcript", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("sentiment", sa.String(length=20), nullable=True),
        sa.Column("cost_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transfer_to", sa.String(length=20), nullable=True),
        sa.Column("transfer_reason", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "tool_calls",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.CheckConstraint("direction IN ('inbound', 'outbound')", name="call_direction_check"),
        sa.CheckConstraint(
            "status IN ('initiated', 'ringing', 'in_progress', 'completed', 'failed', 'busy', 'no_answer', 'cancelled')",
            name="call_status_check",
        ),
    )
    op.create_index("ix_call_logs_tenant_id", "call_logs", ["tenant_id"])
    op.create_index("ix_call_logs_call_id", "call_logs", ["call_id"], unique=True)
    op.create_index("ix_call_logs_agent_id", "call_logs", ["agent_id"])
    op.create_index("ix_call_logs_phone_number_id", "call_logs", ["phone_number_id"])
    op.create_index("ix_call_logs_provider_call_sid", "call_logs", ["provider_call_sid"])
    op.create_index("ix_call_logs_campaign_id", "call_logs", ["campaign_id"])
    op.create_index("ix_call_logs_contact_id", "call_logs", ["contact_id"])
    op.create_index("ix_call_logs_created_at", "call_logs", ["created_at"])

    # RLS Policies
    for table in ["phone_numbers", "call_logs"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
        """)

    # Triggers for updated_at
    for table in ["phone_numbers", "call_logs"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    op.drop_table("call_logs")
    op.drop_table("phone_numbers")
