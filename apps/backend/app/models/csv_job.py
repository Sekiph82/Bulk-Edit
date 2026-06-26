import uuid
from sqlalchemy import String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class CSVJob(Base, TimestampMixin):
    __tablename__ = "csv_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    job_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="uploaded", index=True)
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    changed_row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unchanged_row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ignored_column_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ignored_columns: Mapped[object] = mapped_column(JSON, nullable=True)
    summary: Mapped[object] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    converted_bulk_edit_session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    completed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)

    rows: Mapped[list["CSVRow"]] = relationship("CSVRow", back_populates="job", cascade="all, delete-orphan")
