from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.schemas.bulk_edit_variation import (
    VariationJobCreate,
    VariationJobOut,
    VariationPreviewItemOut,
    VariationPreviewPageOut,
    VariationResultPageOut,
    VariationBackupSnapshotOut,
)
from app.services.bulk_edit_variation import (
    create_variation_job,
    generate_variation_preview,
    apply_variation_job,
    get_variation_job,
    list_variation_jobs,
    get_variation_preview,
    get_variation_results,
    get_variation_backups,
)

router = APIRouter(prefix="/bulk-edit/variations", tags=["bulk-edit-variations"])


@router.post("/jobs", response_model=VariationJobOut, status_code=201)
async def create_job(
    body: VariationJobCreate,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_variation_job(
        db=db,
        organization_id=org_id,
        user_id=str(user.id),
        listing_ids=body.listing_ids,
        operation_type=body.operation_type,
        operation_payload=body.payload,
    )


@router.get("/jobs", response_model=list[VariationJobOut])
async def list_jobs(
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_variation_jobs(db=db, organization_id=org_id)


@router.get("/jobs/{job_id}", response_model=VariationJobOut)
async def get_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_variation_job(db=db, organization_id=org_id, variation_job_id=job_id)


@router.post("/jobs/{job_id}/preview", response_model=VariationJobOut)
async def generate_preview(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await generate_variation_preview(db=db, organization_id=org_id, variation_job_id=job_id)


@router.get("/jobs/{job_id}/preview", response_model=VariationPreviewPageOut)
async def get_preview(
    job_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_variation_preview(
        db=db, organization_id=org_id, variation_job_id=job_id, page=page, per_page=per_page
    )


@router.post("/jobs/{job_id}/apply", response_model=VariationJobOut)
async def apply_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await apply_variation_job(
        db=db, organization_id=org_id, user_id=str(user.id), variation_job_id=job_id
    )


@router.get("/jobs/{job_id}/results", response_model=VariationResultPageOut)
async def get_results(
    job_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_variation_results(
        db=db, organization_id=org_id, variation_job_id=job_id, page=page, per_page=per_page
    )


@router.get("/jobs/{job_id}/backups", response_model=list[VariationBackupSnapshotOut])
async def get_backups(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_variation_backups(db=db, organization_id=org_id, variation_job_id=job_id)
