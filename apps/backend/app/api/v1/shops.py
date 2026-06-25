from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.models.sync_job import SyncJob
from app.schemas.listings import SyncJobResponse
from app.services.etsy_sync import SyncError, sync_shop_listings

router = APIRouter(prefix="/shops", tags=["shops"])


@router.post("/{shop_id}/sync", response_model=SyncJobResponse)
async def trigger_sync(
    shop_id: str,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    # Future: dispatch to Celery background task instead of inline execution.
    # task = sync_shop_listings_task.delay(org_id, shop_id)
    try:
        job = await sync_shop_listings(db, org_id, shop_id)
    except SyncError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return SyncJobResponse(
        sync_job_id=job.id,
        status=job.status,
        processed_items=job.processed_items,
        total_items=job.total_items,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/{shop_id}/sync-status", response_model=SyncJobResponse)
async def get_sync_status(
    shop_id: str,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    result = await db.execute(
        select(SyncJob)
        .where(SyncJob.etsy_shop_id == shop_id, SyncJob.organization_id == org_id)
        .order_by(desc(SyncJob.created_at))
        .limit(1)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="No sync job found for this shop.")
    return SyncJobResponse(
        sync_job_id=job.id,
        status=job.status,
        processed_items=job.processed_items,
        total_items=job.total_items,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
