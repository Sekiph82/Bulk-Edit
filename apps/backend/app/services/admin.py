from __future__ import annotations
import logging
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

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
from app.models.comp_access_grant import CompAccessGrant
from app.models.owner_alert_rule import OwnerAlertRule
from app.models.owner_action_log import OwnerActionLog
from app.services.billing import ensure_subscription_exists

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
    AdminCompGrantOut,
    AdminEffectiveAccess,
    AdminSyncTriggerResult,
    AdminPaymentItem,
    AdminAlertRuleOut,
    AdminAlertCheckResult,
)

_MAX_PAGE = 100

# Alert rules seeded on first access if missing — keeps the 5 supported
# event types deterministic without needing a data migration.
_DEFAULT_ALERT_RULES: list[dict] = [
    {"event_type": "payment_failure", "name": "Payment failures", "threshold_count": 3, "window_minutes": 60},
    {"event_type": "sync_failure_spike", "name": "Sync failure spike", "threshold_count": 5, "window_minutes": 60},
    {"event_type": "bulk_edit_failures", "name": "Failed bulk edit jobs", "threshold_count": 5, "window_minutes": 60},
    {"event_type": "system_health", "name": "API/system health issue", "threshold_count": 1, "window_minutes": 15},
    {"event_type": "ai_failures", "name": "AI job failures", "threshold_count": 5, "window_minutes": 60},
]


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
        effective_access=await get_effective_access(db, org_id),
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


# ── Owner action audit logging ────────────────────────────────────────────────
# Every owner action below writes one of these. Never include tokens,
# password reset tokens, Slack webhook URLs, card data, or Stripe secret
# values in `message` or `extra_data`.

async def _write_owner_audit_log(
    db: AsyncSession,
    actor_user_id: str,
    action_type: str,
    message: str,
    organization_id: str | None = None,
    target_user_id: str | None = None,
) -> None:
    log = OwnerActionLog(
        actor_user_id=actor_user_id,
        organization_id=organization_id,
        target_user_id=target_user_id,
        action_type=action_type,
        message=message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()


# ── Plan change / comp access ─────────────────────────────────────────────────

_ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}


async def get_effective_access(db: AsyncSession, org_id: str) -> AdminEffectiveAccess:
    sub = (await db.execute(select(Subscription).where(Subscription.organization_id == org_id))).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    comp = (await db.execute(
        select(CompAccessGrant).where(
            CompAccessGrant.organization_id == org_id,
            CompAccessGrant.revoked_at.is_(None),
        ).order_by(desc(CompAccessGrant.created_at))
    )).scalars().first()

    active_comp = None
    if comp:
        ends_at = comp.ends_at
        if ends_at and ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        if not ends_at or ends_at > now:
            active_comp = comp

    stripe_managed = bool(sub and sub.stripe_subscription_id and sub.status in _ACTIVE_SUBSCRIPTION_STATUSES)
    effective_plan = active_comp.comp_plan if active_comp else (sub.plan if sub else "free")

    return AdminEffectiveAccess(
        subscription_plan=sub.plan if sub else None,
        subscription_status=sub.status if sub else None,
        stripe_managed=stripe_managed,
        comp=AdminCompGrantOut.model_validate(active_comp) if active_comp else None,
        effective_plan=effective_plan,
    )


async def change_plan(db: AsyncSession, org_id: str, plan: str, reason: str, actor_user_id: str) -> Subscription:
    from app.core.plans import ALL_PLANS

    if plan not in ALL_PLANS:
        raise HTTPException(status_code=400, detail=f"Unknown plan '{plan}'. Must be one of: {', '.join(sorted(ALL_PLANS))}.")

    sub = await ensure_subscription_exists(org_id, db)
    if sub.stripe_subscription_id and sub.status in _ACTIVE_SUBSCRIPTION_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "This organization has an active Stripe-managed subscription. Change the plan via the "
                "Stripe dashboard or the customer billing portal — editing it directly here would desync "
                "billing from what Stripe actually charges."
            ),
        )

    old_plan = sub.plan
    sub.plan = plan
    db.add(sub)
    await _write_owner_audit_log(
        db, actor_user_id, "owner_plan_change",
        f"Plan changed from '{old_plan}' to '{plan}'. Reason: {reason}",
        organization_id=org_id,
    )
    await db.commit()
    await db.refresh(sub)
    return sub


