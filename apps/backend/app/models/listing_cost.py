from sqlalchemy import Boolean, String, Numeric, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin
import uuid


class ListingCost(Base, TimestampMixin):
    __tablename__ = "listing_costs"
    __table_args__ = (
        UniqueConstraint("organization_id", "listing_id", name="uq_listing_costs_org_listing"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    product_cost: Mapped[object] = mapped_column(Numeric(10, 4), nullable=False, default="0.0000")
    shipping_cost: Mapped[object] = mapped_column(Numeric(10, 4), nullable=False, default="0.0000")
    packaging_cost: Mapped[object] = mapped_column(Numeric(10, 4), nullable=False, default="0.0000")
    ad_cost: Mapped[object] = mapped_column(Numeric(10, 4), nullable=False, default="0.0000")
    other_cost: Mapped[object] = mapped_column(Numeric(10, 4), nullable=False, default="0.0000")
    include_offsite_ads: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cost_profile_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cost_profiles.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
