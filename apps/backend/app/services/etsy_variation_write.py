"""
Etsy variation inventory write service — Sprint 12.

Strategy: fetch-patch-put
  1. GET current Etsy inventory tree (never guess variation structure)
  2. Patch the fetched tree in memory
  3. PUT the full patched tree back

Supported operations:
  set_variation_price, adjust_variation_price_percent, adjust_variation_price_fixed
  set_variation_quantity, adjust_variation_quantity_fixed
  set_variation_sku, replace_variation_sku_text
  set_variation_availability

Safety: callers must create backup snapshot before calling put_etsy_listing_inventory.
"""
from __future__ import annotations

import copy
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.services.etsy_http import etsy_get

logger = logging.getLogger(__name__)

ETSY_API_BASE = "https://openapi.etsy.com/v3"

MAX_SKU_LENGTH = 32  # Conservative Etsy-safe limit


class EtsyVariationWriteError(Exception):
    def __init__(self, message: str, status_code: int = 500, response_body: Any = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


def _auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "x-api-key": settings.ETSY_CLIENT_ID,
        "Content-Type": "application/json",
    }


# ── Etsy inventory fetch ──────────────────────────────────────────────────────

async def fetch_etsy_listing_inventory(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
) -> dict[str, Any]:
    """
    GET /v3/application/shops/{shop_id}/listings/{listing_id}/inventory
    Returns the full Etsy inventory tree.
    Raises EtsyVariationWriteError on HTTP error.
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await etsy_get(
            client,
            f"{ETSY_API_BASE}/application/shops/{shop_etsy_id}/listings/{listing_etsy_id}/inventory",
            headers=_auth_headers(access_token),
        )

    if resp.status_code >= 400:
        body: Any = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise EtsyVariationWriteError(
            f"Fetch inventory failed for listing {listing_etsy_id}: HTTP {resp.status_code}",
            status_code=resp.status_code,
            response_body=body,
        )
    return resp.json()


# ── Etsy inventory write ──────────────────────────────────────────────────────

async def put_etsy_listing_inventory(
    access_token: str,
    shop_etsy_id: str,
    listing_etsy_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    PUT /v3/application/shops/{shop_id}/listings/{listing_id}/inventory
    Sends full inventory tree. Raises EtsyVariationWriteError on HTTP error.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            f"{ETSY_API_BASE}/application/shops/{shop_etsy_id}/listings/{listing_etsy_id}/inventory",
            headers=_auth_headers(access_token),
            json=payload,
        )

    if resp.status_code >= 400:
        body: Any = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise EtsyVariationWriteError(
            f"Inventory PUT failed for listing {listing_etsy_id}: HTTP {resp.status_code}",
            status_code=resp.status_code,
            response_body=body,
        )
    return resp.json()


# ── Inventory tree helpers ────────────────────────────────────────────────────

def normalize_etsy_inventory_tree(inventory_response: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize raw Etsy GET inventory response for safe PUT.
    Returns a dict with: products, price_on_property, quantity_on_property, sku_on_property.
    Strips read-only fields that Etsy rejects on PUT.
    """
    products = []
    for p in inventory_response.get("products", []):
        if p.get("is_deleted"):
            continue
        product: dict[str, Any] = {
            "sku": p.get("sku", ""),
            "property_values": p.get("property_values", []),
            "offerings": [],
        }
        # Keep product_id if present (Etsy may require it on update)
        if p.get("product_id"):
            product["product_id"] = p["product_id"]

        for o in p.get("offerings", []):
            offering: dict[str, Any] = {
                "quantity": o.get("quantity", 0),
                "is_enabled": o.get("is_enabled", True),
                "price": {
                    "amount": o["price"]["amount"],
                    "divisor": o["price"]["divisor"],
                    "currency_code": o["price"]["currency_code"],
                },
            }
            if o.get("offering_id"):
                offering["offering_id"] = o["offering_id"]
            product["offerings"].append(offering)

        products.append(product)

    return {
        "products": products,
        "price_on_property": inventory_response.get("price_on_property", []),
        "quantity_on_property": inventory_response.get("quantity_on_property", []),
        "sku_on_property": inventory_response.get("sku_on_property", []),
    }


