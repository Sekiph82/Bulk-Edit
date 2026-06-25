import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Uuid, JSON
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class BulkEditMediaJob(Base, TimestampMixin):
    __tablename__ = "bulk_edit_media_jobs"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    bulk_edit_session_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("bulk_edit_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    operation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    operation_payload: Mapped[object | None] = mapped_column(JSON, nullable=True)
    listing_ids: Mapped[object | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
