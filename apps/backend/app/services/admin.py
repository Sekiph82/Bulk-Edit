from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_
from fastapi import HTTPException, status

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.subscription import Subscription
from app.models.usage_counter import UsageCounter
from app.models.etsy_shop import EtsyShop
from app.models.sync_job import SyncJob
from app.models.bulk_edit_session import BulkEditSession
from app.models.bulk_edit_media_job import BulkEditMediaJob
from app.models.ai_session import AISession
from app.models.csv_job import CSVJob
from app.models.dynamic_pricing_job import DynamicPricingJob
from app.models.scheduled_job import ScheduledJob
from app.models.scheduled_job_run import ScheduledJobRun
from app.models.audit_log import AuditLog
from app.models.listing import Listing
from app.models.billing_event import BillingEvent
from app.models.contact_submission import ContactSubmission
from app.models.video_render import VideoRender

from app.schemas.admin import (
    AdminUserListItem,
    AdminUserDetail,
    AdminUserOrgMembership,
    AdminUserUsageSummary,
    AdminAuditEventSummary,
    AdminOrganizationListItem,
    AdminOrganizationDetail,
    AdminOrgMemberItem,
    AdminOrgUsageSummary,
    AdminOrgRiskSummary,
    AdminSubscriptionSummary,
    AdminShopSummary,
    AdminTrendPoint,
    AdminTrendSeries,
    AdminTrendsOut,
)

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


def _parse_date_bound(value: str | None, end_of_day: bool = False) -> datetime | None:
    """Parse a YYYY-MM-DD (or full ISO) date-range bound. Returns None on empty/invalid input."""
    if not value:
        return None
    try:
        if len(value) == 10:
            d = date.fromisoformat(value)
            t = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc) if end_of_day else datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
            return t
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def _primary_orgs_for_users(db: AsyncSession, user_ids: list[str]) -> dict[str, dict]:
    """First (oldest) organization membership per user, enriched with org name + plan.
    Display convenience only — a user could technically belong to more than one org."""
    if not user_ids:
        return {}

    memberships = (await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.user_id.in_(user_ids))
        .order_by(OrganizationMember.created_at.asc())
    )).scalars().all()

    primary_org_id_by_user: dict[str, str] = {}
    primary_role_by_user: dict[str, str] = {}
    for m in memberships:
        if m.user_id not in primary_org_id_by_user:
            primary_org_id_by_user[m.user_id] = m.organization_id
            primary_role_by_user[m.user_id] = m.role

    org_ids = list(set(primary_org_id_by_user.values()))
    if not org_ids:
        return {}

    orgs = (await db.execute(select(Organization).where(Organization.id.in_(org_ids)))).scalars().all()
    orgs_by_id = {o.id: o for o in orgs}
    subs = (await db.execute(select(Subscription).where(Subscription.organization_id.in_(org_ids)))).scalars().all()
    subs_by_org = {s.organization_id: s for s in subs}

    result: dict[str, dict] = {}
    for user_id, org_id in primary_org_id_by_user.items():
        org = orgs_by_id.get(org_id)
        if not org:
            continue
        sub = subs_by_org.get(org_id)
        result[user_id] = {
            "organization_id": org_id,
            "organization_name": org.name,
            "plan": sub.plan if sub else None,
            "role": primary_role_by_user[user_id],
        }
    return result


async def list_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 25,
    q: str | None = None,
    status: str | None = None,
    role: str | None = None,
    organization_id: str | None = None,
    plan: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
) -> dict:
    filters = []
    if q:
        like = f"%{q}%"
        filters.append(or_(User.email.ilike(like), User.full_name.ilike(like), User.id == q))
    if status == "active":
        filters.append(User.is_active.is_(True))
    elif status == "disabled":
        filters.append(User.is_active.is_(False))
    if role == "superuser":
        filters.append(User.is_superuser.is_(True))
    elif role == "user":
        filters.append(User.is_superuser.is_(False))
    if organization_id:
        filters.append(User.id.in_(
            select(OrganizationMember.user_id).where(OrganizationMember.organization_id == organization_id)
        ))
    if plan:
        filters.append(User.id.in_(
            select(OrganizationMember.user_id)
            .join(Subscription, Subscription.organization_id == OrganizationMember.organization_id)
            .where(Subscription.plan == plan)
        ))
    from_dt = _parse_date_bound(created_from)
    to_dt = _parse_date_bound(created_to, end_of_day=True)
    if from_dt:
        filters.append(User.created_at >= from_dt)
    if to_dt:
        filters.append(User.created_at <= to_dt)

    result = await _paginate(db, User, page, page_size, filters=filters)
    org_info = await _primary_orgs_for_users(db, [u.id for u in result["items"]])

    items = []
    for u in result["items"]:
        item = AdminUserListItem.model_validate(u)
        info = org_info.get(u.id)
        if info:
            item.organization_id = info["organization_id"]
            item.organization_name = info["organization_name"]
            item.plan = info["plan"]
        items.append(item)

    result["items"] = items
    return result


