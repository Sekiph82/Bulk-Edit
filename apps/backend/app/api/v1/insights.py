"""Shop Insights — real listing/shop data computed from synced Etsy listings.

Etsy does not expose reliable revenue/views/favourites trend endpoints
through the scopes this app requests, so this deliberately does not invent
that data. Instead it summarizes what is actually known from the connected,
synced shop: listing counts by state, tag/photo coverage gaps, and price
distribution — computed directly from the `listings` table that
`etsy_sync` already populates. Nothing here is hardcoded or fabricated.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.models.etsy_shop import EtsyShop
from app.models.listing import Listing
from app.models.listing_image import ListingImage

router = APIRouter(prefix="/insights", tags=["insights"])

# Below this many photos a listing is considered under-illustrated.
# Etsy allows up to 10 photos per listing; 3 is a conservative "low" bar.
LOW_PHOTO_COUNT_THRESHOLD = 3


class ListingStateCount(BaseModel):
    state: str
    count: int


class InsightSummary(BaseModel):
    shop_connected: bool
    last_synced_at: Optional[str] = None
    total_listings: int
    listings_by_state: list[ListingStateCount]
    listings_missing_tags: int
    listings_low_photo_count: int
    average_price_cents: Optional[int] = None
    min_price_cents: Optional[int] = None
    max_price_cents: Optional[int] = None
    note: str


# Below this many characters a title is considered too short to be
# discoverable — same threshold app.services.listing_health uses, kept in
# sync deliberately so the two surfaces never disagree about what "short"
# means.
LOW_TITLE_LENGTH_THRESHOLD = 20
AFFECTED_LISTINGS_LIMIT = 10


class AffectedListingItem(BaseModel):
    listing_id: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metric: str


class AffectedListingsSection(BaseModel):
    category: str
    label: str
    count: int
    items: list[AffectedListingItem]


class AffectedListingsOut(BaseModel):
    sections: list[AffectedListingsSection]


@router.get("/summary", response_model=InsightSummary)
async def get_insights_summary(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Real listing/shop insights computed from synced data for this org.

    Deliberately does not include revenue, views, or favourites — those
    are not reliably available from the Etsy scopes this app requests, and
    faking them would be a false product claim.
    """
    shop_result = await db.execute(
        select(EtsyShop).where(EtsyShop.organization_id == org_id)
    )
    shops = shop_result.scalars().all()
    shop_connected = any(s.is_connected for s in shops)
    sync_times = [s.last_synced_at for s in shops if s.last_synced_at]
    last_synced_at = max(sync_times).isoformat() if sync_times else None

    total_result = await db.execute(
        select(func.count(Listing.id)).where(Listing.organization_id == org_id)
    )
    total_listings = total_result.scalar_one() or 0

    if total_listings == 0:
        return InsightSummary(
            shop_connected=shop_connected,
            last_synced_at=last_synced_at,
            total_listings=0,
            listings_by_state=[],
            listings_missing_tags=0,
            listings_low_photo_count=0,
            note=(
                "No synced listings yet."
                if shop_connected
                else "Connect an Etsy shop to see listing insights."
            ),
        )

    state_result = await db.execute(
        select(Listing.state, func.count(Listing.id))
        .where(Listing.organization_id == org_id)
        .group_by(Listing.state)
    )
    listings_by_state = [
        ListingStateCount(state=state or "unknown", count=count)
        for state, count in state_result.all()
    ]

    all_listings_result = await db.execute(
        select(Listing.id, Listing.tags, Listing.price_amount).where(
            Listing.organization_id == org_id
        )
    )
    listing_rows = all_listings_result.all()

    missing_tags = sum(1 for _id, tags, _price in listing_rows if not tags)
    prices = [price for _id, _tags, price in listing_rows if price is not None]

    photo_counts_result = await db.execute(
        select(Listing.id, func.count(ListingImage.id))
        .select_from(Listing)
        .outerjoin(ListingImage, ListingImage.listing_id == Listing.id)
        .where(Listing.organization_id == org_id)
        .group_by(Listing.id)
    )
    low_photo_count = sum(
        1 for _id, count in photo_counts_result.all() if count < LOW_PHOTO_COUNT_THRESHOLD
    )

    return InsightSummary(
        shop_connected=shop_connected,
        last_synced_at=last_synced_at,
        total_listings=total_listings,
        listings_by_state=listings_by_state,
        listings_missing_tags=missing_tags,
        listings_low_photo_count=low_photo_count,
        average_price_cents=(round(sum(prices) / len(prices)) if prices else None),
        min_price_cents=(min(prices) if prices else None),
        max_price_cents=(max(prices) if prices else None),
        note="Computed from your most recently synced listing data.",
    )


