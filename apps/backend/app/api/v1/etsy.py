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

router = APIRouter(prefix="/etsy", tags=["etsy"])


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

    if error or not code or not state:
        return RedirectResponse(url=f"{frontend_shops_url}?error=etsy_connect_failed", status_code=302)

    try:
        await etsy_service.handle_oauth_callback(code, state, db)
        return RedirectResponse(url=f"{frontend_shops_url}?connected=true", status_code=302)
    except Exception:
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
