"""create etsy tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "etsy_shops",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False, index=True),
        sa.Column("etsy_shop_id", sa.String(50), unique=True, nullable=False),
        sa.Column("shop_name", sa.String(255), nullable=True),
        sa.Column("is_connected", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "etsy_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("etsy_shop_id", sa.String(36), sa.ForeignKey("etsy_shops.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("access_token_enc", sa.Text, nullable=False),
        sa.Column("refresh_token_enc", sa.Text, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scopes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "etsy_oauth_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("state", sa.String(128), unique=True, nullable=False, index=True),
        sa.Column("code_verifier", sa.Text, nullable=False),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("etsy_oauth_states")
    op.drop_table("etsy_tokens")
    op.drop_table("etsy_shops")
