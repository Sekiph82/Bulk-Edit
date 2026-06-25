"""
Etsy API write service.

Endpoints used:
  PATCH /v3/application/listings/{listing_id}       — text/bool fields
  PUT   /v3/application/shops/{shop_id}/listings/{listing_id}/inventory
                                                     — price + quantity (Sprint 10)

Safety contract: callers must have:
  1. Generated preview
  2. Received user confirmation
  3. Created a backup snapshot
  4. Verified permissions and subscription gate
  5. Written to audit log
before calling patch_etsy_listing() or patch_etsy_listing_inventory().

Variation-level inventory (multi-SKU) is deferred to Sprint 11.
Photo/video writes are deferred to Sprint 11.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.listing import Listing

logger = logging.getLogger(__name__)

ETSY_API_BASE = "https://openapi.etsy.com/v3"

# Fields supported by PATCH /v3/application/listings/{listing_id}
# price/quantity require the inventory endpoint — excluded here
PATCHABLE_TEXT_FIELDS = {
    "title",
    "description",
    "tags",
    "materials",
    "who_made",
    "when_made",
    "taxonomy_id",
    "shop_section_id",
    "processing_min",
    "processing_max",
}

PATCHABLE_BOOL_FIELDS = {
    "is_supply",
    "is_customizable",
    "is_personalizable",
    "personalization_is_required",
}


def build_etsy_patch_payload(diff: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a bulk edit diff dict to an Etsy PATCH payload.
    Returns only fields that Etsy's PATCH endpoint accepts.
    section_id (local name) maps to shop_section_id (Etsy API name).
    Price and quantity are always excluded — use build_etsy_inventory_payload.
    """
    payload: dict[str, Any] = {}

    for field, change in diff.items():
        after = change.get("after")

        if field == "section_id":
            payload["shop_section_id"] = after
        elif field in PATCHABLE_TEXT_FIELDS or field in PATCHABLE_BOOL_FIELDS:
            payload[field] = after

    return payload


def build_etsy_inventory_payload(
    listing: "Listing",
    after_data: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Build Etsy inventory PUT payload for price/quantity writes.
    Supports single-SKU/simple listings only (Sprint 10).

    Returns None when:
    - listing.has_variations is True (variation inventory deferred to Sprint 11)
    - Neither price_amount nor quantity differs from current listing values
    - currency_code is unavailable

    For apply: pass preview_item.after_data as after_data (diff gates the call).
    For revert: pass snapshot_data as after_data (snapshot values are the target).
    """
    if listing.has_variations:
        return None

    new_price = after_data.get("price_amount")
    new_qty = after_data.get("quantity")

    price_changed = new_price is not None and new_price != listing.price_amount
    qty_changed = new_qty is not None and new_qty != listing.quantity

    if not price_changed and not qty_changed:
        return None

    currency_code = listing.currency_code
    if not currency_code:
        return None

    price_amount = int(new_price) if price_changed else int(listing.price_amount or 0)
    price_divisor = int(after_data.get("price_divisor") or listing.price_divisor or 100)
    quantity = int(new_qty) if qty_changed else int(listing.quantity or 0)

    return {
        "products": [
            {
                "sku": listing.sku or "",
                "offerings": [
                    {
                        "price": {
                            "amount": price_amount,
                            "divisor": price_divisor,
                            "currency_code": currency_code,
                        },
                        "quantity": quantity,
                        "is_enabled": True,
                    }
                ],
            }
        ]
    }


class EtsyWriteError(Exception):
    def __init__(self, message: str, status_code: int = 500, response_body: Any = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


async def patch_etsy_listing(
    access_token: str,
    etsy_listing_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    PATCH a single Etsy listing (text/bool fields).
    Returns Etsy response JSON on success. Raises EtsyWriteError on HTTP error.
    """
    if not payload:
        raise EtsyWriteError("Empty payload — nothing to write to Etsy.", 400)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-key": settings.ETSY_CLIENT_ID,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.patch(
            f"{ETSY_API_BASE}/application/listings/{etsy_listing_id}",
            headers=headers,
            data=_flatten_payload(payload),
        )

    if resp.status_code >= 400:
        body: Any = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise EtsyWriteError(
            f"Etsy PATCH {etsy_listing_id} failed: HTTP {resp.status_code}",
            status_code=resp.status_code,
            response_body=body,
        )

    return resp.json()


async def patch_etsy_listing_inventory(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    PUT inventory for a single Etsy listing (price + quantity).
    Endpoint: PUT /v3/application/shops/{shop_id}/listings/{listing_id}/inventory
    Returns Etsy response JSON on success. Raises EtsyWriteError on HTTP error.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-key": settings.ETSY_CLIENT_ID,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            f"{ETSY_API_BASE}/application/shops/{shop_etsy_id}/listings/{listing_etsy_id}/inventory",
            headers=headers,
            json=payload,
        )

    if resp.status_code >= 400:
        body: Any = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise EtsyWriteError(
            f"Etsy inventory PUT {listing_etsy_id} failed: HTTP {resp.status_code}",
            status_code=resp.status_code,
            response_body=body,
        )

    return resp.json()


def _flatten_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Etsy v3 PATCH expects application/x-www-form-urlencoded.
    Lists (tags, materials) are serialized as repeated keys.
    httpx handles repeated keys when passed as a list of tuples.
    """
    result: dict[str, Any] = {}
    for k, v in payload.items():
        if isinstance(v, list):
            result[k] = v
        elif isinstance(v, bool):
            result[k] = str(v).lower()
        elif v is None:
            pass
        else:
            result[k] = str(v)
    return result
