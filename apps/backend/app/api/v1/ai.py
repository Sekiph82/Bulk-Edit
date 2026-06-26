from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.schemas.ai import (
    AISessionCreate,
    AISessionOut,
    AISessionPageOut,
    AISuggestionOut,
    AIUsageOut,
    ConvertToSessionOut,
)
from app.services.ai_tools import (
    AIToolsError,
    create_ai_session,
    run_ai_session,
    get_ai_session,
    list_ai_sessions,
    accept_suggestion,
    reject_suggestion,
    convert_to_bulk_edit,
    get_ai_usage,
)
from fastapi import HTTPException

router = APIRouter(prefix="/ai", tags=["ai"])


def _raise(exc: AIToolsError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/sessions", response_model=AISessionOut, status_code=201)
async def create_session(
    body: AISessionCreate,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_ai_session(
            org_id=org_id,
            user_id=str(user.id),
            listing_id=body.listing_id,
            tool=body.tool,
            extra_context=body.extra_context,
            db=db,
        )
    except AIToolsError as exc:
        _raise(exc)


@router.get("/sessions", response_model=AISessionPageOut)
async def list_sessions(
    listing_id: str | None = Query(None),
    tool: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await list_ai_sessions(org_id, db, listing_id=listing_id, tool=tool, page=page, page_size=page_size)
    return AISessionPageOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/sessions/{session_id}", response_model=AISessionOut)
async def get_session(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_ai_session(session_id, org_id, db)
    except AIToolsError as exc:
        _raise(exc)


@router.post("/sessions/{session_id}/run", response_model=AISessionOut)
async def run_session(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await run_ai_session(session_id, org_id, db)
    except AIToolsError as exc:
        _raise(exc)


@router.get("/sessions/{session_id}/suggestions", response_model=list[AISuggestionOut])
async def get_suggestions(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await get_ai_session(session_id, org_id, db)
        return session.suggestions
    except AIToolsError as exc:
        _raise(exc)


@router.post("/suggestions/{suggestion_id}/accept", response_model=AISuggestionOut)
async def accept_sug(
    suggestion_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await accept_suggestion(suggestion_id, org_id, db)
    except AIToolsError as exc:
        _raise(exc)


@router.post("/suggestions/{suggestion_id}/reject", response_model=AISuggestionOut)
async def reject_sug(
    suggestion_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await reject_suggestion(suggestion_id, org_id, db)
    except AIToolsError as exc:
        _raise(exc)


@router.post("/sessions/{session_id}/convert", response_model=ConvertToSessionOut)
async def convert_session(
    session_id: str,
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        bulk_session = await convert_to_bulk_edit(session_id, org_id, str(user.id), db)
        return ConvertToSessionOut(
            bulk_edit_session_id=bulk_session.id,
            message="Bulk edit session created. Review and apply in the Bulk Edit tool.",
        )
    except AIToolsError as exc:
        _raise(exc)


@router.get("/usage", response_model=AIUsageOut)
async def usage(
    org_id: str = Depends(get_current_org_id),
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    data = await get_ai_usage(org_id, db)
    return AIUsageOut(**data)
