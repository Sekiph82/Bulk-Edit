from sqlalchemy import Boolean, String, Text, DateTime, Integer, Numeric, JSON, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
import uuid


class Listing(Base, TimestampMixin):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("etsy_shop_id", "etsy_listing_id", name="uq_listing_shop_etsy_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_shop_id: Mapped[str] = mapped_column(String(36), ForeignKey("etsy_shops.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_listing_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)

    price_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_divisor: Mapped[int | None] = mapped_column(Integer, nullable=True, default=100)
    currency_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tags: Mapped[object] = mapped_column(JSON, nullable=True)
    materials: Mapped[object] = mapped_column(JSON, nullable=True)

    taxonomy_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category_path: Mapped[object] = mapped_column(JSON, nullable=True)
    section_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    shipping_profile_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    return_policy_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    processing_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    who_made: Mapped[str | None] = mapped_column(String(50), nullable=True)
    when_made: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_supply: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_customizable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_personalizable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    personalization_is_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    personalization_char_count_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    personalization_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    item_weight: Mapped[object] = mapped_column(Numeric(10, 3), nullable=True)
    item_weight_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    item_length: Mapped[object] = mapped_column(Numeric(10, 3), nullable=True)
    item_width: Mapped[object] = mapped_column(Numeric(10, 3), nullable=True)
    item_height: Mapped[object] = mapped_column(Numeric(10, 3), nullable=True)
    item_dimensions_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)

    has_variations: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_data: Mapped[object] = mapped_column(JSON, nullable=True)
    etsy_updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)

    images: Mapped[list["ListingImage"]] = relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan")
    videos: Mapped[list["ListingVideo"]] = relationship("ListingVideo", back_populates="listing", cascade="all, delete-orphan")
    variations: Mapped[list["ListingVariation"]] = relationship("ListingVariation", back_populates="listing", cascade="all, delete-orphan")
