import uuid
from sqlalchemy import String, ForeignKey, Uuid, JSON
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class ListingMediaBackupSnapshot(Base, TimestampMixin):
    __tablename__ = "listing_media_backup_snapshots"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    media_job_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("bulk_edit_media_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    bulk_edit_session_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("bulk_edit_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    listing_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_shop_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("etsy_shops.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_listing_id: Mapped[str] = mapped_column(String(50), nullable=False)

    snapshot_type: Mapped[str] = mapped_column(String(50), nullable=False, default="pre_media_write")
    images_snapshot: Mapped[object | None] = mapped_column(JSON, nullable=True)
    videos_snapshot: Mapped[object | None] = mapped_column(JSON, nullable=True)
    raw_snapshot: Mapped[object | None] = mapped_column(JSON, nullable=True)

    created_by_user_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
