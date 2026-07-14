"""
Etsy listing sync service. Read-only: no writes to Etsy API.

Access tokens nearing expiry are auto-refreshed via etsy.refresh_etsy_token()
before use. If Etsy rejects the refresh (grant revoked by the seller, or the
refresh token itself expired), the shop is marked disconnected and callers
get a clear "reconnect your shop" error instead of an opaque failure.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_token
from app.core.plans import get_plan_limits
from app.models.etsy_shop import EtsyShop
from app.models.etsy_token import EtsyToken
from app.models.listing import Listing
from app.models.listing_image import ListingImage
from app.models.listing_video import ListingVideo
from app.models.listing_variation import ListingVariation
from app.models.subscription import Subscription
from app.models.sync_job import SyncJob
from app.services.etsy_http import etsy_get

logger = logging.getLogger(__name__)

ETSY_API_BASE = "https://openapi.etsy.com/v3"
PAGE_LIMIT = 100
TOKEN_REFRESH_BUFFER_SECONDS = 300


class SyncError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def get_valid_etsy_access_token(shop: EtsyShop, db: AsyncSession) -> str:
    """
    Return a decrypted, valid access token — auto-refreshing it first if it's
    expired or within TOKEN_REFRESH_BUFFER_SECONDS of expiry. Raises SyncError
    (401) if no token exists or Etsy rejects the refresh (revoked grant).
    """
    result = await db.execute(select(EtsyToken).where(EtsyToken.etsy_shop_id == shop.id))
    token_row = result.scalar_one_or_none()
    if not token_row:
        raise SyncError("No Etsy token found for shop. Please reconnect your shop.", 401)

    now = datetime.now(timezone.utc)
    expires = token_row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now >= (expires - timedelta(seconds=TOKEN_REFRESH_BUFFER_SECONDS)):
        from app.services.etsy import refresh_etsy_token

        try:
            return await refresh_etsy_token(shop.id, db)
        except httpx.HTTPStatusError:
            shop.is_connected = False
            db.add(shop)
            await db.commit()
            logger.warning("Etsy token refresh failed for shop %s — grant likely revoked.", shop.id)
            raise SyncError(
                "Etsy access has expired or was revoked. Please reconnect your shop.", 401
            )

    return decrypt_token(token_row.access_token_enc)


async def fetch_shop_listings(
    access_token: str, etsy_shop_id: str, limit: int = PAGE_LIMIT, offset: int = 0
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-key": "",  # populated from config by callers if needed
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await etsy_get(
            client,
            f"{ETSY_API_BASE}/application/shops/{etsy_shop_id}/listings/active",
            headers=headers,
            params={"limit": limit, "offset": offset, "includes": "Images,MainImage"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_listing_images(access_token: str, listing_id: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await etsy_get(
            client,
            f"{ETSY_API_BASE}/application/listings/{listing_id}/images",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])


async def fetch_listing_videos(access_token: str, listing_id: str) -> list[dict[str, Any]]:
    """Placeholder — Etsy video API may not always be available."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await etsy_get(
            client,
            f"{ETSY_API_BASE}/application/listings/{listing_id}/videos",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code in (404, 405):
            return []
        if not resp.is_success:
            return []
        data = resp.json()
        return data.get("results", [])


