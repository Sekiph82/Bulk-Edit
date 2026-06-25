"""create bulk edit apply tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listing_backup_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bulk_edit_session_id", sa.String(36), sa.ForeignKey("bulk_edit_sessions.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_shop_id", sa.String(36), sa.ForeignKey("etsy_shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("etsy_listing_id", sa.String(50), nullable=False),
        sa.Column("snapshot_type", sa.String(50), nullable=False, server_default=sa.text("'pre_write'")),
        sa.Column("snapshot_data", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "bulk_edit_apply_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bulk_edit_session_id", sa.String(36), sa.ForeignKey("bulk_edit_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("total_items", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("success_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("failure_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("skipped_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "bulk_edit_apply_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("apply_job_id", sa.String(36), sa.ForeignKey("bulk_edit_apply_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bulk_edit_session_id", sa.String(36), sa.ForeignKey("bulk_edit_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_listing_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("request_payload", sa.JSON, nullable=True),
        sa.Column("response_payload", sa.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("backup_snapshot_id", sa.String(36), sa.ForeignKey("listing_backup_snapshots.id", ondelete="SET NULL"), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(255), nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("bulk_edit_apply_results")
    op.drop_table("bulk_edit_apply_jobs")
    op.drop_table("listing_backup_snapshots")
