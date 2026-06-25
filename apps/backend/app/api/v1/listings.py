from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.models.listing import Listing
from app.models.listing_image import ListingImage
from app.models.listing_video import ListingVideo
from app.models.listing_variation import ListingVariation
from app.schemas.listings import (
    ListingDetailResponse,
    ListingImageResponse,
    ListingPageResponse,
    ListingListItemResponse,
    ListingVariationResponse,
    ListingVideoResponse,
)

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=ListingPageResponse)
async def list_listings(
    shop_id: str | None = Query(None),
    state: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sort_by: str = Query("updated_at"),
    sort_dir: str = Query("desc"),
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    query = select(Listing).where(Listing.organization_id == org_id)

    if shop_id:
        query = query.where(Listing.etsy_shop_id == shop_id)
    if state:
        query = query.where(Listing.state == state)
    if search:
        query = query.where(Listing.title.ilike(f"%{search}%"))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    sort_col = getattr(Listing, sort_by, Listing.updated_at)
    if sort_dir.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = result.scalars().all()

    return ListingPageResponse(
        items=[ListingListItemResponse.model_validate(i) for i in items],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{listing_id}", response_model=ListingDetailResponse)
async def get_listing(
    listing_id: str,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.organization_id == org_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")
    return ListingDetailResponse.model_validate(listing)


@router.get("/{listing_id}/images", response_model=list[ListingImageResponse])
async def get_listing_images(
    listing_id: str,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.organization_id == org_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Listing not found.")
    imgs = await db.execute(select(ListingImage).where(ListingImage.listing_id == listing_id))
    return [ListingImageResponse.model_validate(i) for i in imgs.scalars().all()]


@router.get("/{listing_id}/videos", response_model=list[ListingVideoResponse])
async def get_listing_videos(
    listing_id: str,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.organization_id == org_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Listing not found.")
    vids = await db.execute(select(ListingVideo).where(ListingVideo.listing_id == listing_id))
    return [ListingVideoResponse.model_validate(v) for v in vids.scalars().all()]


@router.get("/{listing_id}/variations", response_model=list[ListingVariationResponse])
async def get_listing_variations(
    listing_id: str,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.organization_id == org_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Listing not found.")
    vars_ = await db.execute(select(ListingVariation).where(ListingVariation.listing_id == listing_id))
    return [ListingVariationResponse.model_validate(v) for v in vars_.scalars().all()]
