from sqlalchemy import String, Text, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
import uuid


class ListingImage(Base, TimestampMixin):
    __tablename__ = "listing_images"
    __table_args__ = (
        UniqueConstraint("listing_id", "etsy_image_id", name="uq_image_listing_etsy_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_image_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    url_fullxfull: Mapped[str | None] = mapped_column(Text, nullable=True)
    url_570xN: Mapped[str | None] = mapped_column(Text, nullable=True)
    url_170x135: Mapped[str | None] = mapped_column(Text, nullable=True)
    alt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_data: Mapped[object] = mapped_column(JSON, nullable=True)

    listing: Mapped["Listing"] = relationship("Listing", back_populates="images")
