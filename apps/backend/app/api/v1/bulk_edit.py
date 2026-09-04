from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user, get_current_user
from app.core.job_states import canonical_apply_job_state
from app.db.session import get_db
from app.schemas.bulk_edit import (
    BulkEditSessionCreateRequest,
    BulkEditSessionResponse,
    BulkEditSessionDetailResponse,
    BulkEditChangeCreateRequest,
    BulkEditChangeResponse,
    BulkEditPreviewGenerateResponse,
    BulkEditPreviewPageResponse,
    BulkEditPreviewSummary,
    BulkEditPreviewItemResponse,
)
from app.schemas.bulk_edit_apply import (
    ApplyJobOut,
    ApplyJobWithResultsOut,
    ApplyResultOut,
    BackupSnapshotOut,
    ApplyJobHistoryPageOut,
    ApplyJobHistoryItemOut,
    FieldAuditLogOut,
    FieldAuditLogPageOut,
)
from app.schemas.bulk_edit_revert import (
    RevertJobOut,
    RevertJobWithResultsOut,
    RevertResultOut,
    RevertResultPageOut,
)
from app.services.bulk_edit import (
    create_bulk_edit_session,
    list_bulk_edit_sessions,
    get_bulk_edit_session,
    cancel_bulk_edit_session,
    add_bulk_edit_change,
    remove_bulk_edit_change,
    generate_bulk_edit_preview,
    get_bulk_edit_preview_page,
)
from app.services.bulk_edit_apply import (
    apply_bulk_edit_session,
    get_apply_job,
    list_apply_jobs_for_session,
    list_apply_jobs_for_org,
    get_apply_results,
    list_backup_snapshots_for_session,
    list_field_audit_trail,
    export_field_audit_trail_csv,
)
from app.services.bulk_edit_revert import (
    revert_apply_job,
    get_revert_job,
    list_revert_jobs_for_apply_job,
    get_revert_results,
    get_revert_eligibility_map,
)

router = APIRouter(prefix="/bulk-edit", tags=["bulk-edit"])


def _with_canonical_state(job_out: ApplyJobOut, revert_status: str | None = None) -> ApplyJobOut:
    state = canonical_apply_job_state(job_out.status, job_out.success_count, job_out.error_message, revert_status)
    return job_out.model_copy(update={"canonical_state": state})


@router.post("/sessions", response_model=BulkEditSessionResponse, status_code=201)
async def create_session(
    body: BulkEditSessionCreateRequest,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    session = await create_bulk_edit_session(
        db,
        organization_id=org_id,
        user_id=user.id,
        listing_ids=body.listing_ids,
        name=body.name,
    )
    return BulkEditSessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[BulkEditSessionResponse])
