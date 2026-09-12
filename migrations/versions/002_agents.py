"""agents

Revision ID: 002
Revises: 001
Create Date: 2026-09-09 10:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # agents table
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('published_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name='agent_status_check'),
    )
    op.create_index(op.f('ix_agents_tenant_id'), 'agents', ['tenant_id'], unique=False)
    
    # agent_versions table
    op.create_table(
        'agent_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('personality', sa.Text(), nullable=True),
        sa.Column('voice', sa.String(length=50), nullable=False, server_default='ash'),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('languages', postgresql.JSONB(astext_type=sa.Text()), server_default='["en"]', nullable=False),
        sa.Column('system_instructions', sa.Text(), nullable=True),
        sa.Column('business_context', sa.Text(), nullable=True),
        sa.Column('greeting_message', sa.Text(), nullable=True),
        sa.Column('objectives', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('fallback_message', sa.Text(), nullable=True),
        sa.Column('max_call_duration_seconds', sa.Integer(), server_default='1800', nullable=False),
        sa.Column('knowledge_config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('tool_permissions', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('transfer_rules', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('business_hours', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('compliance_config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('turn_detection_config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('loop_protection_config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['published_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('agent_id', 'version_number', name='uix_agent_version'),
        sa.CheckConstraint("status IN ('draft', 'testing', 'published', 'archived')", name='agent_version_status_check'),
    )
    op.create_index(op.f('ix_agent_versions_tenant_id'), 'agent_versions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_agent_versions_agent_id'), 'agent_versions', ['agent_id'], unique=False)

    # RLS Policies
    op.execute("ALTER TABLE agents ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON agents "
        "USING (tenant_id = current_setting('app.current_tenant', TRUE)::uuid);"
    )

    op.execute("ALTER TABLE agent_versions ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON agent_versions "
        "USING (tenant_id = current_setting('app.current_tenant', TRUE)::uuid);"
    )

    # Updated At Triggers
    op.execute("""
        CREATE TRIGGER set_timestamp_agents
        BEFORE UPDATE ON agents
        FOR EACH ROW
        EXECUTE FUNCTION trigger_set_timestamp();
    """)
    op.execute("""
        CREATE TRIGGER set_timestamp_agent_versions
        BEFORE UPDATE ON agent_versions
        FOR EACH ROW
        EXECUTE FUNCTION trigger_set_timestamp();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS set_timestamp_agent_versions ON agent_versions;")
    op.execute("DROP TRIGGER IF EXISTS set_timestamp_agents ON agents;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON agent_versions;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON agents;")
    
    op.drop_index(op.f('ix_agent_versions_agent_id'), table_name='agent_versions')
    op.drop_index(op.f('ix_agent_versions_tenant_id'), table_name='agent_versions')
    op.drop_table('agent_versions')
    
    op.drop_index(op.f('ix_agents_tenant_id'), table_name='agents')
    op.drop_table('agents')