async def grant_comp_access(
    db: AsyncSession, org_id: str, comp_plan: str, reason: str, ends_at: datetime | None, actor_user_id: str
) -> CompAccessGrant:
    from app.core.plans import ALL_PLANS

    org = (await db.execute(select(Organization).where(Organization.id == org_id))).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if comp_plan not in ALL_PLANS:
        raise HTTPException(status_code=400, detail=f"Unknown plan '{comp_plan}'. Must be one of: {', '.join(sorted(ALL_PLANS))}.")

    grant = CompAccessGrant(
        organization_id=org_id,
        comp_plan=comp_plan,
        reason=reason,
        granted_by_user_id=actor_user_id,
        starts_at=datetime.now(timezone.utc),
        ends_at=ends_at,
    )
    db.add(grant)
    await db.flush()
    await _write_owner_audit_log(
        db, actor_user_id, "owner_comp_grant",
        f"Comp access granted: plan={comp_plan}. Reason: {reason}",
        organization_id=org_id,
    )
    await db.commit()
    await db.refresh(grant)
    return grant


async def revoke_comp_access(db: AsyncSession, org_id: str, actor_user_id: str) -> CompAccessGrant:
    grant = (await db.execute(
        select(CompAccessGrant).where(
            CompAccessGrant.organization_id == org_id,
            CompAccessGrant.revoked_at.is_(None),
        ).order_by(desc(CompAccessGrant.created_at))
    )).scalars().first()
    if not grant:
        raise HTTPException(status_code=404, detail="No active comp access grant for this organization.")

    grant.revoked_at = datetime.now(timezone.utc)
    grant.revoked_by_user_id = actor_user_id
    db.add(grant)
    await _write_owner_audit_log(
        db, actor_user_id, "owner_comp_revoke",
        f"Comp access revoked (was plan={grant.comp_plan}).",
        organization_id=org_id,
    )
    await db.commit()
    await db.refresh(grant)
    return grant


# ── Manual Etsy sync ───────────────────────────────────────────────────────────

async def trigger_manual_sync(
    db: AsyncSession, org_id: str, shop_id: str | None, reason: str | None, actor_user_id: str
) -> AdminSyncTriggerResult:
    """Runs synchronously in-request — this codebase has no background job
    queue yet (see sync_shop_listings docstring). Not queued; the request
    blocks until the sync finishes or fails."""
    from app.services.etsy_sync import sync_shop_listings, SyncError

    if shop_id:
        shop = (await db.execute(
            select(EtsyShop).where(EtsyShop.id == shop_id, EtsyShop.organization_id == org_id)
        )).scalar_one_or_none()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found or does not belong to this organization.")
    else:
        shop = (await db.execute(
            select(EtsyShop).where(EtsyShop.organization_id == org_id, EtsyShop.is_connected.is_(True))
            .order_by(desc(EtsyShop.created_at))
        )).scalar_one_or_none()
        if not shop:
            raise HTTPException(status_code=400, detail="No connected Etsy shop found for this organization.")

    await _write_owner_audit_log(
        db, actor_user_id, "owner_manual_sync_requested",
        f"Manual sync requested for shop {shop.shop_name}. Reason: {reason or 'not given'}",
        organization_id=org_id,
    )
    await db.commit()

    try:
        job = await sync_shop_listings(db, org_id, shop.id)
    except SyncError as exc:
        await _write_owner_audit_log(
            db, actor_user_id, "owner_manual_sync_failed",
            f"Manual sync failed for shop {shop.shop_name}: {exc.message}",
            organization_id=org_id,
        )
        await db.commit()
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    await _write_owner_audit_log(
        db, actor_user_id, "owner_manual_sync_completed",
        f"Manual sync finished for shop {shop.shop_name}: status={job.status}",
        organization_id=org_id,
    )
    await db.commit()

    return AdminSyncTriggerResult(status=job.status, job_id=job.id, message=f"Sync {job.status}.")


# ── Password reset ─────────────────────────────────────────────────────────────

async def send_owner_password_reset(db: AsyncSession, user_id: str, actor_user_id: str) -> str:
    from app.services.auth import request_password_reset

    user = await _get_user_row(db, user_id)
    await request_password_reset(user.email, db)

    await _write_owner_audit_log(
        db, actor_user_id, "owner_password_reset_requested",
        f"Owner requested a password reset email for user {user.email}.",
        target_user_id=user.id,
    )
    await db.commit()

    return "Password reset email sent if the account can receive email."


# ── Payments ──────────────────────────────────────────────────────────────────

