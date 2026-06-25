"""
Bulk Edit Variation Service — Sprint 12.

Flow:
  1. create_variation_job     → status: draft
  2. generate_variation_preview → status: preview_ready
  3. apply_variation_job      → status: running → completed / completed_with_errors / failed

Safety contract:
  1. All listing_ids must belong to organization
  2. Job must be preview_ready before apply
  3. No invalid preview items before apply
  4. Etsy must be configured
  5. Backup snapshot created BEFORE every Etsy inventory write
  6. Local ListingVariation rows updated ONLY after Etsy write success
  7. Audit log on apply start and finish
  8. Partial failure supported — each listing gets its own BulkEditVariationResult row
  9. Variation revert deferred to Sprint 13 — snapshots are created here to enable it

Design: fetch-patch-put
  - Always GET current Etsy inventory tree before writing
  - Patch the tree in memory
  - PUT the full tree back
  - Never guess or construct variation tree from local data alone
"""
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.bulk_edit_variation_job import BulkEditVariationJob
from app.models.bulk_edit_variation_preview_item import BulkEditVariationPreviewItem
from app.models.bulk_edit_variation_result import BulkEditVariationResult
from app.models.etsy_shop import EtsyShop
from app.models.listing import Listing
from app.models.listing_variation import ListingVariation
from app.models.listing_variation_backup_snapshot import ListingVariationBackupSnapshot
from app.services.etsy_sync import get_valid_etsy_access_token
from app.services.etsy_variation_write import (
    EtsyVariationWriteError,
    MAX_SKU_LENGTH,
    extract_local_variation_snapshot,
    fetch_etsy_listing_inventory,
    normalize_etsy_inventory_tree,
    patch_inventory_tree_for_variation_operation,
    put_etsy_listing_inventory,
)

logger = logging.getLogger(__name__)

VALID_OPERATION_TYPES = {
    "set_variation_price",
    "adjust_variation_price_percent",
    "adjust_variation_price_fixed",
    "set_variation_quantity",
    "adjust_variation_quantity_fixed",
    "set_variation_sku",
    "replace_variation_sku_text",
    "set_variation_availability",
}


# ── Audit helper ──────────────────────────────────────────────────────────────

async def _audit(
    db: AsyncSession,
    org_id: str,
    user_id: str | None,
    event_type: str,
    entity_id: str | None = None,
    message: str | None = None,
    extra_data: Any = None,
) -> None:
    log = AuditLog(
        organization_id=org_id,
        user_id=user_id,
        event_type=event_type,
        entity_type="bulk_edit_variation_job",
        entity_id=entity_id,
        message=message,
        extra_data=extra_data,
    )
    db.add(log)
    await db.flush()


# ── Payload validation ────────────────────────────────────────────────────────

def validate_variation_job_payload(operation_type: str, payload: dict[str, Any]) -> list[str]:
    """Returns list of validation error strings. Empty = valid."""
    errors: list[str] = []
    if operation_type not in VALID_OPERATION_TYPES:
        errors.append(f"Unknown operation_type: {operation_type}")
        return errors

    if operation_type == "set_variation_price":
        pa = payload.get("price_amount")
        if pa is None:
            errors.append("price_amount is required")
        elif int(pa) < 0:
            errors.append("price_amount must be >= 0")

    elif operation_type == "adjust_variation_price_percent":
        if payload.get("percent") is None:
            errors.append("percent is required")

    elif operation_type == "adjust_variation_price_fixed":
        if payload.get("amount_delta") is None:
            errors.append("amount_delta is required")

    elif operation_type == "set_variation_quantity":
        qty = payload.get("quantity")
        if qty is None:
            errors.append("quantity is required")
        elif int(qty) < 0:
            errors.append("quantity must be >= 0")

    elif operation_type == "adjust_variation_quantity_fixed":
        if payload.get("quantity_delta") is None:
            errors.append("quantity_delta is required")

    elif operation_type == "set_variation_sku":
        sku = payload.get("sku")
        if sku is None:
            errors.append("sku is required")
        elif len(str(sku)) > MAX_SKU_LENGTH:
            errors.append(f"sku too long (max {MAX_SKU_LENGTH} chars)")

    elif operation_type == "replace_variation_sku_text":
        find = payload.get("find", "")
        if not find:
            errors.append("find must be non-empty for replace_variation_sku_text")

    elif operation_type == "set_variation_availability":
        if payload.get("is_available") is None:
            errors.append("is_available is required")
        elif not isinstance(payload.get("is_available"), bool):
            errors.append("is_available must be boolean")

    return errors


