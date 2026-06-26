from fastapi import APIRouter, Depends, Query
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.schemas.dynamic_pricing import (
    DynamicPricingJobCreate,
    DynamicPricingJobOut,
    DynamicPricingRecommendationOut,
    DynamicPricingRecommendationPageOut,
    DynamicPricingConvertResponse,
    DynamicPricingSummaryOut,
)
from app.services.dynamic_pricing import (
    DynamicPricingError,
    create_dynamic_pricing_job,
    generate_dynamic_pricing_preview,
    accept_recommendation,
    reject_recommendation,
    accept_all_recommendations,
    convert_dynamic_pricing_job_to_bulk_edit_session,
    list_dynamic_pricing_jobs,
    get_dynamic_pricing_job,
    get_dynamic_pricing_recommendations,
    get_dynamic_pricing_summary,
)

router = APIRouter(prefix="/dynamic-pricing", tags=["dynamic-pricing"])


def _raise(exc: DynamicPricingError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/jobs", response_model=DynamicPricingJobOut, status_code=201)
async def create_job(
    body: DynamicPricingJobCreate,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        job = await create_dynamic_pricing_job(
            db=db,
            organization_id=org_id,
            user_id=str(user.id),
            selected_listing_ids=body.selected_listing_ids,
            rule_type=body.rule_type,
            rule_payload=body.rule_payload,
            safety_payload=body.safety_payload,
        )
        return DynamicPricingJobOut.model_validate(job)
    except DynamicPricingError as exc:
        _raise(exc)


@router.get("/jobs", response_model=list[DynamicPricingJobOut])
async def list_jobs(
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    jobs = await list_dynamic_pricing_jobs(db, org_id)
    return [DynamicPricingJobOut.model_validate(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=DynamicPricingJobOut)
async def get_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        job = await get_dynamic_pricing_job(db, org_id, job_id)
        return DynamicPricingJobOut.model_validate(job)
    except DynamicPricingError as exc:
        _raise(exc)


@router.post("/jobs/{job_id}/preview", response_model=DynamicPricingJobOut)
async def preview_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        job = await generate_dynamic_pricing_preview(db, org_id, str(user.id), job_id)
        return DynamicPricingJobOut.model_validate(job)
    except DynamicPricingError as exc:
        _raise(exc)


@router.get("/jobs/{job_id}/recommendations", response_model=DynamicPricingRecommendationPageOut)
async def list_recommendations(
    job_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    status: str | None = Query(None),
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        recs, total = await get_dynamic_pricing_recommendations(db, org_id, job_id, page, per_page, status)
        return DynamicPricingRecommendationPageOut(
            items=[DynamicPricingRecommendationOut.model_validate(r) for r in recs],
            total=total,
            page=page,
            per_page=per_page,
            job_id=job_id,
        )
    except DynamicPricingError as exc:
        _raise(exc)


@router.post("/recommendations/{recommendation_id}/accept", response_model=DynamicPricingRecommendationOut)
async def accept_rec(
    recommendation_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        rec = await accept_recommendation(db, org_id, str(user.id), recommendation_id)
        return DynamicPricingRecommendationOut.model_validate(rec)
    except DynamicPricingError as exc:
        _raise(exc)


@router.post("/recommendations/{recommendation_id}/reject", response_model=DynamicPricingRecommendationOut)
async def reject_rec(
    recommendation_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        rec = await reject_recommendation(db, org_id, str(user.id), recommendation_id)
        return DynamicPricingRecommendationOut.model_validate(rec)
    except DynamicPricingError as exc:
        _raise(exc)


@router.post("/jobs/{job_id}/accept-all")
async def accept_all(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        count = await accept_all_recommendations(db, org_id, str(user.id), job_id)
        return {"accepted_count": count, "message": f"Accepted {count} recommendations."}
    except DynamicPricingError as exc:
        _raise(exc)


@router.post("/jobs/{job_id}/convert", response_model=DynamicPricingConvertResponse)
async def convert_job(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        session, converted, changes = await convert_dynamic_pricing_job_to_bulk_edit_session(
            db, org_id, str(user.id), job_id
        )
        return DynamicPricingConvertResponse(
            bulk_edit_session_id=session.id,
            converted_count=converted,
            created_changes=changes,
            message=(
                f"Created bulk edit session from {converted} approved price recommendations "
                f"({changes} price changes). Review and apply in Bulk Edit — "
                "changes will NOT be published to Etsy until you approve them there."
            ),
        )
    except DynamicPricingError as exc:
        _raise(exc)


@router.get("/jobs/{job_id}/summary", response_model=DynamicPricingSummaryOut)
async def job_summary(
    job_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        summary = await get_dynamic_pricing_summary(db, org_id, job_id)
        return DynamicPricingSummaryOut(**summary)
    except DynamicPricingError as exc:
        _raise(exc)
