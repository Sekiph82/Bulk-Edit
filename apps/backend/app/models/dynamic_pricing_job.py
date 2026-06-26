import uuid
from sqlalchemy import String, Text, Integer, DateTime, JSON, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class DynamicPricingJob(Base, TimestampMixin):
    __tablename__ = "dynamic_pricing_jobs"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    selected_listing_ids: Mapped[object] = mapped_column(JSON, nullable=False, default=list)
    rule_type: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_payload: Mapped[object] = mapped_column(JSON, nullable=False)
    safety_payload: Mapped[object] = mapped_column(JSON, nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recommended_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    converted_bulk_edit_session_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)

    recommendations: Mapped[list["DynamicPricingRecommendation"]] = relationship(
        "DynamicPricingRecommendation", back_populates="job", cascade="all, delete-orphan"
    )
