"""create profit calculator tables

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-27

"""
from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cost_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, server_default="Default"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("transaction_fee_percent", sa.Numeric(6, 5), nullable=False, server_default="0.06500"),
        sa.Column("payment_fee_percent", sa.Numeric(6, 5), nullable=False, server_default="0.03000"),
        sa.Column("payment_fixed_fee", sa.Numeric(10, 4), nullable=False, server_default="0.2500"),
        sa.Column("listing_fee", sa.Numeric(10, 4), nullable=False, server_default="0.2000"),
        sa.Column("offsite_ads_percent", sa.Numeric(6, 5), nullable=False, server_default="0.15000"),
        sa.Column("currency_conversion_percent", sa.Numeric(6, 5), nullable=False, server_default="0.02500"),
        sa.Column("default_shipping_cost", sa.Numeric(10, 4), nullable=False, server_default="0.0000"),
        sa.Column("default_packaging_cost", sa.Numeric(10, 4), nullable=False, server_default="0.0000"),
        sa.Column("target_margin_percent", sa.Numeric(6, 5), nullable=False, server_default="0.30000"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_cost_profiles_organization_id", "cost_profiles", ["organization_id"])

    op.create_table(
        "listing_costs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_cost", sa.Numeric(10, 4), nullable=False, server_default="0.0000"),
        sa.Column("shipping_cost", sa.Numeric(10, 4), nullable=False, server_default="0.0000"),
        sa.Column("packaging_cost", sa.Numeric(10, 4), nullable=False, server_default="0.0000"),
        sa.Column("ad_cost", sa.Numeric(10, 4), nullable=False, server_default="0.0000"),
        sa.Column("other_cost", sa.Numeric(10, 4), nullable=False, server_default="0.0000"),
        sa.Column("include_offsite_ads", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cost_profile_id", sa.String(36), sa.ForeignKey("cost_profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "listing_id", name="uq_listing_costs_org_listing"),
    )
    op.create_index("ix_listing_costs_organization_id", "listing_costs", ["organization_id"])
    op.create_index("ix_listing_costs_listing_id", "listing_costs", ["listing_id"])


def downgrade() -> None:
    op.drop_table("listing_costs")
    op.drop_table("cost_profiles")
