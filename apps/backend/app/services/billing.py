from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import stripe
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.plans import get_plan_limits
from app.models.billing_event import BillingEvent
from app.models.subscription import Subscription
from app.models.usage_counter import UsageCounter


class BillingError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _current_period_key() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m")


async def get_subscription(org_id: str, db: AsyncSession) -> Subscription | None:
    result = await db.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    return result.scalar_one_or_none()


async def ensure_subscription_exists(org_id: str, db: AsyncSession) -> Subscription:
    sub = await get_subscription(org_id, db)
    if sub:
        return sub
    sub = Subscription(organization_id=org_id, plan="free", status="free")
    db.add(sub)
    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        sub = await get_subscription(org_id, db)
    return sub


def can_use_feature(subscription: Subscription, feature_name: str) -> bool:
    limits = get_plan_limits(subscription.plan)
    return bool(limits.get(feature_name, False))


async def get_or_create_usage(org_id: str, db: AsyncSession) -> UsageCounter:
    period = _current_period_key()
    result = await db.execute(
        select(UsageCounter).where(
            UsageCounter.organization_id == org_id,
            UsageCounter.period_key == period,
        )
    )
    counter = result.scalar_one_or_none()
    if not counter:
        counter = UsageCounter(organization_id=org_id, period_key=period)
        db.add(counter)
        await db.flush()
    return counter


async def check_usage_limit(org_id: str, usage_key: str, db: AsyncSession) -> bool:
    sub = await ensure_subscription_exists(org_id, db)
    limits = get_plan_limits(sub.plan)
    counter = await get_or_create_usage(org_id, db)
    current = getattr(counter, usage_key, 0)
    limit_key = _usage_to_limit_key(usage_key)
    limit = limits.get(limit_key, 0)
    return current < limit


async def increment_usage(org_id: str, usage_key: str, db: AsyncSession, amount: int = 1) -> None:
    counter = await get_or_create_usage(org_id, db)
    current = getattr(counter, usage_key, 0)
    setattr(counter, usage_key, current + amount)
    db.add(counter)
    await db.commit()


def _usage_to_limit_key(usage_key: str) -> str:
    mapping = {
        "bulk_edits_used": "bulk_edits_per_month",
        "ai_credits_used": "ai_credits_per_month",
        "listings_synced": "max_listings",
        "media_assets_used": "media_assets",
        "dynamic_pricing_jobs_used": "dynamic_pricing_jobs_per_month",
    }
    return mapping.get(usage_key, usage_key)


async def create_stripe_customer(org_id: str, user_email: str) -> str:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    customer = stripe.Customer.create(
        email=user_email,
        metadata={"organization_id": org_id},
    )
    return customer.id


async def create_checkout_session(
    org_id: str,
    user_email: str,
    plan: str,
    db: AsyncSession,
) -> str:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    price_id = settings.get_stripe_price_id(plan)
    if not price_id:
        raise BillingError("Stripe price not configured for this plan", 503)

    sub = await ensure_subscription_exists(org_id, db)

    customer_id = sub.stripe_customer_id
    if not customer_id:
        customer_id = await create_stripe_customer(org_id, user_email)
        sub.stripe_customer_id = customer_id
        db.add(sub)
        await db.commit()

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer=customer_id,
        metadata={"organization_id": org_id, "plan": plan},
        success_url=f"{settings.FRONTEND_URL}/billing?success=true",
        cancel_url=f"{settings.FRONTEND_URL}/pricing?canceled=true",
    )
    return session.url


async def create_portal_session(org_id: str, db: AsyncSession) -> str:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    sub = await get_subscription(org_id, db)
    if not sub or not sub.stripe_customer_id:
        raise BillingError("No paid subscription found. Upgrade to access the billing portal.", 400)

    portal = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/billing",
    )
    return portal.url