# ── Job create ────────────────────────────────────────────────────────────────

async def create_variation_job(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    listing_ids: list[str],
    operation_type: str,
    operation_payload: dict[str, Any],
) -> BulkEditVariationJob:
    if not listing_ids:
        raise HTTPException(status_code=400, detail="listing_ids must not be empty.")

    errors = validate_variation_job_payload(operation_type, operation_payload)
    if errors:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {'; '.join(errors)}")

    # Org-scoped listing check
    listings_q = await db.execute(
        select(Listing).where(
            Listing.id.in_(listing_ids),
            Listing.organization_id == organization_id,
        )
    )
    found = {l.id for l in listings_q.scalars().all()}
    missing = [lid for lid in listing_ids if lid not in found]
    if missing:
        raise HTTPException(status_code=404, detail=f"Listing(s) not found: {missing[:5]}")

    job = BulkEditVariationJob(
        organization_id=organization_id,
        created_by_user_id=user_id,
        operation_type=operation_type,
        operation_payload=operation_payload,
        selected_listing_ids=listing_ids,
        status="draft",
        selected_count=len(listing_ids),
    )
    db.add(job)
    await db.flush()
    await db.commit()
    await db.refresh(job)
    return job


# ── Preview generation ────────────────────────────────────────────────────────

def _variation_to_dict(v: ListingVariation) -> dict[str, Any]:
    return {
        "id": v.id,
        "property_name": v.property_name,
        "value_name": v.value_name,
        "sku": v.sku,
        "price_amount": v.price_amount,
        "price_divisor": v.price_divisor,
        "currency_code": v.currency_code,
        "quantity": v.quantity,
        "is_available": v.is_available,
    }


def _selector_matches(v: ListingVariation, selector: dict[str, Any] | None) -> bool:
    if not selector:
        return True
    prop = selector.get("property_name", "").lower()
    val = selector.get("value_name", "").lower()
    return (
        (v.property_name or "").lower() == prop
        and (v.value_name or "").lower() == val
    )


