from fastapi import APIRouter, Depends, Query
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.schemas.scheduled_jobs import (
    RunDueResponse,
    ScheduledJobCreate,
    ScheduledJobOut,
    ScheduledJobRunOut,
    ScheduledJobUpdate,
)
from app.services.scheduled_jobs import (
    ScheduledJobError,
    create_scheduled_job,
    disable_scheduled_job,
    find_due_jobs,
    get_scheduled_job,
    list_all_runs,
    list_job_runs,
    list_scheduled_jobs,
    pause_scheduled_job,
    resume_scheduled_job,
    run_due_jobs,
    run_scheduled_job_now,
    update_scheduled_job,
)

router = APIRouter(prefix="/scheduled-jobs", tags=["scheduled-jobs"])


def _raise(exc: ScheduledJobError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/jobs", response_model=ScheduledJobOut, status_code=201)
async def create_job(
    body: ScheduledJobCreate,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        job = await create_scheduled_job(
            db=db,
            organization_id=org_id,
            user_id=str(user.id),
            name=body.name,
            job_type=body.job_type,
            schedule_type=body.schedule_type,
            schedule_payload=body.schedule_payload,
            job_payload=body.job_payload,
            timezone_str=body.timezone,
            max_runs=body.max_runs,
            starts_at=body.starts_at,
            ends_at=body.ends_at,
        )
        return ScheduledJobOut.model_validate(job)
    except ScheduledJobError as exc:
        _raise(exc)


@router.get("/jobs", response_model=list[ScheduledJobOut])
async def list_jobs(
    status: str | None = Query(None),
    job_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    jobs = await list_scheduled_jobs(db, org_id, status=status, job_type=job_type, limit=limit, offset=offset)
    return [ScheduledJobOut.model_validate(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=ScheduledJobOut)
async def get_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        job = await get_scheduled_job(db, job_id, org_id)
        return ScheduledJobOut.model_validate(job)
    except ScheduledJobError as exc:
        _raise(exc)


@router.patch("/jobs/{job_id}", response_model=ScheduledJobOut)
async def update_job(
    job_id: str,
    body: ScheduledJobUpdate,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        job = await update_scheduled_job(
            db=db,
            job_id=job_id,
            organization_id=org_id,
            name=body.name,
            job_payload=body.job_payload,
            schedule_payload=body.schedule_payload,
            timezone_str=body.timezone,
            max_runs=body.max_runs,
            ends_at=body.ends_at,
        )
        return ScheduledJobOut.model_validate(job)
    except ScheduledJobError as exc:
        _raise(exc)


@router.post("/jobs/{job_id}/pause", response_model=ScheduledJobOut)
async def pause_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        job = await pause_scheduled_job(db, job_id, org_id)
        return ScheduledJobOut.model_validate(job)
    except ScheduledJobError as exc:
        _raise(exc)


@router.post("/jobs/{job_id}/resume", response_model=ScheduledJobOut)
async def resume_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        job = await resume_scheduled_job(db, job_id, org_id)
        return ScheduledJobOut.model_validate(job)
    except ScheduledJobError as exc:
        _raise(exc)


@router.post("/jobs/{job_id}/disable", response_model=ScheduledJobOut)
async def disable_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        job = await disable_scheduled_job(db, job_id, org_id)
        return ScheduledJobOut.model_validate(job)
    except ScheduledJobError as exc:
        _raise(exc)


@router.post("/jobs/{job_id}/run-now", response_model=ScheduledJobRunOut, status_code=201)
async def run_now(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        run = await run_scheduled_job_now(db, job_id, org_id, str(user.id))
        return ScheduledJobRunOut.model_validate(run)
    except ScheduledJobError as exc:
        _raise(exc)


@router.get("/jobs/{job_id}/runs", response_model=list[ScheduledJobRunOut])
async def get_job_runs(
    job_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_scheduled_job(db, job_id, org_id)
    except ScheduledJobError as exc:
        _raise(exc)
    runs = await list_job_runs(db, job_id, org_id, limit=limit, offset=offset)
    return [ScheduledJobRunOut.model_validate(r) for r in runs]


@router.get("/runs", response_model=list[ScheduledJobRunOut])
async def get_all_runs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    runs = await list_all_runs(db, org_id, limit=limit, offset=offset)
    return [ScheduledJobRunOut.model_validate(r) for r in runs]


@router.post("/run-due", response_model=RunDueResponse)
async def run_due(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    runs = await run_due_jobs(db, org_id)
    return RunDueResponse(executed=len(runs), run_ids=[r.id for r in runs])
