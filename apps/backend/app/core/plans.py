from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

PLAN_LIMITS: dict[str, dict[str, Any]] = {
    "free": {
        "max_shops": 1,
        "max_listings": 25,
        "bulk_edits_per_month": 10,
        "ai_credits_per_month": 5,
        "media_assets": 25,
        "can_bulk_edit_photos": False,
        "can_bulk_edit_variations": False,
        "can_use_magic_revert": False,
        "can_use_dynamic_pricing": False,
        "can_schedule_jobs": False,
        "dynamic_pricing_jobs_per_month": 0,
        "max_scheduled_jobs": 0,
    },
    "basic_monthly": {
        "max_shops": 3,
        "max_listings": 1000,
        "bulk_edits_per_month": 250,
        "ai_credits_per_month": 250,
        "media_assets": 1000,
        "can_bulk_edit_photos": True,
        "can_bulk_edit_variations": False,
        "can_use_magic_revert": True,
        "can_use_dynamic_pricing": False,
        "can_schedule_jobs": True,
        "dynamic_pricing_jobs_per_month": 0,
        "max_scheduled_jobs": 3,
    },
    "pro_monthly": {
        "max_shops": 10,
        "max_listings": 10000,
        "bulk_edits_per_month": 5000,
        "ai_credits_per_month": 2000,
        "media_assets": 10000,
        "can_bulk_edit_photos": True,
        "can_bulk_edit_variations": True,
        "can_use_magic_revert": True,
        "can_use_dynamic_pricing": True,
        "can_schedule_jobs": True,
        "dynamic_pricing_jobs_per_month": 100,
        "max_scheduled_jobs": 25,
    },
}

# Yearly plans share limits with their monthly counterparts
PLAN_LIMITS["basic_yearly"] = PLAN_LIMITS["basic_monthly"]
PLAN_LIMITS["pro_yearly"] = PLAN_LIMITS["pro_monthly"]

VALID_PAID_PLANS = {"basic_monthly", "pro_monthly", "basic_yearly", "pro_yearly"}
ALL_PLANS = set(PLAN_LIMITS.keys())

PLAN_DISPLAY_NAMES = {
    "free": "Free",
    "basic_monthly": "Basic (Monthly)",
    "pro_monthly": "Pro (Monthly)",
    "basic_yearly": "Basic (Yearly)",
    "pro_yearly": "Pro (Yearly)",
}


def get_plan_limits(plan: str) -> dict[str, Any]:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


async def get_effective_plan(db: AsyncSession, org_id: str) -> str:
    """
    The plan that should actually gate features for this org: an active
    (non-revoked, non-expired) comp grant overrides the real subscription
    plan, else the subscription plan, else "free". Mirrors
    app.services.admin.get_effective_access's resolution exactly -- that
    function returns the full admin-facing view (comp details, Stripe
    status); this returns just the plan string for feature-gating call
    sites that only need to know which limits apply (e.g. etsy_sync).
    """
    from app.models.comp_access_grant import CompAccessGrant
    from app.models.subscription import Subscription

    sub = (await db.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )).scalar_one_or_none()

    comp = (await db.execute(
        select(CompAccessGrant).where(
            CompAccessGrant.organization_id == org_id,
            CompAccessGrant.revoked_at.is_(None),
        ).order_by(desc(CompAccessGrant.created_at))
    )).scalars().first()

    if comp:
        ends_at = comp.ends_at
        if ends_at and ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        if not ends_at or ends_at > datetime.now(timezone.utc):
            return comp.comp_plan

    return sub.plan if sub else "free"
