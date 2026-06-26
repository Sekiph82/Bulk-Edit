from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, field_validator

VALID_RULE_TYPES = {
    "percentage_adjustment",
    "fixed_amount_adjustment",
    "set_price",
    "reference_price",
}

VALID_ROUNDING_RULES = {
    "none",
    "ending_99",
    "ending_95",
    "nearest_50",
    "nearest_100",
}

VALID_REFERENCE_MODES = {
    "match",
    "reference_minus_percent",
    "reference_plus_percent",
    "reference_minus_amount",
    "reference_plus_amount",
}


class DynamicPricingJobCreate(BaseModel):
    selected_listing_ids: list[str]
    rule_type: str
    rule_payload: dict[str, Any]
    safety_payload: Optional[dict[str, Any]] = None

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v: str) -> str:
        if v not in VALID_RULE_TYPES:
            raise ValueError(f"rule_type must be one of: {sorted(VALID_RULE_TYPES)}")
        return v

    @field_validator("selected_listing_ids")
    @classmethod
    def validate_listing_ids(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("selected_listing_ids cannot be empty")
        return v


class DynamicPricingJobOut(BaseModel):
    id: str
    organization_id: str
    user_id: Optional[str]
    status: str
    selected_listing_ids: Any
    rule_type: str
    rule_payload: Any
    safety_payload: Any
    row_count: int
    recommended_count: int
    skipped_count: int
    warning_count: int
    invalid_count: int
    converted_bulk_edit_session_id: Optional[str]
    error_message: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DynamicPricingRecommendationOut(BaseModel):
    id: str
    organization_id: str
    dynamic_pricing_job_id: str
    listing_id: Optional[str]
    etsy_listing_id: Optional[str]
    listing_title: Optional[str]
    currency_code: Optional[str]
    current_price_amount: Optional[int]
    recommended_price_amount: Optional[int]
    reference_price_amount: Optional[int]
    cost_amount: Optional[int]
    margin_percent: Optional[Decimal]
    diff_amount: Optional[int]
    diff_percent: Optional[Decimal]
    status: str
    reason: Optional[str]
    calculation_details: Optional[Any]
    validation_errors: Optional[list[str]]
    validation_warnings: Optional[list[str]]
    decided_at: Optional[datetime]
    decided_by_user_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DynamicPricingRecommendationPageOut(BaseModel):
    items: list[DynamicPricingRecommendationOut]
    total: int
    page: int
    per_page: int
    job_id: str


class DynamicPricingConvertResponse(BaseModel):
    bulk_edit_session_id: str
    converted_count: int
    created_changes: int
    message: str


class DynamicPricingSummaryOut(BaseModel):
    job_id: str
    total_listings: int
    current_total_price: int
    recommended_total_price: int
    total_diff_amount: int
    total_diff_percent: Optional[Decimal]
    recommended_count: int
    accepted_count: int
    skipped_count: int
    warning_count: int
    invalid_count: int
    converted_count: int
