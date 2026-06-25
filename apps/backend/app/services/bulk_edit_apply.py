"""
Bulk Edit Apply Service — Sprint 10.

Safety contract enforced before any Etsy write:
  1. Session must be preview_ready
  2. No invalid preview items
  3. Etsy client ID must be configured
  4. User must be within plan limits
  5. Backup snapshot created per listing before write
  6. Local Listing row updated ONLY after ALL required Etsy writes succeed
  7. Audit log written for every apply job start/finish

Write flow per listing:
  a. Build listing PATCH payload (text/bool fields via PATCH /listings/{id})
  b. Build inventory PUT payload (price/quantity via PUT /shops/{s}/listings/{l}/inventory)
  c. If listing PATCH exists: execute first; on failure → mark failed, skip inventory
  d. If inventory PUT exists: execute after listing PATCH; on failure → mark failed
     (listing PATCH already happened externally — documented partial write caveat)
  e. Local Listing updated only after ALL writes succeed

Variation listings: inventory write skipped (Sprint 11); text fields still applied.
Photo/video writes: deferred to Sprint 11.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.bulk_edit_apply_job import BulkEditApplyJob
from app.models.bulk_edit_apply_result import BulkEditApplyResult
from app.models.bulk_edit_preview_item import BulkEditPreviewItem
from app.models.bulk_edit_session import BulkEditSession
from app.models.etsy_shop import EtsyShop
from app.models.listing import Listing
from app.models.listing_backup_snapshot import ListingBackupSnapshot
from app.services.billing import (
    check_usage_limit,
    increment_usage,
    ensure_subscription_exists,
)
from app.services.bulk_edit import get_bulk_edit_session, build_before_data
from app.services.etsy_sync import get_valid_etsy_access_token
from app.services.etsy_write import (
    build_etsy_patch_payload,
    build_etsy_inventory_payload,
    patch_etsy_listing,
    patch_etsy_listing_inventory,
    EtsyWriteError,
)

logger = logging.getLogger(__name__)

# Fields in after_data that map back to Listing columns
_AFTER_TO_LISTING: dict[str, str] = {
    "title": "title",
    "description": "description",
    "sku": "sku",
    "section_id": "section_id",
    "taxonomy_id": "taxonomy_id",
    "personalization_instructions": "personalization_instructions",
    "is_personalizable": "is_personalizable",
    "is_customizable": "is_customizable",
    "personalization_is_required": "personalization_is_required",
    "has_variations": "has_variations",
    "processing_min": "processing_min",
    "processing_max": "processing_max",
    "personalization_char_count_max": "personalization_char_count_max",
    "item_weight": "item_weight",
    "item_length": "item_length",
    "item_width": "item_width",
    "item_height": "item_height",
    "tags": "tags",
    "materials": "materials",
}

# price_amount and quantity excluded — not written via PATCH /listings


async def _write_audit_log(
    db: AsyncSession,
    org_id: str,
    user_id: str | None,
    event_type: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    message: str | None = None,
    metadata: Any = None,
) -> None:
    log = AuditLog(
        organization_id=org_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        message=message,
        extra_data=metadata,
    )
    db.add(log)
    await db.flush()


async def apply_bulk_edit_session(
    db: AsyncSession,
    session_id: str,
    organization_id: str,
    user_id: str,
) -> BulkEditApplyJob:
    """
    Orchestrate safe Etsy write for a previewed bulk edit session.
    Returns the completed BulkEditApplyJob.
    """
    # 1. Load and validate session
    session = await get_bulk_edit_session(db, session_id, organization_id)

    if session.status != "preview_ready":
        raise HTTPException(
            status_code=400,
            detail=f"Session must be in 'preview_ready' status to apply. Current status: '{session.status}'.",
        )

    # 2. Check for invalid preview items
    invalid_count_result = await db.execute(
        select(func.count()).select_from(
            select(BulkEditPreviewItem).where(
                BulkEditPreviewItem.bulk_edit_session_id == session_id,
                BulkEditPreviewItem.validation_status == "invalid",
            ).subquery()
        )
    )
    invalid_count = invalid_count_result.scalar_one()
    if invalid_count > 0:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot apply: {invalid_count} listing(s) have validation errors. Fix or remove invalid listings first.",
        )

    # 3. Check Etsy is configured
    if not settings.is_etsy_configured():
        raise HTTPException(
            status_code=503,
            detail="Etsy integration is not configured. Set ETSY_CLIENT_ID in environment.",
        )

    # 4. Check subscription / usage limit
    within_limit = await check_usage_limit(organization_id, "bulk_edits_used", db)
    if not within_limit:
        raise HTTPException(
            status_code=402,
            detail="Monthly bulk edit limit reached. Upgrade your plan to continue.",
        )

    # 5. Load preview items
    items_result = await db.execute(
        select(BulkEditPreviewItem).where(
            BulkEditPreviewItem.bulk_edit_session_id == session_id,
        )
    )
    preview_items = list(items_result.scalars().all())

    if not preview_items:
        raise HTTPException(
            status_code=400,
            detail="No preview items found. Generate preview first.",
        )

    # 6. Create apply job
    job = BulkEditApplyJob(
        organization_id=organization_id,
        bulk_edit_session_id=session_id,
        created_by_user_id=user_id,
        status="running",
        total_items=len(preview_items),
        success_count=0,
        failure_count=0,
        skipped_count=0,
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()

    await _write_audit_log(
        db,
        org_id=organization_id,
        user_id=user_id,
        event_type="bulk_edit_apply_started",
        entity_type="bulk_edit_session",
        entity_id=session_id,
        message=f"Apply job {job.id} started for session {session_id}. Items: {len(preview_items)}.",
        metadata={"apply_job_id": job.id, "total_items": len(preview_items)},
    )
    await db.commit()

    # 7. Load shop + token once (all listings in a session share one org → one shop per session)
    listing_ids = [item.listing_id for item in preview_items]
    listings_result = await db.execute(
        select(Listing).where(
            Listing.id.in_(listing_ids),
            Listing.organization_id == organization_id,
        )
    )
    listings_map: dict[str, Listing] = {l.id: l for l in listings_result.scalars().all()}

    # Get all shop IDs from the listings, then load shops
    shop_ids = list({l.etsy_shop_id for l in listings_map.values()})
    shops_result = await db.execute(
        select(EtsyShop).where(EtsyShop.id.in_(shop_ids))
    )
    shops_map: dict[str, EtsyShop] = {s.id: s for s in shops_result.scalars().all()}

    # Pre-fetch access tokens per shop
    access_tokens: dict[str, str] = {}
    for shop_id, shop in shops_map.items():
        try:
            token = await get_valid_etsy_access_token(shop, db)
            access_tokens[shop_id] = token
        except Exception as e:
            logger.warning("Could not get token for shop %s: %s", shop_id, e)

    # 8. Apply per listing
    success_count = 0
    failure_count = 0
    skipped_count = 0

    for preview_item in preview_items:
        listing = listings_map.get(preview_item.listing_id)
        if not listing:
            skipped_count += 1
            result = BulkEditApplyResult(
                organization_id=organization_id,
                apply_job_id=job.id,
                bulk_edit_session_id=session_id,
                listing_id=preview_item.listing_id,
                etsy_listing_id=preview_item.listing_id,
                status="skipped",
                error_message="Listing not found in database.",
                attempted_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            db.add(result)
            await db.flush()
            continue

        access_token = access_tokens.get(listing.etsy_shop_id)
        if not access_token:
            skipped_count += 1
            result = BulkEditApplyResult(
                organization_id=organization_id,
                apply_job_id=job.id,
                bulk_edit_session_id=session_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                status="skipped",
                error_message="No valid Etsy access token for this shop.",
                attempted_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            db.add(result)
            await db.flush()
            continue

        shop = shops_map.get(listing.etsy_shop_id)

        # 8a. Create backup snapshot before any write
        snapshot_data = build_before_data(listing)
        snapshot = ListingBackupSnapshot(
            organization_id=organization_id,
            bulk_edit_session_id=session_id,
            listing_id=listing.id,
            etsy_shop_id=listing.etsy_shop_id,
            etsy_listing_id=listing.etsy_listing_id,
            snapshot_type="pre_write",
            snapshot_data=snapshot_data,
            created_by_user_id=user_id,
        )
        db.add(snapshot)
        await db.flush()

        # 8b. Build payloads
        diff: dict = preview_item.diff or {}
        after_data: dict = preview_item.after_data or {}

        listing_payload = build_etsy_patch_payload(diff)
        inventory_payload = build_etsy_inventory_payload(listing, after_data)

        # Variation inventory skip — text patch may still proceed
        inventory_skipped = listing.has_variations and ("price_amount" in diff or "quantity" in diff)
        inventory_skip_reason = "Variation inventory support deferred to Sprint 11" if inventory_skipped else None

        # Build structured request payload
        if inventory_payload or inventory_skipped:
            req_payload: Any = {}
            if listing_payload:
                req_payload["listing_patch"] = listing_payload
            if inventory_payload:
                req_payload["inventory_patch"] = inventory_payload
            if inventory_skipped:
                req_payload["inventory_skipped"] = True
                req_payload["inventory_skip_reason"] = inventory_skip_reason
        else:
            req_payload = listing_payload

        result = BulkEditApplyResult(
            organization_id=organization_id,
            apply_job_id=job.id,
            bulk_edit_session_id=session_id,
            listing_id=listing.id,
            etsy_listing_id=listing.etsy_listing_id,
            status="pending",
            request_payload=req_payload,
            backup_snapshot_id=snapshot.id,
            attempted_at=datetime.now(timezone.utc),
        )
        db.add(result)
        await db.flush()

        # Nothing to write
        if not listing_payload and not inventory_payload:
            result.status = "skipped"
            result.error_message = inventory_skip_reason or "No patchable fields in diff."
            result.completed_at = datetime.now(timezone.utc)
            skipped_count += 1
            await db.flush()
            continue

        # 8c. Write text/bool fields (listing PATCH)
        listing_resp: Any = None
        if listing_payload:
            try:
                listing_resp = await patch_etsy_listing(
                    access_token=access_token,
                    etsy_listing_id=listing.etsy_listing_id,
                    payload=listing_payload,
                )
            except EtsyWriteError as e:
                result.status = "failed"
                result.error_message = e.message
                result.response_payload = {"listing_patch_error": {"message": e.message, "response": e.response_body}} if inventory_payload else e.response_body
                result.completed_at = datetime.now(timezone.utc)
                failure_count += 1
                logger.warning("Etsy listing PATCH failed for %s: %s", listing.etsy_listing_id, e.message)
                await db.flush()
                continue
            except Exception as e:
                result.status = "failed"
                result.error_message = str(e)
                result.completed_at = datetime.now(timezone.utc)
                failure_count += 1
                logger.exception("Unexpected error on listing PATCH %s", listing.etsy_listing_id)
                await db.flush()
                continue

        # 8d. Write price/quantity (inventory PUT)
        inventory_resp: Any = None
        if inventory_payload and shop:
            try:
                inventory_resp = await patch_etsy_listing_inventory(
                    access_token=access_token,
                    shop_etsy_id=shop.etsy_shop_id,
                    listing_etsy_id=listing.etsy_listing_id,
                    payload=inventory_payload,
                )
            except EtsyWriteError as e:
                result.status = "failed"
                result.error_message = f"Inventory write failed: {e.message}"
                resp_struct: dict[str, Any] = {}
                if listing_resp is not None:
                    resp_struct["listing_patch"] = listing_resp
                resp_struct["inventory_patch_error"] = {"message": e.message, "response": e.response_body}
                result.response_payload = resp_struct
                result.completed_at = datetime.now(timezone.utc)
                failure_count += 1
                logger.warning("Etsy inventory PUT failed for %s: %s (listing PATCH already applied)", listing.etsy_listing_id, e.message)
                await db.flush()
                continue
            except Exception as e:
                result.status = "failed"
                result.error_message = f"Inventory write error: {str(e)}"
                result.completed_at = datetime.now(timezone.utc)
                failure_count += 1
                logger.exception("Unexpected error on inventory PUT %s", listing.etsy_listing_id)
                await db.flush()
                continue

        # 8e. All writes succeeded — build response payload
        resp_payload: Any
        if inventory_resp is not None or inventory_skipped:
            resp_payload = {}
            if listing_resp is not None:
                resp_payload["listing_patch"] = listing_resp
            if inventory_resp is not None:
                resp_payload["inventory_patch"] = inventory_resp
            if inventory_skipped:
                resp_payload["inventory_skipped"] = True
                resp_payload["inventory_skip_reason"] = inventory_skip_reason
        else:
            resp_payload = listing_resp

        result.response_payload = resp_payload
        result.status = "success"
        result.completed_at = datetime.now(timezone.utc)

        # 8f. Update local Listing — text/bool fields only after all writes succeed
        for after_field, listing_attr in _AFTER_TO_LISTING.items():
            if after_field in diff:
                setattr(listing, listing_attr, after_data.get(after_field))

        # Update price/quantity only after inventory write succeeds
        if inventory_resp is not None:
            if "price_amount" in diff:
                listing.price_amount = after_data.get("price_amount")
            if "price_divisor" in diff:
                listing.price_divisor = after_data.get("price_divisor")
            if "quantity" in diff:
                listing.quantity = after_data.get("quantity")

        db.add(listing)
        success_count += 1
        await db.flush()

    # 9. Finalize job
    job.success_count = success_count
    job.failure_count = failure_count
    job.skipped_count = skipped_count
    job.finished_at = datetime.now(timezone.utc)
    job.status = (
        "completed" if failure_count == 0 and skipped_count == 0
        else "completed_with_errors" if success_count > 0
        else "failed"
    )

    # 10. Update session applied_at if any successes
    if success_count > 0:
        session.applied_at = datetime.now(timezone.utc)
        db.add(session)

    # 11. Increment usage counter (count by number of listings actually written)
    if success_count > 0:
        await increment_usage(organization_id, "bulk_edits_used", db, amount=success_count)

    await _write_audit_log(
        db,
        org_id=organization_id,
        user_id=user_id,
        event_type="bulk_edit_apply_finished",
        entity_type="bulk_edit_apply_job",
        entity_id=job.id,
        message=(
            f"Apply job {job.id} finished. "
            f"success={success_count}, failure={failure_count}, skipped={skipped_count}."
        ),
        metadata={
            "apply_job_id": job.id,
            "session_id": session_id,
            "success_count": success_count,
            "failure_count": failure_count,
            "skipped_count": skipped_count,
            "status": job.status,
        },
    )

    await db.commit()
    await db.refresh(job)
    return job


async def get_apply_job(
    db: AsyncSession,
    job_id: str,
    organization_id: str,
) -> BulkEditApplyJob:
    result = await db.execute(
        select(BulkEditApplyJob).where(
            BulkEditApplyJob.id == job_id,
            BulkEditApplyJob.organization_id == organization_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Apply job not found.")
    return job


async def list_apply_jobs_for_session(
    db: AsyncSession,
    session_id: str,
    organization_id: str,
) -> list[BulkEditApplyJob]:
    result = await db.execute(
        select(BulkEditApplyJob).where(
            BulkEditApplyJob.bulk_edit_session_id == session_id,
            BulkEditApplyJob.organization_id == organization_id,
        ).order_by(BulkEditApplyJob.created_at.desc())
    )
    return list(result.scalars().all())


async def get_apply_results(
    db: AsyncSession,
    job_id: str,
    organization_id: str,
) -> list[BulkEditApplyResult]:
    result = await db.execute(
        select(BulkEditApplyResult).where(
            BulkEditApplyResult.apply_job_id == job_id,
            BulkEditApplyResult.organization_id == organization_id,
        ).order_by(BulkEditApplyResult.created_at.asc())
    )
    return list(result.scalars().all())


async def list_backup_snapshots_for_session(
    db: AsyncSession,
    session_id: str,
    organization_id: str,
) -> list[ListingBackupSnapshot]:
    result = await db.execute(
        select(ListingBackupSnapshot).where(
            ListingBackupSnapshot.bulk_edit_session_id == session_id,
            ListingBackupSnapshot.organization_id == organization_id,
        ).order_by(ListingBackupSnapshot.created_at.desc())
    )
    return list(result.scalars().all())
