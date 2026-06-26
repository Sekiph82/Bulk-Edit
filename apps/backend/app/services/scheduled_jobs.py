"""
Scheduled Jobs service.

SAFETY GUARANTEE:
- Scheduled jobs NEVER write to Etsy directly.
- etsy_sync: read-only listing sync only.
- bulk_edit_draft: creates BulkEditSession(status="draft") — never applies.
- dynamic_pricing_preview: creates preview job — never converts or applies.
- csv_export_snapshot: returns metadata summary — no file write, no Etsy write.
- User must take explicit action to apply any output.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import get_plan_limits
from app.models.bulk_edit_change import BulkEditChange
from app.models.bulk_edit_session import BulkEditSession
from app.models.etsy_shop import EtsyShop
from app.models.listing import Listing
from app.models.scheduled_job import ScheduledJob, VALID_JOB_TYPES, VALID_STATUSES, VALID_SCHEDULE_TYPES
from app.models.scheduled_job_run import ScheduledJobRun
from app.services.billing import ensure_subscription_exists
from app.services.schedule_calculator import (
    ScheduleError,
    calculate_next_run,
    should_run_now,
    validate_schedule,
)

logger = logging.getLogger(__name__)


class ScheduledJobError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ── Plan gate ─────────────────────────────────────────────────────────────────

async def assert_scheduling_allowed(org_id: str, db: AsyncSession) -> None:
    sub = await ensure_subscription_exists(org_id, db)
    limits = get_plan_limits(sub.plan)
    if not limits.get("can_schedule_jobs", False):
        raise ScheduledJobError(
            "Scheduled jobs require a Basic or Pro plan. Upgrade to access this feature.", 402
        )
    max_jobs = limits.get("max_scheduled_jobs", 0)
    result = await db.execute(
        select(func.count(ScheduledJob.id)).where(
            ScheduledJob.organization_id == org_id,
            ScheduledJob.status == "active",
        )
    )
    active_count = result.scalar_one()
    if active_count >= max_jobs:
        raise ScheduledJobError(
            f"Active scheduled job limit reached ({max_jobs} active jobs on your plan). "
            "Pause or disable existing jobs, or upgrade your plan.", 402
        )


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def create_scheduled_job(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    name: str,
    job_type: str,
    schedule_type: str,
    schedule_payload: dict[str, Any],
    job_payload: dict[str, Any] | None,
    timezone_str: str,
    max_runs: int | None,
    starts_at: datetime | None,
    ends_at: datetime | None,
) -> ScheduledJob:
    if job_type not in VALID_JOB_TYPES:
        raise ScheduledJobError(f"Invalid job_type: {job_type!r}. Must be one of: {sorted(VALID_JOB_TYPES)}", 400)
    if schedule_type not in VALID_SCHEDULE_TYPES:
        raise ScheduledJobError(f"Invalid schedule_type: {schedule_type!r}. Must be one of: {sorted(VALID_SCHEDULE_TYPES)}", 400)

    try:
        validate_schedule(schedule_type, schedule_payload)
    except ScheduleError as exc:
        raise ScheduledJobError(exc.message, exc.status_code)

    await assert_scheduling_allowed(organization_id, db)

    try:
        next_run = calculate_next_run(schedule_type, schedule_payload, timezone_str)
    except ScheduleError as exc:
        raise ScheduledJobError(exc.message, exc.status_code)

    job = ScheduledJob(
        organization_id=organization_id,
        created_by_user_id=user_id,
        name=name,
        job_type=job_type,
        status="active",
        schedule_type=schedule_type,
        schedule_payload=schedule_payload,
        job_payload=job_payload or {},
        timezone=timezone_str,
        next_run_at=next_run,
        max_runs=max_runs,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    db.add(job)
    await db.flush()
    await db.commit()
    await db.refresh(job)
    return job


async def list_scheduled_jobs(
    db: AsyncSession,
    organization_id: str,
    status: str | None = None,
    job_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ScheduledJob]:
    q = select(ScheduledJob).where(ScheduledJob.organization_id == organization_id)
    if status:
        q = q.where(ScheduledJob.status == status)
    if job_type:
        q = q.where(ScheduledJob.job_type == job_type)
    q = q.order_by(ScheduledJob.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_scheduled_job(db: AsyncSession, job_id: str, organization_id: str) -> ScheduledJob:
    result = await db.execute(
        select(ScheduledJob).where(
            ScheduledJob.id == job_id,
            ScheduledJob.organization_id == organization_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise ScheduledJobError("Scheduled job not found.", 404)
    return job


async def update_scheduled_job(
    db: AsyncSession,
    job_id: str,
    organization_id: str,
    name: str | None = None,
    job_payload: dict[str, Any] | None = None,
    schedule_payload: dict[str, Any] | None = None,
    timezone_str: str | None = None,
    max_runs: int | None = None,
    ends_at: datetime | None = None,
) -> ScheduledJob:
    job = await get_scheduled_job(db, job_id, organization_id)
    if name is not None:
        job.name = name
    if job_payload is not None:
        job.job_payload = job_payload
    if schedule_payload is not None or timezone_str is not None:
        new_payload = schedule_payload if schedule_payload is not None else job.schedule_payload
        new_tz = timezone_str if timezone_str is not None else job.timezone
        try:
            validate_schedule(job.schedule_type, new_payload)
            next_run = calculate_next_run(job.schedule_type, new_payload, new_tz)
        except ScheduleError as exc:
            raise ScheduledJobError(exc.message, exc.status_code)
        job.schedule_payload = new_payload
        job.timezone = new_tz
        job.next_run_at = next_run
    if max_runs is not None:
        job.max_runs = max_runs
    if ends_at is not None:
        job.ends_at = ends_at
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def pause_scheduled_job(db: AsyncSession, job_id: str, organization_id: str) -> ScheduledJob:
    job = await get_scheduled_job(db, job_id, organization_id)
    if job.status not in ("active",):
        raise ScheduledJobError(f"Cannot pause job with status '{job.status}'.", 400)
    job.status = "paused"
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def resume_scheduled_job(db: AsyncSession, job_id: str, organization_id: str) -> ScheduledJob:
    job = await get_scheduled_job(db, job_id, organization_id)
    if job.status != "paused":
        raise ScheduledJobError(f"Cannot resume job with status '{job.status}'.", 400)
    await assert_scheduling_allowed(organization_id, db)
    try:
        job.next_run_at = calculate_next_run(job.schedule_type, job.schedule_payload, job.timezone)
    except ScheduleError as exc:
        raise ScheduledJobError(exc.message, exc.status_code)
    job.status = "active"
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def disable_scheduled_job(db: AsyncSession, job_id: str, organization_id: str) -> ScheduledJob:
    job = await get_scheduled_job(db, job_id, organization_id)
    if job.status == "disabled":
        raise ScheduledJobError("Job is already disabled.", 400)
    job.status = "disabled"
    job.disabled_at = datetime.now(timezone.utc)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


# ── Run ───────────────────────────────────────────────────────────────────────

async def run_scheduled_job_now(
    db: AsyncSession,
    job_id: str,
    organization_id: str,
    user_id: str,
) -> ScheduledJobRun:
    job = await get_scheduled_job(db, job_id, organization_id)
    return await execute_scheduled_job(db, job, trigger_type="manual", triggered_by_user_id=user_id)


async def find_due_jobs(db: AsyncSession, organization_id: str) -> list[ScheduledJob]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ScheduledJob).where(
            ScheduledJob.organization_id == organization_id,
            ScheduledJob.status == "active",
            ScheduledJob.next_run_at <= now,
        )
    )
    jobs = list(result.scalars().all())
    return [j for j in jobs if should_run_now(j, now)]


async def run_due_jobs(db: AsyncSession, organization_id: str) -> list[ScheduledJobRun]:
    due = await find_due_jobs(db, organization_id)
    runs: list[ScheduledJobRun] = []
    for job in due:
        try:
            run = await execute_scheduled_job(db, job, trigger_type="scheduled")
            runs.append(run)
        except Exception as exc:
            logger.warning("Scheduled job %s failed: %s", job.id, exc)
    return runs


async def execute_scheduled_job(
    db: AsyncSession,
    job: ScheduledJob,
    trigger_type: str = "scheduled",
    triggered_by_user_id: str | None = None,
) -> ScheduledJobRun:
    now = datetime.now(timezone.utc)
    run = ScheduledJobRun(
        organization_id=job.organization_id,
        scheduled_job_id=job.id,
        triggered_by_user_id=triggered_by_user_id,
        trigger_type=trigger_type,
        job_type=job.job_type,
        status="running",
        started_at=now,
        input_payload=job.job_payload,
    )
    db.add(run)
    await db.flush()

    output: dict[str, Any] = {}
    error_msg: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    success = False

    try:
        result = await execute_job_payload(db, job)
        output = result.get("output", {})
        resource_type = result.get("resource_type")
        resource_id = result.get("resource_id")
        success = True
    except Exception as exc:
        error_msg = str(exc)
        logger.error("Job %s (%s) failed: %s", job.id, job.job_type, exc)

    finished = datetime.now(timezone.utc)
    duration_ms = int((finished - now).total_seconds() * 1000)

    run.status = "success" if success else "failed"
    run.finished_at = finished
    run.duration_ms = duration_ms
    run.output_payload = output
    run.error_message = error_msg
    run.created_resource_type = resource_type
    run.created_resource_id = resource_id
    db.add(run)

    # Update job counters and next_run_at
    job.last_run_at = now
    job.run_count = (job.run_count or 0) + 1
    if not success:
        job.failure_count = (job.failure_count or 0) + 1

    if job.schedule_type == "one_time":
        job.status = "completed"
        job.completed_at = finished
        job.next_run_at = None
    elif success:
        try:
            job.next_run_at = calculate_next_run(job.schedule_type, job.schedule_payload, job.timezone, after=finished)
        except Exception:
            job.next_run_at = None
    db.add(job)
    await db.commit()
    await db.refresh(run)
    return run


async def execute_job_payload(db: AsyncSession, job: ScheduledJob) -> dict[str, Any]:
    payload = job.job_payload or {}

    if job.job_type == "etsy_sync":
        return await _execute_etsy_sync(db, job.organization_id, payload)
    elif job.job_type == "bulk_edit_draft":
        return await _execute_bulk_edit_draft(db, job.organization_id, payload)
    elif job.job_type == "dynamic_pricing_preview":
        return await _execute_dynamic_pricing_preview(db, job.organization_id, payload)
    elif job.job_type == "csv_export_snapshot":
        return await _execute_csv_export_snapshot(db, job.organization_id, payload)
    else:
        raise ScheduledJobError(f"Unknown job_type: {job.job_type!r}", 400)


# ── Executors ────────────────────────────────────────────────────────────────

async def _execute_etsy_sync(db: AsyncSession, org_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    shop_id = payload.get("shop_id")
    if not shop_id:
        raise ScheduledJobError("etsy_sync requires 'shop_id' in job_payload", 400)

    # Verify shop belongs to org
    result = await db.execute(
        select(EtsyShop).where(EtsyShop.id == shop_id, EtsyShop.organization_id == org_id)
    )
    shop = result.scalar_one_or_none()
    if not shop:
        raise ScheduledJobError("Shop not found or does not belong to your organization.", 404)

    from app.services.etsy_sync import sync_shop_listings, SyncError
    try:
        sync_job = await sync_shop_listings(db=db, org_id=org_id, shop_db_id=shop_id)
        return {
            "output": {
                "sync_job_id": sync_job.id,
                "status": sync_job.status,
                "listings_fetched": sync_job.listings_fetched,
            },
            "resource_type": "sync_job",
            "resource_id": sync_job.id,
        }
    except SyncError as exc:
        raise ScheduledJobError(exc.message, exc.status_code)


async def _execute_bulk_edit_draft(db: AsyncSession, org_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    listing_ids = payload.get("listing_ids", [])
    changes = payload.get("changes", [])
    session_name = payload.get("name", "Scheduled bulk edit draft")

    if not listing_ids:
        raise ScheduledJobError("bulk_edit_draft requires 'listing_ids' in job_payload", 400)
    if not changes:
        raise ScheduledJobError("bulk_edit_draft requires 'changes' in job_payload", 400)

    # Verify listings belong to org
    result = await db.execute(
        select(Listing.id).where(
            Listing.id.in_(listing_ids),
            Listing.organization_id == org_id,
        )
    )
    found_ids = {row[0] for row in result.all()}
    missing = set(listing_ids) - found_ids
    if missing:
        raise ScheduledJobError(f"Listings not found or not in your organization: {sorted(missing)}", 404)

    session = BulkEditSession(
        organization_id=org_id,
        name=session_name,
        status="draft",
        selected_listing_ids=listing_ids,
        selected_count=len(listing_ids),
        change_count=len(changes),
    )
    db.add(session)
    await db.flush()

    for change_spec in changes:
        change = BulkEditChange(
            bulk_edit_session_id=session.id,
            field_name=change_spec.get("field_name", ""),
            operation=change_spec.get("operation", "set"),
            new_value=change_spec.get("value"),
            operation_value=change_spec.get("value"),
        )
        db.add(change)

    await db.flush()
    return {
        "output": {
            "bulk_edit_session_id": session.id,
            "status": session.status,
            "listing_count": len(listing_ids),
            "change_count": len(changes),
            "message": "Draft created. Review and apply in Bulk Edit. Nothing published to Etsy.",
        },
        "resource_type": "bulk_edit_session",
        "resource_id": session.id,
    }


async def _execute_dynamic_pricing_preview(db: AsyncSession, org_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    listing_ids = payload.get("listing_ids", [])
    rule_type = payload.get("rule_type", "percentage_adjustment")
    rule_payload = payload.get("rule_payload", {})
    safety_payload = payload.get("safety_payload")

    if not listing_ids:
        raise ScheduledJobError("dynamic_pricing_preview requires 'listing_ids' in job_payload", 400)

    # Verify listings belong to org
    result = await db.execute(
        select(Listing.id).where(
            Listing.id.in_(listing_ids),
            Listing.organization_id == org_id,
        )
    )
    found_ids = {row[0] for row in result.all()}
    missing = set(listing_ids) - found_ids
    if missing:
        raise ScheduledJobError(f"Listings not found or not in your organization: {sorted(missing)}", 404)

    from app.services.dynamic_pricing import (
        DynamicPricingError,
        assert_dynamic_pricing_allowed,
        create_dynamic_pricing_job,
        generate_dynamic_pricing_preview,
    )
    try:
        await assert_dynamic_pricing_allowed(org_id, db)
        dp_job = await create_dynamic_pricing_job(
            db=db,
            organization_id=org_id,
            user_id=None,
            selected_listing_ids=listing_ids,
            rule_type=rule_type,
            rule_payload=rule_payload,
            safety_payload=safety_payload,
        )
        dp_job = await generate_dynamic_pricing_preview(db=db, job_id=dp_job.id, organization_id=org_id)
        return {
            "output": {
                "dynamic_pricing_job_id": dp_job.id,
                "status": dp_job.status,
                "recommended_count": dp_job.recommended_count,
                "skipped_count": dp_job.skipped_count,
                "message": "Preview generated. Review recommendations before converting. Nothing published to Etsy.",
            },
            "resource_type": "dynamic_pricing_job",
            "resource_id": dp_job.id,
        }
    except DynamicPricingError as exc:
        raise ScheduledJobError(exc.message, exc.status_code)


async def _execute_csv_export_snapshot(db: AsyncSession, org_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    shop_id = payload.get("shop_id")

    q = select(func.count(Listing.id)).where(Listing.organization_id == org_id)
    if shop_id:
        result_shop = await db.execute(
            select(EtsyShop).where(EtsyShop.id == shop_id, EtsyShop.organization_id == org_id)
        )
        shop = result_shop.scalar_one_or_none()
        if not shop:
            raise ScheduledJobError("Shop not found or does not belong to your organization.", 404)
        q = q.where(Listing.etsy_shop_id == shop_id)

    count_result = await db.execute(q)
    row_count = count_result.scalar_one()

    return {
        "output": {
            "message": "CSV snapshot generated as metadata only. File persistence deferred.",
            "row_count": row_count,
            "shop_id": shop_id,
        },
        "resource_type": None,
        "resource_id": None,
    }


# ── Run history ───────────────────────────────────────────────────────────────

async def list_job_runs(
    db: AsyncSession,
    scheduled_job_id: str,
    organization_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[ScheduledJobRun]:
    result = await db.execute(
        select(ScheduledJobRun)
        .where(
            ScheduledJobRun.scheduled_job_id == scheduled_job_id,
            ScheduledJobRun.organization_id == organization_id,
        )
        .order_by(ScheduledJobRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def list_all_runs(
    db: AsyncSession,
    organization_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[ScheduledJobRun]:
    result = await db.execute(
        select(ScheduledJobRun)
        .where(ScheduledJobRun.organization_id == organization_id)
        .order_by(ScheduledJobRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