async def process_webhook_event(event: Any, db: AsyncSession) -> None:
    stripe_event_id = event["id"]

    existing = await db.execute(
        select(BillingEvent).where(BillingEvent.stripe_event_id == stripe_event_id)
    )
    if existing.scalar_one_or_none():
        return

    billing_event = BillingEvent(
        stripe_event_id=stripe_event_id,
        event_type=event["type"],
        payload=dict(event),
        created_at=datetime.now(timezone.utc),
    )
    db.add(billing_event)
    await db.flush()

    event_type = event["type"]
    obj = event["data"]["object"]

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(obj, db)
        elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
            await _handle_subscription_updated(obj, db)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(obj, db)
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(obj, db)

        billing_event.processed_at = datetime.now(timezone.utc)
    except Exception:
        pass

    await db.commit()


async def _handle_checkout_completed(obj: Any, db: AsyncSession) -> None:
    org_id = obj.get("metadata", {}).get("organization_id")
    plan = obj.get("metadata", {}).get("plan", "free")
    customer_id = obj.get("customer")
    subscription_id = obj.get("subscription")
    if not org_id:
        return

    sub = await ensure_subscription_exists(org_id, db)
    sub.plan = plan
    sub.status = "active"
    sub.stripe_customer_id = customer_id
    sub.stripe_subscription_id = subscription_id
    db.add(sub)


async def _handle_subscription_updated(obj: Any, db: AsyncSession) -> None:
    stripe_sub_id = obj.get("id")
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    stripe_status = obj.get("status", "active")
    sub.status = stripe_status
    sub.stripe_price_id = _extract_price_id(obj)
    sub.cancel_at_period_end = bool(obj.get("cancel_at_period_end", False))

    period_start = obj.get("current_period_start")
    period_end = obj.get("current_period_end")
    if period_start:
        sub.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
    if period_end:
        sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
    db.add(sub)


async def _handle_subscription_deleted(obj: Any, db: AsyncSession) -> None:
    stripe_sub_id = obj.get("id")
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return
    sub.status = "canceled"
    sub.plan = "free"
    db.add(sub)


async def _handle_payment_failed(obj: Any, db: AsyncSession) -> None:
    customer_id = obj.get("customer")
    if not customer_id:
        return
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_customer_id == customer_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return
    sub.status = "past_due"
    db.add(sub)


def _extract_price_id(subscription_obj: Any) -> str | None:
    try:
        items = subscription_obj.get("items", {}).get("data", [])
        if items:
            return items[0].get("price", {}).get("id")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Account-deletion billing eligibility
#
# Owner decision (2026-07-13, third session): do NOT auto-cancel Stripe
# subscriptions on account deletion. Instead, block deletion outright while
# a paid subscription is still active or billable, so a user never loses
# their only self-service cancellation path (the Stripe customer portal,
# which requires a logged-in org) while Stripe keeps charging them.
#
# This uses ONLY the local Subscription row, kept current by verified Stripe
# webhooks (see process_webhook_event above) — no live Stripe API call is
# made here. That is a deliberate choice, not an oversight: a live call on
# every deletion attempt adds latency and a new Stripe-availability
# dependency to a safety check that must itself be reliable, and the local
# state is authoritative for exactly the kinds of decisions this makes
# (Stripe's own webhook delivery is what keeps it current). If the local
# state doesn't match one of the explicitly-defined safe shapes below, this
# fails closed — deletion is blocked, not guessed at.
# ---------------------------------------------------------------------------

class AccountDeletionBillingStatus(str, Enum):
    SAFE_NO_SUBSCRIPTION = "safe_no_subscription"
    SAFE_FREE_PLAN = "safe_free_plan"
    SAFE_SUBSCRIPTION_ENDED = "safe_subscription_ended"
    BLOCKED_ACTIVE_SUBSCRIPTION = "blocked_active_subscription"
    BLOCKED_NO_PORTAL_ACCESS = "blocked_no_portal_access"


@dataclass(frozen=True)
class AccountDeletionBillingCheck:
    safe: bool
    status: AccountDeletionBillingStatus
    reason: str


