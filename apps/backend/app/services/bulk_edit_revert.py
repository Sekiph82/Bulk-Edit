"""
Bulk Edit Revert Service — Sprint 10.

Magic Revert: reverts successful Etsy writes from a BulkEditApplyJob
using the ListingBackupSnapshot records created in Sprint 8.

Safety contract:
  1. Apply job must belong to organization
  2. Apply job must be completed or completed_with_errors
  3. No completed/running RevertJob may already exist for this apply job
  4. Only successful BulkEditApplyResult rows are reverted
  5. Every revert write uses the pre-write backup snapshot
  6. Local Listing row updated ONLY after ALL required Etsy revert writes succeed
  7. Audit log written on revert start and completion
  8. Backup snapshots are never deleted
  9. Price/quantity reverted via inventory endpoint (PUT /shops/{s}/listings/{l}/inventory)
     Variation listings: inventory revert skipped (Sprint 11); text fields still reverted.
 10. Photo/video not reverted (deferred to Sprint 11)

Partial write caveat: if text PATCH succeeds but inventory PUT fails, Etsy has reverted text
but not price/quantity. Local DB not updated. Next sync resolves the discrepancy.
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
from app.models.etsy_shop import EtsyShop
from app.models.listing import Listing
from app.models.listing_backup_snapshot import ListingBackupSnapshot
from app.models.revert_job import RevertJob
from app.models.revert_result import RevertResult
from app.services.etsy_sync import get_valid_etsy_access_token
from app.services.etsy_write import (
    build_etsy_patch_payload,
    build_etsy_inventory_payload,
    patch_etsy_listing,
    patch_etsy_listing_inventory,
    EtsyWriteError,
)

logger = logging.getLogger(__name__)

# Fields in snapshot_data that map back to Listing columns (same as apply)
_SNAPSHOT_TO_LISTING: dict[str, str] = {
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


async def _write_audit_log(
    db: AsyncSession,
    org_id: str,
    user_id: str | None,
    event_type: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    message: str | None = None,
    extra_data: Any = None,
) -> None:
    log = AuditLog(
        organization_id=org_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        message=message,
        extra_data=extra_data,
    )
    db.add(log)
    await db.flush()


def build_etsy_revert_payload(snapshot_data: dict[str, Any]) -> dict[str, Any]:
    """
    Build Etsy PATCH payload from snapshot_data (pre-write backup).
    Reuses build_etsy_patch_payload by treating each snapshot field as a "change".
    Price and quantity excluded — use build_etsy_inventory_payload for those.
    """
    diff: dict[str, Any] = {
        field: {"before": None, "after": snapshot_data.get(field)}
        for field in snapshot_data
    }
    return build_etsy_patch_payload(diff)


def update_local_listing_from_snapshot(
    listing: Listing,
    snapshot_data: dict[str, Any],
) -> None:
    """Apply all snapshot fields to local Listing object (in-place)."""
    for snap_field, listing_attr in _SNAPSHOT_TO_LISTING.items():
        if snap_field in snapshot_data:
            setattr(listing, listing_attr, snapshot_data[snap_field])


async def validate_apply_job_revertable(
    db: AsyncSession,
    organization_id: str,
    apply_job_id: str,
) -> BulkEditApplyJob:
    """
    Load and validate apply job is revertable. Returns job on success.
    Raises HTTPException on any validation failure.
    """
    result = await db.execute(
        select(BulkEditApplyJob).where(
            BulkEditApplyJob.id == apply_job_id,
            BulkEditApplyJob.organization_id == organization_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Apply job not found.")

    if job.status not in ("completed", "completed_with_errors"):
        raise HTTPException(
            status_code=400,
            detail=f"Apply job must be 'completed' or 'completed_with_errors' to revert. Current status: '{job.status}'.",
        )

    # Check for existing completed or running revert
    existing_result = await db.execute(
        select(RevertJob).where(
            RevertJob.apply_job_id == apply_job_id,
            RevertJob.organization_id == organization_id,
            RevertJob.status.in_(("completed", "completed_with_errors", "running")),
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Apply job already has a revert job (id={existing.id}, status={existing.status}). Cannot revert twice.",
        )

    return job


async def revert_apply_job(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    apply_job_id: str,
) -> RevertJob:
    """
    Orchestrate revert of a completed apply job.
    Returns finished RevertJob.
    """
    if not settings.is_etsy_configured():
        raise HTTPException(
            status_code=503,
            detail="Etsy integration is not configured. Set ETSY_CLIENT_ID in environment.",
        )

    apply_job = await validate_apply_job_revertable(db, organization_id, apply_job_id)

    # Load only successful apply results
    apply_results_q = await db.execute(
        select(BulkEditApplyResult).where(
            BulkEditApplyResult.apply_job_id == apply_job_id,
            BulkEditApplyResult.organization_id == organization_id,
            BulkEditApplyResult.status == "success",
        )
    )
    apply_results = list(apply_results_q.scalars().all())

    # Create revert job
    revert_job = RevertJob(
        organization_id=organization_id,
        bulk_edit_session_id=apply_job.bulk_edit_session_id,
        apply_job_id=apply_job_id,
        created_by_user_id=user_id,
        status="running",
        total_items=len(apply_results),
        started_at=datetime.now(timezone.utc),
    )
    db.add(revert_job)
    await db.flush()

    await _write_audit_log(
        db,
        org_id=organization_id,
        user_id=user_id,
        event_type="bulk_edit_revert_started",
        entity_type="bulk_edit_apply_job",
        entity_id=apply_job_id,
        message=f"Revert job {revert_job.id} started for apply job {apply_job_id}. Revertable items: {len(apply_results)}.",
        extra_data={"revert_job_id": revert_job.id, "apply_job_id": apply_job_id, "total_items": len(apply_results)},
    )
    await db.commit()

    if not apply_results:
        revert_job.status = "completed"
        revert_job.finished_at = datetime.now(timezone.utc)
        revert_job.skipped_count = 0
        db.add(revert_job)
        await db.commit()
        await db.refresh(revert_job)
        return revert_job

    # Load listings and snapshots
    listing_ids = [r.listing_id for r in apply_results]
    listings_q = await db.execute(
        select(Listing).where(
            Listing.id.in_(listing_ids),
            Listing.organization_id == organization_id,
        )
    )
    listings_map: dict[str, Listing] = {l.id: l for l in listings_q.scalars().all()}

    snapshot_ids = [r.backup_snapshot_id for r in apply_results if r.backup_snapshot_id]
    snapshots_map: dict[str, ListingBackupSnapshot] = {}
    if snapshot_ids:
        snaps_q = await db.execute(
            select(ListingBackupSnapshot).where(
                ListingBackupSnapshot.id.in_(snapshot_ids)
            )
        )
        snapshots_map = {s.id: s for s in snaps_q.scalars().all()}

    # Load shops + tokens
    shop_ids = list({l.etsy_shop_id for l in listings_map.values()})
    shops_q = await db.execute(select(EtsyShop).where(EtsyShop.id.in_(shop_ids)))
    shops_map: dict[str, EtsyShop] = {s.id: s for s in shops_q.scalars().all()}

    access_tokens: dict[str, str] = {}
    for shop_id, shop in shops_map.items():
        try:
            token = await get_valid_etsy_access_token(shop, db)
            access_tokens[shop_id] = token
        except Exception as e:
            logger.warning("Could not get token for shop %s: %s", shop_id, e)

    success_count = 0
    failure_count = 0
    skipped_count = 0

    for apply_result in apply_results:
        now = datetime.now(timezone.utc)

        listing = listings_map.get(apply_result.listing_id)
        if not listing:
            skipped_count += 1
            rr = RevertResult(
                organization_id=organization_id,
                revert_job_id=revert_job.id,
                apply_job_id=apply_job_id,
                bulk_edit_session_id=apply_job.bulk_edit_session_id,
                listing_id=apply_result.listing_id,
                etsy_listing_id=apply_result.etsy_listing_id,
                backup_snapshot_id=None,
                status="skipped",
                error_message="Listing not found in database.",
                attempted_at=now,
                completed_at=now,
            )
            db.add(rr)
            await db.flush()
            continue

        if not apply_result.backup_snapshot_id:
            skipped_count += 1
            rr = RevertResult(
                organization_id=organization_id,
                revert_job_id=revert_job.id,
                apply_job_id=apply_job_id,
                bulk_edit_session_id=apply_job.bulk_edit_session_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                backup_snapshot_id=None,
                status="skipped",
                error_message="No backup snapshot ID on apply result.",
                attempted_at=now,
                completed_at=now,
            )
            db.add(rr)
            await db.flush()
            continue

        snapshot = snapshots_map.get(apply_result.backup_snapshot_id)
        if not snapshot:
            skipped_count += 1
            rr = RevertResult(
                organization_id=organization_id,
                revert_job_id=revert_job.id,
                apply_job_id=apply_job_id,
                bulk_edit_session_id=apply_job.bulk_edit_session_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                backup_snapshot_id=apply_result.backup_snapshot_id,
                status="skipped",
                error_message="Backup snapshot not found.",
                attempted_at=now,
                completed_at=now,
            )
            db.add(rr)
            await db.flush()
            continue

        access_token = access_tokens.get(listing.etsy_shop_id)
        if not access_token:
            skipped_count += 1
            rr = RevertResult(
                organization_id=organization_id,
                revert_job_id=revert_job.id,
                apply_job_id=apply_job_id,
                bulk_edit_session_id=apply_job.bulk_edit_session_id,
                listing_id=listing.id,
                etsy_listing_id=listing.etsy_listing_id,
                backup_snapshot_id=snapshot.id,
                status="skipped",
                error_message="No valid Etsy access token for this shop.",
                attempted_at=now,
                completed_at=now,
            )
            db.add(rr)
            await db.flush()
            continue

        shop = shops_map.get(listing.etsy_shop_id)
        snapshot_data: dict[str, Any] = snapshot.snapshot_data or {}

        standard_payload = build_etsy_revert_payload(snapshot_data)
        inventory_payload = build_etsy_inventory_payload(listing, snapshot_data)

        # Variation inventory skip — text revert may still proceed
        inventory_skipped = listing.has_variations and (
            "price_amount" in snapshot_data or "quantity" in snapshot_data
        )
        inventory_skip_reason = "Variation inventory revert deferred to Sprint 11" if inventory_skipped else None

        # Build structured request payload
        if inventory_payload or inventory_skipped:
            req_payload: Any = {}
            if standard_payload:
                req_payload["listing_patch"] = standard_payload
            if inventory_payload:
                req_payload["inventory_patch"] = inventory_payload
            if inventory_skipped:
                req_payload["inventory_skipped"] = True
                req_payload["inventory_skip_reason"] = inventory_skip_reason
        else:
            req_payload = standard_payload

        rr = RevertResult(
            organization_id=organization_id,
            revert_job_id=revert_job.id,
            apply_job_id=apply_job_id,
            bulk_edit_session_id=apply_job.bulk_edit_session_id,
            listing_id=listing.id,
            etsy_listing_id=listing.etsy_listing_id,
            backup_snapshot_id=snapshot.id,
            status="pending",
            request_payload=req_payload,
            attempted_at=now,
        )
        db.add(rr)
        await db.flush()

        if not standard_payload and not inventory_payload:
            skipped_count += 1
            rr.status = "skipped"
            rr.error_message = inventory_skip_reason or "No patchable fields in snapshot."
            rr.completed_at = datetime.now(timezone.utc)
            await db.flush()
            continue

        # Step 1: revert text/bool fields (listing PATCH)
        listing_resp: Any = None
        if standard_payload:
            try:
                listing_resp = await patch_etsy_listing(
                    access_token=access_token,
                    etsy_listing_id=listing.etsy_listing_id,
                    payload=standard_payload,
                )
            except EtsyWriteError as e:
                rr.status = "failed"
                rr.error_message = e.message
                rr.response_payload = (
                    {"listing_patch_error": {"message": e.message, "response": e.response_body}}
                    if inventory_payload
                    else e.response_body
                )
                rr.completed_at = datetime.now(timezone.utc)
                failure_count += 1
                logger.warning("Etsy revert PATCH failed for %s: %s", listing.etsy_listing_id, e.message)
                await db.flush()
                continue
            except Exception as e:
                rr.status = "failed"
                rr.error_message = str(e)
                rr.completed_at = datetime.now(timezone.utc)
                failure_count += 1
                logger.exception("Unexpected error on revert PATCH %s", listing.etsy_listing_id)
                await db.flush()
                continue

        # Step 2: revert price/quantity (inventory PUT)
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
                rr.status = "failed"
                rr.error_message = f"Inventory revert failed: {e.message}"
                resp_struct: dict[str, Any] = {}
                if listing_resp is not None:
                    resp_struct["listing_patch"] = listing_resp
                resp_struct["inventory_patch_error"] = {"message": e.message, "response": e.response_body}
                rr.response_payload = resp_struct
                rr.completed_at = datetime.now(timezone.utc)
                failure_count += 1
                logger.warning(
                    "Etsy inventory revert PUT failed for %s: %s (listing PATCH already applied)",
                    listing.etsy_listing_id,
                    e.message,
                )
                await db.flush()
                continue
            except Exception as e:
                rr.status = "failed"
                rr.error_message = f"Inventory revert error: {str(e)}"
                rr.completed_at = datetime.now(timezone.utc)
                failure_count += 1
                logger.exception("Unexpected error on inventory revert PUT %s", listing.etsy_listing_id)
                await db.flush()
                continue

        # All revert writes succeeded — build response payload
        if inventory_resp is not None or inventory_skipped:
            resp_payload: Any = {}
            if listing_resp is not None:
                resp_payload["listing_patch"] = listing_resp
            if inventory_resp is not None:
                resp_payload["inventory_patch"] = inventory_resp
            if inventory_skipped:
                resp_payload["inventory_skipped"] = True
                resp_payload["inventory_skip_reason"] = inventory_skip_reason
        else:
            resp_payload = listing_resp

        rr.response_payload = resp_payload
        rr.status = "success"
        rr.completed_at = datetime.now(timezone.utc)

        # Update local text/bool fields from snapshot
        update_local_listing_from_snapshot(listing, snapshot_data)

        # Update price/quantity only after inventory revert write succeeds
        if inventory_resp is not None:
            if "price_amount" in snapshot_data:
                listing.price_amount = snapshot_data.get("price_amount")
            if "quantity" in snapshot_data:
                listing.quantity = snapshot_data.get("quantity")

        db.add(listing)
        success_count += 1
        await db.flush()

    # Finalize
    revert_job.success_count = success_count
    revert_job.failure_count = failure_count
    revert_job.skipped_count = skipped_count
    revert_job.finished_at = datetime.now(timezone.utc)
    revert_job.status = (
        "completed" if failure_count == 0 and skipped_count == 0
        else "completed_with_errors" if success_count > 0
        else "failed"
    )

    db.add(revert_job)

    await _write_audit_log(
        db,
        org_id=organization_id,
        user_id=user_id,
        event_type="bulk_edit_revert_finished",
        entity_type="revert_job",
        entity_id=revert_job.id,
        message=(
            f"Revert job {revert_job.id} finished. "
            f"success={success_count}, failure={failure_count}, skipped={skipped_count}."
        ),
        extra_data={
            "revert_job_id": revert_job.id,
            "apply_job_id": apply_job_id,
            "success_count": success_count,
            "failure_count": failure_count,
            "skipped_count": skipped_count,
            "status": revert_job.status,
        },
    )

    await db.commit()
    await db.refresh(revert_job)
    return revert_job


async def get_revert_job(
    db: AsyncSession,
    organization_id: str,
    revert_job_id: str,
) -> RevertJob:
    result = await db.execute(
        select(RevertJob).where(
            RevertJob.id == revert_job_id,
            RevertJob.organization_id == organization_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Revert job not found.")
    return job


async def list_revert_jobs_for_apply_job(
    db: AsyncSession,
    organization_id: str,
    apply_job_id: str,
) -> list[RevertJob]:
    result = await db.execute(
        select(RevertJob).where(
            RevertJob.apply_job_id == apply_job_id,
            RevertJob.organization_id == organization_id,
        ).order_by(RevertJob.created_at.desc())
    )
    return list(result.scalars().all())


async def get_revert_results(
    db: AsyncSession,
    organization_id: str,
    revert_job_id: str,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    await get_revert_job(db, organization_id, revert_job_id)

    q = select(RevertResult).where(
        RevertResult.revert_job_id == revert_job_id,
        RevertResult.organization_id == organization_id,
    )
    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar_one()

    q = q.order_by(RevertResult.created_at.asc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = list(result.scalars().all())

    return {"items": items, "page": page, "per_page": per_page, "total": total, "revert_job_id": revert_job_id}
