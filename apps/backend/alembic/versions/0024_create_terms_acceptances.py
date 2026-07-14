"""create terms_acceptances table

Revision ID: 0024
Revises: 0023
Create Date: 2026-07-13

"""
from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "terms_acceptances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("terms_version", sa.String(50), nullable=False),
        sa.Column("privacy_version", sa.String(50), nullable=False),
        sa.Column("acceptance_source", sa.String(50), nullable=False, server_default="web_registration"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_terms_acceptances_user_id", "terms_acceptances", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_terms_acceptances_user_id", table_name="terms_acceptances")
    op.drop_table("terms_acceptances")
