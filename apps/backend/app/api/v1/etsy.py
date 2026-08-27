import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.schemas.etsy import (
    EtsyAuthorizeResponse,
    EtsyDisconnectResponse,
    EtsyShopResponse,
    EtsyShopsResponse,
)
from app.services import etsy as etsy_service
from app.services.etsy import EtsyOAuthError

router = APIRouter(prefix="/etsy", tags=["etsy"])
logger = logging.getLogger(__name__)


def _log_callback_failure(
    category: str,
    code,
    state,
    error,
    exc: Exception | None = None,
    stage: str | None = None,
    status_code: int | None = None,
) -> None:
    logger.warning(
        "etsy_oauth_callback_failed category=%s has_code=%s has_state=%s has_error=%s exc_type=%s stage=%s status_code=%s",
        category,
        bool(code),
        bool(state),
        bool(error),
        exc.__class__.__name__ if exc is not None else None,
        stage,
        status_code,
    )


@router.get("/authorize", response_model=EtsyAuthorizeResponse)
async def authorize(
    user=Depends(require_active_user),
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    if not settings.is_etsy_configured():
        raise HTTPException(status_code=503, detail="Etsy is not configured.")
    url = await etsy_service.create_authorization_session(org_id, user.id, db)
    return EtsyAuthorizeResponse(authorization_url=url)


@router.get("/callback")
async def callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    frontend_shops_url = f"{settings.FRONTEND_URL}/shops"

    if error:
        _log_callback_failure("etsy_oauth_provider_error_param", code, state, error)
        return RedirectResponse(url=f"{frontend_shops_url}?error=etsy_connect_failed", status_code=302)
    if not code or not state:
        _log_callback_failure("etsy_oauth_missing_params", code, state, error)
        return RedirectResponse(url=f"{frontend_shops_url}?error=etsy_connect_failed", status_code=302)

    try:
        await etsy_service.handle_oauth_callback(code, state, db)
        return RedirectResponse(url=f"{frontend_shops_url}?connected=true", status_code=302)
    except EtsyOAuthError as exc:
        _log_callback_failure(exc.category, code, state, error, exc, stage=exc.stage, status_code=exc.status_code)
        return RedirectResponse(url=f"{frontend_shops_url}?error=etsy_connect_failed", status_code=302)
    except Exception as exc:
        _log_callback_failure("etsy_oauth_unknown", code, state, error, exc)
        return RedirectResponse(url=f"{frontend_shops_url}?error=etsy_connect_failed", status_code=302)


@router.get("/shops", response_model=EtsyShopsResponse)
async def list_shops(
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    shops = await etsy_service.list_connected_shops(org_id, db)
    return EtsyShopsResponse(
        shops=[EtsyShopResponse.model_validate(s) for s in shops],
        total=len(shops),
    )


@router.delete("/shops/{shop_id}", response_model=EtsyDisconnectResponse)
async def disconnect_shop(
    shop_id: str,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    await etsy_service.disconnect_shop(shop_id, org_id, db)
    return EtsyDisconnectResponse(message="Shop disconnected successfully.")
