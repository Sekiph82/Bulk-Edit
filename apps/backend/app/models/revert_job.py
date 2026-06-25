import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class RevertJob(Base, TimestampMixin):
    __tablename__ = "revert_jobs"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    bulk_edit_session_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("bulk_edit_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    apply_job_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("bulk_edit_apply_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
