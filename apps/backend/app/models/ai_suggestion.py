import uuid
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class AISuggestion(Base, TimestampMixin):
    __tablename__ = "ai_suggestions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True, index=True)
    field: Mapped[str] = mapped_column(String(50), nullable=False)
    suggested_value: Mapped[object] = mapped_column(JSON, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    accepted_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    converted_to_session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    session: Mapped["AISession"] = relationship("AISession", back_populates="suggestions")