def _extract_payment_refs(event_type: str, payload: dict) -> dict:
    """Best-effort, conservative extraction from a raw Stripe webhook payload.
    Only reads well-known top-level keys shared by invoice/checkout-session/
    payment-intent-shaped objects; returns None for anything not confidently
    present rather than guessing. Never touches card data — Stripe never puts
    full card numbers in webhook payloads."""
    obj = (payload or {}).get("data", {}).get("object", {}) if payload else {}
    if not isinstance(obj, dict):
        return {}

    charge_id = obj.get("charge") if isinstance(obj.get("charge"), str) else None
    payment_intent_id = obj.get("payment_intent") if isinstance(obj.get("payment_intent"), str) else None
    amount_raw = obj.get("amount_due") or obj.get("amount_total") or obj.get("amount_paid") or obj.get("amount")
    amount = round(amount_raw / 100, 2) if isinstance(amount_raw, (int, float)) else None
    currency = obj.get("currency") if isinstance(obj.get("currency"), str) else None

    refundable_ref = payment_intent_id or charge_id
    return {"refundable_ref": refundable_ref, "amount": amount, "currency": currency}


def _derive_payment_status(event_type: str) -> str:
    if "failed" in event_type:
        return "failed"
    if "completed" in event_type or "succeeded" in event_type or "paid" in event_type:
        return "succeeded"
    return "recorded"


def _mask_stripe_id(value: str | None) -> str | None:
    if not value or len(value) <= 8:
        return value
    return f"{value[:6]}…{value[-4:]}"


async def list_payments(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 25,
    q: str | None = None,
    organization_id: str | None = None,
    plan: str | None = None,
    subscription_status: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
) -> dict:
    filters = []
    if organization_id:
        filters.append(BillingEvent.organization_id == organization_id)
    from_dt = _parse_date_bound(created_from)
    to_dt = _parse_date_bound(created_to, end_of_day=True)
    if from_dt:
        filters.append(BillingEvent.created_at >= from_dt)
    if to_dt:
        filters.append(BillingEvent.created_at <= to_dt)

    if q or plan or subscription_status:
        org_ids_q = select(Organization.id)
        if q:
            like = f"%{q}%"
            owner_ids_q = select(User.id).where(User.email.ilike(like))
            org_ids_q = org_ids_q.where(or_(Organization.name.ilike(like), Organization.id == q, Organization.owner_id.in_(owner_ids_q)))
        if plan or subscription_status:
            sub_filter = []
            if plan:
                sub_filter.append(Subscription.plan == plan)
            if subscription_status:
                sub_filter.append(Subscription.status == subscription_status)
            org_ids_q = org_ids_q.where(Organization.id.in_(select(Subscription.organization_id).where(*sub_filter)))
        filters.append(BillingEvent.organization_id.in_(org_ids_q))

    result = await _paginate(db, BillingEvent, page, page_size, filters=filters)
    events: list[BillingEvent] = result["items"]

    org_ids = list({e.organization_id for e in events if e.organization_id})
    orgs_by_id: dict[str, Organization] = {}
    owners_by_org: dict[str, User] = {}
    subs_by_org: dict[str, Subscription] = {}
    if org_ids:
        orgs = (await db.execute(select(Organization).where(Organization.id.in_(org_ids)))).scalars().all()
        orgs_by_id = {o.id: o for o in orgs}
        owner_ids = list({o.owner_id for o in orgs})
        owners = (await db.execute(select(User).where(User.id.in_(owner_ids)))).scalars().all()
        owners_by_id = {u.id: u for u in owners}
        owners_by_org = {o.id: owners_by_id.get(o.owner_id) for o in orgs}
        subs = (await db.execute(select(Subscription).where(Subscription.organization_id.in_(org_ids)))).scalars().all()
        subs_by_org = {s.organization_id: s for s in subs}

    items = []
    for e in events:
        org = orgs_by_id.get(e.organization_id) if e.organization_id else None
        owner = owners_by_org.get(e.organization_id) if e.organization_id else None
        sub = subs_by_org.get(e.organization_id) if e.organization_id else None
        refs = _extract_payment_refs(e.event_type, e.payload)
        items.append(AdminPaymentItem(
            id=e.id,
            organization_id=e.organization_id,
            organization_name=org.name if org else None,
            owner_email=owner.email if owner else None,
            plan=sub.plan if sub else None,
            subscription_status=sub.status if sub else None,
            event_type=e.event_type,
            status=_derive_payment_status(e.event_type),
            amount=refs.get("amount"),
            currency=refs.get("currency"),
            stripe_customer_id=_mask_stripe_id(sub.stripe_customer_id if sub else None),
            refundable_ref=_mask_stripe_id(refs.get("refundable_ref")),
            created_at=e.created_at,
        ))

    result["items"] = items
    return result