def build_variation_preview_for_listing(
    listing: Listing,
    variations: list[ListingVariation],
    operation_type: str,
    operation_payload: dict[str, Any],
) -> tuple[list[dict], list[dict], list[dict], str, list[dict]]:
    """
    Compute before/after/diff for a listing's variations.
    Returns (before_variations, after_variations, diff_list, validation_status, validation_messages).
    """
    selector = operation_payload.get("selector")
    before = [_variation_to_dict(v) for v in variations]
    after = [_variation_to_dict(v) for v in variations]
    messages: list[dict] = []

    if not listing.has_variations:
        return (
            before, before, [],
            "invalid",
            [{"level": "error", "message": "Listing does not have variations."}],
        )

    if not variations:
        return (
            before, before, [],
            "warning",
            [{"level": "warning", "message": "No local variation data synced yet. Sync listing first."}],
        )

    selector_matched = False
    diff: list[dict] = []

    for i, v in enumerate(variations):
        if not _selector_matches(v, selector):
            continue
        selector_matched = True
        after_v = dict(after[i])
        changes: dict[str, Any] = {}

        if operation_type == "set_variation_price":
            new_price = int(operation_payload.get("price_amount", 0))
            if new_price < 0:
                messages.append({"level": "error", "message": f"price_amount < 0 ({new_price})"})
            else:
                changes["price_amount"] = {"before": after_v["price_amount"], "after": new_price}
                after_v["price_amount"] = new_price

        elif operation_type == "adjust_variation_price_percent":
            pct = float(operation_payload.get("percent", 0))
            old = after_v["price_amount"] or 0
            new_price = int(round(old * (1 + pct / 100.0)))
            if new_price < 0:
                messages.append({"level": "error", "message": f"Adjusted price would be negative ({new_price})"})
            else:
                changes["price_amount"] = {"before": old, "after": new_price}
                after_v["price_amount"] = new_price

        elif operation_type == "adjust_variation_price_fixed":
            delta = int(operation_payload.get("amount_delta", 0))
            old = after_v["price_amount"] or 0
            new_price = old + delta
            if new_price < 0:
                messages.append({"level": "error", "message": f"Adjusted price would be negative ({new_price})"})
            else:
                changes["price_amount"] = {"before": old, "after": new_price}
                after_v["price_amount"] = new_price

        elif operation_type == "set_variation_quantity":
            qty = int(operation_payload.get("quantity", 0))
            if qty < 0:
                messages.append({"level": "error", "message": f"quantity < 0 ({qty})"})
            else:
                changes["quantity"] = {"before": after_v["quantity"], "after": qty}
                after_v["quantity"] = qty

        elif operation_type == "adjust_variation_quantity_fixed":
            delta = int(operation_payload.get("quantity_delta", 0))
            old = after_v["quantity"] or 0
            new_qty = old + delta
            if new_qty < 0:
                messages.append({"level": "error", "message": f"Adjusted quantity would be negative ({new_qty})"})
            else:
                changes["quantity"] = {"before": old, "after": new_qty}
                after_v["quantity"] = new_qty

        elif operation_type == "set_variation_sku":
            sku = str(operation_payload.get("sku", ""))
            if len(sku) > MAX_SKU_LENGTH:
                messages.append({"level": "error", "message": f"SKU too long ({len(sku)} chars)"})
            else:
                changes["sku"] = {"before": after_v["sku"], "after": sku}
                after_v["sku"] = sku

        elif operation_type == "replace_variation_sku_text":
            find = str(operation_payload.get("find", ""))
            replace = str(operation_payload.get("replace", ""))
            old_sku = after_v["sku"] or ""
            new_sku = old_sku.replace(find, replace)
            if len(new_sku) > MAX_SKU_LENGTH:
                messages.append({"level": "error", "message": f"SKU after replace too long ({len(new_sku)} chars)"})
            else:
                changes["sku"] = {"before": old_sku, "after": new_sku}
                after_v["sku"] = new_sku

        elif operation_type == "set_variation_availability":
            is_avail = bool(operation_payload.get("is_available"))
            changes["is_available"] = {"before": after_v["is_available"], "after": is_avail}
            after_v["is_available"] = is_avail

        if changes:
            diff.append({
                "variation_index": i,
                "property_name": v.property_name,
                "value_name": v.value_name,
                "changes": changes,
            })
        after[i] = after_v

    if selector and not selector_matched:
        messages.append({
            "level": "warning",
            "message": f"No variation matched selector property_name='{selector.get('property_name')}' value_name='{selector.get('value_name')}'.",
        })

    error_msgs = [m for m in messages if m.get("level") == "error"]
    validation_status = "invalid" if error_msgs else ("warning" if messages else "valid")
    return before, after, diff, validation_status, messages if messages else None


async def generate_variation_preview(
    db: AsyncSession,
    organization_id: str,
    variation_job_id: str,
) -> BulkEditVariationJob:
    job_q = await db.execute(
        select(BulkEditVariationJob).where(
            BulkEditVariationJob.id == variation_job_id,
            BulkEditVariationJob.organization_id == organization_id,
        )
    )
    job = job_q.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Variation job not found.")

    if job.status not in ("draft", "preview_ready"):
        raise HTTPException(status_code=400, detail=f"Cannot preview job with status '{job.status}'.")

    listing_ids: list[str] = job.selected_listing_ids or []
    operation_type: str = job.operation_type
    operation_payload: dict[str, Any] = job.operation_payload or {}

    # Clear existing preview items
    await db.execute(
        sa_delete(BulkEditVariationPreviewItem).where(
            BulkEditVariationPreviewItem.variation_job_id == variation_job_id
        )
    )
    await db.flush()

    listings_q = await db.execute(
        select(Listing).where(
            Listing.id.in_(listing_ids),
            Listing.organization_id == organization_id,
        )
    )
    listings = {l.id: l for l in listings_q.scalars().all()}

    preview_count = 0
    for listing_id in listing_ids:
        listing = listings.get(listing_id)
        if not listing:
            continue

        vars_q = await db.execute(
            select(ListingVariation).where(ListingVariation.listing_id == listing.id)
        )
        variations = list(vars_q.scalars().all())

        before, after, diff, v_status, v_msgs = build_variation_preview_for_listing(
            listing, variations, operation_type, operation_payload
        )

        preview_item = BulkEditVariationPreviewItem(
            organization_id=organization_id,
            variation_job_id=variation_job_id,
            listing_id=listing.id,
            etsy_listing_id=listing.etsy_listing_id,
            listing_title=listing.title,
            before_variations=before,
            after_variations=after,
            diff=diff,
            validation_status=v_status,
            validation_messages=v_msgs,
        )
        db.add(preview_item)
        preview_count += 1

    job.status = "preview_ready"
    job.preview_count = preview_count
    job.preview_generated_at = datetime.now(timezone.utc)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