@router.get("/affected-listings", response_model=AffectedListingsOut)
async def get_affected_listings(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    "Missing tags" / "low photo count" etc. in the summary are bare counts —
    this drills into WHICH listings, so an owner can act on them directly.
    Computed entirely from already-synced local data (no Etsy call). Each
    section returns up to AFFECTED_LISTINGS_LIMIT listings, newest-updated
    first, plus the section's true total count (which may exceed the
    returned item list).
    """
    listings_result = await db.execute(
        select(Listing)
        .where(Listing.organization_id == org_id)
        .order_by(Listing.updated_at.desc())
    )
    listings = list(listings_result.scalars().all())

    if not listings:
        return AffectedListingsOut(sections=[])

    listing_ids = [l.id for l in listings]
    photo_counts_result = await db.execute(
        select(Listing.id, func.count(ListingImage.id))
        .select_from(Listing)
        .outerjoin(ListingImage, ListingImage.listing_id == Listing.id)
        .where(Listing.id.in_(listing_ids))
        .group_by(Listing.id)
    )
    photo_counts: dict[str, int] = {lid: count for lid, count in photo_counts_result.all()}

    thumbnails: dict[str, Optional[str]] = {}
    img_result = await db.execute(
        select(ListingImage.listing_id, ListingImage.url_570xN)
        .where(ListingImage.listing_id.in_(listing_ids))
        .order_by(ListingImage.listing_id, ListingImage.rank.asc())
    )
    for lid, url in img_result.all():
        if lid not in thumbnails:
            thumbnails[lid] = url

    def _item(listing: Listing, metric: str) -> AffectedListingItem:
        return AffectedListingItem(
            listing_id=listing.id,
            title=listing.title,
            thumbnail_url=thumbnails.get(listing.id),
            metric=metric,
        )

    missing_tags: list[AffectedListingItem] = []
    low_photos: list[AffectedListingItem] = []
    short_titles: list[AffectedListingItem] = []
    missing_price: list[AffectedListingItem] = []
    zero_quantity: list[AffectedListingItem] = []

    for listing in listings:
        tags = listing.tags if isinstance(listing.tags, list) else []
        tag_count = len(tags)
        if tag_count == 0:
            missing_tags.append(_item(listing, "0/13 tags"))

        photo_count = photo_counts.get(listing.id, 0)
        if photo_count < LOW_PHOTO_COUNT_THRESHOLD:
            low_photos.append(_item(listing, f"{photo_count} photo{'s' if photo_count != 1 else ''}"))

        title_len = len((listing.title or "").strip())
        if title_len < LOW_TITLE_LENGTH_THRESHOLD:
            short_titles.append(_item(listing, f"{title_len}-char title" if title_len else "No title"))

        if listing.price_amount is None or listing.price_amount == 0:
            missing_price.append(_item(listing, "No price set"))

        if listing.quantity is not None and listing.quantity == 0:
            zero_quantity.append(_item(listing, "0 in stock"))

    sections = [
        AffectedListingsSection(
            category="missing_tags", label="Missing tags",
            count=len(missing_tags), items=missing_tags[:AFFECTED_LISTINGS_LIMIT],
        ),
        AffectedListingsSection(
            category="low_photo_count", label="Low photo count",
            count=len(low_photos), items=low_photos[:AFFECTED_LISTINGS_LIMIT],
        ),
        AffectedListingsSection(
            category="short_title", label="Short titles",
            count=len(short_titles), items=short_titles[:AFFECTED_LISTINGS_LIMIT],
        ),
        AffectedListingsSection(
            category="missing_price", label="Missing or zero price",
            count=len(missing_price), items=missing_price[:AFFECTED_LISTINGS_LIMIT],
        ),
        AffectedListingsSection(
            category="zero_quantity", label="Zero quantity",
            count=len(zero_quantity), items=zero_quantity[:AFFECTED_LISTINGS_LIMIT],
        ),
    ]

    return AffectedListingsOut(sections=sections)
