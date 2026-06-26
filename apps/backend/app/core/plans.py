from typing import Any

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
