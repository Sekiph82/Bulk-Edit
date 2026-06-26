import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class RevertResult(Base, TimestampMixin):
    __tablename__ = "revert_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    revert_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("revert_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    apply_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("bulk_edit_apply_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    bulk_edit_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("bulk_edit_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    etsy_listing_id: Mapped[str] = mapped_column(String(50), nullable=False)
    backup_snapshot_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("listing_backup_snapshots.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    request_payload: Mapped[object | None] = mapped_column(JSON, nullable=True)
    response_payload: Mapped[object | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
