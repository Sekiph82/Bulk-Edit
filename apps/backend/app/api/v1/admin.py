from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_superuser
from app.schemas.admin import (
    AdminOverviewOut,
    AdminPage,
    AdminUserListItem,
    AdminUserDetail,
    AdminOrganizationListItem,
    AdminOrganizationDetail,
    AdminSubscriptionListItem,
    AdminSubscriptionSummary,
    AdminUsageSummary,
    AdminShopSummary,
    AdminSyncJobSummary,
    AdminBulkEditSessionSummary,
    AdminAiSessionSummary,
    AdminCsvJobSummary,
    AdminDynamicPricingJobSummary,
    AdminScheduledJobSummary,
    AdminScheduledJobRunSummary,
    AdminAuditEventSummary,
    AdminActionResult,
    AdminBillingSummary,
    AdminStripeSummary,
    AdminProductUsage,
    AdminSystemHealth,
    AdminContactSubmissionSummary,
    AdminFeatureFlags,
    AdminTrendsOut,
)
import app.services.admin as svc

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverviewOut)
async def admin_overview(
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_admin_overview(db)
    return AdminOverviewOut(**data)


@router.get("/users", response_model=AdminPage[AdminUserListItem])
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    q: str | None = Query(None, description="Search email, name, or exact user id"),
    status: str | None = Query(None, pattern="^(active|disabled|all)$"),
    role: str | None = Query(None, pattern="^(superuser|user|all)$"),
    organization_id: str | None = Query(None),
    plan: str | None = Query(None),
    created_from: str | None = Query(None, description="YYYY-MM-DD"),
    created_to: str | None = Query(None, description="YYYY-MM-DD"),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_users(
        db, page=page, page_size=page_size, q=q,
        status=None if status == "all" else status,
        role=None if role == "all" else role,
        organization_id=organization_id, plan=plan,
        created_from=created_from, created_to=created_to,
    )
    return AdminPage[AdminUserListItem](
        items=result["items"],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def admin_get_user(
    user_id: str,
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_user_detail(db, user_id)


@router.get("/organizations", response_model=AdminPage[AdminOrganizationListItem])
async def admin_list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    q: str | None = Query(None, description="Search name, exact org id, or owner email"),
    plan: str | None = Query(None),
    subscription_status: str | None = Query(None),
    etsy_connected: bool | None = Query(None),
    created_from: str | None = Query(None, description="YYYY-MM-DD"),
    created_to: str | None = Query(None, description="YYYY-MM-DD"),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_organizations(
        db, page=page, page_size=page_size, q=q, plan=plan,
        subscription_status=subscription_status, etsy_connected=etsy_connected,
        created_from=created_from, created_to=created_to,
    )
    return AdminPage[AdminOrganizationListItem](
        items=result["items"],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/organizations/{org_id}", response_model=AdminOrganizationDetail)
async def admin_get_organization(
    org_id: str,
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_organization_detail(db, org_id)


@router.get("/metrics/trends", response_model=AdminTrendsOut)
async def admin_metrics_trends(
    days: int = Query(30, ge=1, le=365),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_admin_trends(db, days=days)


@router.get("/subscriptions", response_model=AdminPage[AdminSubscriptionListItem])
async def admin_list_subscriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_subscriptions(db, page=page, page_size=page_size)
    return AdminPage[AdminSubscriptionListItem](
        items=[AdminSubscriptionListItem.model_validate(s) for s in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/usage", response_model=AdminPage[AdminUsageSummary])
async def admin_list_usage(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_usage(db, page=page, page_size=page_size)
    return AdminPage[AdminUsageSummary](
        items=[AdminUsageSummary.model_validate(u) for u in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/shops", response_model=AdminPage[AdminShopSummary])
async def admin_list_shops(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_shops(db, page=page, page_size=page_size)
    return AdminPage[AdminShopSummary](
        items=[AdminShopSummary.model_validate(s) for s in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/sync-jobs", response_model=AdminPage[AdminSyncJobSummary])
async def admin_list_sync_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_sync_jobs(db, page=page, page_size=page_size)
    return AdminPage[AdminSyncJobSummary](
        items=[AdminSyncJobSummary.model_validate(s) for s in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/bulk-edit-sessions", response_model=AdminPage[AdminBulkEditSessionSummary])
async def admin_list_bulk_edit_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_bulk_edit_sessions(db, page=page, page_size=page_size)
    return AdminPage[AdminBulkEditSessionSummary](
        items=[AdminBulkEditSessionSummary.model_validate(s) for s in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/ai-sessions", response_model=AdminPage[AdminAiSessionSummary])
async def admin_list_ai_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_ai_sessions(db, page=page, page_size=page_size)
    return AdminPage[AdminAiSessionSummary](
        items=[AdminAiSessionSummary.model_validate(s) for s in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/csv-jobs", response_model=AdminPage[AdminCsvJobSummary])
async def admin_list_csv_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_csv_jobs(db, page=page, page_size=page_size)
    return AdminPage[AdminCsvJobSummary](
        items=[AdminCsvJobSummary.model_validate(j) for j in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/dynamic-pricing-jobs", response_model=AdminPage[AdminDynamicPricingJobSummary])
async def admin_list_dynamic_pricing_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_dynamic_pricing_jobs(db, page=page, page_size=page_size)
    return AdminPage[AdminDynamicPricingJobSummary](
        items=[AdminDynamicPricingJobSummary.model_validate(j) for j in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/scheduled-jobs", response_model=AdminPage[AdminScheduledJobSummary])
async def admin_list_scheduled_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_scheduled_jobs(db, page=page, page_size=page_size)
    return AdminPage[AdminScheduledJobSummary](
        items=[AdminScheduledJobSummary.model_validate(j) for j in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/scheduled-job-runs", response_model=AdminPage[AdminScheduledJobRunSummary])
async def admin_list_scheduled_job_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_scheduled_job_runs(db, page=page, page_size=page_size)
    return AdminPage[AdminScheduledJobRunSummary](
        items=[AdminScheduledJobRunSummary.model_validate(r) for r in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/events", response_model=AdminPage[AdminAuditEventSummary])
async def admin_list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_events(db, page=page, page_size=page_size)
    return AdminPage[AdminAuditEventSummary](
        items=[AdminAuditEventSummary.model_validate(e) for e in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.post("/users/{user_id}/disable", response_model=AdminActionResult)
async def admin_disable_user(
    user_id: str,
    su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    user = await svc.disable_user(db, user_id, acting_user_id=su.id)
    return AdminActionResult(ok=True, message=f"User {user.email} disabled")


@router.post("/users/{user_id}/enable", response_model=AdminActionResult)
async def admin_enable_user(
    user_id: str,
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    user = await svc.enable_user(db, user_id)
    return AdminActionResult(ok=True, message=f"User {user.email} enabled")


@router.post("/scheduled-jobs/{job_id}/pause", response_model=AdminActionResult)
async def admin_pause_scheduled_job(
    job_id: str,
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    job = await svc.pause_scheduled_job(db, job_id)
    return AdminActionResult(ok=True, message=f"Scheduled job '{job.name}' paused")


@router.post("/scheduled-jobs/{job_id}/resume", response_model=AdminActionResult)
async def admin_resume_scheduled_job(
    job_id: str,
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    job = await svc.resume_scheduled_job(db, job_id)
    return AdminActionResult(ok=True, message=f"Scheduled job '{job.name}' resumed")


# ── Business Dashboard Summary Endpoints ──────────────────────────────────────

@router.get("/billing-summary", response_model=AdminBillingSummary)
async def admin_billing_summary(
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_billing_summary(db)
    return AdminBillingSummary(**data)


@router.get("/stripe-summary", response_model=AdminStripeSummary)
async def admin_stripe_summary(
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_stripe_summary(db)
    return AdminStripeSummary(**data)


@router.get("/product-usage", response_model=AdminProductUsage)
async def admin_product_usage(
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_product_usage(db)
    return AdminProductUsage(**data)


@router.get("/system-health", response_model=AdminSystemHealth)
async def admin_system_health(
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_system_health(db)
    return AdminSystemHealth(**data)


@router.get("/audit-log", response_model=AdminPage[AdminAuditEventSummary])
async def admin_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_events(db, page=page, page_size=page_size)
    return AdminPage[AdminAuditEventSummary](
        items=[AdminAuditEventSummary.model_validate(e) for e in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/contact-submissions", response_model=AdminPage[AdminContactSubmissionSummary])
async def admin_list_contact_submissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _su=Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.list_contact_submissions(db, page=page, page_size=page_size)
    return AdminPage[AdminContactSubmissionSummary](
        items=[AdminContactSubmissionSummary.model_validate(c) for c in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
    )


@router.get("/feature-flags", response_model=AdminFeatureFlags)
async def admin_feature_flags(
    _su=Depends(require_superuser),
):
    return AdminFeatureFlags(**svc.get_feature_flags())
