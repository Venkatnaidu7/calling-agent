"""billing_analytics_integrations

Revision ID: 006
Revises: 005
Create Date: 2026-09-09 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=100), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=100), nullable=True),
        sa.Column('plan_tier', sa.String(length=50), server_default='starter', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='trialing', nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('monthly_minute_limit', sa.Integer(), server_default='500', nullable=False),
        sa.Column('concurrency_limit', sa.Integer(), server_default='2', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("status IN ('trialing', 'active', 'past_due', 'canceled', 'incomplete')", name='subscription_status_check'),
    )
    op.create_index('ix_subscriptions_tenant_id', 'subscriptions', ['tenant_id'], unique=True)
    op.create_index('ix_subscriptions_stripe_customer_id', 'subscriptions', ['stripe_customer_id'])
    op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'])

    # 2. usage_records table
    op.create_table(
        'usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('call_id', sa.String(length=50), nullable=True),
        sa.Column('metric', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('unit_cost_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_cost_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_usage_records_tenant_id', 'usage_records', ['tenant_id'])
    op.create_index('ix_usage_records_call_id', 'usage_records', ['call_id'])
    op.create_index('ix_usage_records_created_at', 'usage_records', ['created_at'])

    # 3. webhook_endpoints table
    op.create_table(
        'webhook_endpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('secret', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('events', postgresql.JSONB(astext_type=sa.Text()), server_default='["*"]', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_webhook_endpoints_tenant_id', 'webhook_endpoints', ['tenant_id'])

    # RLS Policies
    for table in ['subscriptions', 'usage_records', 'webhook_endpoints']:
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE {table} FORCE ROW LEVEL SECURITY')
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
        """)

    # Triggers for updated_at
    for table in ['subscriptions', 'webhook_endpoints']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    op.drop_table('webhook_endpoints')
    op.drop_table('usage_records')
    op.drop_table('subscriptions')
