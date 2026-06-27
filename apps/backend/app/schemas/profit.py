from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class ProfitStatus(str, Enum):
    PROFITABLE = "profitable"
    LOW_MARGIN = "low_margin"
    LOSS = "loss"
    MISSING_COSTS = "missing_costs"


class CostProfileBase(BaseModel):
    name: str = "Default"
    currency: str = "USD"
    transaction_fee_percent: Decimal = Decimal("0.065")
    payment_fee_percent: Decimal = Decimal("0.030")
    payment_fixed_fee: Decimal = Decimal("0.25")
    listing_fee: Decimal = Decimal("0.20")
    offsite_ads_percent: Decimal = Decimal("0.15")
    currency_conversion_percent: Decimal = Decimal("0.025")
    default_shipping_cost: Decimal = Decimal("0.0")
    default_packaging_cost: Decimal = Decimal("0.0")
    target_margin_percent: Decimal = Decimal("0.30")
    is_default: bool = False


class CostProfileCreate(CostProfileBase):
    pass


class CostProfileUpdate(CostProfileBase):
    pass


class CostProfileResponse(CostProfileBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ListingCostUpdate(BaseModel):
    product_cost: Decimal = Decimal("0.0")
    shipping_cost: Decimal = Decimal("0.0")
    packaging_cost: Decimal = Decimal("0.0")
    ad_cost: Decimal = Decimal("0.0")
    other_cost: Decimal = Decimal("0.0")
    include_offsite_ads: bool = False
    cost_profile_id: Optional[str] = None
    notes: Optional[str] = None


class ProfitCalculation(BaseModel):
    listing_id: str
    title: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    sale_price: Decimal
    shipping_charged: Decimal
    gross_revenue: Decimal
    product_cost: Decimal
    shipping_cost: Decimal
    packaging_cost: Decimal
    ad_cost: Decimal
    other_cost: Decimal
    etsy_transaction_fee: Decimal
    etsy_payment_fee: Decimal
    etsy_listing_fee: Decimal
    etsy_offsite_ads_fee: Decimal
    total_etsy_fees: Decimal
    total_costs: Decimal
    net_profit: Decimal
    margin_percent: Decimal
    break_even_price: Decimal
    recommended_min_price: Decimal
    roi_percent: Decimal
    status: ProfitStatus


class ProfitListingRow(BaseModel):
    listing_id: str
    title: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    product_cost: Optional[Decimal] = None
    shipping_cost: Optional[Decimal] = None
    total_etsy_fees: Optional[Decimal] = None
    net_profit: Optional[Decimal] = None
    margin_percent: Optional[Decimal] = None
    break_even_price: Optional[Decimal] = None
    recommended_min_price: Optional[Decimal] = None
    status: ProfitStatus
    health_score: Optional[int] = None


class ProfitListingPage(BaseModel):
    items: List[ProfitListingRow]
    total: int
    page: int
    page_size: int


class ProfitSummary(BaseModel):
    listings_with_costs: int
    listings_missing_costs: int
    average_margin: Optional[Decimal] = None
    low_margin_count: int
    loss_making_count: int
    estimated_total_profit: Optional[Decimal] = None
    currency: str
