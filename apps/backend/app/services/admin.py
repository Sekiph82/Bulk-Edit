from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from fastapi import HTTPException, status

from app.models.user import User
from app.models.organization import Organization
from app.models.subscription import Subscription
from app.models.usage_counter import UsageCounter
from app.models.etsy_shop import EtsyShop
from app.models.sync_job import SyncJob
from app.models.bulk_edit_session import BulkEditSession
from app.models.ai_session import AISession
from app.models.csv_job import CSVJob
from app.models.dynamic_pricing_job import DynamicPricingJob
from app.models.scheduled_job import ScheduledJob
from app.models.scheduled_job_run import ScheduledJobRun
from app.models.audit_log import AuditLog
from app.models.listing import Listing
from app.models.billing_event import BillingEvent

_MAX_PAGE = 100


async def _paginate(db: AsyncSession, model, page: int, page_size: int, filters: list | None = None) -> dict:
    page_size = min(max(page_size, 1), _MAX_PAGE)
    page = max(page, 1)
    offset = (page - 1) * page_size

    count_q = select(func.count()).select_from(model)
    items_q = select(model)

    if filters:
        for f in filters:
            count_q = count_q.where(f)
            items_q = items_q.where(f)

    total = (await db.execute(count_q)).scalar_one()
    items_q = items_q.order_by(desc(model.created_at)).offset(offset).limit(page_size)
    result = await db.execute(items_q)
    items = result.scalars().all()

    return {"items": items, "page": page, "page_size": page_size, "total": total}


async def get_admin_overview(db: AsyncSession) -> dict:
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    total_orgs = (await db.execute(select(func.count()).select_from(Organization))).scalar_one()
    active_subs = (await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.status == "active")
    )).scalar_one()
    paid_subs = (await db.execute(
        select(func.count()).select_from(Subscription).where(
            Subscription.plan != "free",
            Subscription.status.in_(["active", "trialing"]),
        )
    )).scalar_one()
    total_listings = (await db.execute(select(func.count()).select_from(Listing))).scalar_one()
    total_scheduled = (await db.execute(select(func.count()).select_from(ScheduledJob))).scalar_one()
    total_ai = (await db.execute(select(func.count()).select_from(AISession))).scalar_one()
    total_csv = (await db.execute(select(func.count()).select_from(CSVJob))).scalar_one()

    return {
        "total_users": total_users,
        "total_organizations": total_orgs,
        "active_subscriptions": active_subs,
        "paid_subscriptions": paid_subs,
        "total_listings": total_listings,
        "total_scheduled_jobs": total_scheduled,
        "total_ai_sessions": total_ai,
        "total_csv_jobs": total_csv,
    }


async def list_users(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, User, page, page_size)


async def get_user_detail(db: AsyncSession, user_id: str) -> User:
    row = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


async def list_organizations(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, Organization, page, page_size)


async def get_organization_detail(db: AsyncSession, org_id: str) -> dict:
    org = (await db.execute(select(Organization).where(Organization.id == org_id))).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    sub = (await db.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )).scalar_one_or_none()

    shop_count = (await db.execute(
        select(func.count()).select_from(EtsyShop).where(EtsyShop.organization_id == org_id)
    )).scalar_one()

    listing_count = (await db.execute(
        select(func.count()).select_from(Listing).where(Listing.organization_id == org_id)
    )).scalar_one()

    return {"org": org, "subscription": sub, "shop_count": shop_count, "listing_count": listing_count}


async def list_subscriptions(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, Subscription, page, page_size)


async def list_usage(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, UsageCounter, page, page_size)


async def list_shops(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, EtsyShop, page, page_size)


async def list_sync_jobs(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, SyncJob, page, page_size)


async def list_bulk_edit_sessions(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, BulkEditSession, page, page_size)


async def list_ai_sessions(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, AISession, page, page_size)


async def list_csv_jobs(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, CSVJob, page, page_size)


async def list_dynamic_pricing_jobs(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, DynamicPricingJob, page, page_size)


async def list_scheduled_jobs(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, ScheduledJob, page, page_size)


async def list_scheduled_job_runs(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, ScheduledJobRun, page, page_size)


async def list_events(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, AuditLog, page, page_size)


async def disable_user(db: AsyncSession, user_id: str, acting_user_id: str) -> User:
    if user_id == acting_user_id:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")
    user = await get_user_detail(db, user_id)
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user


async def enable_user(db: AsyncSession, user_id: str) -> User:
    user = await get_user_detail(db, user_id)
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return user


