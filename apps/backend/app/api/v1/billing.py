from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

import stripe

from app.core.config import settings
from app.core.deps import get_current_org_id, require_active_user
from app.core.plans import PLAN_DISPLAY_NAMES, PLAN_LIMITS, VALID_PAID_PLANS, get_plan_limits
from app.db.session import get_db
from app.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PlansResponse,
    PortalResponse,
    SubscriptionResponse,
    UsageResponse,
)
from app.services.billing import (
    BillingError,
    create_checkout_session,
    create_portal_session,
    ensure_subscription_exists,
    get_or_create_usage,
    process_webhook_event,
)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=PlansResponse)
async def get_plans():
    return PlansResponse(plans=PLAN_LIMITS)


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    sub = await ensure_subscription_exists(org_id, db)
    limits = get_plan_limits(sub.plan)
    return SubscriptionResponse(
        id=sub.id,
        organization_id=sub.organization_id,
        plan=sub.plan,
        status=sub.status,
        stripe_customer_id=sub.stripe_customer_id,
        stripe_subscription_id=sub.stripe_subscription_id,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        limits=limits,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    data: CheckoutRequest,
    user=Depends(require_active_user),
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    if data.plan == "free":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot checkout free plan.")
    if data.plan not in VALID_PAID_PLANS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan.")
    if not settings.is_stripe_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe is not configured.")

    try:
        url = await create_checkout_session(org_id, user.email, data.plan, db)
    except BillingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return CheckoutResponse(checkout_url=url)


@router.post("/portal", response_model=PortalResponse)
async def portal(
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    if not settings.is_stripe_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe is not configured.")

    try:
        url = await create_portal_session(org_id, db)
    except BillingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return PortalResponse(portal_url=url)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.is_stripe_webhook_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe webhook is not configured.")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature.")

    await process_webhook_event(event, db)
    return {"received": True}


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    sub = await ensure_subscription_exists(org_id, db)
    limits = get_plan_limits(sub.plan)
    counter = await get_or_create_usage(org_id, db)
    await db.commit()

    return UsageResponse(
        period_key=counter.period_key,
        usage={
            "listings_synced": counter.listings_synced,
            "bulk_edits_used": counter.bulk_edits_used,
            "ai_credits_used": counter.ai_credits_used,
            "media_assets_used": counter.media_assets_used,
        },
        limits=limits,
    )
