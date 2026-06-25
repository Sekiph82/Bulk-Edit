import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Uuid
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class BulkEditVariationResult(Base, TimestampMixin):
    __tablename__ = "bulk_edit_variation_results"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    variation_job_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("bulk_edit_variation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_listing_id: Mapped[str] = mapped_column(String(50), nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    request_payload: Mapped[object | None] = mapped_column(JSON, nullable=True)
    response_payload: Mapped[object | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
