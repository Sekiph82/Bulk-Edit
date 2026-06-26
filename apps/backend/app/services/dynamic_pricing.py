"""
Dynamic Pricing service.

SAFETY: Dynamic pricing NEVER writes directly to Etsy.
Approved recommendations are converted to a BulkEditSession (draft) only.
User must run existing bulk edit preview + apply flow before any Etsy write.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bulk_edit_change import BulkEditChange
from app.models.bulk_edit_session import BulkEditSession
from app.models.dynamic_pricing_job import DynamicPricingJob
from app.models.dynamic_pricing_recommendation import DynamicPricingRecommendation
from app.models.listing import Listing
from app.services.billing import ensure_subscription_exists, get_or_create_usage


VALID_RULE_TYPES = {
    "percentage_adjustment",
    "fixed_amount_adjustment",
    "set_price",
    "reference_price",
}

VALID_ROUNDING_RULES = {
    "none", "ending_99", "ending_95", "nearest_50", "nearest_100",
}


class DynamicPricingError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ── Billing gate ──────────────────────────────────────────────────────────────

async def assert_dynamic_pricing_allowed(org_id: str, db: AsyncSession) -> None:
    sub = await ensure_subscription_exists(org_id, db)
    from app.core.plans import get_plan_limits
    limits = get_plan_limits(sub.plan)
    if not limits.get("can_use_dynamic_pricing", False):
        raise DynamicPricingError(
            "Dynamic pricing requires a Pro plan. Upgrade to access this feature.", 402
        )
    monthly_limit = limits.get("dynamic_pricing_jobs_per_month", 0)
    counter = await get_or_create_usage(org_id, db)
    if counter.dynamic_pricing_jobs_used >= monthly_limit:
        raise DynamicPricingError(
            f"Dynamic pricing job limit reached ({monthly_limit}/month). Upgrade for more.", 402
        )


# ── Rounding ──────────────────────────────────────────────────────────────────

def apply_rounding_rule(amount_cents: int, rounding_rule: str | None) -> int:
    if not rounding_rule or rounding_rule == "none":
        return amount_cents

    if rounding_rule == "ending_99":
        if amount_cents % 100 == 99:
            return amount_cents
        remainder = amount_cents % 100
        if remainder == 0:
            return max(0, amount_cents - 1)
        same_99 = (amount_cents // 100) * 100 + 99
        prev_99 = (amount_cents // 100) * 100 - 1
        if prev_99 < 0:
            return same_99
        dist_same = same_99 - amount_cents
        dist_prev = amount_cents - prev_99
        return same_99 if dist_same <= dist_prev else prev_99

    if rounding_rule == "ending_95":
        if amount_cents % 100 == 95:
            return amount_cents
        remainder = amount_cents % 100
        if remainder < 95:
            same_95 = (amount_cents // 100) * 100 + 95
            prev_95 = (amount_cents // 100) * 100 - 5
            if prev_95 < 0:
                return same_95
            dist_same = same_95 - amount_cents
            dist_prev = amount_cents - prev_95
            return same_95 if dist_same <= dist_prev else prev_95
        else:
            # remainder > 95: between same .95 (below) and next .95 (above)
            same_95 = (amount_cents // 100) * 100 + 95
            next_95 = (amount_cents // 100 + 1) * 100 + 95
            dist_same = amount_cents - same_95
            dist_next = next_95 - amount_cents
            return same_95 if dist_same <= dist_next else next_95

    if rounding_rule == "nearest_50":
        return ((amount_cents + 25) // 50) * 50

    if rounding_rule == "nearest_100":
        return ((amount_cents + 50) // 100) * 100

    return amount_cents


# ── Safety guardrails ─────────────────────────────────────────────────────────

def apply_margin_floor(
    amount_cents: int,
    cost_amount: int | None,
    minimum_margin_percent: float | None,
    minimum_price_amount: int | None,
) -> tuple[int, list[str]]:
    warnings: list[str] = []
    result = amount_cents

    if minimum_price_amount is not None and result < minimum_price_amount:
        result = minimum_price_amount
        warnings.append(
            f"Price raised to minimum floor of {minimum_price_amount} cents."
        )

    if cost_amount is not None and minimum_margin_percent is not None and minimum_margin_percent > 0:
        # Required price = cost / (1 - margin_pct/100)
        margin_dec = Decimal(str(minimum_margin_percent)) / 100
        if margin_dec >= 1:
            margin_dec = Decimal("0.999")
        min_price_for_margin = int(
            (Decimal(str(cost_amount)) / (1 - margin_dec)).to_integral_value(ROUND_HALF_UP)
        )
        if result < min_price_for_margin:
            result = min_price_for_margin
            warnings.append(
                f"Price raised to meet {minimum_margin_percent}% margin floor ({min_price_for_margin} cents)."
            )

    return result, warnings


def apply_price_cap(amount_cents: int, max_price_amount: int | None) -> tuple[int, list[str]]:
    warnings: list[str] = []
    if max_price_amount is not None and amount_cents > max_price_amount:
        return max_price_amount, [f"Price capped at maximum of {max_price_amount} cents."]
    return amount_cents, warnings


def calculate_diff(current: int, recommended: int) -> tuple[int, Decimal | None]:
    diff_amount = recommended - current
    if current > 0:
        diff_pct = (Decimal(str(diff_amount)) / Decimal(str(current)) * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        diff_pct = None
    return diff_amount, diff_pct


# ── Core calculation ──────────────────────────────────────────────────────────

def calculate_recommendation_for_listing(
    listing: Listing,
    rule_type: str,
    rule_payload: dict[str, Any],
    safety_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Returns a dict with keys:
      status, recommended_price_amount, reference_price_amount,
      reason, warnings, calculation_details, validation_errors
    """
    safety = safety_payload or {}
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}

    # Variation listings: skip
    if listing.has_variations:
        return {
            "status": "skipped",
            "recommended_price_amount": None,
            "reference_price_amount": None,
            "reason": "Variation pricing is handled in Variation Editor.",
            "warnings": [],
            "validation_errors": [],
            "calculation_details": {},
        }

    # No price: invalid
    if listing.price_amount is None:
        return {
            "status": "invalid",
            "recommended_price_amount": None,
            "reference_price_amount": None,
            "reason": "Listing has no current price.",
            "warnings": [],
            "validation_errors": ["Listing has no current price."],
            "calculation_details": {},
        }

    current = listing.price_amount
    ref_price: int | None = None
    raw_price: int | None = None

    if rule_type == "percentage_adjustment":
        percent = float(rule_payload.get("percent", 0))
        raw_price = int(current * (1 + percent / 100))
        details = {"rule": "percentage_adjustment", "percent": percent, "current": current}

    elif rule_type == "fixed_amount_adjustment":
        delta = int(rule_payload.get("amount_delta", 0))
        raw_price = current + delta
        details = {"rule": "fixed_amount_adjustment", "amount_delta": delta, "current": current}

    elif rule_type == "set_price":
        raw_price = int(rule_payload.get("price_amount", 0))
        details = {"rule": "set_price", "price_amount": raw_price, "current": current}

    elif rule_type == "reference_price":
        mode = rule_payload.get("mode", "match")
        per_listing = rule_payload.get("per_listing_reference_prices", {}) or {}
        ref_price = per_listing.get(str(listing.id)) or per_listing.get(listing.etsy_listing_id)
        if ref_price is None:
            ref_price = rule_payload.get("default_reference_price_amount")
        if ref_price is None:
            return {
                "status": "invalid",
                "recommended_price_amount": None,
                "reference_price_amount": None,
                "reason": "No reference price provided for this listing.",
                "warnings": [],
                "validation_errors": ["No reference price provided."],
                "calculation_details": {},
            }
        ref_price = int(ref_price)
        if mode == "match":
            raw_price = ref_price
        elif mode == "reference_minus_percent":
            pct = float(rule_payload.get("percent", 0))
            raw_price = int(ref_price * (1 - pct / 100))
        elif mode == "reference_plus_percent":
            pct = float(rule_payload.get("percent", 0))
            raw_price = int(ref_price * (1 + pct / 100))
        elif mode == "reference_minus_amount":
            delta = int(rule_payload.get("amount_delta", 0))
            raw_price = ref_price - delta
        elif mode == "reference_plus_amount":
            delta = int(rule_payload.get("amount_delta", 0))
            raw_price = ref_price + delta
        else:
            raw_price = ref_price
        details = {"rule": "reference_price", "mode": mode, "reference_price": ref_price, "current": current}
    else:
        return {
            "status": "invalid",
            "recommended_price_amount": None,
            "reference_price_amount": None,
            "reason": f"Unknown rule type: {rule_type}",
            "warnings": [],
            "validation_errors": [f"Unknown rule type: {rule_type}"],
            "calculation_details": {},
        }

    if raw_price < 0:
        return {
            "status": "invalid",
            "recommended_price_amount": None,
            "reference_price_amount": ref_price,
            "reason": "Calculated price is negative.",
            "warnings": [],
            "validation_errors": ["Calculated price is negative."],
            "calculation_details": details,
        }

    details["raw_price"] = raw_price

    # Apply rounding
    rounding_rule = safety.get("rounding_rule", "none")
    rounded = apply_rounding_rule(raw_price, rounding_rule)
    details["rounded_price"] = rounded
    if rounded != raw_price:
        details["rounding_applied"] = rounding_rule

    # Apply margin floor + price floor
    cost_amount = safety.get("cost_amount")
    min_margin_pct = safety.get("minimum_margin_percent")
    min_price = safety.get("minimum_price_amount")
    floored, floor_warnings = apply_margin_floor(rounded, cost_amount, min_margin_pct, min_price)
    warnings.extend(floor_warnings)

    # Apply price cap
    max_price = safety.get("max_price_amount")
    capped, cap_warnings = apply_price_cap(floored, max_price)
    warnings.extend(cap_warnings)

    if capped < 0:
        errors.append("Final price is negative after guardrails.")
        return {
            "status": "invalid",
            "recommended_price_amount": None,
            "reference_price_amount": ref_price,
            "reason": "Final price is negative after guardrails.",
            "warnings": warnings,
            "validation_errors": errors,
            "calculation_details": details,
        }

    details["final_price"] = capped

    # Determine status
    if errors:
        status = "invalid"
        reason = "; ".join(errors)
    elif warnings:
        status = "warning"
        reason = "; ".join(warnings)
    elif capped == current:
        status = "warning"
        reason = "No price change."
    else:
        status = "recommended"
        reason = None

    return {
        "status": status,
        "recommended_price_amount": capped,
        "reference_price_amount": ref_price,
        "reason": reason,
        "warnings": warnings,
        "validation_errors": errors,
        "calculation_details": details,
    }


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def create_dynamic_pricing_job(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    selected_listing_ids: list[str],
    rule_type: str,
    rule_payload: dict[str, Any],
    safety_payload: dict[str, Any] | None = None,
) -> DynamicPricingJob:
    if not selected_listing_ids:
        raise DynamicPricingError("selected_listing_ids cannot be empty.")

    if rule_type not in VALID_RULE_TYPES:
        raise DynamicPricingError(f"Unknown rule_type: {rule_type}.")

    # Validate all listings belong to org
    deduped = list(dict.fromkeys(selected_listing_ids))
    result = await db.execute(
        select(Listing).where(
            Listing.id.in_(deduped),
            Listing.organization_id == organization_id,
        )
    )
    found = result.scalars().all()
    if len(found) != len(deduped):
        raise DynamicPricingError(
            "One or more listing IDs not found or do not belong to your organization.", 404
        )

    # Validate safety_payload rounding rule if provided
    if safety_payload:
        rr = safety_payload.get("rounding_rule", "none")
        if rr and rr not in VALID_ROUNDING_RULES:
            raise DynamicPricingError(
                f"Invalid rounding_rule '{rr}'. Valid: {sorted(VALID_ROUNDING_RULES)}."
            )
        # Validate guardrail values
        for key in ("minimum_price_amount", "max_price_amount", "cost_amount"):
            val = safety_payload.get(key)
            if val is not None and int(val) < 0:
                raise DynamicPricingError(f"{key} must be >= 0.")
        min_p = safety_payload.get("minimum_price_amount")
        max_p = safety_payload.get("max_price_amount")
        if min_p is not None and max_p is not None and int(max_p) < int(min_p):
            raise DynamicPricingError("max_price_amount must be >= minimum_price_amount.")
        min_m = safety_payload.get("minimum_margin_percent")
        if min_m is not None and float(min_m) < 0:
            raise DynamicPricingError("minimum_margin_percent must be >= 0.")

    # Validate rule_payload
    _validate_rule_payload(rule_type, rule_payload)

    job = DynamicPricingJob(
        organization_id=organization_id,
        user_id=user_id,
        status="draft",
        selected_listing_ids=deduped,
        rule_type=rule_type,
        rule_payload=rule_payload,
        safety_payload=safety_payload,
        row_count=len(deduped),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


def _validate_rule_payload(rule_type: str, payload: dict[str, Any]) -> None:
    if rule_type == "percentage_adjustment":
        pct = payload.get("percent")
        if pct is None:
            raise DynamicPricingError("rule_payload.percent is required for percentage_adjustment.")
        pct = float(pct)
        if pct < -90 or pct > 500:
            raise DynamicPricingError("percent must be between -90 and 500.")

    elif rule_type == "fixed_amount_adjustment":
        if "amount_delta" not in payload:
            raise DynamicPricingError("rule_payload.amount_delta is required for fixed_amount_adjustment.")

    elif rule_type == "set_price":
        price = payload.get("price_amount")
        if price is None:
            raise DynamicPricingError("rule_payload.price_amount is required for set_price.")
        if int(price) < 0:
            raise DynamicPricingError("price_amount must be >= 0.")

    elif rule_type == "reference_price":
        mode = payload.get("mode")
        from app.schemas.dynamic_pricing import VALID_REFERENCE_MODES
        if mode not in VALID_REFERENCE_MODES:
            raise DynamicPricingError(
                f"reference_price mode must be one of: {sorted(VALID_REFERENCE_MODES)}."
            )


async def generate_dynamic_pricing_preview(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    job_id: str,
) -> DynamicPricingJob:
    job = await get_dynamic_pricing_job(db, organization_id, job_id)

    if job.status == "converted":
        raise DynamicPricingError("Job already converted to bulk edit session.", 400)
    if job.status == "canceled":
        raise DynamicPricingError("Cannot preview a canceled job.", 400)

    # Billing gate
    await assert_dynamic_pricing_allowed(organization_id, db)

    # Load listings
    listing_ids: list[str] = list(job.selected_listing_ids or [])
    result = await db.execute(
        select(Listing).where(
            Listing.id.in_(listing_ids),
            Listing.organization_id == organization_id,
        )
    )
    listings = {l.id: l for l in result.scalars().all()}

    # Delete existing recommendations for this job (re-generate)
    existing_recs = await db.execute(
        select(DynamicPricingRecommendation).where(
            DynamicPricingRecommendation.dynamic_pricing_job_id == job_id
        )
    )
    for rec in existing_recs.scalars().all():
        await db.delete(rec)
    await db.flush()

    counts = {"recommended": 0, "skipped": 0, "warning": 0, "invalid": 0}

    for lid in listing_ids:
        listing = listings.get(lid)
        if not listing:
            rec = DynamicPricingRecommendation(
                organization_id=organization_id,
                dynamic_pricing_job_id=job_id,
                listing_id=lid,
                status="invalid",
                reason="Listing not found.",
                validation_errors=["Listing not found."],
            )
            db.add(rec)
            counts["invalid"] += 1
            continue

        calc = calculate_recommendation_for_listing(
            listing, job.rule_type, job.rule_payload, job.safety_payload
        )

        rec_price = calc["recommended_price_amount"]
        diff_amount, diff_pct = (None, None)
        if rec_price is not None and listing.price_amount is not None:
            diff_amount, diff_pct = calculate_diff(listing.price_amount, rec_price)

        margin_pct = None
        if rec_price and job.safety_payload and job.safety_payload.get("cost_amount"):
            cost = job.safety_payload["cost_amount"]
            if rec_price > 0:
                margin_pct = ((rec_price - cost) / rec_price * 100)

        rec = DynamicPricingRecommendation(
            organization_id=organization_id,
            dynamic_pricing_job_id=job_id,
            listing_id=listing.id,
            etsy_listing_id=listing.etsy_listing_id,
            listing_title=listing.title,
            currency_code=listing.currency_code or "USD",
            current_price_amount=listing.price_amount,
            recommended_price_amount=rec_price,
            reference_price_amount=calc["reference_price_amount"],
            cost_amount=job.safety_payload.get("cost_amount") if job.safety_payload else None,
            margin_percent=margin_pct,
            diff_amount=diff_amount,
            diff_percent=diff_pct,
            status=calc["status"],
            reason=calc["reason"],
            calculation_details=calc["calculation_details"],
            validation_errors=calc["validation_errors"] or None,
            validation_warnings=calc["warnings"] or None,
        )
        db.add(rec)

        status_key = calc["status"]
        if status_key not in counts:
            status_key = "recommended"
        counts[status_key] = counts.get(status_key, 0) + 1

    # Increment usage
    counter = await get_or_create_usage(organization_id, db)
    counter.dynamic_pricing_jobs_used = (counter.dynamic_pricing_jobs_used or 0) + 1
    db.add(counter)

    job.status = "preview_ready"
    job.recommended_count = counts.get("recommended", 0)
    job.skipped_count = counts.get("skipped", 0)
    job.warning_count = counts.get("warning", 0)
    job.invalid_count = counts.get("invalid", 0)
    job.completed_at = datetime.now(timezone.utc)
    db.add(job)

    await db.commit()
    await db.refresh(job)
    return job


async def accept_recommendation(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    recommendation_id: str,
) -> DynamicPricingRecommendation:
    rec = await _get_recommendation(db, organization_id, recommendation_id)
    if rec.status in ("accepted", "converted"):
        return rec
    if rec.status in ("skipped", "invalid"):
        raise DynamicPricingError(
            f"Cannot accept a recommendation with status '{rec.status}'.", 400
        )
    rec.status = "accepted"
    rec.decided_at = datetime.now(timezone.utc)
    rec.decided_by_user_id = user_id
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


async def reject_recommendation(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    recommendation_id: str,
) -> DynamicPricingRecommendation:
    rec = await _get_recommendation(db, organization_id, recommendation_id)
    if rec.status == "converted":
        raise DynamicPricingError("Cannot reject a converted recommendation.", 400)
    rec.status = "rejected"
    rec.decided_at = datetime.now(timezone.utc)
    rec.decided_by_user_id = user_id
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


async def accept_all_recommendations(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    job_id: str,
) -> int:
    """Accept all recommended/warning rows. Returns count accepted."""
    job = await get_dynamic_pricing_job(db, organization_id, job_id)
    result = await db.execute(
        select(DynamicPricingRecommendation).where(
            DynamicPricingRecommendation.dynamic_pricing_job_id == job_id,
            DynamicPricingRecommendation.status.in_(["recommended", "warning"]),
        )
    )
    recs = result.scalars().all()
    now = datetime.now(timezone.utc)
    for rec in recs:
        rec.status = "accepted"
        rec.decided_at = now
        rec.decided_by_user_id = user_id
        db.add(rec)
    await db.commit()
    return len(recs)


async def convert_dynamic_pricing_job_to_bulk_edit_session(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    job_id: str,
) -> tuple[BulkEditSession, int, int]:
    """
    SAFETY: Creates BulkEditSession (draft) only.
    Does NOT write to Etsy. Does NOT update Listing.price_amount.
    User must run existing bulk edit preview + apply flow to publish.
    """
    job = await get_dynamic_pricing_job(db, organization_id, job_id)

    if job.status not in ("preview_ready", "converted"):
        raise DynamicPricingError(
            "Job must be preview_ready before converting. Run preview first.", 400
        )
    if job.status == "converted":
        raise DynamicPricingError("Job already converted.", 400)

    # Get accepted recommendations only
    result = await db.execute(
        select(DynamicPricingRecommendation).where(
            DynamicPricingRecommendation.dynamic_pricing_job_id == job_id,
            DynamicPricingRecommendation.status == "accepted",
        )
    )
    accepted = result.scalars().all()

    if not accepted:
        raise DynamicPricingError(
            "No accepted recommendations. Accept at least one recommendation before converting.", 400
        )

    listing_ids = [r.listing_id for r in accepted if r.listing_id]

    # Create BulkEditSession (draft — NOT applied to Etsy)
    session = BulkEditSession(
        organization_id=organization_id,
        created_by_user_id=user_id,
        name=f"Dynamic Pricing Job {job_id[:8]}",
        status="draft",
        selected_listing_ids=listing_ids,
        selected_count=len(listing_ids),
    )
    db.add(session)
    await db.flush()

    # Create one BulkEditChange per accepted recommendation
    # target_listing_ids=[listing_id] so each listing gets its own price
    change_count = 0
    for rec in accepted:
        if rec.listing_id is None or rec.recommended_price_amount is None:
            continue
        change = BulkEditChange(
            bulk_edit_session_id=session.id,
            field_name="price_amount",
            operation="set",
            new_value=rec.recommended_price_amount,
            operation_value=rec.recommended_price_amount,
            validation_status="pending",
            target_listing_ids=[rec.listing_id],
        )
        db.add(change)
        change_count += 1

        # Mark recommendation converted
        rec.status = "converted"
        db.add(rec)

    job.status = "converted"
    job.converted_bulk_edit_session_id = session.id
    db.add(job)

    await db.commit()
    await db.refresh(session)
    return session, len(accepted), change_count


# ── Query helpers ─────────────────────────────────────────────────────────────

async def list_dynamic_pricing_jobs(
    db: AsyncSession,
    organization_id: str,
) -> list[DynamicPricingJob]:
    result = await db.execute(
        select(DynamicPricingJob)
        .where(DynamicPricingJob.organization_id == organization_id)
        .order_by(DynamicPricingJob.created_at.desc())
    )
    return list(result.scalars().all())


async def get_dynamic_pricing_job(
    db: AsyncSession,
    organization_id: str,
    job_id: str,
) -> DynamicPricingJob:
    result = await db.execute(
        select(DynamicPricingJob).where(
            DynamicPricingJob.id == job_id,
            DynamicPricingJob.organization_id == organization_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise DynamicPricingError("Dynamic pricing job not found.", 404)
    return job


async def get_dynamic_pricing_recommendations(
    db: AsyncSession,
    organization_id: str,
    job_id: str,
    page: int = 1,
    per_page: int = 50,
    status: str | None = None,
) -> tuple[list[DynamicPricingRecommendation], int]:
    await get_dynamic_pricing_job(db, organization_id, job_id)

    q = select(DynamicPricingRecommendation).where(
        DynamicPricingRecommendation.dynamic_pricing_job_id == job_id
    )
    if status:
        q = q.where(DynamicPricingRecommendation.status == status)

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar_one()

    q = q.order_by(DynamicPricingRecommendation.created_at).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_dynamic_pricing_summary(
    db: AsyncSession,
    organization_id: str,
    job_id: str,
) -> dict:
    await get_dynamic_pricing_job(db, organization_id, job_id)

    result = await db.execute(
        select(DynamicPricingRecommendation).where(
            DynamicPricingRecommendation.dynamic_pricing_job_id == job_id
        )
    )
    recs = result.scalars().all()

    current_total = sum(r.current_price_amount or 0 for r in recs if r.current_price_amount)
    rec_total = sum(r.recommended_price_amount or 0 for r in recs if r.recommended_price_amount)
    diff_total = rec_total - current_total
    diff_pct = None
    if current_total > 0:
        diff_pct = Decimal(str(diff_total)) / Decimal(str(current_total)) * 100

    counts: dict[str, int] = {}
    for r in recs:
        counts[r.status] = counts.get(r.status, 0) + 1

    return {
        "job_id": job_id,
        "total_listings": len(recs),
        "current_total_price": current_total,
        "recommended_total_price": rec_total,
        "total_diff_amount": diff_total,
        "total_diff_percent": diff_pct,
        "recommended_count": counts.get("recommended", 0),
        "accepted_count": counts.get("accepted", 0),
        "skipped_count": counts.get("skipped", 0),
        "warning_count": counts.get("warning", 0),
        "invalid_count": counts.get("invalid", 0),
        "converted_count": counts.get("converted", 0),
    }


async def _get_recommendation(
    db: AsyncSession,
    organization_id: str,
    recommendation_id: str,
) -> DynamicPricingRecommendation:
    result = await db.execute(
        select(DynamicPricingRecommendation).where(
            DynamicPricingRecommendation.id == recommendation_id,
            DynamicPricingRecommendation.organization_id == organization_id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise DynamicPricingError("Recommendation not found.", 404)
    return rec
