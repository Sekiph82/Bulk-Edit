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
  a. Build listing PATCH payload (text/bool fields via PATCH /shops/{s}/listings/{l})
  b. If price/quantity changed: fetch-patch-put the full Etsy inventory tree
     (GET /listings/{l}/inventory, mutate only the changed field(s), PUT the
     full tree back) — see etsy_write.apply_single_listing_price_quantity()
  c. If listing PATCH exists: execute first; on failure → mark failed, skip inventory
  d. If inventory write needed: execute after listing PATCH; on failure → mark failed
     (listing PATCH already happened externally — documented partial write caveat)
  e. Local Listing updated only after ALL writes succeed

Variation listings: inventory write skipped (Sprint 11); text fields still applied.
Photo/video writes: deferred to Sprint 11.
"""
import csv
import io
import json
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
from app.models.bulk_edit_change import BulkEditChange
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
    apply_single_listing_price_quantity,
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


async def _write_field_audit_trail(
    db: AsyncSession,
    org_id: str,
    user_id: str | None,
    shop_etsy_id: str | None,
    listing: Listing,
    apply_job_id: str,
    session_id: str,
    diff: dict[str, Any],
    field_operations: dict[str, str],
    result_status: str,
    error_message: str | None,
) -> None:
    """M06.04 per-item write audit trail — one AuditLog row per field this
    apply's diff actually touched (not per listing): BulkEditApplyResult is
    per-listing and can't distinguish which of several changed fields
    succeeded independently, since Etsy's PATCH covers every changed field
    in one call, so this records the same listing-level result_status
    against each field. Before/after values and a sanitized, size-limited
    error live in extra_data — never a raw Etsy response body, token, or
    header."""
    safe_error = (error_message or "")[:500] if error_message else None
    for field_name, change in diff.items():
        db.add(AuditLog(
            organization_id=org_id,
            user_id=user_id,
            event_type="bulk_edit_field_write",
            entity_type="listing",
            entity_id=listing.id,
            apply_job_id=apply_job_id,
            field_name=field_name,
            result_status=result_status,
            message=f"{field_name} on listing {listing.etsy_listing_id}: {result_status}",
            extra_data={
                "etsy_shop_id": shop_etsy_id,
                "etsy_listing_id": listing.etsy_listing_id,
                "bulk_edit_session_id": session_id,
                "operation": field_operations.get(field_name),
                "before": change.get("before") if isinstance(change, dict) else None,
                "after": change.get("after") if isinstance(change, dict) else None,
                "error_message": safe_error,
            },
        ))
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

    # 4. Check subscription / usage limit (effective plan -- comp-grant aware)
    within_limit, current_usage, usage_limit = await check_usage_limit(
        organization_id, "bulk_edits_used", db
    )
    if not within_limit:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Monthly bulk edit limit reached. Used {current_usage} of {usage_limit} "
                "this month. Upgrade your plan to continue."
            ),
        )

    # 5. Load preview items
    items_result = await db.execute(
        select(BulkEditPreviewItem).where(
            BulkEditPreviewItem.bulk_edit_session_id == session_id,
        )
    )
    preview_items = list(items_result.scalars().all())

    # M06.04: field_name -> operation, for the per-field audit trail below.
    changes_result = await db.execute(
        select(BulkEditChange.field_name, BulkEditChange.operation).where(
            BulkEditChange.bulk_edit_session_id == session_id
        )
    )
    field_operations: dict[str, str] = {row[0]: row[1] for row in changes_result.all()}

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
            await _write_field_audit_trail(
                db, organization_id, user_id, shop.etsy_shop_id if shop else None, listing,
                job.id, session_id, diff, field_operations, "skipped", result.error_message,
            )
            continue

        # 8c. Write text/bool fields (listing PATCH)
        listing_resp: Any = None
        if listing_payload and shop:
            try:
                listing_resp = await patch_etsy_listing(
                    access_token=access_token,
                    shop_etsy_id=shop.etsy_shop_id,
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
                await _write_field_audit_trail(
                    db, organization_id, user_id, shop.etsy_shop_id if shop else None, listing,
                    job.id, session_id, diff, field_operations, "failed", e.message,
                )
                continue
            except Exception as e:
                result.status = "failed"
                result.error_message = str(e)
                result.completed_at = datetime.now(timezone.utc)
                failure_count += 1
                logger.exception("Unexpected error on listing PATCH %s", listing.etsy_listing_id)
                await _write_field_audit_trail(
                    db, organization_id, user_id, shop.etsy_shop_id if shop else None, listing,
                    job.id, session_id, diff, field_operations, "failed", str(e),
                )
                continue

        # 8d. Write price/quantity (fetch-patch-put inventory tree)
        inventory_resp: Any = None
        if inventory_payload and shop:
            try:
                inventory_resp = await apply_single_listing_price_quantity(
                    access_token=access_token,
                    shop_etsy_id=shop.etsy_shop_id,
                    listing_etsy_id=listing.etsy_listing_id,
                    price_amount=after_data.get("price_amount") if "price_amount" in diff else None,
                    quantity=after_data.get("quantity") if "quantity" in diff else None,
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
                await _write_field_audit_trail(
                    db, organization_id, user_id, shop.etsy_shop_id if shop else None, listing,
                    job.id, session_id, diff, field_operations, "failed", result.error_message,
                )
                continue
            except Exception as e:
                result.status = "failed"
                result.error_message = f"Inventory write error: {str(e)}"
                result.completed_at = datetime.now(timezone.utc)
                failure_count += 1
                logger.exception("Unexpected error on inventory PUT %s", listing.etsy_listing_id)
                await _write_field_audit_trail(
                    db, organization_id, user_id, shop.etsy_shop_id if shop else None, listing,
                    job.id, session_id, diff, field_operations, "failed", result.error_message,
                )
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
        await _write_field_audit_trail(
            db, organization_id, user_id, shop.etsy_shop_id if shop else None, listing,
            job.id, session_id, diff, field_operations, "success", None,
        )

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


async def list_apply_jobs_for_org(
    db: AsyncSession,
    organization_id: str,
    page: int = 1,
    per_page: int = 50,
    status: str | None = None,
) -> tuple[list[BulkEditApplyJob], int]:
    """
    Org-wide apply job history, across every session — used by Magic Revert
    History (/magic-revert) and Activity & Audit (/account/activity).
    list_apply_jobs_for_session() above is scoped to one session and isn't
    useful for a customer who doesn't know/track session ids.
    """
    query = select(BulkEditApplyJob).where(BulkEditApplyJob.organization_id == organization_id)
    if status:
        query = query.where(BulkEditApplyJob.status == status)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(BulkEditApplyJob.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return list(result.scalars().all()), total


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


def _field_audit_trail_query(
    organization_id: str,
    apply_job_id: str | None = None,
    listing_id: str | None = None,
    field_name: str | None = None,
    result_status: str | None = None,
    revert_status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    """Shared, unordered/unpaginated filter builder for the M06.04 audit
    trail — reused by both the paginated list endpoint and the CSV export,
    so the two can never silently drift apart on what a given filter set
    matches.

    `revert_status="not_reverted"` is a sentinel value (not a real DB value)
    meaning "this row has never been linked to a revert job" — i.e.
    `AuditLog.revert_status IS NULL`. Every other value is matched exactly
    against the real RevertJob.status value the row was last linked to.
    There is deliberately no "conflict" sentinel here: `AuditLog.revert_status`
    is set from the *revert job's* overall status (see revert_apply_job()'s
    bulk UPDATE), not from the per-listing RevertResult.status a specific
    conflict lives on — a row's revert_status cannot truthfully answer
    "was THIS field's revert a conflict," only "what happened to the revert
    job this field was part of." Filtering on conflict would require joining
    to RevertResult, which does not exist yet — see DECISIONS.md."""
    query = select(AuditLog).where(
        AuditLog.organization_id == organization_id,
        AuditLog.event_type == "bulk_edit_field_write",
    )
    if apply_job_id:
        query = query.where(AuditLog.apply_job_id == apply_job_id)
    if listing_id:
        query = query.where(AuditLog.entity_id == listing_id)
    if field_name:
        query = query.where(AuditLog.field_name == field_name)
    if result_status:
        query = query.where(AuditLog.result_status == result_status)
    if revert_status == "not_reverted":
        query = query.where(AuditLog.revert_status.is_(None))
    elif revert_status:
        query = query.where(AuditLog.revert_status == revert_status)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)
    return query


async def list_field_audit_trail(
    db: AsyncSession,
    organization_id: str,
    apply_job_id: str | None = None,
    listing_id: str | None = None,
    field_name: str | None = None,
    result_status: str | None = None,
    revert_status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[AuditLog], int]:
    """M06.04: searchable per-item write audit trail. Org-scoped always —
    cross-org isolation is enforced by the organization_id filter below, not
    by the caller."""
    query = _field_audit_trail_query(
        organization_id, apply_job_id, listing_id, field_name,
        result_status, revert_status, date_from, date_to,
    )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return list(result.scalars().all()), total


_AUDIT_EXPORT_HEADERS = [
    "created_at", "organization_id", "user_id", "etsy_shop_id",
    "listing_id", "etsy_listing_id", "field_name", "operation",
    "before", "after", "result_status", "revert_status",
    "apply_job_id", "bulk_edit_session_id", "revert_job_id", "error_message",
]
# ponytail: single-file, non-streamed export capped at this many rows. Add
# real streaming/chunked export if an org's audit trail ever grows past this
# in one filtered request.
_EXPORT_ROW_CAP = 5000
_CSV_VALUE_MAX_LEN = 2000


def _csv_safe_value(value: Any) -> str:
    """Flattens a before/after value for CSV — objects/arrays become compact
    JSON text (never a raw Python repr like "[object Object]"-equivalent),
    everything else is str()'d, and anything implausibly long is truncated.
    These values only ever come from bulk-edit field diffs (title, price,
    tags, etc.) — never tokens/credentials — but length-capping stays as a
    defensive measure against a pathologically large field value."""
    if value is None:
        return ""
    text = json.dumps(value, ensure_ascii=False, default=str) if isinstance(value, (dict, list)) else str(value)
    if len(text) > _CSV_VALUE_MAX_LEN:
        text = text[:_CSV_VALUE_MAX_LEN] + "…(truncated)"
    return text


async def export_field_audit_trail_csv(
    db: AsyncSession,
    organization_id: str,
    apply_job_id: str | None = None,
    listing_id: str | None = None,
    field_name: str | None = None,
    result_status: str | None = None,
    revert_status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> str:
    """M06.04 CSV export — same filters and org-scoping as
    list_field_audit_trail() (shared query builder), just unpaginated up to
    _EXPORT_ROW_CAP. Never includes tokens/OAuth codes/x-api-key/secret env
    values — the only Etsy-facing values ever stored here are bulk-edit
    field diffs (title/price/tags/etc.), not credentials."""
    query = _field_audit_trail_query(
        organization_id, apply_job_id, listing_id, field_name,
        result_status, revert_status, date_from, date_to,
    ).order_by(AuditLog.created_at.desc()).limit(_EXPORT_ROW_CAP)
    result = await db.execute(query)
    rows = list(result.scalars().all())

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_AUDIT_EXPORT_HEADERS)
    writer.writeheader()
    for row in rows:
        extra = row.extra_data if isinstance(row.extra_data, dict) else {}
        writer.writerow({
            "created_at": row.created_at.isoformat() if row.created_at else "",
            "organization_id": row.organization_id,
            "user_id": row.user_id or "",
            "etsy_shop_id": extra.get("etsy_shop_id") or "",
            "listing_id": row.entity_id or "",
            "etsy_listing_id": extra.get("etsy_listing_id") or "",
            "field_name": row.field_name or "",
            "operation": extra.get("operation") or "",
            "before": _csv_safe_value(extra.get("before")),
            "after": _csv_safe_value(extra.get("after")),
            "result_status": row.result_status or "",
            "revert_status": row.revert_status or "",
            "apply_job_id": row.apply_job_id or "",
            "bulk_edit_session_id": extra.get("bulk_edit_session_id") or "",
            "revert_job_id": row.revert_job_id or "",
            "error_message": extra.get("error_message") or "",
        })
    return output.getvalue()
