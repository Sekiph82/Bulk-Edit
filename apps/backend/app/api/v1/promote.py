"""Promote — Pinterest and Instagram sharing config status."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_org_id, require_active_user
from app.core.config import settings

router = APIRouter(prefix="/promote", tags=["promote"])


class PromoteConfigStatus(BaseModel):
    pinterest_configured: bool
    instagram_configured: bool


@router.get("/config-status", response_model=PromoteConfigStatus)
async def get_promote_config_status(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
):
    pinterest_ok = bool(settings.PINTEREST_CLIENT_ID and "placeholder" not in settings.PINTEREST_CLIENT_ID)
    instagram_ok = bool(settings.META_APP_ID and "placeholder" not in settings.META_APP_ID)

    return PromoteConfigStatus(
        pinterest_configured=pinterest_ok,
        instagram_configured=instagram_ok,
    )