async def get_user_detail(db: AsyncSession, user_id: str) -> AdminUserDetail:
    row = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    memberships = (await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == user_id)
        .order_by(OrganizationMember.created_at.asc())
    )).scalars().all()
    org_ids = [m.organization_id for m in memberships]
    orgs_by_id: dict[str, Organization] = {}
    if org_ids:
        orgs = (await db.execute(select(Organization).where(Organization.id.in_(org_ids)))).scalars().all()
        orgs_by_id = {o.id: o for o in orgs}

    organizations = [
        AdminUserOrgMembership(
            organization_id=m.organization_id,
            organization_name=orgs_by_id[m.organization_id].name if m.organization_id in orgs_by_id else "—",
            role=m.role,
        )
        for m in memberships
        if m.organization_id in orgs_by_id
    ]

    bulk_edit_count = (await db.execute(
        select(func.count()).select_from(BulkEditSession).where(BulkEditSession.created_by_user_id == user_id)
    )).scalar_one()
    ai_count = (await db.execute(
        select(func.count()).select_from(AISession).where(AISession.created_by_user_id == user_id)
    )).scalar_one()
    csv_count = (await db.execute(
        select(func.count()).select_from(CSVJob).where(CSVJob.user_id == user_id)
    )).scalar_one()
    dp_count = (await db.execute(
        select(func.count()).select_from(DynamicPricingJob).where(DynamicPricingJob.user_id == user_id)
    )).scalar_one()
    media_count = (await db.execute(
        select(func.count()).select_from(BulkEditMediaJob).where(BulkEditMediaJob.created_by_user_id == user_id)
    )).scalar_one()

    events = (await db.execute(
        select(AuditLog).where(AuditLog.user_id == user_id).order_by(desc(AuditLog.created_at)).limit(10)
    )).scalars().all()

    primary = organizations[0] if organizations else None
    detail = AdminUserDetail(
        id=row.id,
        email=row.email,
        full_name=row.full_name,
        is_active=row.is_active,
        is_verified=row.is_verified,
        is_superuser=row.is_superuser,
        created_at=row.created_at,
        updated_at=row.updated_at,
        organization_id=primary.organization_id if primary else None,
        organization_name=primary.organization_name if primary else None,
        plan=None,
        organizations=organizations,
        usage=AdminUserUsageSummary(
            bulk_edit_sessions_count=bulk_edit_count,
            ai_sessions_count=ai_count,
            csv_jobs_count=csv_count,
            dynamic_pricing_jobs_count=dp_count,
            media_jobs_count=media_count,
        ),
        recent_events=[AdminAuditEventSummary.model_validate(e) for e in events],
    )
    if primary:
        sub = (await db.execute(
            select(Subscription).where(Subscription.organization_id == primary.organization_id)
        )).scalar_one_or_none()
        detail.plan = sub.plan if sub else None
    return detail