# ── Apply ─────────────────────────────────────────────────────────────────────

async def apply_variation_job(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    variation_job_id: str,
) -> BulkEditVariationJob:
    job_q = await db.execute(
        select(BulkEditVariationJob).where(
            BulkEditVariationJob.id == variation_job_id,
            BulkEditVariationJob.organization_id == organization_id,
        )
    )
    job = job_q.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Variation job not found.")

    if job.status != "preview_ready":
        raise HTTPException(
            status_code=400,
            detail=f"Job cannot be applied: status is '{job.status}'. Must be 'preview_ready'.",
        )

    if not settings.is_etsy_configured():
        raise HTTPException(status_code=503, detail="Etsy integration not configured. Set ETSY_CLIENT_ID.")

    # Check for invalid preview items
    invalid_q = await db.execute(
        select(func.count()).where(
            BulkEditVariationPreviewItem.variation_job_id == variation_job_id,
            BulkEditVariationPreviewItem.validation_status == "invalid",
        )
    )
    invalid_count = invalid_q.scalar_one()
    if invalid_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot apply: {invalid_count} invalid preview item(s). Fix or remove them first.",
        )

    # Load preview items
    previews_q = await db.execute(
        select(BulkEditVariationPreviewItem).where(
            BulkEditVariationPreviewItem.variation_job_id == variation_job_id,
            BulkEditVariationPreviewItem.organization_id == organization_id,
        )
    )
    preview_items = list(previews_q.scalars().all())

    # Load listings + shops + tokens
    listing_ids = [pi.listing_id for pi in preview_items]
    listings_q = await db.execute(
        select(Listing).where(Listing.id.in_(listing_ids), Listing.organization_id == organization_id)
    )
    listings_map = {l.id: l for l in listings_q.scalars().all()}

    shop_ids = list({l.etsy_shop_id for l in listings_map.values()})
    shops_q = await db.execute(select(EtsyShop).where(EtsyShop.id.in_(shop_ids)))
    shops_map = {s.id: s for s in shops_q.scalars().all()}

    access_tokens: dict[str, str] = {}
    for shop_id, shop in shops_map.items():
        try:
            token = await get_valid_etsy_access_token(shop, db)
            access_tokens[shop_id] = token
        except Exception as e:
            logger.warning("No token for shop %s: %s", shop_id, e)

    # Mark running
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    db.add(job)
    await db.flush()

    await _audit(
        db, org_id=organization_id, user_id=user_id,
        event_type="bulk_edit_variation_job_started",
        entity_id=variation_job_id,
        message=f"Variation job {variation_job_id} started. operation={job.operation_type}, listings={len(preview_items)}.",
        extra_data={"variation_job_id": variation_job_id, "operation_type": job.operation_type, "total": len(preview_items)},
    )
    await db.commit()

    success_count = 0
    failure_count = 0
    skipped_count = 0

    for preview_item in preview_items:
        now = datetime.now(timezone.utc)
        listing = listings_map.get(preview_item.listing_id)

        if not listing:
            skipped_count += 1
            result = BulkEditVariationResult(
                organization_id=organization_id,
                variation_job_id=variation_job_id,
                listing_id=preview_item.listing_id,
                etsy_listing_id=preview_item.etsy_listing_id,
                status="skipped",
                error_message="Listing not found.",
                attempted_at=now,
                completed_at=now,
            )
            db.add(result)
            await db.flush()
            continue

        access_token = access_tokens.get(listing.etsy_shop_id)
        if not access_token:
            skipped_count += 1
            result = BulkEditVariationResult(
                organization_id=organization_id,
                variation_job_id=variation_job_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                status="skipped",
                error_message="No valid Etsy access token for this shop.",
                attempted_at=now,
                completed_at=now,
            )
            db.add(result)
            await db.flush()
            continue

        shop = shops_map.get(listing.etsy_shop_id)
        if not shop:
            skipped_count += 1
            result = BulkEditVariationResult(
                organization_id=organization_id,
                variation_job_id=variation_job_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                status="skipped",
                error_message="Shop not found.",
                attempted_at=now,
                completed_at=now,
            )
            db.add(result)
            await db.flush()
            continue

        # Load local variations for snapshot
        vars_q = await db.execute(
            select(ListingVariation).where(ListingVariation.listing_id == listing.id)
        )
        local_variations = list(vars_q.scalars().all())
        local_snap = extract_local_variation_snapshot(local_variations)

        # Fetch Etsy inventory BEFORE writing (fetch-patch-put pattern)
        try:
            etsy_inventory_raw = await fetch_etsy_listing_inventory(
                access_token=access_token,
                shop_etsy_id=shop.etsy_shop_id,
                listing_etsy_id=listing.etsy_listing_id,
            )
        except EtsyVariationWriteError as e:
            failure_count += 1
            result = BulkEditVariationResult(
                organization_id=organization_id,
                variation_job_id=variation_job_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                status="failed",
                error_message=f"Inventory fetch failed: {e.message}",
                attempted_at=now,
                completed_at=datetime.now(timezone.utc),
            )
            db.add(result)
            await db.flush()
            continue

        # Create backup snapshot BEFORE write
        snapshot = ListingVariationBackupSnapshot(
            organization_id=organization_id,
            variation_job_id=variation_job_id,
            listing_id=listing.id,
            etsy_shop_id=listing.etsy_shop_id,
            etsy_listing_id=listing.etsy_listing_id,
            snapshot_type="pre_variation_write",
            local_variations_snapshot=local_snap,
            etsy_inventory_snapshot=etsy_inventory_raw,
            created_by_user_id=user_id,
        )
        db.add(snapshot)
        await db.flush()

        # Patch inventory tree in memory
        normalized = normalize_etsy_inventory_tree(etsy_inventory_raw)
        try:
            patched_tree = patch_inventory_tree_for_variation_operation(
                normalized, job.operation_type, job.operation_payload or {}
            )
        except EtsyVariationWriteError as e:
            failure_count += 1
            result = BulkEditVariationResult(
                organization_id=organization_id,
                variation_job_id=variation_job_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                status="failed",
                error_message=f"Inventory patch error: {e.message}",
                request_payload={"normalized_inventory": normalized},
                attempted_at=now,
                completed_at=datetime.now(timezone.utc),
            )
            db.add(result)
            await db.flush()
            continue

        # PUT full patched tree to Etsy
        result = BulkEditVariationResult(
            organization_id=organization_id,
            variation_job_id=variation_job_id,
            listing_id=listing.id,
            etsy_listing_id=listing.etsy_listing_id,
            status="pending",
            request_payload={"inventory": patched_tree},
            attempted_at=now,
        )
        db.add(result)
        await db.flush()

        try:
            etsy_response = await put_etsy_listing_inventory(
                access_token=access_token,
                shop_etsy_id=shop.etsy_shop_id,
                listing_etsy_id=listing.etsy_listing_id,
                payload=patched_tree,
            )
            result.status = "success"
            result.response_payload = etsy_response
            result.completed_at = datetime.now(timezone.utc)
            success_count += 1

            # Update local ListingVariation rows ONLY after Etsy success
            await _update_local_variations(
                db, listing, preview_item.after_variations or []
            )

        except EtsyVariationWriteError as e:
            result.status = "failed"
            result.error_message = e.message
            result.response_payload = e.response_body
            result.completed_at = datetime.now(timezone.utc)
            failure_count += 1
            logger.warning(
                "Variation write failed for listing %s: %s",
                listing.etsy_listing_id, e.message,
            )

        await db.flush()

    # Finalize job
    job.success_count = success_count
    job.failure_count = failure_count
    job.skipped_count = skipped_count
    job.finished_at = datetime.now(timezone.utc)
    job.status = (
        "completed" if failure_count == 0 and skipped_count == 0
        else "completed_with_errors" if success_count > 0
        else "failed"
    )
    db.add(job)

    await _audit(
        db, org_id=organization_id, user_id=user_id,
        event_type="bulk_edit_variation_job_finished",
        entity_id=variation_job_id,
        message=(
            f"Variation job {variation_job_id} finished. "
            f"success={success_count}, failure={failure_count}, skipped={skipped_count}."
        ),
        extra_data={
            "variation_job_id": variation_job_id,
            "operation_type": job.operation_type,
            "success_count": success_count,
            "failure_count": failure_count,
            "skipped_count": skipped_count,
            "status": job.status,
        },
    )
    await db.commit()
    await db.refresh(job)
    return job


