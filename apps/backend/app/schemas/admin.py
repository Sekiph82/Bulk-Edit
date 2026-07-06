from __future__ import annotations
from datetime import datetime
from typing import Generic, TypeVar, Any
from pydantic import BaseModel

T = TypeVar("T")


class AdminPage(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int


# ── Overview ─────────────────────────────────────────────────────────────────

class AdminOverviewOut(BaseModel):
    total_users: int
    total_organizations: int
    active_subscriptions: int
    paid_subscriptions: int
    total_listings: int
    total_scheduled_jobs: int
    total_ai_sessions: int
    total_csv_jobs: int


# ── Audit Events ──────────────────────────────────────────────────────────────
# Defined early so User/Organization detail schemas below can embed it.

class AdminAuditEventSummary(BaseModel):
    id: str
    organization_id: str
    user_id: str | None
    event_type: str
    entity_type: str | None
    entity_id: str | None
    message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Shops ─────────────────────────────────────────────────────────────────────
# SECURITY: no Etsy access_token or refresh_token in response
# Defined early so Organization detail schema below can embed it.

class AdminShopSummary(BaseModel):
    id: str
    organization_id: str
    etsy_shop_id: str
    shop_name: str
    is_connected: bool
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Users ────────────────────────────────────────────────────────────────────
# SECURITY: password_hash never included

class AdminUserListItem(BaseModel):
    id: str
    email: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    # Primary organization (first membership) — display convenience only,
    # a user could technically belong to more than one organization.
    organization_id: str | None = None
    organization_name: str | None = None
    plan: str | None = None

    class Config:
        from_attributes = True


class AdminUserOrgMembership(BaseModel):
    organization_id: str
    organization_name: str
    role: str


class AdminUserUsageSummary(BaseModel):
    bulk_edit_sessions_count: int
    ai_sessions_count: int
    csv_jobs_count: int
    dynamic_pricing_jobs_count: int
    media_jobs_count: int


class AdminUserDetail(AdminUserListItem):
    organizations: list[AdminUserOrgMembership] = []
    usage: AdminUserUsageSummary
    recent_events: list[AdminAuditEventSummary] = []


# ── Organizations ─────────────────────────────────────────────────────────────

class AdminOrganizationListItem(BaseModel):
    id: str
    name: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    owner_email: str | None = None
    plan: str | None = None
    subscription_status: str | None = None
    etsy_connected: bool = False
    users_count: int = 0

    class Config:
        from_attributes = True


class AdminSubscriptionSummary(BaseModel):
    id: str
    organization_id: str
    plan: str
    status: str
    stripe_customer_id: str | None      # customer id OK; secret key never returned
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminOrgMemberItem(BaseModel):
    user_id: str
    email: str
    full_name: str | None
    role: str


class AdminOrgUsageSummary(BaseModel):
    bulk_edit_sessions_count: int
    ai_sessions_count: int
    csv_jobs_count: int
    dynamic_pricing_jobs_count: int
    sync_jobs_count: int
    media_jobs_count: int
    video_renders_count: int


class AdminOrgRiskSummary(BaseModel):
    failed_bulk_edit_count: int
    failed_ai_count: int
    failed_scheduled_runs_count: int
    etsy_disconnected: bool
    billing_issue: bool


class AdminOrganizationDetail(AdminOrganizationListItem):
    subscription: AdminSubscriptionSummary | None
    shop_count: int
    listing_count: int
    members: list[AdminOrgMemberItem] = []
    shops: list[AdminShopSummary] = []
    usage: AdminOrgUsageSummary
    recent_events: list[AdminAuditEventSummary] = []
    risk: AdminOrgRiskSummary


# ── Subscriptions ─────────────────────────────────────────────────────────────

class AdminSubscriptionListItem(AdminSubscriptionSummary):
    pass


# ── Usage ─────────────────────────────────────────────────────────────────────

class AdminUsageSummary(BaseModel):
    id: str
    organization_id: str
    period_key: str
    listings_synced: int
    bulk_edits_used: int
    ai_credits_used: int
    media_assets_used: int
    dynamic_pricing_jobs_used: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True




# ── Sync Jobs ─────────────────────────────────────────────────────────────────

class AdminSyncJobSummary(BaseModel):
    id: str
    organization_id: str
    etsy_shop_id: str
    job_type: str
    status: str
    total_items: int
    processed_items: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Bulk Edit Sessions ────────────────────────────────────────────────────────

class AdminBulkEditSessionSummary(BaseModel):
    id: str
    organization_id: str
    created_by_user_id: str | None
    name: str | None
    status: str
    selected_count: int
    change_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── AI Sessions ───────────────────────────────────────────────────────────────

class AdminAiSessionSummary(BaseModel):
    id: str
    organization_id: str
    created_by_user_id: str | None
    listing_id: str | None
    tool: str
    status: str
    ai_provider: str | None
    ai_model: str | None
    suggestion_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── CSV Jobs ──────────────────────────────────────────────────────────────────

class AdminCsvJobSummary(BaseModel):
    id: str
    organization_id: str
    user_id: str | None
    job_type: str
    status: str
    original_filename: str | None
    row_count: int
    valid_row_count: int
    invalid_row_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Dynamic Pricing Jobs ──────────────────────────────────────────────────────

class AdminDynamicPricingJobSummary(BaseModel):
    id: str
    organization_id: str
    user_id: str | None
    status: str
    rule_type: str
    row_count: int
    recommended_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Scheduled Jobs ────────────────────────────────────────────────────────────

class AdminScheduledJobSummary(BaseModel):
    id: str
    organization_id: str
    created_by_user_id: str | None
    name: str
    job_type: str
    status: str
    schedule_type: str
    timezone: str
    next_run_at: datetime | None
    last_run_at: datetime | None
    run_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Scheduled Job Runs ────────────────────────────────────────────────────────

class AdminScheduledJobRunSummary(BaseModel):
    id: str
    organization_id: str
    scheduled_job_id: str
    trigger_type: str
    job_type: str
    status: str
    duration_ms: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Safe action response ──────────────────────────────────────────────────────

class AdminActionResult(BaseModel):
    ok: bool
    message: str


# ── Business Dashboard Summaries ──────────────────────────────────────────────

class AdminBillingSummary(BaseModel):
    total_subscriptions: int
    free_plan_count: int
    basic_monthly_count: int
    basic_yearly_count: int
    pro_monthly_count: int
    pro_yearly_count: int
    active_count: int
    trialing_count: int
    canceled_count: int
    cancel_at_period_end_count: int
    estimated_monthly_revenue: float  # projected, not guaranteed cash


class AdminStripeSummary(BaseModel):
    total_stripe_customers: int
    subscriptions_with_stripe_sub: int
    active_stripe_subscriptions: int
    canceling_at_period_end: int
    total_billing_events: int


class AdminProductUsage(BaseModel):
    total_listings: int
    total_bulk_edit_sessions: int
    total_ai_sessions: int
    total_csv_jobs: int
    total_dynamic_pricing_jobs: int
    total_sync_jobs: int
    total_shops: int


# ── Contact Submissions ────────────────────────────────────────────────────────

class AdminContactSubmissionSummary(BaseModel):
    id: str
    name: str
    email: str
    subject: str
    message: str
    email_delivered: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Feature Flags (read-only) ─────────────────────────────────────────────────
# Reflects real env-driven config. No functional toggle exists yet — this is
# display-only until a real admin-controlled flag store is built.

class AdminFeatureFlag(BaseModel):
    key: str
    enabled: bool
    source: str  # "env" — always env for now, no DB-backed override exists


class AdminFeatureFlags(BaseModel):
    flags: list[AdminFeatureFlag]


class AdminSystemHealth(BaseModel):
    database_status: str
    redis_status: str          # "ok" | "not_configured" | "error"
    rate_limit_backend: str    # "memory" | "redis"
    rate_limit_enabled: bool
    sentry_configured: bool
    worker_status: str         # "not_configured" | "configured"
    csp_mode: str              # "unsafe_inline_deferred" | "hash_based"
    total_users: int
    total_organizations: int
    total_audit_events: int
    recent_failed_scheduled_runs: int
    recent_failed_ai_sessions: int


# ── Trends ────────────────────────────────────────────────────────────────────
# Real daily counts from the database only — zero-filled for days with no
# activity. Never estimated or extrapolated.

class AdminTrendPoint(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class AdminTrendSeries(BaseModel):
    users: list[AdminTrendPoint]
    organizations: list[AdminTrendPoint]
    bulk_edit_jobs: list[AdminTrendPoint]
    media_jobs: list[AdminTrendPoint]


class AdminTrendsOut(BaseModel):
    days: int
    series: AdminTrendSeries
