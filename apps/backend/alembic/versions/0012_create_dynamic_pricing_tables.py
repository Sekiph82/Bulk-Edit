"""create dynamic pricing tables

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-26

"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add dynamic_pricing_jobs_used to usage_counters
    op.add_column(
        "usage_counters",
        sa.Column("dynamic_pricing_jobs_used", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "dynamic_pricing_jobs",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("organization_id", sa.Uuid(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("selected_listing_ids", sa.JSON(), nullable=False),
        sa.Column("rule_type", sa.String(100), nullable=False),
        sa.Column("rule_payload", sa.JSON(), nullable=False),
        sa.Column("safety_payload", sa.JSON(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recommended_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invalid_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("converted_bulk_edit_session_id", sa.Uuid(as_uuid=False), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "dynamic_pricing_recommendations",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("organization_id", sa.Uuid(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("dynamic_pricing_job_id", sa.Uuid(as_uuid=False), sa.ForeignKey("dynamic_pricing_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("listing_id", sa.Uuid(as_uuid=False), sa.ForeignKey("listings.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("etsy_listing_id", sa.String(50), nullable=True),
        sa.Column("listing_title", sa.Text(), nullable=True),
        sa.Column("currency_code", sa.String(10), nullable=True),
        sa.Column("current_price_amount", sa.Integer(), nullable=True),
        sa.Column("recommended_price_amount", sa.Integer(), nullable=True),
        sa.Column("reference_price_amount", sa.Integer(), nullable=True),
        sa.Column("cost_amount", sa.Integer(), nullable=True),
        sa.Column("margin_percent", sa.Numeric(10, 4), nullable=True),
        sa.Column("diff_amount", sa.Integer(), nullable=True),
        sa.Column("diff_percent", sa.Numeric(10, 4), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="recommended"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("calculation_details", sa.JSON(), nullable=True),
        sa.Column("validation_errors", sa.JSON(), nullable=True),
        sa.Column("validation_warnings", sa.JSON(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by_user_id", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("dynamic_pricing_recommendations")
    op.drop_table("dynamic_pricing_jobs")
    op.drop_column("usage_counters", "dynamic_pricing_jobs_used")
