"""create csv import export tables

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-26

"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add target_listing_ids to existing bulk_edit_changes table
    op.add_column(
        "bulk_edit_changes",
        sa.Column("target_listing_ids", sa.JSON, nullable=True),
    )

    op.create_table(
        "csv_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("job_type", sa.String(20), nullable=False, index=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="uploaded", index=True),
        sa.Column("filename", sa.String(512), nullable=True),
        sa.Column("original_filename", sa.String(512), nullable=True),
        sa.Column("row_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("valid_row_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("invalid_row_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("changed_row_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("unchanged_row_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ignored_column_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ignored_columns", sa.JSON, nullable=True),
        sa.Column("summary", sa.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("converted_bulk_edit_session_id", sa.String(36), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "csv_rows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("csv_job_id", sa.String(36), sa.ForeignKey("csv_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("etsy_listing_id", sa.String(50), nullable=True),
        sa.Column("raw_data", sa.JSON, nullable=False),
        sa.Column("normalized_data", sa.JSON, nullable=True),
        sa.Column("diff", sa.JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="invalid", index=True),
        sa.Column("validation_errors", sa.JSON, nullable=True),
        sa.Column("validation_warnings", sa.JSON, nullable=True),
        sa.Column("listing_title", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("csv_rows")
    op.drop_table("csv_jobs")
    op.drop_column("bulk_edit_changes", "target_listing_ids")
