import uuid
from sqlalchemy import String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class BulkEditSession(Base, TimestampMixin):
    __tablename__ = "bulk_edit_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    selected_listing_ids: Mapped[object] = mapped_column(JSON, nullable=False, default=list)
    selected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    change_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    preview_generated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)

    changes: Mapped[list["BulkEditChange"]] = relationship("BulkEditChange", back_populates="session", cascade="all, delete-orphan")
    preview_items: Mapped[list["BulkEditPreviewItem"]] = relationship("BulkEditPreviewItem", back_populates="session", cascade="all, delete-orphan")
