"""create listing and sync tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False, index=True),
        sa.Column("etsy_shop_id", sa.String(36), sa.ForeignKey("etsy_shops.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_listing_id", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("state", sa.String(50), nullable=True, index=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("price_amount", sa.Integer, nullable=True),
        sa.Column("price_divisor", sa.Integer, nullable=True, server_default=sa.text("100")),
        sa.Column("currency_code", sa.String(10), nullable=True),
        sa.Column("quantity", sa.Integer, nullable=True),
        sa.Column("sku", sa.String(255), nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("materials", sa.JSON, nullable=True),
        sa.Column("taxonomy_id", sa.String(50), nullable=True),
        sa.Column("category_path", sa.JSON, nullable=True),
        sa.Column("section_id", sa.String(50), nullable=True),
        sa.Column("shipping_profile_id", sa.String(50), nullable=True),
        sa.Column("return_policy_id", sa.String(50), nullable=True),
        sa.Column("processing_min", sa.Integer, nullable=True),
        sa.Column("processing_max", sa.Integer, nullable=True),
        sa.Column("who_made", sa.String(50), nullable=True),
        sa.Column("when_made", sa.String(50), nullable=True),
        sa.Column("is_supply", sa.Boolean, nullable=True),
        sa.Column("is_customizable", sa.Boolean, nullable=True),
        sa.Column("is_personalizable", sa.Boolean, nullable=True),
        sa.Column("personalization_is_required", sa.Boolean, nullable=True),
        sa.Column("personalization_char_count_max", sa.Integer, nullable=True),
        sa.Column("personalization_instructions", sa.Text, nullable=True),
        sa.Column("item_weight", sa.Numeric(10, 3), nullable=True),
        sa.Column("item_weight_unit", sa.String(20), nullable=True),
        sa.Column("item_length", sa.Numeric(10, 3), nullable=True),
        sa.Column("item_width", sa.Numeric(10, 3), nullable=True),
        sa.Column("item_height", sa.Numeric(10, 3), nullable=True),
        sa.Column("item_dimensions_unit", sa.String(20), nullable=True),
        sa.Column("has_variations", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("raw_data", sa.JSON, nullable=True),
        sa.Column("etsy_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("etsy_shop_id", "etsy_listing_id", name="uq_listing_shop_etsy_id"),
    )

    op.create_table(
        "listing_images",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_image_id", sa.String(50), nullable=True, index=True),
        sa.Column("url_fullxfull", sa.Text, nullable=True),
        sa.Column("url_570xN", sa.Text, nullable=True),
        sa.Column("url_170x135", sa.Text, nullable=True),
        sa.Column("alt_text", sa.Text, nullable=True),
        sa.Column("rank", sa.Integer, nullable=True),
        sa.Column("width", sa.Integer, nullable=True),
        sa.Column("height", sa.Integer, nullable=True),
        sa.Column("raw_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("listing_id", "etsy_image_id", name="uq_image_listing_etsy_id"),
    )

    op.create_table(
        "listing_videos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_video_id", sa.String(50), nullable=True, index=True),
        sa.Column("video_url", sa.Text, nullable=True),
        sa.Column("thumbnail_url", sa.Text, nullable=True),
        sa.Column("rank", sa.Integer, nullable=True),
        sa.Column("raw_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "listing_variations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("listing_id", sa.String(36), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("etsy_product_id", sa.String(50), nullable=True, index=True),
        sa.Column("sku", sa.String(255), nullable=True),
        sa.Column("property_id", sa.String(50), nullable=True),
        sa.Column("property_name", sa.String(255), nullable=True),
        sa.Column("value_id", sa.String(50), nullable=True),
        sa.Column("value_name", sa.String(255), nullable=True),
        sa.Column("price_amount", sa.Integer, nullable=True),
        sa.Column("price_divisor", sa.Integer, nullable=True, server_default=sa.text("100")),
        sa.Column("currency_code", sa.String(10), nullable=True),
        sa.Column("quantity", sa.Integer, nullable=True),
        sa.Column("is_available", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("raw_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False, index=True),
        sa.Column("etsy_shop_id", sa.String(36), sa.ForeignKey("etsy_shops.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_type", sa.String(50), nullable=False, server_default=sa.text("'manual_listing_sync'")),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'pending'"), index=True),
        sa.Column("total_items", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("processed_items", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("sync_jobs")
    op.drop_table("listing_variations")
    op.drop_table("listing_videos")
    op.drop_table("listing_images")
    op.drop_table("listings")
