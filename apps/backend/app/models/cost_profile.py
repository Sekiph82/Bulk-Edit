from sqlalchemy import Boolean, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin
import uuid


class CostProfile(Base, TimestampMixin):
    __tablename__ = "cost_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Default")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    transaction_fee_percent: Mapped[object] = mapped_column(Numeric(6, 5), nullable=False, default="0.06500")
    payment_fee_percent: Mapped[object] = mapped_column(Numeric(6, 5), nullable=False, default="0.03000")
    payment_fixed_fee: Mapped[object] = mapped_column(Numeric(10, 4), nullable=False, default="0.2500")
    listing_fee: Mapped[object] = mapped_column(Numeric(10, 4), nullable=False, default="0.2000")
    offsite_ads_percent: Mapped[object] = mapped_column(Numeric(6, 5), nullable=False, default="0.15000")
    currency_conversion_percent: Mapped[object] = mapped_column(Numeric(6, 5), nullable=False, default="0.02500")
    default_shipping_cost: Mapped[object] = mapped_column(Numeric(10, 4), nullable=False, default="0.0000")
    default_packaging_cost: Mapped[object] = mapped_column(Numeric(10, 4), nullable=False, default="0.0000")
    target_margin_percent: Mapped[object] = mapped_column(Numeric(6, 5), nullable=False, default="0.30000")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
