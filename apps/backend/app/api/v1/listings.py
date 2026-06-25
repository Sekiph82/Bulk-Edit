from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

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

VALID_SORT_COLS = {
    "title", "state", "price_amount", "quantity",
    "etsy_updated_at", "last_synced_at", "updated_at", "created_at",
}


@router.get("", response_model=ListingPageResponse)
async def list_listings(
    shop_id: str | None = Query(None),
    state: str | None = Query(None),
    search: str | None = Query(None),
    tag: str | None = Query(None),
    has_variations: bool | None = Query(None),
    price_min: int | None = Query(None),
    price_max: int | None = Query(None),
    quantity_min: int | None = Query(None),
    quantity_max: int | None = Query(None),
    section_id: str | None = Query(None),
    taxonomy_id: str | None = Query(None),
    is_personalizable: bool | None = Query(None),
    is_customizable: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sort_by: str = Query("updated_at"),
    sort_dir: str = Query("desc"),
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    if sort_by not in VALID_SORT_COLS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by '{sort_by}'. Allowed: {', '.join(sorted(VALID_SORT_COLS))}",
        )
    if sort_dir.lower() not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="sort_dir must be 'asc' or 'desc'")

    query = select(Listing).where(Listing.organization_id == org_id)

    if shop_id:
        query = query.where(Listing.etsy_shop_id == shop_id)
    if state:
        query = query.where(Listing.state == state)
    if search:
        query = query.where(Listing.title.ilike(f"%{search}%"))
    if tag:
        # Cross-DB: cast JSON tags column to text and use ILIKE / contains
        query = query.where(cast(Listing.tags, String).ilike(f"%{tag}%"))
    if has_variations is not None:
        query = query.where(Listing.has_variations == has_variations)
    if price_min is not None:
        query = query.where(Listing.price_amount >= price_min)
    if price_max is not None:
        query = query.where(Listing.price_amount <= price_max)
    if quantity_min is not None:
        query = query.where(Listing.quantity >= quantity_min)
    if quantity_max is not None:
        query = query.where(Listing.quantity <= quantity_max)
    if section_id:
        query = query.where(Listing.section_id == section_id)
    if taxonomy_id:
        query = query.where(Listing.taxonomy_id == taxonomy_id)
    if is_personalizable is not None:
        query = query.where(Listing.is_personalizable == is_personalizable)
    if is_customizable is not None:
        query = query.where(Listing.is_customizable == is_customizable)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    sort_col = getattr(Listing, sort_by)
    if sort_dir.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = list(result.scalars().all())

    # Batch thumbnail fetch — one query for all listing IDs on this page
    thumbnails: dict[str, str | None] = {}
    if items:
        listing_ids = [i.id for i in items]
        img_result = await db.execute(
            select(ListingImage.listing_id, ListingImage.url_570xN)
            .where(ListingImage.listing_id.in_(listing_ids))
            .order_by(ListingImage.listing_id, ListingImage.rank.asc())
        )
        for row in img_result.all():
            lid, url = row[0], row[1]
            if lid not in thumbnails:
                thumbnails[lid] = url

    active_filters = {
        k: v for k, v in {
            "shop_id": shop_id, "state": state, "search": search, "tag": tag,
            "has_variations": has_variations, "price_min": price_min, "price_max": price_max,
            "quantity_min": quantity_min, "quantity_max": quantity_max,
            "section_id": section_id, "taxonomy_id": taxonomy_id,
            "is_personalizable": is_personalizable, "is_customizable": is_customizable,
        }.items() if v is not None
    }

    items_response = []
    for item in items:
        base = ListingListItemResponse.model_validate(item)
        base = base.model_copy(update={"thumbnail_url": thumbnails.get(item.id)})
        items_response.append(base)

    return ListingPageResponse(
        items=items_response,
        page=page,
        per_page=per_page,
        total=total,
        filters=active_filters if active_filters else None,
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
    imgs = await db.execute(
        select(ListingImage).where(ListingImage.listing_id == listing_id).order_by(ListingImage.rank.asc())
    )
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