async def _update_local_variations(
    db: AsyncSession,
    listing: Listing,
    after_variations: list[dict[str, Any]],
) -> None:
    """Update local ListingVariation rows to match after_variations from preview."""
    vars_q = await db.execute(
        select(ListingVariation).where(ListingVariation.listing_id == listing.id)
    )
    local_vars = list(vars_q.scalars().all())

    for i, after_v in enumerate(after_variations):
        if i < len(local_vars):
            v = local_vars[i]
            if "price_amount" in after_v:
                v.price_amount = after_v["price_amount"]
            if "quantity" in after_v:
                v.quantity = after_v["quantity"]
            if "sku" in after_v:
                v.sku = after_v["sku"]
            if "is_available" in after_v:
                v.is_available = after_v["is_available"]

    await db.flush()


# ── Query helpers ─────────────────────────────────────────────────────────────

async def list_variation_jobs(
    db: AsyncSession,
    organization_id: str,
) -> list[BulkEditVariationJob]:
    q = await db.execute(
        select(BulkEditVariationJob).where(
            BulkEditVariationJob.organization_id == organization_id,
        ).order_by(BulkEditVariationJob.created_at.desc())
    )
    return list(q.scalars().all())


async def get_variation_job(
    db: AsyncSession,
    organization_id: str,
    variation_job_id: str,
) -> BulkEditVariationJob:
    q = await db.execute(
        select(BulkEditVariationJob).where(
            BulkEditVariationJob.id == variation_job_id,
            BulkEditVariationJob.organization_id == organization_id,
        )
    )
    job = q.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Variation job not found.")
    return job


