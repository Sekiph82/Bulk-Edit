"""create billing tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("status", sa.String(50), nullable=False, server_default="free"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", name="uq_subscription_org"),
    )
    op.create_index("ix_subscriptions_stripe_customer_id", "subscriptions", ["stripe_customer_id"])
    op.create_index("ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"])

    op.create_table(
        "billing_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("stripe_event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_billing_events_stripe_event_id", "billing_events", ["stripe_event_id"], unique=True)
    op.create_index("ix_billing_events_event_type", "billing_events", ["event_type"])

    op.create_table(
        "usage_counters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_key", sa.String(7), nullable=False),
        sa.Column("listings_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bulk_edits_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_credits_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("media_assets_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "period_key", name="uq_usage_org_period"),
    )
    op.create_index("ix_usage_counters_organization_id", "usage_counters", ["organization_id"])


def downgrade() -> None:
    op.drop_table("usage_counters")
    op.drop_table("billing_events")
    op.drop_index("ix_subscriptions_stripe_subscription_id", "subscriptions")
    op.drop_index("ix_subscriptions_stripe_customer_id", "subscriptions")
    op.drop_table("subscriptions")
