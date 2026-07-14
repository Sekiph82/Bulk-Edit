import uuid
from sqlalchemy import String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin
from app.models.listing_backup_snapshot import _default_expiry
from datetime import datetime


class ListingVariationBackupSnapshot(Base, TimestampMixin):
    __tablename__ = "listing_variation_backup_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_default_expiry, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    variation_job_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("bulk_edit_variation_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_shop_id: Mapped[str] = mapped_column(String(36), ForeignKey("etsy_shops.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_listing_id: Mapped[str] = mapped_column(String(50), nullable=False)

    snapshot_type: Mapped[str] = mapped_column(String(50), nullable=False, default="pre_variation_write")
    local_variations_snapshot: Mapped[object | None] = mapped_column(JSON, nullable=True)
    etsy_inventory_snapshot: Mapped[object | None] = mapped_column(JSON, nullable=True)
    raw_snapshot: Mapped[object | None] = mapped_column(JSON, nullable=True)

    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