async def get_variation_preview(
    db: AsyncSession,
    organization_id: str,
    variation_job_id: str,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    await get_variation_job(db, organization_id, variation_job_id)

    base_q = select(BulkEditVariationPreviewItem).where(
        BulkEditVariationPreviewItem.variation_job_id == variation_job_id,
        BulkEditVariationPreviewItem.organization_id == organization_id,
    )
    count_q = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_q.scalar_one()

    paged_q = base_q.order_by(BulkEditVariationPreviewItem.created_at.asc()).offset((page - 1) * per_page).limit(per_page)
    items = list((await db.execute(paged_q)).scalars().all())

    return {"items": items, "page": page, "per_page": per_page, "total": total, "variation_job_id": variation_job_id}


async def get_variation_results(
    db: AsyncSession,
    organization_id: str,
    variation_job_id: str,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    await get_variation_job(db, organization_id, variation_job_id)

    base_q = select(BulkEditVariationResult).where(
        BulkEditVariationResult.variation_job_id == variation_job_id,
        BulkEditVariationResult.organization_id == organization_id,
    )
    count_q = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_q.scalar_one()

    paged_q = base_q.order_by(BulkEditVariationResult.created_at.asc()).offset((page - 1) * per_page).limit(per_page)
    items = list((await db.execute(paged_q)).scalars().all())

    return {"items": items, "page": page, "per_page": per_page, "total": total, "variation_job_id": variation_job_id}


async def get_variation_backups(
    db: AsyncSession,
    organization_id: str,
    variation_job_id: str,
) -> list[ListingVariationBackupSnapshot]:
    await get_variation_job(db, organization_id, variation_job_id)

    q = await db.execute(
        select(ListingVariationBackupSnapshot).where(
            ListingVariationBackupSnapshot.variation_job_id == variation_job_id,
            ListingVariationBackupSnapshot.organization_id == organization_id,
        ).order_by(ListingVariationBackupSnapshot.created_at.asc())
    )
    return list(q.scalars().all())
