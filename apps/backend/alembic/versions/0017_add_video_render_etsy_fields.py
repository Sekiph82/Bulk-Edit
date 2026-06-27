"""add etsy readiness fields to video_renders

Revision ID: 0017
Revises: 0016
Create Date: 2026-06-27

"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("video_renders", sa.Column("aspect_ratio", sa.String(10), nullable=True))
    op.add_column("video_renders", sa.Column("width", sa.Integer(), nullable=True))
    op.add_column("video_renders", sa.Column("height", sa.Integer(), nullable=True))
    op.add_column("video_renders", sa.Column("is_etsy_ready", sa.Boolean(), nullable=True))
    op.add_column("video_renders", sa.Column("etsy_issues_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("video_renders", "etsy_issues_json")
    op.drop_column("video_renders", "is_etsy_ready")
    op.drop_column("video_renders", "height")
    op.drop_column("video_renders", "width")
    op.drop_column("video_renders", "aspect_ratio")
