from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.schemas.bulk_edit_media import (
    MediaJobCreate,
    MediaJobOut,
    MediaJobWithResultsOut,
    MediaResultPageOut,
    MediaBackupSnapshotOut,
)
from app.services.bulk_edit_media import (
    create_media_job,
    apply_media_job,
    get_media_job,
    list_media_jobs,
    get_media_results,
    get_media_backups,
)

router = APIRouter(prefix="/bulk-edit/media", tags=["bulk-edit-media"])


@router.post("/jobs", response_model=MediaJobOut, status_code=201)
async def create_job(
    body: MediaJobCreate,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    job = await create_media_job(
        db=db,
        organization_id=org_id,
        user_id=str(user.id),
        operation_type=body.operation_type,
        listing_ids=body.listing_ids,
        payload=body.payload,
    )
    return job


@router.get("/jobs", response_model=list[MediaJobOut])
async def list_jobs(
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_media_jobs(db=db, organization_id=org_id)


@router.get("/jobs/{job_id}", response_model=MediaJobWithResultsOut)
async def get_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    job = await get_media_job(db=db, organization_id=org_id, media_job_id=job_id)
    results = await get_media_results(db=db, organization_id=org_id, media_job_id=job_id, page=1, per_page=1000)
    out = MediaJobWithResultsOut.model_validate(job)
    out.results = results["items"]
    return out


@router.post("/jobs/{job_id}/apply", response_model=MediaJobOut)
async def apply_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    job = await apply_media_job(
        db=db,
        organization_id=org_id,
        user_id=str(user.id),
        media_job_id=job_id,
    )
    return job


@router.get("/jobs/{job_id}/results", response_model=MediaResultPageOut)
async def get_job_results(
    job_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_media_results(
        db=db, organization_id=org_id, media_job_id=job_id, page=page, per_page=per_page
    )


@router.get("/jobs/{job_id}/backups", response_model=list[MediaBackupSnapshotOut])
async def get_job_backups(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_media_backups(db=db, organization_id=org_id, media_job_id=job_id)
