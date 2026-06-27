"""Action Queue — items across all job types awaiting user approval."""

from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db

router = APIRouter(prefix="/action-queue", tags=["action-queue"])


class ActionItem(BaseModel):
    id: str
    type: str
    label: str
    href: str
    created_at: str | None = None


class ActionQueueResponse(BaseModel):
    items: List[ActionItem]
    total: int


@router.get("", response_model=ActionQueueResponse)
async def get_action_queue(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return jobs across all types with status 'preview_ready' (awaiting approval)."""
    from app.models.bulk_edit_variation_job import BulkEditVariationJob
    from app.models.bulk_edit_media_job import BulkEditMediaJob
    from app.models.csv_job import CSVJob
    from app.models.dynamic_pricing_job import DynamicPricingJob

    items: List[ActionItem] = []

    # Variation jobs
    result = await db.execute(
        select(BulkEditVariationJob)
        .where(
            BulkEditVariationJob.organization_id == org_id,
            BulkEditVariationJob.status == "preview_ready",
        )
        .order_by(BulkEditVariationJob.created_at.desc())
        .limit(20)
    )
    for job in result.scalars().all():
        items.append(ActionItem(
            id=str(job.id),
            type="variation_edit",
            label=f"Variation edit — {job.operation_type} — review & apply",
            href=f"/variations?job={job.id}",
            created_at=job.created_at.isoformat() if job.created_at else None,
        ))

    # Media jobs
    result = await db.execute(
        select(BulkEditMediaJob)
        .where(
            BulkEditMediaJob.organization_id == org_id,
            BulkEditMediaJob.status == "preview_ready",
        )
        .order_by(BulkEditMediaJob.created_at.desc())
        .limit(20)
    )
    for job in result.scalars().all():
        items.append(ActionItem(
            id=str(job.id),
            type="media_edit",
            label=f"Media edit — {job.operation_type} — review & apply",
            href=f"/media?job={job.id}",
            created_at=job.created_at.isoformat() if job.created_at else None,
        ))

    # CSV jobs
    result = await db.execute(
        select(CSVJob)
        .where(
            CSVJob.organization_id == org_id,
            CSVJob.status == "preview_ready",
        )
        .order_by(CSVJob.created_at.desc())
        .limit(20)
    )
    for job in result.scalars().all():
        items.append(ActionItem(
            id=str(job.id),
            type="csv_import",
            label=f"CSV import — {job.row_count} rows ready to convert",
            href=f"/csv?job={job.id}",
            created_at=job.created_at.isoformat() if job.created_at else None,
        ))

    # Dynamic pricing jobs
    result = await db.execute(
        select(DynamicPricingJob)
        .where(
            DynamicPricingJob.organization_id == org_id,
            DynamicPricingJob.status == "preview_ready",
        )
        .order_by(DynamicPricingJob.created_at.desc())
        .limit(20)
    )
    for job in result.scalars().all():
        items.append(ActionItem(
            id=str(job.id),
            type="pricing",
            label=f"Pricing recommendations — {job.recommended_count} to review",
            href=f"/pricing-rules?job={job.id}",
            created_at=job.created_at.isoformat() if job.created_at else None,
        ))

    items.sort(key=lambda x: x.created_at or "", reverse=True)
    trimmed = items[:50]

    return ActionQueueResponse(items=trimmed, total=len(trimmed))