async def pause_scheduled_job(db: AsyncSession, job_id: str) -> ScheduledJob:
    job = (await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    if job.status not in ("active", "idle"):
        raise HTTPException(status_code=400, detail=f"Cannot pause job in status '{job.status}'")
    job.status = "paused"
    await db.commit()
    await db.refresh(job)
    return job


async def resume_scheduled_job(db: AsyncSession, job_id: str) -> ScheduledJob:
    job = (await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    if job.status != "paused":
        raise HTTPException(status_code=400, detail=f"Cannot resume job in status '{job.status}'")
    job.status = "active"
    await db.commit()
    await db.refresh(job)
    return job


# ── Business Dashboard Summary Services ───────────────────────────────────────

_PLAN_MRR: dict[str, float] = {
    "basic_monthly": 9.0,
    "pro_monthly": 29.0,
    "basic_yearly": 7.5,    # annualized / 12
    "pro_yearly": 20.83,
}


async def get_billing_summary(db: AsyncSession) -> dict:
    plans = ["free", "basic_monthly", "basic_yearly", "pro_monthly", "pro_yearly"]
    plan_counts: dict[str, int] = {}
    for plan in plans:
        count = (await db.execute(
            select(func.count()).select_from(Subscription).where(Subscription.plan == plan)
        )).scalar_one()
        plan_counts[plan] = count

    total = (await db.execute(select(func.count()).select_from(Subscription))).scalar_one()
    active = (await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.status == "active")
    )).scalar_one()
    trialing = (await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.status == "trialing")
    )).scalar_one()
    canceled = (await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.status == "canceled")
    )).scalar_one()
    cancel_eop = (await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.cancel_at_period_end == True)
    )).scalar_one()

    estimated_mrr = sum(plan_counts.get(p, 0) * price for p, price in _PLAN_MRR.items())

    return {
        "total_subscriptions": total,
        "free_plan_count": plan_counts.get("free", 0),
        "basic_monthly_count": plan_counts.get("basic_monthly", 0),
        "basic_yearly_count": plan_counts.get("basic_yearly", 0),
        "pro_monthly_count": plan_counts.get("pro_monthly", 0),
        "pro_yearly_count": plan_counts.get("pro_yearly", 0),
        "active_count": active,
        "trialing_count": trialing,
        "canceled_count": canceled,
        "cancel_at_period_end_count": cancel_eop,
        "estimated_monthly_revenue": round(estimated_mrr, 2),
    }


async def get_stripe_summary(db: AsyncSession) -> dict:
    total_stripe_customers = (await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.stripe_customer_id.isnot(None))
    )).scalar_one()
    subs_with_stripe = (await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.stripe_subscription_id.isnot(None))
    )).scalar_one()
    active_stripe = (await db.execute(
        select(func.count()).select_from(Subscription).where(
            Subscription.stripe_subscription_id.isnot(None),
            Subscription.status == "active",
        )
    )).scalar_one()
    canceling = (await db.execute(
        select(func.count()).select_from(Subscription).where(Subscription.cancel_at_period_end == True)
    )).scalar_one()
    total_billing_events = (await db.execute(select(func.count()).select_from(BillingEvent))).scalar_one()

    return {
        "total_stripe_customers": total_stripe_customers,
        "subscriptions_with_stripe_sub": subs_with_stripe,
        "active_stripe_subscriptions": active_stripe,
        "canceling_at_period_end": canceling,
        "total_billing_events": total_billing_events,
    }


async def get_product_usage(db: AsyncSession) -> dict:
    total_listings = (await db.execute(select(func.count()).select_from(Listing))).scalar_one()
    total_bulk = (await db.execute(select(func.count()).select_from(BulkEditSession))).scalar_one()
    total_ai = (await db.execute(select(func.count()).select_from(AISession))).scalar_one()
    total_csv = (await db.execute(select(func.count()).select_from(CSVJob))).scalar_one()
    total_dp = (await db.execute(select(func.count()).select_from(DynamicPricingJob))).scalar_one()
    total_sync = (await db.execute(select(func.count()).select_from(SyncJob))).scalar_one()
    total_shops = (await db.execute(select(func.count()).select_from(EtsyShop))).scalar_one()

    return {
        "total_listings": total_listings,
        "total_bulk_edit_sessions": total_bulk,
        "total_ai_sessions": total_ai,
        "total_csv_jobs": total_csv,
        "total_dynamic_pricing_jobs": total_dp,
        "total_sync_jobs": total_sync,
        "total_shops": total_shops,
    }


async def _check_redis_health(redis_url: str) -> str:
    if not redis_url:
        return "not_configured"
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        return "ok"
    except Exception:
        return "error"


async def get_system_health(db: AsyncSession) -> dict:
    from app.core.config import settings

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    total_orgs = (await db.execute(select(func.count()).select_from(Organization))).scalar_one()
    total_audit = (await db.execute(select(func.count()).select_from(AuditLog))).scalar_one()
    failed_runs = (await db.execute(
        select(func.count()).select_from(ScheduledJobRun).where(ScheduledJobRun.status == "failed")
    )).scalar_one()
    failed_ai = (await db.execute(
        select(func.count()).select_from(AISession).where(AISession.status == "failed")
    )).scalar_one()

    redis_status = await _check_redis_health(settings.REDIS_URL)

    sentry_dsn = settings.SENTRY_DSN or ""
    sentry_configured = bool(sentry_dsn) and "placeholder" not in sentry_dsn.lower() and not sentry_dsn.startswith("YOUR_")

    return {
        "database_status": "ok",
        "redis_status": redis_status,
        "rate_limit_backend": settings.RATE_LIMIT_BACKEND,
        "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
        "sentry_configured": sentry_configured,
        "worker_status": "not_configured",
        "csp_mode": "unsafe_inline_deferred",
        "total_users": total_users,
        "total_organizations": total_orgs,
        "total_audit_events": total_audit,
        "recent_failed_scheduled_runs": failed_runs,
        "recent_failed_ai_sessions": failed_ai,
    }
