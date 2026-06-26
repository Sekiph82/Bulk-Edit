import uuid
from datetime import datetime
from sqlalchemy import String, Integer, JSON, Text, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.base import Base, TimestampMixin

VALID_JOB_TYPES = {"etsy_sync", "bulk_edit_draft", "dynamic_pricing_preview", "csv_export_snapshot"}
VALID_STATUSES = {"active", "paused", "disabled", "completed", "failed"}
VALID_SCHEDULE_TYPES = {"one_time", "interval", "daily", "weekly", "monthly"}


class ScheduledJob(Base, TimestampMixin):
    __tablename__ = "scheduled_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    schedule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    schedule_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    job_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_runs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    runs: Mapped[list["ScheduledJobRun"]] = relationship("ScheduledJobRun", back_populates="job", lazy="select")
