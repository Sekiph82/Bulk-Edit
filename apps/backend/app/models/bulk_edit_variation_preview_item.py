import uuid
from sqlalchemy import String, Text, JSON, ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class BulkEditVariationPreviewItem(Base, TimestampMixin):
    __tablename__ = "bulk_edit_variation_preview_items"
    __table_args__ = (
        UniqueConstraint("variation_job_id", "listing_id", name="uq_var_preview_job_listing"),
    )

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    variation_job_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("bulk_edit_variation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_listing_id: Mapped[str] = mapped_column(String(50), nullable=False)
    listing_title: Mapped[str | None] = mapped_column(Text, nullable=True)

    before_variations: Mapped[object] = mapped_column(JSON, nullable=False)
    after_variations: Mapped[object] = mapped_column(JSON, nullable=False)
    diff: Mapped[object] = mapped_column(JSON, nullable=False)

    validation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="valid")
    validation_messages: Mapped[object | None] = mapped_column(JSON, nullable=True)
