"""add account fields and status to social_connections

Revision ID: 0018
Revises: 0017
Create Date: 2026-06-27

"""
from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("social_connections", sa.Column("status", sa.String(50), nullable=True, server_default="connected"))
    op.add_column("social_connections", sa.Column("account_name", sa.String(255), nullable=True))
    op.add_column("social_connections", sa.Column("username", sa.String(255), nullable=True))
    op.add_column("social_connections", sa.Column("external_account_id", sa.String(255), nullable=True))
    op.add_column("social_connections", sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True))
    # Make access_token_encrypted nullable so revoked connections can clear the token
    op.alter_column(
        "social_connections",
        "access_token_encrypted",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "social_connections",
        "access_token_encrypted",
        existing_type=sa.Text(),
        nullable=False,
    )
    op.drop_column("social_connections", "disconnected_at")
    op.drop_column("social_connections", "external_account_id")
    op.drop_column("social_connections", "username")
    op.drop_column("social_connections", "account_name")
    op.drop_column("social_connections", "status")