async def list_organizations(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 25,
    q: str | None = None,
    plan: str | None = None,
    subscription_status: str | None = None,
    etsy_connected: bool | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
) -> dict:
    filters = []
    if q:
        like = f"%{q}%"
        owner_ids_q = select(User.id).where(or_(User.email.ilike(like)))
        filters.append(or_(
            Organization.name.ilike(like),
            Organization.id == q,
            Organization.owner_id.in_(owner_ids_q),
        ))
    if plan:
        filters.append(Organization.id.in_(
            select(Subscription.organization_id).where(Subscription.plan == plan)
        ))
    if subscription_status:
        filters.append(Organization.id.in_(
            select(Subscription.organization_id).where(Subscription.status == subscription_status)
        ))
    if etsy_connected is not None:
        connected_org_ids_q = select(EtsyShop.organization_id).where(EtsyShop.is_connected.is_(True))
        if etsy_connected:
            filters.append(Organization.id.in_(connected_org_ids_q))
        else:
            filters.append(Organization.id.notin_(connected_org_ids_q))
    from_dt = _parse_date_bound(created_from)
    to_dt = _parse_date_bound(created_to, end_of_day=True)
    if from_dt:
        filters.append(Organization.created_at >= from_dt)
    if to_dt:
        filters.append(Organization.created_at <= to_dt)

    result = await _paginate(db, Organization, page, page_size, filters=filters)
    org_ids = [o.id for o in result["items"]]

    owners_by_id: dict[str, User] = {}
    subs_by_org: dict[str, Subscription] = {}
    connected_org_ids: set[str] = set()
    users_count_by_org: dict[str, int] = {}
    if org_ids:
        owner_ids = list({o.owner_id for o in result["items"]})
        owners = (await db.execute(select(User).where(User.id.in_(owner_ids)))).scalars().all()
        owners_by_id = {u.id: u for u in owners}

        subs = (await db.execute(select(Subscription).where(Subscription.organization_id.in_(org_ids)))).scalars().all()
        subs_by_org = {s.organization_id: s for s in subs}

        connected_rows = (await db.execute(
            select(EtsyShop.organization_id).where(
                EtsyShop.organization_id.in_(org_ids), EtsyShop.is_connected.is_(True)
            ).distinct()
        )).scalars().all()
        connected_org_ids = set(connected_rows)

        member_counts = (await db.execute(
            select(OrganizationMember.organization_id, func.count())
            .where(OrganizationMember.organization_id.in_(org_ids))
            .group_by(OrganizationMember.organization_id)
        )).all()
        users_count_by_org = {org_id: count for org_id, count in member_counts}

    items = []
    for o in result["items"]:
        item = AdminOrganizationListItem.model_validate(o)
        owner = owners_by_id.get(o.owner_id)
        sub = subs_by_org.get(o.id)
        item.owner_email = owner.email if owner else None
        item.plan = sub.plan if sub else None
        item.subscription_status = sub.status if sub else None
        item.etsy_connected = o.id in connected_org_ids
        item.users_count = users_count_by_org.get(o.id, 0)
        items.append(item)

    result["items"] = items
    return result


async def get_organization_detail(db: AsyncSession, org_id: str) -> AdminOrganizationDetail:
    org = (await db.execute(select(Organization).where(Organization.id == org_id))).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    sub = (await db.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )).scalar_one_or_none()

    shops = (await db.execute(
        select(EtsyShop).where(EtsyShop.organization_id == org_id).order_by(desc(EtsyShop.created_at))
    )).scalars().all()
    shop_count = len(shops)
    any_connected = any(s.is_connected for s in shops)

    listing_count = (await db.execute(
        select(func.count()).select_from(Listing).where(Listing.organization_id == org_id)
    )).scalar_one()

    memberships = (await db.execute(
        select(OrganizationMember).where(OrganizationMember.organization_id == org_id)
    )).scalars().all()
    member_user_ids = [m.user_id for m in memberships]
    users_by_id: dict[str, User] = {}
    if member_user_ids:
        users = (await db.execute(select(User).where(User.id.in_(member_user_ids)))).scalars().all()
        users_by_id = {u.id: u for u in users}
    members = [
        AdminOrgMemberItem(
            user_id=m.user_id,
            email=users_by_id[m.user_id].email if m.user_id in users_by_id else "—",
            full_name=users_by_id[m.user_id].full_name if m.user_id in users_by_id else None,
            role=m.role,
        )
        for m in memberships
        if m.user_id in users_by_id
    ]

    bulk_edit_count = (await db.execute(
        select(func.count()).select_from(BulkEditSession).where(BulkEditSession.organization_id == org_id)
    )).scalar_one()
    ai_count = (await db.execute(
        select(func.count()).select_from(AISession).where(AISession.organization_id == org_id)
    )).scalar_one()
    csv_count = (await db.execute(
        select(func.count()).select_from(CSVJob).where(CSVJob.organization_id == org_id)
    )).scalar_one()
    dp_count = (await db.execute(
        select(func.count()).select_from(DynamicPricingJob).where(DynamicPricingJob.organization_id == org_id)
    )).scalar_one()
    sync_count = (await db.execute(
        select(func.count()).select_from(SyncJob).where(SyncJob.organization_id == org_id)
    )).scalar_one()
    media_count = (await db.execute(
        select(func.count()).select_from(BulkEditMediaJob).where(BulkEditMediaJob.organization_id == org_id)
    )).scalar_one()
    video_count = (await db.execute(
        select(func.count()).select_from(VideoRender).where(VideoRender.organization_id == org_id)
    )).scalar_one()

    failed_bulk_edit = (await db.execute(
        select(func.count()).select_from(BulkEditSession).where(
            BulkEditSession.organization_id == org_id, BulkEditSession.status == "failed"
        )
    )).scalar_one()
    failed_ai = (await db.execute(
        select(func.count()).select_from(AISession).where(
            AISession.organization_id == org_id, AISession.status == "failed"
        )
    )).scalar_one()
    failed_scheduled = (await db.execute(
        select(func.count()).select_from(ScheduledJobRun).where(
            ScheduledJobRun.organization_id == org_id, ScheduledJobRun.status == "failed"
        )
    )).scalar_one()

    events = (await db.execute(
        select(AuditLog).where(AuditLog.organization_id == org_id).order_by(desc(AuditLog.created_at)).limit(10)
    )).scalars().all()

    billing_issue = bool(sub) and (sub.status not in ("active", "trialing", "free") or sub.cancel_at_period_end)

    return AdminOrganizationDetail(
        id=org.id,
        name=org.name,
        owner_id=org.owner_id,
        created_at=org.created_at,
        updated_at=org.updated_at,
        owner_email=users_by_id.get(org.owner_id).email if org.owner_id in users_by_id else None,
        plan=sub.plan if sub else None,
        subscription_status=sub.status if sub else None,
        etsy_connected=any_connected,
        users_count=len(memberships),
        subscription=AdminSubscriptionSummary.model_validate(sub) if sub else None,
        shop_count=shop_count,
        listing_count=listing_count,
        members=members,
        shops=[AdminShopSummary.model_validate(s) for s in shops],
        usage=AdminOrgUsageSummary(
            bulk_edit_sessions_count=bulk_edit_count,
            ai_sessions_count=ai_count,
            csv_jobs_count=csv_count,
            dynamic_pricing_jobs_count=dp_count,
            sync_jobs_count=sync_count,
            media_jobs_count=media_count,
            video_renders_count=video_count,
        ),
        recent_events=[AdminAuditEventSummary.model_validate(e) for e in events],
        risk=AdminOrgRiskSummary(
            failed_bulk_edit_count=failed_bulk_edit,
            failed_ai_count=failed_ai,
            failed_scheduled_runs_count=failed_scheduled,
            etsy_disconnected=shop_count > 0 and not any_connected,
            billing_issue=billing_issue,
        ),
    )


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


