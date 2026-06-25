import uuid
from sqlalchemy import String, Text, JSON, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class BulkEditChange(Base, TimestampMixin):
    __tablename__ = "bulk_edit_changes"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    bulk_edit_session_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("bulk_edit_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[object] = mapped_column(JSON, nullable=True)
    new_value: Mapped[object] = mapped_column(JSON, nullable=True)
    operation_value: Mapped[object] = mapped_column(JSON, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    validation_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped["BulkEditSession"] = relationship("BulkEditSession", back_populates="changes")
