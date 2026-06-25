"""create bulk edit revert tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "revert_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bulk_edit_session_id", sa.String(36), sa.ForeignKey("bulk_edit_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("apply_job_id", sa.String(36), sa.ForeignKey("bulk_edit_apply_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
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
        "revert_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("revert_job_id", sa.String(36), sa.ForeignKey("revert_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("apply_job_id", sa.String(36), sa.ForeignKey("bulk_edit_apply_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bulk_edit_session_id", sa.String(36), sa.ForeignKey("bulk_edit_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_listing_id", sa.String(50), nullable=False),
        sa.Column("backup_snapshot_id", sa.String(36), sa.ForeignKey("listing_backup_snapshots.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("request_payload", sa.JSON, nullable=True),
        sa.Column("response_payload", sa.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("revert_results")
    op.drop_table("revert_jobs")
