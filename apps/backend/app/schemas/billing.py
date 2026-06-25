from datetime import datetime
from typing import Any
from pydantic import BaseModel, field_validator

from app.core.plans import ALL_PLANS, VALID_PAID_PLANS


class PlanLimitsResponse(BaseModel):
    max_shops: int
    max_listings: int
    bulk_edits_per_month: int
    ai_credits_per_month: int
    media_assets: int
    can_bulk_edit_photos: bool
    can_bulk_edit_variations: bool
    can_use_magic_revert: bool
    can_use_dynamic_pricing: bool
    can_schedule_jobs: bool


class PlanResponse(BaseModel):
    plan: str
    display_name: str
    limits: PlanLimitsResponse


class PlansResponse(BaseModel):
    plans: dict[str, PlanLimitsResponse]


class SubscriptionResponse(BaseModel):
    id: str
    organization_id: str
    plan: str
    status: str
    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    limits: dict[str, Any]

    model_config = {"from_attributes": True}


class CheckoutRequest(BaseModel):
    plan: str

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: str) -> str:
        if v not in ALL_PLANS:
            raise ValueError(f"Invalid plan. Must be one of: {', '.join(sorted(ALL_PLANS))}")
        return v


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


class UsageResponse(BaseModel):
    period_key: str
    usage: dict[str, int]
    limits: dict[str, Any]
