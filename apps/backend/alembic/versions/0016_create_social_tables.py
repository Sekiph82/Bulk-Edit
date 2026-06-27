"""create social connection tables

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-27

"""
from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "social_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("token_type", sa.String(50), nullable=False, server_default="Bearer"),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "platform", name="uq_social_connections_org_platform"),
    )
    op.create_index("ix_social_connections_organization_id", "social_connections", ["organization_id"])
    op.create_index("ix_social_connections_platform", "social_connections", ["platform"])

    op.create_table(
        "social_oauth_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("state_hash", name="uq_social_oauth_states_hash"),
    )
    op.create_index("ix_social_oauth_states_state_hash", "social_oauth_states", ["state_hash"])


def downgrade() -> None:
    op.drop_index("ix_social_oauth_states_state_hash", "social_oauth_states")
    op.drop_table("social_oauth_states")
    op.drop_index("ix_social_connections_platform", "social_connections")
    op.drop_index("ix_social_connections_organization_id", "social_connections")
    op.drop_table("social_connections")