async def list_contact_submissions(db: AsyncSession, page: int = 1, page_size: int = 25) -> dict:
    return await _paginate(db, ContactSubmission, page, page_size)


def get_feature_flags() -> dict:
    from app.core.config import settings

    flags = [
        {"key": "VIDEO_RENDERER_ENABLED", "enabled": bool(settings.VIDEO_RENDERER_ENABLED), "source": "env"},
        {"key": "RATE_LIMIT_ENABLED", "enabled": bool(settings.RATE_LIMIT_ENABLED), "source": "env"},
        {"key": "EMAIL_CONFIGURED", "enabled": settings.is_email_configured(), "source": "env"},
        {"key": "AI_PROVIDER_LIVE", "enabled": settings.AI_PROVIDER != "mock", "source": "env"},
    ]
    return {"flags": flags}


async def _get_user_row(db: AsyncSession, user_id: str) -> User:
    row = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


async def disable_user(db: AsyncSession, user_id: str, acting_user_id: str) -> User:
    if user_id == acting_user_id:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")
    user = await _get_user_row(db, user_id)
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user


async def enable_user(db: AsyncSession, user_id: str) -> User:
    user = await _get_user_row(db, user_id)
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


# ── Trends ────────────────────────────────────────────────────────────────────

async def _daily_counts(db: AsyncSession, model, date_column, since: datetime) -> dict[str, int]:
    rows = (await db.execute(
        select(func.date(date_column).label("d"), func.count())
        .select_from(model)
        .where(date_column >= since)
        .group_by(func.date(date_column))
    )).all()
    return {str(d): c for d, c in rows}


async def get_admin_trends(db: AsyncSession, days: int = 30) -> AdminTrendsOut:
    """Real daily counts only — zero-filled for days with no activity, never estimated."""
    days = max(1, min(days, 365))
    today = datetime.now(timezone.utc).date()
    since = datetime(today.year, today.month, today.day, tzinfo=timezone.utc) - timedelta(days=days - 1)

    users_counts = await _daily_counts(db, User, User.created_at, since)
    orgs_counts = await _daily_counts(db, Organization, Organization.created_at, since)
    bulk_counts = await _daily_counts(db, BulkEditSession, BulkEditSession.created_at, since)
    media_counts = await _daily_counts(db, BulkEditMediaJob, BulkEditMediaJob.created_at, since)

    def build_series(counts: dict[str, int]) -> list[AdminTrendPoint]:
        points = []
        for i in range(days):
            key = (since.date() + timedelta(days=i)).isoformat()
            points.append(AdminTrendPoint(date=key, count=counts.get(key, 0)))
        return points

    return AdminTrendsOut(
        days=days,
        series=AdminTrendSeries(
            users=build_series(users_counts),
            organizations=build_series(orgs_counts),
            bulk_edit_jobs=build_series(bulk_counts),
            media_jobs=build_series(media_counts),
        ),
    )
