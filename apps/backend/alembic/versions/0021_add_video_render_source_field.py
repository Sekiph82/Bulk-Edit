"""add source field to video_renders

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "video_renders",
        sa.Column("source", sa.String(20), nullable=False, server_default="generated"),
    )


def downgrade() -> None:
    op.drop_column("video_renders", "source")