async def fetch_listing_inventory(access_token: str, listing_id: str) -> list[dict[str, Any]]:
    """Fetch product variations from Etsy inventory endpoint."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await etsy_get(
            client,
            f"{ETSY_API_BASE}/application/listings/{listing_id}/inventory",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code in (404, 405):
            return []
        if not resp.is_success:
            return []
        data = resp.json()
        products = data.get("products", [])
        return products


def _parse_listing(listing_data: dict[str, Any], org_id: str, shop_db_id: str) -> dict[str, Any]:
    price = listing_data.get("price") or {}
    etsy_updated = listing_data.get("last_modified_tsz") or listing_data.get("updated_timestamp")
    etsy_updated_at = None
    if etsy_updated:
        try:
            etsy_updated_at = datetime.fromtimestamp(int(etsy_updated), tz=timezone.utc)
        except (ValueError, TypeError):
            pass

    return {
        "organization_id": org_id,
        "etsy_shop_id": shop_db_id,
        "etsy_listing_id": str(listing_data.get("listing_id", "")),
        "title": listing_data.get("title"),
        "description": listing_data.get("description"),
        "state": listing_data.get("state"),
        "url": listing_data.get("url"),
        "price_amount": price.get("amount"),
        "price_divisor": price.get("divisor", 100),
        "currency_code": price.get("currency_code"),
        "quantity": listing_data.get("quantity"),
        "sku": listing_data.get("sku"),
        "tags": listing_data.get("tags"),
        "materials": listing_data.get("materials"),
        "taxonomy_id": str(listing_data["taxonomy_id"]) if listing_data.get("taxonomy_id") else None,
        "category_path": listing_data.get("taxonomy_path"),
        "section_id": str(listing_data["shop_section_id"]) if listing_data.get("shop_section_id") else None,
        "shipping_profile_id": str(listing_data["shipping_profile_id"]) if listing_data.get("shipping_profile_id") else None,
        "return_policy_id": str(listing_data["return_policy_id"]) if listing_data.get("return_policy_id") else None,
        "processing_min": listing_data.get("processing_min"),
        "processing_max": listing_data.get("processing_max"),
        "who_made": listing_data.get("who_made"),
        "when_made": listing_data.get("when_made"),
        "is_supply": listing_data.get("is_supply"),
        "is_customizable": listing_data.get("is_customizable"),
        "is_personalizable": listing_data.get("is_personalizable"),
        "personalization_is_required": listing_data.get("personalization_is_required"),
        "personalization_char_count_max": listing_data.get("personalization_char_count_max"),
        "personalization_instructions": listing_data.get("personalization_instructions"),
        "item_weight": listing_data.get("item_weight"),
        "item_weight_unit": listing_data.get("item_weight_unit"),
        "item_length": listing_data.get("item_length"),
        "item_width": listing_data.get("item_width"),
        "item_height": listing_data.get("item_height"),
        "item_dimensions_unit": listing_data.get("item_dimensions_unit"),
        "has_variations": bool(listing_data.get("has_variations", False)),
        "raw_data": listing_data,
        "etsy_updated_at": etsy_updated_at,
        "last_synced_at": datetime.now(timezone.utc),
    }


async def upsert_listing(
    db: AsyncSession, org_id: str, shop: EtsyShop, listing_data: dict[str, Any]
) -> Listing:
    etsy_listing_id = str(listing_data.get("listing_id", ""))
    result = await db.execute(
        select(Listing).where(
            Listing.etsy_shop_id == shop.id,
            Listing.etsy_listing_id == etsy_listing_id,
        )
    )
    listing = result.scalar_one_or_none()
    parsed = _parse_listing(listing_data, org_id, shop.id)

    if listing is None:
        listing = Listing(**parsed)
        db.add(listing)
        await db.flush()
    else:
        for key, val in parsed.items():
            setattr(listing, key, val)
        await db.flush()

    return listing


async def upsert_listing_images(
    db: AsyncSession, listing: Listing, images: list[dict[str, Any]]
) -> None:
    for img in images:
        etsy_image_id = str(img.get("listing_image_id", img.get("image_id", "")))
        result = await db.execute(
            select(ListingImage).where(
                ListingImage.listing_id == listing.id,
                ListingImage.etsy_image_id == etsy_image_id,
            )
        )
        row = result.scalar_one_or_none()
        fields = {
            "listing_id": listing.id,
            "etsy_image_id": etsy_image_id,
            "url_fullxfull": img.get("url_fullxfull"),
            "url_570xN": img.get("url_570xN"),
            "url_170x135": img.get("url_170x135"),
            "alt_text": img.get("alt_text"),
            "rank": img.get("rank"),
            "width": img.get("full_width"),
            "height": img.get("full_height"),
            "raw_data": img,
        }
        if row is None:
            db.add(ListingImage(**fields))
        else:
            for k, v in fields.items():
                setattr(row, k, v)
    await db.flush()


async def upsert_listing_videos(
    db: AsyncSession, listing: Listing, videos: list[dict[str, Any]]
) -> None:
    for vid in videos:
        etsy_video_id = str(vid.get("video_id", ""))
        result = await db.execute(
            select(ListingVideo).where(
                ListingVideo.listing_id == listing.id,
                ListingVideo.etsy_video_id == etsy_video_id,
            )
        )
        row = result.scalar_one_or_none()
        fields = {
            "listing_id": listing.id,
            "etsy_video_id": etsy_video_id,
            "video_url": vid.get("video_url") or vid.get("url"),
            "thumbnail_url": vid.get("thumbnail_url"),
            "rank": vid.get("rank"),
            "raw_data": vid,
        }
        if row is None:
            db.add(ListingVideo(**fields))
        else:
            for k, v in fields.items():
                setattr(row, k, v)
    await db.flush()


async def upsert_listing_variations(
    db: AsyncSession, listing: Listing, products: list[dict[str, Any]]
) -> None:
    for product in products:
        etsy_product_id = str(product.get("product_id", ""))
        offerings = product.get("offerings", [{}])
        first_offering = offerings[0] if offerings else {}
        price = first_offering.get("price") or {}
        property_values = product.get("property_values", [{}])
        first_prop = property_values[0] if property_values else {}

        result = await db.execute(
            select(ListingVariation).where(
                ListingVariation.listing_id == listing.id,
                ListingVariation.etsy_product_id == etsy_product_id,
            )
        )
        row = result.scalar_one_or_none()
        fields = {
            "listing_id": listing.id,
            "etsy_product_id": etsy_product_id,
            "sku": product.get("sku"),
            "property_id": str(first_prop.get("property_id", "")) or None,
            "property_name": first_prop.get("property_name"),
            "value_id": str(first_prop.get("value_ids", [""])[0]) if first_prop.get("value_ids") else None,
            "value_name": first_prop.get("values", [None])[0] if first_prop.get("values") else None,
            "price_amount": price.get("amount"),
            "price_divisor": price.get("divisor", 100),
            "currency_code": price.get("currency_code"),
            "quantity": first_offering.get("quantity"),
            "is_available": bool(first_offering.get("is_enabled", True)),
            "raw_data": product,
        }
        if row is None:
            db.add(ListingVariation(**fields))
        else:
            for k, v in fields.items():
                setattr(row, k, v)
    await db.flush()


async def sync_shop_listings(
    db: AsyncSession,
    org_id: str,
    shop_db_id: str,
) -> SyncJob:
    """
    Full listing sync for a shop. Read-only from Etsy.
    Enforces max_listings plan limit.
    Returns SyncJob with final status.

    Future: convert to Celery task for background execution.
    """
    # Verify shop belongs to org and is connected
    result = await db.execute(
        select(EtsyShop).where(EtsyShop.id == shop_db_id, EtsyShop.organization_id == org_id)
    )
    shop = result.scalar_one_or_none()
    if not shop:
        raise SyncError("Shop not found or does not belong to your organization.", 404)
    if not shop.is_connected:
        raise SyncError("Shop is disconnected. Please reconnect your Etsy shop.", 400)

    # Determine max_listings from subscription plan
    sub_result = await db.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    subscription = sub_result.scalar_one_or_none()
    plan = subscription.plan if subscription else "free"
    limits = get_plan_limits(plan)
    max_listings: int = limits.get("max_listings", 25)

    # Create sync job
    job = SyncJob(
        organization_id=org_id,
        etsy_shop_id=shop_db_id,
        job_type="manual_listing_sync",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()

    try:
        access_token = await get_valid_etsy_access_token(shop, db)

        offset = 0
        total_fetched = 0
        processed = 0

        while True:
            remaining = max_listings - total_fetched
            if remaining <= 0:
                break

            page_limit = min(PAGE_LIMIT, remaining)
            page_data = await fetch_shop_listings(
                access_token, shop.etsy_shop_id, limit=page_limit, offset=offset
            )
            results = page_data.get("results", [])
            count = page_data.get("count", len(results))

            if not results:
                break

            # Cap results to remaining budget (Etsy may return more than page_limit in some cases)
            results = results[:remaining]

            if job.total_items == 0:
                job.total_items = min(count, max_listings)
                await db.flush()

            for listing_data in results:
                listing = await upsert_listing(db, org_id, shop, listing_data)

                # Sync images: try inline Images include first, then fetch separately
                inline_images = listing_data.get("Images") or listing_data.get("images") or []
                if inline_images:
                    await upsert_listing_images(db, listing, inline_images)
                else:
                    try:
                        images = await fetch_listing_images(access_token, listing_data["listing_id"])
                        if images:
                            await upsert_listing_images(db, listing, images)
                    except Exception as exc:
                        logger.warning("Failed to fetch images for listing %s: %s", listing_data.get("listing_id"), exc)

                # Sync videos (best-effort)
                try:
                    videos = await fetch_listing_videos(access_token, listing_data["listing_id"])
                    if videos:
                        await upsert_listing_videos(db, listing, videos)
                except Exception as exc:
                    logger.warning("Failed to fetch videos for listing %s: %s", listing_data.get("listing_id"), exc)

                # Sync variations/inventory (best-effort)
                if listing_data.get("has_variations"):
                    try:
                        products = await fetch_listing_inventory(access_token, listing_data["listing_id"])
                        if products:
                            await upsert_listing_variations(db, listing, products)
                    except Exception as exc:
                        logger.warning("Failed to fetch inventory for listing %s: %s", listing_data.get("listing_id"), exc)

                processed += 1
                job.processed_items = processed
                await db.flush()

            total_fetched += len(results)
            offset += len(results)

            if len(results) < page_limit:
                break

        # Update shop last_synced_at
        shop.last_synced_at = datetime.now(timezone.utc)
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.total_items = job.total_items or processed
        job.processed_items = processed
        await db.commit()

    except SyncError:
        await db.rollback()
        job.status = "failed"
        job.error_message = str(job.error_message or "Sync error")
        raise
    except Exception as exc:
        await db.rollback()
        logger.exception("Sync failed for shop %s: %s", shop_db_id, exc)
        # Re-fetch job since rollback cleared session state
        result2 = await db.execute(select(SyncJob).where(SyncJob.id == job.id))
        job2 = result2.scalar_one_or_none()
        if job2:
            job2.status = "failed"
            job2.error_message = str(exc)[:1000]
            job2.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return job2
        # Fallback: create a new failed job record
        failed_job = SyncJob(
            organization_id=org_id,
            etsy_shop_id=shop_db_id,
            job_type="manual_listing_sync",
            status="failed",
            error_message=str(exc)[:1000],
            started_at=job.started_at,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(failed_job)
        await db.commit()
        return failed_job

    return job
