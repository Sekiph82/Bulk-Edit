"""add expires_at (30-day snapshot retention) to backup snapshot and csv job tables

Revision ID: 0023
Revises: 0022
Create Date: 2026-07-13

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta, timezone

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None

TABLES = [
    "listing_backup_snapshots",
    "listing_media_backup_snapshots",
    "listing_variation_backup_snapshots",
    "csv_jobs",
]


def upgrade() -> None:
    default_expiry = datetime.now(timezone.utc) + timedelta(days=30)
    for table in TABLES:
        op.add_column(table, sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        op.execute(
            sa.text(f"UPDATE {table} SET expires_at = :expires_at WHERE expires_at IS NULL")
            .bindparams(expires_at=default_expiry)
        )
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column("expires_at", nullable=False)
        op.create_index(f"ix_{table}_expires_at", table, ["expires_at"])


def downgrade() -> None:
    for table in TABLES:
        op.drop_index(f"ix_{table}_expires_at", table_name=table)
        op.drop_column(table, "expires_at")
