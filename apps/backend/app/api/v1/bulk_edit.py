from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user, get_current_user
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
from app.services.bulk_edit import (
    create_bulk_edit_session,
    list_bulk_edit_sessions,
    get_bulk_edit_session,
    cancel_bulk_edit_session,
    add_bulk_edit_change,
    remove_bulk_edit_change,
    generate_bulk_edit_preview,
    get_bulk_edit_preview_page,
    apply_bulk_edit_stub,
)

router = APIRouter(prefix="/bulk-edit", tags=["bulk-edit"])


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


@router.post("/sessions/{session_id}/apply", status_code=409)
async def apply_session(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Sprint 7 stub. Etsy write operations start in Sprint 8."""
    await apply_bulk_edit_stub(db, session_id, org_id)