async def refund_payment(db: AsyncSession, billing_event_id: str, reason: str, amount: float | None, actor_user_id: str) -> dict:
    event = (await db.execute(select(BillingEvent).where(BillingEvent.id == billing_event_id))).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Payment record not found.")

    refs = _extract_payment_refs(event.event_type, event.payload)
    ref = refs.get("refundable_ref")
    org_id = event.organization_id

    if not ref:
        raise HTTPException(
            status_code=400,
            detail="No refundable charge or payment intent reference was found on this record. Refund it directly in the Stripe dashboard.",
        )
    if not settings.is_stripe_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured in this environment.")

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    kwargs: dict = {"reason": "requested_by_customer"}
    if ref.startswith("pi_"):
        kwargs["payment_intent"] = ref
    else:
        kwargs["charge"] = ref
    if amount is not None:
        kwargs["amount"] = int(round(amount * 100))

    try:
        refund = stripe.Refund.create(**kwargs)
        ok = True
        message = f"Refund created (status={refund.get('status', 'unknown')})."
    except Exception as exc:
        ok = False
        message = f"Stripe refund failed: {exc}"

    await _write_owner_audit_log(
        db, actor_user_id,
        "owner_refund_success" if ok else "owner_refund_failed",
        f"Refund attempt on {_mask_stripe_id(ref)}: {message}. Reason: {reason}",
        organization_id=org_id,
    )
    await db.commit()

    if not ok:
        raise HTTPException(status_code=502, detail=message)
    return {"ok": True, "message": message}


# ── Alerts ────────────────────────────────────────────────────────────────────

async def _ensure_default_alert_rules(db: AsyncSession) -> None:
    existing = (await db.execute(select(OwnerAlertRule.event_type))).scalars().all()
    existing_set = set(existing)
    created = False
    for defaults in _DEFAULT_ALERT_RULES:
        if defaults["event_type"] not in existing_set:
            db.add(OwnerAlertRule(**defaults))
            created = True
    if created:
        await db.commit()


async def list_alert_rules(db: AsyncSession) -> list[AdminAlertRuleOut]:
    await _ensure_default_alert_rules(db)
    rules = (await db.execute(select(OwnerAlertRule).order_by(OwnerAlertRule.name))).scalars().all()
    return [
        AdminAlertRuleOut(
            id=r.id, name=r.name, event_type=r.event_type, enabled=r.enabled,
            threshold_count=r.threshold_count, window_minutes=r.window_minutes,
            channel_email_enabled=r.channel_email_enabled, channel_email_to=r.channel_email_to,
            channel_slack_enabled=r.channel_slack_enabled,
            slack_webhook_configured=bool(r.encrypted_slack_webhook),
            last_triggered_at=r.last_triggered_at, updated_at=r.updated_at,
        )
        for r in rules
    ]


async def update_alert_rule(db: AsyncSession, rule_id: str, update: dict, actor_user_id: str) -> AdminAlertRuleOut:
    from app.core.encryption import encrypt_token

    rule = (await db.execute(select(OwnerAlertRule).where(OwnerAlertRule.id == rule_id))).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found.")

    changed_fields = []
    for field in ("enabled", "threshold_count", "window_minutes", "channel_email_enabled", "channel_email_to", "channel_slack_enabled"):
        if update.get(field) is not None:
            setattr(rule, field, update[field])
            changed_fields.append(field)

    slack_url = update.get("slack_webhook_url")
    if slack_url is not None:
        rule.encrypted_slack_webhook = encrypt_token(slack_url) if slack_url else None
        changed_fields.append("slack_webhook")

    rule.updated_by_user_id = actor_user_id
    db.add(rule)
    await db.flush()

    await _write_owner_audit_log(
        db, actor_user_id, "owner_alert_rule_updated",
        f"Alert rule '{rule.name}' updated: {', '.join(changed_fields) or 'no changes'}.",
    )
    await db.commit()
    await db.refresh(rule)

    return AdminAlertRuleOut(
        id=rule.id, name=rule.name, event_type=rule.event_type, enabled=rule.enabled,
        threshold_count=rule.threshold_count, window_minutes=rule.window_minutes,
        channel_email_enabled=rule.channel_email_enabled, channel_email_to=rule.channel_email_to,
        channel_slack_enabled=rule.channel_slack_enabled,
        slack_webhook_configured=bool(rule.encrypted_slack_webhook),
        last_triggered_at=rule.last_triggered_at, updated_at=rule.updated_at,
    )


