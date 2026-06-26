import uuid
from sqlalchemy import String, Text, Integer, ForeignKey, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class AISession(Base, TimestampMixin):
    __tablename__ = "ai_sessions"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    listing_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True, index=True)
    tool: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    input_payload: Mapped[object] = mapped_column(JSON, nullable=False, default=dict)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestion_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    suggestions: Mapped[list["AISuggestion"]] = relationship("AISuggestion", back_populates="session", cascade="all, delete-orphan")