async def list_sessions(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    sessions = await list_bulk_edit_sessions(db, org_id)
    return [BulkEditSessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=BulkEditSessionDetailResponse)
async def get_session(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, func
    from app.models.bulk_edit_change import BulkEditChange
    from app.models.bulk_edit_preview_item import BulkEditPreviewItem

    session = await get_bulk_edit_session(db, session_id, org_id)

    changes_result = await db.execute(
        select(BulkEditChange).where(BulkEditChange.bulk_edit_session_id == session_id)
    )
    changes = list(changes_result.scalars().all())

    count_result = await db.execute(
        select(func.count()).select_from(
            select(BulkEditPreviewItem)
            .where(BulkEditPreviewItem.bulk_edit_session_id == session_id)
            .subquery()
        )
    )
    preview_count = count_result.scalar_one()

    base = BulkEditSessionResponse.model_validate(session)
    return BulkEditSessionDetailResponse(
        **base.model_dump(),
        changes=[BulkEditChangeResponse.model_validate(c) for c in changes],
        preview_item_count=preview_count,
    )


@router.delete("/sessions/{session_id}", response_model=BulkEditSessionResponse)
async def delete_session(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    session = await cancel_bulk_edit_session(db, session_id, org_id)
    return BulkEditSessionResponse.model_validate(session)


@router.post("/sessions/{session_id}/changes", response_model=BulkEditChangeResponse, status_code=201)
async def add_change(
    session_id: str,
    body: BulkEditChangeCreateRequest,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    change = await add_bulk_edit_change(
        db,
        session_id=session_id,
        organization_id=org_id,
        field_name=body.field_name,
        operation=body.operation,
        operation_value=body.operation_value,
    )
    return BulkEditChangeResponse.model_validate(change)


@router.delete("/sessions/{session_id}/changes/{change_id}", status_code=204)
async def remove_change(
    session_id: str,
    change_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    await remove_bulk_edit_change(db, session_id, change_id, org_id)
    return None


@router.post("/sessions/{session_id}/preview", response_model=BulkEditPreviewGenerateResponse)
async def trigger_preview(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await generate_bulk_edit_preview(db, session_id, org_id)
    return BulkEditPreviewGenerateResponse(
        session=BulkEditSessionResponse.model_validate(result["session"]),
        summary=BulkEditPreviewSummary(**result["summary"]),
    )


@router.get("/sessions/{session_id}/preview", response_model=BulkEditPreviewPageResponse)
async def get_preview(
    session_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    validation_status: str | None = Query(None),
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_bulk_edit_preview_page(db, session_id, org_id, page, per_page, validation_status)
    return BulkEditPreviewPageResponse(
        items=[BulkEditPreviewItemResponse.model_validate(i) for i in result["items"]],
        page=result["page"],
        per_page=result["per_page"],
        total=result["total"],
        session_id=result["session_id"],
    )


@router.post("/sessions/{session_id}/apply", response_model=ApplyJobOut, status_code=202)
async def apply_session(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    job = await apply_bulk_edit_session(db, session_id, org_id, user.id)
    return _with_canonical_state(ApplyJobOut.model_validate(job))


@router.get("/sessions/{session_id}/apply-jobs", response_model=list[ApplyJobOut])
async def list_apply_jobs(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    jobs = await list_apply_jobs_for_session(db, session_id, org_id)
    eligibility = await get_revert_eligibility_map(db, org_id, jobs)
    return [
        _with_canonical_state(ApplyJobOut.model_validate(j), eligibility.get(j.id, {}).get("revert_status"))
        for j in jobs
    ]


@router.get("/apply-jobs", response_model=ApplyJobHistoryPageOut)
async def list_apply_job_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Org-wide apply job history (Magic Revert History / Activity & Audit) —
    across every session, not just one. Decorated with can_revert using the
    exact same eligibility rules Revert itself enforces (effective-plan gate,
    job status, no existing non-terminal revert), computed batch/read-only
    so this never has to guess or duplicate that logic.
    """
    jobs, total = await list_apply_jobs_for_org(db, org_id, page, per_page, status)
    eligibility = await get_revert_eligibility_map(db, org_id, jobs)

    items = []
    for job in jobs:
        elig = eligibility.get(job.id, {})
        item = ApplyJobHistoryItemOut.model_validate(job)
        item = item.model_copy(update={
            "canonical_state": canonical_apply_job_state(
                job.status, job.success_count, job.error_message, elig.get("revert_status")
            ),
            "can_revert": elig.get("can_revert", False),
            "revert_blocked_reason": elig.get("revert_blocked_reason"),
            "revert_job_id": elig.get("revert_job_id"),
            "revert_status": elig.get("revert_status"),
        })
        items.append(item)

    return ApplyJobHistoryPageOut(items=items, page=page, per_page=per_page, total=total)


@router.get("/apply-jobs/{job_id}", response_model=ApplyJobWithResultsOut)
async def get_apply_job_detail(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    job = await get_apply_job(db, job_id, org_id)
    results = await get_apply_results(db, job_id, org_id)
    eligibility = await get_revert_eligibility_map(db, org_id, [job])
    return ApplyJobWithResultsOut(
        job=_with_canonical_state(ApplyJobOut.model_validate(job), eligibility.get(job.id, {}).get("revert_status")),
        results=[ApplyResultOut.model_validate(r) for r in results],
    )


@router.get("/sessions/{session_id}/backups", response_model=list[BackupSnapshotOut])
async def list_backups(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    snapshots = await list_backup_snapshots_for_session(db, session_id, org_id)
    return [BackupSnapshotOut.model_validate(s) for s in snapshots]


@router.post("/apply-jobs/{apply_job_id}/revert", response_model=RevertJobOut, status_code=202)
async def revert_apply_job_endpoint(
    apply_job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    job = await revert_apply_job(db, org_id, user.id, apply_job_id)
    return RevertJobOut.model_validate(job)


@router.get("/apply-jobs/{apply_job_id}/revert-jobs", response_model=list[RevertJobOut])
async def list_revert_jobs(
    apply_job_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    jobs = await list_revert_jobs_for_apply_job(db, org_id, apply_job_id)
    return [RevertJobOut.model_validate(j) for j in jobs]


@router.get("/revert-jobs/{revert_job_id}", response_model=RevertJobWithResultsOut)
async def get_revert_job_detail(
    revert_job_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    job = await get_revert_job(db, org_id, revert_job_id)
    data = await get_revert_results(db, org_id, revert_job_id)
    return RevertJobWithResultsOut(
        job=RevertJobOut.model_validate(job),
        results=[RevertResultOut.model_validate(r) for r in data["items"]],
    )


@router.get("/revert-jobs/{revert_job_id}/results", response_model=RevertResultPageOut)
async def get_revert_results_paginated(
    revert_job_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    data = await get_revert_results(db, org_id, revert_job_id, page, per_page)
    return RevertResultPageOut(
        items=[RevertResultOut.model_validate(r) for r in data["items"]],
        page=data["page"],
        per_page=data["per_page"],
        total=data["total"],
        revert_job_id=data["revert_job_id"],
    )


@router.get("/audit-trail", response_model=FieldAuditLogPageOut)
async def get_field_audit_trail(
    apply_job_id: str | None = Query(None),
    listing_id: str | None = Query(None),
    field_name: str | None = Query(None),
    result_status: str | None = Query(None),
    revert_status: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """M06.04 per-item write audit trail — searchable, org-scoped, read-only.
    See also GET /audit-trail/export.csv (same filters, CSV output)."""
    items, total = await list_field_audit_trail(
        db, org_id,
        apply_job_id=apply_job_id, listing_id=listing_id, field_name=field_name,
        result_status=result_status, revert_status=revert_status,
        date_from=date_from, date_to=date_to, page=page, per_page=per_page,
    )
    # Decorate with the listing's current title (cheap local join, no live
    # Etsy call) — purely a UI convenience so the Audit Trail table doesn't
    # have to show a bare listing id. Never included in the CSV export,
    # which keeps its documented, stable column set.
    listing_ids = {i.entity_id for i in items if i.entity_id}
    titles: dict[str, str] = {}
    if listing_ids:
        from sqlalchemy import select as _select
        from app.models.listing import Listing
        title_rows = await db.execute(
            _select(Listing.id, Listing.title).where(Listing.id.in_(listing_ids))
        )
        titles = {lid: title for lid, title in title_rows.all() if title}

    return FieldAuditLogPageOut(
        items=[
            FieldAuditLogOut.model_validate(i).model_copy(update={"listing_title": titles.get(i.entity_id)})
            for i in items
        ],
        page=page, per_page=per_page, total=total,
    )


@router.get("/audit-trail/export.csv")
async def export_audit_trail_csv(
    apply_job_id: str | None = Query(None),
    listing_id: str | None = Query(None),
    field_name: str | None = Query(None),
    result_status: str | None = Query(None),
    revert_status: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """M06.04 CSV export — same filters as GET /audit-trail, org-scoped,
    read-only. See export_field_audit_trail_csv() for the row cap and
    safe-value flattening."""
    csv_text = await export_field_audit_trail_csv(
        db, org_id,
        apply_job_id=apply_job_id, listing_id=listing_id, field_name=field_name,
        result_status=result_status, revert_status=revert_status,
        date_from=date_from, date_to=date_to,
    )
    filename = f"bulk-edit-audit-trail-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.csv"

    def _iter():
        yield csv_text.encode("utf-8")

    return StreamingResponse(
        _iter(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/onboarding-status")
async def bulk_edit_onboarding_status(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Durable, all-time onboarding signal for the dashboard "Try bulk edit"
    step. True when this org has ever run a Bulk Edit apply with at least one
    successful item write (`success_count > 0`) — which covers succeeded and
    partially-failed jobs, and stays true for jobs later reverted (revert is a
    separate RevertJob and never changes the apply job's success_count). It is
    org-scoped and NOT tied to the monthly `UsageCounter` (that resets each
    billing period, which is why the old dashboard signal regressed to
    unchecked after a period rollover). Skipped-only / failed-only jobs
    (success_count == 0) do not count."""
    from sqlalchemy import select as _select
    from app.models.bulk_edit_apply_job import BulkEditApplyJob

    exists_q = await db.execute(
        _select(BulkEditApplyJob.id)
        .where(
            BulkEditApplyJob.organization_id == org_id,
            BulkEditApplyJob.success_count > 0,
        )
        .limit(1)
    )
    has_completed = exists_q.scalar_one_or_none() is not None
    return {"has_completed_bulk_edit": has_completed}
