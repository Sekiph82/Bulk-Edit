"""Bulk Create Etsy Listings — draft management before publish."""

from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_org_id, require_active_user

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
    _user=Depends(require_active_user),
):
    return BulkCreateStatusResponse(
        status="not_configured",
        message="Bulk create requires an active Etsy connection. Connect your shop to enable listing creation.",
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
