import uuid
from datetime import datetime
from sqlalchemy import String, Integer, JSON, Text, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.base import Base, TimestampMixin


class ScheduledJobRun(Base, TimestampMixin):
    __tablename__ = "scheduled_job_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("scheduled_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    triggered_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    job: Mapped["ScheduledJob"] = relationship("ScheduledJob", back_populates="runs", lazy="select")
