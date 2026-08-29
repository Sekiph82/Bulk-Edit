"""Bulk Create Etsy Listings — draft management before publish."""

from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.models.etsy_shop import EtsyShop

router = APIRouter(prefix="/bulk-create", tags=["bulk-create"])


class BulkCreateStatusResponse(BaseModel):
    status: str
    message: str


class BulkCreateDraftRequest(BaseModel):
    title: str
    description: str
    tags: List[str] = []
    price_cents: int = 0
    quantity: int = 1
    image_filenames: List[str] = []


class BulkCreateDraftResponse(BaseModel):
    id: str
    title: str
    status: str


@router.get("/status", response_model=BulkCreateStatusResponse)
async def get_bulk_create_status(
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    # Previously hardcoded "not_configured" regardless of org_id — never
    # actually checked shop connection, so this page showed "Connect your
    # Etsy shop first" even for an account with a connected shop. Same
    # is_connected check as etsy.list_connected_shops() / the Connected
    # Shops page, so the two surfaces can't disagree again.
    result = await db.execute(
        select(EtsyShop.id).where(EtsyShop.organization_id == org_id, EtsyShop.is_connected == True).limit(1)
    )
    if result.scalar_one_or_none() is None:
        return BulkCreateStatusResponse(
            status="not_configured",
            message="Bulk create requires an active Etsy connection. Connect your shop to enable listing creation.",
        )
    return BulkCreateStatusResponse(
        status="not_yet_enabled",
        message="Your Etsy shop is connected. Bulk Create's draft-publishing workflow is still being built — drafts cannot be created yet.",
    )


@router.post("/drafts", response_model=BulkCreateStatusResponse)
async def create_bulk_drafts(
    request: BulkCreateDraftRequest,
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
):
    """Create a draft for review — never auto-publishes to Etsy."""
    return BulkCreateStatusResponse(
        status="not_configured",
        message="Bulk create is not yet enabled. Connect your Etsy shop and upgrade your plan to use this feature.",
    )