def _is_period_over(period_end: datetime | None) -> bool:
    """
    True only if current_period_end is present AND already in the past.
    Absent (None) is NOT treated as "over" — see the fail-closed reasoning
    at the call site below. A missing value means we have no positive proof
    the billing period has ended, not that it's safe to assume so.
    """
    if period_end is None:
        return False
    if period_end.tzinfo is None:
        period_end = period_end.replace(tzinfo=timezone.utc)
    return period_end < datetime.now(timezone.utc)


async def assert_account_deletion_billing_safe(org_id: str, db: AsyncSession) -> AccountDeletionBillingCheck:
    """
    Classifies whether an organization's billing state permits account
    deletion right now. Only three shapes are treated as safe — everything
    else, including any Stripe status this function doesn't explicitly
    recognize, is blocked by default (fail closed).

    Deliberately uses get_subscription(), not ensure_subscription_exists():
    a safety check must not have the side effect of creating a row, and
    "no Subscription row exists at all" is itself one of the safe cases.
    """
    sub = await get_subscription(org_id, db)

    if sub is None:
        return AccountDeletionBillingCheck(
            True, AccountDeletionBillingStatus.SAFE_NO_SUBSCRIPTION,
            "No subscription record exists for this organization.",
        )

    if sub.plan == "free" and not sub.stripe_subscription_id:
        return AccountDeletionBillingCheck(
            True, AccountDeletionBillingStatus.SAFE_FREE_PLAN,
            "Organization is on the free plan with no Stripe subscription.",
        )

    if sub.status == "canceled" and _is_period_over(sub.current_period_end):
        # REQUIRES current_period_end to be present AND in the past —
        # status == "canceled" alone is not trusted as a standalone signal.
        #
        # Traced every local write path (2026-07-14 narrow review) before
        # relying on status alone: status="canceled" is NOT set exclusively
        # by _handle_subscription_deleted (Stripe's definitive
        # customer.subscription.deleted event, which never touches
        # current_period_end at all). It can also be set by
        # _handle_subscription_updated, which fires on the more general
        # customer.subscription.updated event and writes whatever raw
        # `status` string Stripe sends — Stripe subscriptions can reach a
        # terminal "canceled" status via an .updated event, not just
        # .deleted, depending on the cancellation path and API version. That
        # handler's current_period_end write is conditional
        # (`if period_end: ...`) on the webhook payload actually containing
        # it — not guaranteed. There is no separate local field (no
        # "ended_at"/"fully_deleted_at") distinguishing "canceled via the
        # definitive .deleted event" from "canceled via .updated with an
        # incomplete or delayed payload." Given that ambiguity, a NULL
        # current_period_end on a canceled subscription is NOT proof the
        # billing period has actually ended — it might just mean we never
        # received (or haven't yet received) the webhook that would have
        # told us. Fail closed: require positive proof (a real, past
        # timestamp), not just the absence of one.
        return AccountDeletionBillingCheck(
            True, AccountDeletionBillingStatus.SAFE_SUBSCRIPTION_ENDED,
            "Subscription has been canceled and its billing period has ended.",
        )

    # Everything else is blocked: active, trialing, past_due, unpaid,
    # incomplete, incomplete_expired, paused, any Stripe status this
    # function doesn't recognize, and "canceled" while still inside a
    # not-yet-ended period (e.g. cancel_at_period_end=true but Stripe
    # hasn't actually ended the subscription yet — status will still read
    # whatever it was before cancellation completes, not "canceled").
    if not sub.stripe_customer_id:
        return AccountDeletionBillingCheck(
            False, AccountDeletionBillingStatus.BLOCKED_NO_PORTAL_ACCESS,
            "Billing state requires resolution but no Stripe customer is on file.",
        )
    return AccountDeletionBillingCheck(
        False, AccountDeletionBillingStatus.BLOCKED_ACTIVE_SUBSCRIPTION,
        "An active or billable subscription must be canceled before the account can be deleted.",
    )
