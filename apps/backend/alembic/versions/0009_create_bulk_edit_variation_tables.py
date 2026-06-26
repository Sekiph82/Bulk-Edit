"""create bulk edit variation tables

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bulk_edit_variation_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operation_type", sa.String(50), nullable=False, index=True),
        sa.Column("operation_payload", sa.JSON, nullable=False),
        sa.Column("selected_listing_ids", sa.JSON, nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft", index=True),
        sa.Column("selected_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("preview_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("preview_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "bulk_edit_variation_preview_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("variation_job_id", sa.String(36), sa.ForeignKey("bulk_edit_variation_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_listing_id", sa.String(50), nullable=False),
        sa.Column("listing_title", sa.Text, nullable=True),
        sa.Column("before_variations", sa.JSON, nullable=False),
        sa.Column("after_variations", sa.JSON, nullable=False),
        sa.Column("diff", sa.JSON, nullable=False),
        sa.Column("validation_status", sa.String(20), nullable=False, server_default="valid"),
        sa.Column("validation_messages", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("variation_job_id", "listing_id", name="uq_var_preview_job_listing"),
    )

    op.create_table(
        "bulk_edit_variation_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("variation_job_id", sa.String(36), sa.ForeignKey("bulk_edit_variation_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_listing_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("request_payload", sa.JSON, nullable=True),
        sa.Column("response_payload", sa.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "listing_variation_backup_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("variation_job_id", sa.String(36), sa.ForeignKey("bulk_edit_variation_jobs.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_shop_id", sa.String(36), sa.ForeignKey("etsy_shops.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_listing_id", sa.String(50), nullable=False),
        sa.Column("snapshot_type", sa.String(50), nullable=False, server_default="pre_variation_write"),
        sa.Column("local_variations_snapshot", sa.JSON, nullable=True),
        sa.Column("etsy_inventory_snapshot", sa.JSON, nullable=True),
        sa.Column("raw_snapshot", sa.JSON, nullable=True),
        sa.Column("created_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("listing_variation_backup_snapshots")
    op.drop_table("bulk_edit_variation_results")
    op.drop_table("bulk_edit_variation_preview_items")
    op.drop_table("bulk_edit_variation_jobs")
