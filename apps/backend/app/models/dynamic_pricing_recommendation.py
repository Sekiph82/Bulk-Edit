import uuid
from sqlalchemy import String, Text, Integer, DateTime, JSON, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class DynamicPricingRecommendation(Base, TimestampMixin):
    __tablename__ = "dynamic_pricing_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    dynamic_pricing_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("dynamic_pricing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True, index=True)
    etsy_listing_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    listing_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    current_price_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_price_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_price_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    margin_percent: Mapped[object] = mapped_column(Numeric(10, 4), nullable=True)
    diff_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diff_percent: Mapped[object] = mapped_column(Numeric(10, 4), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="recommended", index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    calculation_details: Mapped[object] = mapped_column(JSON, nullable=True)
    validation_errors: Mapped[object] = mapped_column(JSON, nullable=True)
    validation_warnings: Mapped[object] = mapped_column(JSON, nullable=True)
    decided_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    job: Mapped["DynamicPricingJob"] = relationship("DynamicPricingJob", back_populates="recommendations")
