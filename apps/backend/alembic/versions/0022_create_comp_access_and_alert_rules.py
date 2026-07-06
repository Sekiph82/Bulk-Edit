"""create comp_access_grants and owner_alert_rules tables

Revision ID: 0022
Revises: 0021
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comp_access_grants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("comp_plan", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("granted_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_comp_access_grants_organization_id", "comp_access_grants", ["organization_id"])

    op.create_table(
        "owner_alert_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("threshold_count", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("window_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("channel_email_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("channel_email_to", sa.String(500), nullable=True),
        sa.Column("channel_slack_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("encrypted_slack_webhook", sa.Text(), nullable=True),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_owner_alert_rules_event_type", "owner_alert_rules", ["event_type"])

    op.create_table(
        "owner_action_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_owner_action_logs_organization_id", "owner_action_logs", ["organization_id"])
    op.create_index("ix_owner_action_logs_target_user_id", "owner_action_logs", ["target_user_id"])
    op.create_index("ix_owner_action_logs_action_type", "owner_action_logs", ["action_type"])


def downgrade() -> None:
    op.drop_index("ix_owner_action_logs_action_type", table_name="owner_action_logs")
    op.drop_index("ix_owner_action_logs_target_user_id", table_name="owner_action_logs")
    op.drop_index("ix_owner_action_logs_organization_id", table_name="owner_action_logs")
    op.drop_table("owner_action_logs")
    op.drop_index("ix_owner_alert_rules_event_type", table_name="owner_alert_rules")
    op.drop_table("owner_alert_rules")
    op.drop_index("ix_comp_access_grants_organization_id", table_name="comp_access_grants")
    op.drop_table("comp_access_grants")
