from sqlalchemy import String, Text, Integer, JSON, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
import uuid


class ListingVideo(Base, TimestampMixin):
    __tablename__ = "listing_videos"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_video_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_data: Mapped[object] = mapped_column(JSON, nullable=True)

    listing: Mapped["Listing"] = relationship("Listing", back_populates="videos")
