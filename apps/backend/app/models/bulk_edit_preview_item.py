import uuid
from sqlalchemy import Text, JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class BulkEditPreviewItem(Base, TimestampMixin):
    __tablename__ = "bulk_edit_preview_items"
    __table_args__ = (
        UniqueConstraint("bulk_edit_session_id", "listing_id", name="uq_preview_item_session_listing"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bulk_edit_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("bulk_edit_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    listing_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_data: Mapped[object] = mapped_column(JSON, nullable=False, default=dict)
    after_data: Mapped[object] = mapped_column(JSON, nullable=False, default=dict)
    diff: Mapped[object] = mapped_column(JSON, nullable=False, default=dict)
    validation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="valid")
    validation_messages: Mapped[object] = mapped_column(JSON, nullable=True)

    session: Mapped["BulkEditSession"] = relationship("BulkEditSession", back_populates="preview_items")
