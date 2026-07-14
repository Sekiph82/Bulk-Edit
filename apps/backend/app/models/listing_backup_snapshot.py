import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from app.core.config import settings
from app.db.base import Base, TimestampMixin

# Deprecated: kept only so any external reference doesn't hard-crash on import.
# The live value is settings.ETSY_DERIVED_DATA_RETENTION_DAYS (see config.py —
# 30 is a conservative default pending Etsy clarification, not an Etsy mandate).
SNAPSHOT_RETENTION_DAYS = 30


def _default_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.ETSY_DERIVED_DATA_RETENTION_DAYS)


class ListingBackupSnapshot(Base, TimestampMixin):
    __tablename__ = "listing_backup_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_default_expiry, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    bulk_edit_session_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("bulk_edit_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_shop_id: Mapped[str] = mapped_column(String(36), ForeignKey("etsy_shops.id", ondelete="CASCADE"), nullable=False)
    etsy_listing_id: Mapped[str] = mapped_column(String(50), nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String(50), nullable=False, default="pre_write")
    snapshot_data: Mapped[object] = mapped_column(JSON, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
