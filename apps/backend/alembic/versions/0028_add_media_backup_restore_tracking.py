"""add restore tracking columns to listing_media_backup_snapshots

M13.04: restore/revert foundation for media backups. `restored_at`/
`restore_media_job_id` let the app answer "has this backup already been
restored" (idempotency guard for POST /bulk-edit/media/backups/{id}/restore)
and link back to the BulkEditMediaJob that performed the restore, reusing
the existing job/result/audit-log infrastructure rather than a parallel
restore-tracking table. See DECISIONS.md.

Revision ID: 0028
Revises: 0027
Create Date: 2026-08-31

"""
import sqlalchemy as sa
from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listing_media_backup_snapshots", sa.Column("restored_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("listing_media_backup_snapshots", sa.Column("restore_media_job_id", sa.String(36), nullable=True))
    op.create_index("ix_listing_media_backup_snapshots_restored_at", "listing_media_backup_snapshots", ["restored_at"])
    op.create_foreign_key(
        "fk_listing_media_backup_snapshots_restore_media_job_id",
        "listing_media_backup_snapshots", "bulk_edit_media_jobs",
        ["restore_media_job_id"], ["id"], ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_listing_media_backup_snapshots_restore_media_job_id", "listing_media_backup_snapshots", type_="foreignkey")
    op.drop_index("ix_listing_media_backup_snapshots_restored_at", table_name="listing_media_backup_snapshots")
    op.drop_column("listing_media_backup_snapshots", "restore_media_job_id")
    op.drop_column("listing_media_backup_snapshots", "restored_at")