def _product_matches_selector(
    product: dict[str, Any],
    selector: dict[str, Any] | None,
) -> bool:
    """True if product matches the (property_name, value_name) selector, or selector is None/empty."""
    if not selector:
        return True
    prop_name = selector.get("property_name", "").lower()
    val_name = selector.get("value_name", "").lower()
    for pv in product.get("property_values", []):
        if pv.get("property_name", "").lower() == prop_name:
            for v in pv.get("values", []):
                if str(v).lower() == val_name:
                    return True
    return False


def patch_inventory_tree_for_variation_operation(
    inventory_tree: dict[str, Any],
    operation_type: str,
    operation_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Apply a variation operation to an Etsy inventory tree (in-place copy).
    Returns a new tree with the operation applied.
    Raises EtsyVariationWriteError if operation is invalid.
    """
    tree = copy.deepcopy(inventory_tree)
    selector = operation_payload.get("selector")

    for product in tree.get("products", []):
        if not _product_matches_selector(product, selector):
            continue

        if operation_type == "set_variation_price":
            new_price = int(operation_payload["price_amount"])
            if new_price < 0:
                raise EtsyVariationWriteError("price_amount must be >= 0", status_code=400)
            for offering in product.get("offerings", []):
                offering["price"]["amount"] = new_price

        elif operation_type == "adjust_variation_price_percent":
            pct = float(operation_payload["percent"])
            for offering in product.get("offerings", []):
                old = offering["price"]["amount"]
                new_val = int(round(old * (1 + pct / 100.0)))
                if new_val < 0:
                    raise EtsyVariationWriteError(
                        f"Adjusted price would be negative ({new_val})", status_code=400
                    )
                offering["price"]["amount"] = new_val

        elif operation_type == "adjust_variation_price_fixed":
            delta = int(operation_payload["amount_delta"])
            for offering in product.get("offerings", []):
                new_val = offering["price"]["amount"] + delta
                if new_val < 0:
                    raise EtsyVariationWriteError(
                        f"Adjusted price would be negative ({new_val})", status_code=400
                    )
                offering["price"]["amount"] = new_val

        elif operation_type == "set_variation_quantity":
            qty = int(operation_payload["quantity"])
            if qty < 0:
                raise EtsyVariationWriteError("quantity must be >= 0", status_code=400)
            for offering in product.get("offerings", []):
                offering["quantity"] = qty

        elif operation_type == "adjust_variation_quantity_fixed":
            delta = int(operation_payload["quantity_delta"])
            for offering in product.get("offerings", []):
                new_qty = offering["quantity"] + delta
                if new_qty < 0:
                    raise EtsyVariationWriteError(
                        f"Adjusted quantity would be negative ({new_qty})", status_code=400
                    )
                offering["quantity"] = new_qty

        elif operation_type == "set_variation_sku":
            sku = str(operation_payload.get("sku", ""))
            if len(sku) > MAX_SKU_LENGTH:
                raise EtsyVariationWriteError(
                    f"SKU too long: {len(sku)} chars (max {MAX_SKU_LENGTH})", status_code=400
                )
            product["sku"] = sku

        elif operation_type == "replace_variation_sku_text":
            find = str(operation_payload.get("find", ""))
            replace = str(operation_payload.get("replace", ""))
            if not find:
                raise EtsyVariationWriteError("'find' must not be empty for replace_variation_sku_text", status_code=400)
            product["sku"] = product.get("sku", "").replace(find, replace)
            if len(product["sku"]) > MAX_SKU_LENGTH:
                raise EtsyVariationWriteError(
                    f"SKU after replace too long: {len(product['sku'])} chars", status_code=400
                )

        elif operation_type == "set_variation_availability":
            is_available = bool(operation_payload["is_available"])
            for offering in product.get("offerings", []):
                offering["is_enabled"] = is_available

        else:
            raise EtsyVariationWriteError(f"Unknown operation: {operation_type}", status_code=400)

    return tree


# ── Local snapshot helper ─────────────────────────────────────────────────────

def extract_local_variation_snapshot(variations: list) -> list[dict[str, Any]]:
    """Convert local ListingVariation rows to a JSON-serializable snapshot list."""
    result = []
    for v in variations:
        result.append({
            "id": v.id,
            "etsy_product_id": v.etsy_product_id,
            "sku": v.sku,
            "property_name": v.property_name,
            "value_name": v.value_name,
            "price_amount": v.price_amount,
            "price_divisor": v.price_divisor,
            "currency_code": v.currency_code,
            "quantity": v.quantity,
            "is_available": v.is_available,
        })
    return result
