"""create bulk edit media tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bulk_edit_media_jobs",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("organization_id", sa.Uuid(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bulk_edit_session_id", sa.Uuid(as_uuid=False), sa.ForeignKey("bulk_edit_sessions.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operation_type", sa.String(50), nullable=False, index=True),
        sa.Column("operation_payload", sa.JSON, nullable=True),
        sa.Column("listing_ids", sa.JSON, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("total_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "bulk_edit_media_results",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("organization_id", sa.Uuid(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("media_job_id", sa.Uuid(as_uuid=False), sa.ForeignKey("bulk_edit_media_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bulk_edit_session_id", sa.Uuid(as_uuid=False), sa.ForeignKey("bulk_edit_sessions.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("listing_id", sa.Uuid(as_uuid=False), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_listing_id", sa.String(50), nullable=False),
        sa.Column("operation_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("before_media", sa.JSON, nullable=True),
        sa.Column("after_media", sa.JSON, nullable=True),
        sa.Column("request_payload", sa.JSON, nullable=True),
        sa.Column("response_payload", sa.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "listing_media_backup_snapshots",
        sa.Column("id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("organization_id", sa.Uuid(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("media_job_id", sa.Uuid(as_uuid=False), sa.ForeignKey("bulk_edit_media_jobs.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("bulk_edit_session_id", sa.Uuid(as_uuid=False), sa.ForeignKey("bulk_edit_sessions.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("listing_id", sa.Uuid(as_uuid=False), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_shop_id", sa.Uuid(as_uuid=False), sa.ForeignKey("etsy_shops.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_listing_id", sa.String(50), nullable=False),
        sa.Column("snapshot_type", sa.String(50), nullable=False, server_default="pre_media_write"),
        sa.Column("images_snapshot", sa.JSON, nullable=True),
        sa.Column("videos_snapshot", sa.JSON, nullable=True),
        sa.Column("raw_snapshot", sa.JSON, nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("listing_media_backup_snapshots")
    op.drop_table("bulk_edit_media_results")
    op.drop_table("bulk_edit_media_jobs")
