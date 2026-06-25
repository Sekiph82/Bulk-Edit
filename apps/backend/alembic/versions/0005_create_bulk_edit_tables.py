"""create bulk edit tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bulk_edit_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'draft'"), index=True),
        sa.Column("selected_listing_ids", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("selected_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("change_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("preview_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "bulk_edit_changes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("bulk_edit_session_id", sa.String(36), sa.ForeignKey("bulk_edit_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("old_value", sa.JSON, nullable=True),
        sa.Column("new_value", sa.JSON, nullable=True),
        sa.Column("operation_value", sa.JSON, nullable=True),
        sa.Column("validation_status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("validation_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "bulk_edit_preview_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("bulk_edit_session_id", sa.String(36), sa.ForeignKey("bulk_edit_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_title", sa.Text, nullable=True),
        sa.Column("before_data", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("after_data", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("diff", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("validation_status", sa.String(20), nullable=False, server_default=sa.text("'valid'")),
        sa.Column("validation_messages", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("bulk_edit_session_id", "listing_id", name="uq_preview_item_session_listing"),
    )


def downgrade() -> None:
    op.drop_table("bulk_edit_preview_items")
    op.drop_table("bulk_edit_changes")
    op.drop_table("bulk_edit_sessions")
