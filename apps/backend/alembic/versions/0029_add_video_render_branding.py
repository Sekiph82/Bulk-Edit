"""add branding_json column to video_renders

M13.05C: stores the branding fields applied to a generated video plus what
actually rendered (`text_rendered`/`logo_rendered`), so the result UI can
report branding status truthfully. Additive, nullable — existing rows and the
plain (no-branding) render path are unaffected.

Revision ID: 0029
Revises: 0028
Create Date: 2026-09-04

"""
import sqlalchemy as sa
from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("video_renders", sa.Column("branding_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("video_renders", "branding_json")
