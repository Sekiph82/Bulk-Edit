from sqlalchemy import String, Integer, Boolean, JSON, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
import uuid


class ListingVariation(Base, TimestampMixin):
    __tablename__ = "listing_variations"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_product_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    property_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    property_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    value_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_divisor: Mapped[int | None] = mapped_column(Integer, nullable=True, default=100)
    currency_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    raw_data: Mapped[object] = mapped_column(JSON, nullable=True)

    listing: Mapped["Listing"] = relationship("Listing", back_populates="variations")
