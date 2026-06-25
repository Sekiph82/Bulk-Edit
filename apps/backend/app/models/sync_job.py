from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin
import uuid


class SyncJob(Base, TimestampMixin):
    __tablename__ = "sync_jobs"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), nullable=False, index=True)
    etsy_shop_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("etsy_shops.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual_listing_sync")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
