import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, JSON, ForeignKey, Uuid
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class BulkEditVariationJob(Base, TimestampMixin):
    __tablename__ = "bulk_edit_variation_jobs"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    operation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    operation_payload: Mapped[object] = mapped_column(JSON, nullable=False)
    selected_listing_ids: Mapped[object] = mapped_column(JSON, nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    selected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    preview_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    preview_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