def _send_slack_message(webhook_url: str, text: str) -> bool:
    import httpx
    try:
        resp = httpx.post(webhook_url, json={"text": text}, timeout=10.0)
        return resp.status_code < 300
    except Exception:
        logger.warning("Slack alert send failed (webhook unreachable or invalid)")
        return False


async def test_alert(db: AsyncSession, rule_id: str, actor_user_id: str) -> dict:
    from app.core.encryption import decrypt_token
    from app.services.email import send_email

    rule = (await db.execute(select(OwnerAlertRule).where(OwnerAlertRule.id == rule_id))).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found.")

    sent_any = False
    results = []
    if rule.channel_email_enabled:
        to = rule.channel_email_to or settings.SUPPORT_EMAIL
        result = send_email(to, f"[Test] Bulk Edit App alert: {rule.name}", f"This is a test of the '{rule.name}' alert rule. No action needed.")
        sent_any = sent_any or result.sent
        results.append(f"email: {result.reason}")
    if rule.channel_slack_enabled and rule.encrypted_slack_webhook:
        ok = _send_slack_message(decrypt_token(rule.encrypted_slack_webhook), f"Test alert: {rule.name} — no action needed.")
        sent_any = sent_any or ok
        results.append(f"slack: {'sent' if ok else 'failed'}")
    if not results:
        results.append("no channels enabled")

    await _write_owner_audit_log(
        db, actor_user_id, "owner_alert_test_sent",
        f"Test alert sent for rule '{rule.name}': {', '.join(results)}.",
    )
    await db.commit()

    return {"ok": sent_any, "message": f"Test alert result — {', '.join(results)}."}


_ALERT_EVENT_COUNTERS = {
    "payment_failure": (BillingEvent, BillingEvent.event_type == "invoice.payment_failed", BillingEvent.created_at),
    "sync_failure_spike": (SyncJob, SyncJob.status == "failed", SyncJob.created_at),
    "bulk_edit_failures": (BulkEditSession, BulkEditSession.status == "failed", BulkEditSession.created_at),
    "ai_failures": (AISession, AISession.status == "failed", AISession.created_at),
}


async def run_alert_check(db: AsyncSession, actor_user_id: str) -> AdminAlertCheckResult:
    """On-demand alert evaluation — there is no background scheduler in this
    codebase yet, so this only runs when an owner clicks "Run alert check
    now". See OwnerAlertRule model docstring."""
    from app.core.encryption import decrypt_token
    from app.services.email import send_email

    await _ensure_default_alert_rules(db)
    rules = (await db.execute(select(OwnerAlertRule).where(OwnerAlertRule.enabled.is_(True)))).scalars().all()

    now = datetime.now(timezone.utc)
    triggered: list[str] = []

    for rule in rules:
        if rule.event_type == "system_health":
            health = await get_system_health(db)
            count = health["recent_failed_scheduled_runs"] + health["recent_failed_ai_sessions"]
            if health["redis_status"] == "error":
                count += 1
        else:
            counter = _ALERT_EVENT_COUNTERS.get(rule.event_type)
            if not counter:
                continue
            model, cond, date_col = counter
            since = now - timedelta(minutes=rule.window_minutes)
            count = (await db.execute(
                select(func.count()).select_from(model).where(cond, date_col >= since)
            )).scalar_one()

        if count < rule.threshold_count:
            continue

        last = rule.last_triggered_at
        if last and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last and (now - last) < timedelta(minutes=rule.window_minutes):
            continue  # dedupe — already alerted within this window

        message = f"{rule.name}: {count} events in the last {rule.window_minutes} minutes (threshold {rule.threshold_count})."
        if rule.channel_email_enabled:
            send_email(rule.channel_email_to or settings.SUPPORT_EMAIL, f"[Alert] {rule.name}", message)
        if rule.channel_slack_enabled and rule.encrypted_slack_webhook:
            _send_slack_message(decrypt_token(rule.encrypted_slack_webhook), message)

        rule.last_triggered_at = now
        db.add(rule)
        triggered.append(rule.event_type)

    await _write_owner_audit_log(
        db, actor_user_id, "owner_alert_check_run",
        f"Alert check run: {len(rules)} enabled rule(s), {len(triggered)} triggered ({', '.join(triggered) or 'none'}).",
    )
    await db.commit()

    return AdminAlertCheckResult(checked=len(rules), triggered=triggered)
