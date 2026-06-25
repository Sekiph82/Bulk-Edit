"""
Etsy API write service. Wraps PATCH /v3/application/listings/{listing_id}.

Safety contract: callers must have:
  1. Generated preview
  2. Received user confirmation
  3. Created a backup snapshot
  4. Verified permissions and subscription gate
  5. Written to audit log
before calling patch_etsy_listing().

Price and quantity are NOT supported here — they require the inventory endpoint
(deferred to Sprint 9).
"""
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ETSY_API_BASE = "https://openapi.etsy.com/v3"

# Fields supported by PATCH /v3/application/listings/{listing_id}
# price/quantity are excluded — they need the inventory endpoint
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
    """
    payload: dict[str, Any] = {}

    for field, change in diff.items():
        after = change.get("after")

        if field == "section_id":
            payload["shop_section_id"] = after
        elif field in PATCHABLE_TEXT_FIELDS or field in PATCHABLE_BOOL_FIELDS:
            payload[field] = after

    return payload


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
    PATCH a single Etsy listing. Returns Etsy response JSON on success.
    Raises EtsyWriteError on HTTP error.
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


def _flatten_payload(payload: dict[str, Any]) -> dict[str, str]:
    """
    Etsy v3 PATCH expects application/x-www-form-urlencoded.
    Lists (tags, materials) are serialized as repeated keys.
    httpx handles repeated keys when passed as a list of tuples.
    This function converts to the format httpx expects for `data=`.
    """
    result: dict[str, Any] = {}
    for k, v in payload.items():
        if isinstance(v, list):
            result[k] = v  # httpx sends repeated keys for lists
        elif isinstance(v, bool):
            result[k] = str(v).lower()
        elif v is None:
            pass  # skip None values
        else:
            result[k] = str(v)
    return result
