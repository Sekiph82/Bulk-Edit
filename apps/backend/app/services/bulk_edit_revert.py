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
  9. Price/quantity reverted via fetch-patch-put on the inventory endpoint
     (GET+PUT /listings/{l}/inventory — listing-scoped, full tree preserved)
     Variation listings: inventory revert skipped (Sprint 11); text fields still reverted.
 10. Photo/video not reverted (deferred to Sprint 11)

Partial write caveat: if text PATCH succeeds but inventory PUT fails, Etsy has reverted text
but not price/quantity. Local DB not updated. Next sync resolves the discrepancy.
"""
import html
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.bulk_edit_apply_job import BulkEditApplyJob
from app.models.bulk_edit_apply_result import BulkEditApplyResult
from app.models.bulk_edit_preview_item import BulkEditPreviewItem
from app.models.etsy_shop import EtsyShop
from app.models.listing import Listing
from app.models.listing_backup_snapshot import ListingBackupSnapshot
from app.models.revert_job import RevertJob
from app.models.revert_result import RevertResult
from app.services.etsy_http import etsy_get
from app.services.etsy_sync import ETSY_API_BASE, _auth_headers, get_valid_etsy_access_token
from app.services.etsy_write import (
    build_etsy_patch_payload,
    build_etsy_inventory_payload,
    patch_etsy_listing,
    apply_single_listing_price_quantity,
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


# M06.03 changed-since-apply conflict detection — remediated 2026-08-31
# after a strict post-merge audit of PR #121 found a MAJOR correctness bug.
#
# PR #121's original version compared the fresh Etsy read to the CURRENT
# local `Listing` row. That is wrong whenever a later write (a second apply
# job, another Magic Revert, a real sync) already moved the local row past
# what THIS apply job actually set:
#
#   Job A: title "A" -> "B" (this is the job being reverted)
#   Job B: title "B" -> "C" (a later, unrelated apply)
#   local Listing.title and live Etsy title are now both "C"
#
# The old check compared live "C" to local "C" -> "no conflict" -> would
# have overwritten Job B's work. The correct question is "does live Etsy
# still hold what Job A itself wrote (\"B\")?" -- it does not, so Job A's
# revert must be refused. The expected-current value for a field is that
# field's captured AFTER value from the apply job actually being reverted,
# never the local Listing row's current value (see build_expected_after_values()).
#
# Text fields are compared normalized (HTML-entity-decoded, whitespace-
# trimmed) so decode-only differences never produce a false conflict.
# price_amount/quantity are compared as exact integers. Every other field
# this revert could touch (the rest of _SNAPSHOT_TO_LISTING) is NOT verified
# here yet -- an unverified field is treated as a conflict rather than
# assumed safe. This is exactly why M06.03 stays `[~]`, not `[x]`.
_CONFLICT_CHECK_TEXT_FIELDS = {"title", "description", "sku"}
_CONFLICT_CHECK_NUMERIC_FIELDS = {"price_amount", "quantity"}


def _normalize_text_for_conflict_check(value: Any) -> str:
    if value is None:
        return ""
    return html.unescape(str(value)).strip()


async def fetch_current_listing_for_conflict_check(
    access_token: str, etsy_listing_id: str
) -> dict[str, Any] | None:
    """Read-only GET of a single listing's current Etsy state, used only to
    detect changed-since-apply conflicts before a revert write. Never writes,
    never calls a status-mutation endpoint."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await etsy_get(
            client,
            f"{ETSY_API_BASE}/application/listings/{etsy_listing_id}",
            headers=_auth_headers(access_token),
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()


async def build_expected_after_values(
    db: AsyncSession,
    organization_id: str,
    apply_job_id: str,
    bulk_edit_session_id: str,
    listing_ids: list[str],
) -> dict[str, tuple[dict[str, Any], set[str]]]:
    """Batch-computes, per listing_id, (expected_after, changed_fields) for
    the M06.03 conflict check.

    changed_fields is the real, per-listing set of fields THIS apply job
    actually touched. expected_after has a value only for fields where a
    reliable source was found -- a field in changed_fields but missing from
    expected_after is unverified, never silently treated as safe.

    Source priority (never falls back to the local Listing row):
      1. The M06.04 per-field AuditLog row for this apply_job_id + this
         listing (entity_id) + result_status="success" -- extra_data["after"].
         Most direct: the exact per-field, per-listing outcome the write
         audit trail already records.
      2. BulkEditPreviewItem.diff for this session+listing -- diff[field]["after"].
         Covers apply jobs that predate the AuditLog migration (0027) and
         this feature entirely; the apply only ever wrote diff's "after"
         value, so it's equally trustworthy for a listing whose apply
         result was "success" (revert_apply_job() only considers those).
    A field with neither source is left out of expected_after entirely --
    detect_revert_conflict() marks it unverified, not safe."""
    audit_q = await db.execute(
        select(AuditLog.entity_id, AuditLog.field_name, AuditLog.extra_data).where(
            AuditLog.organization_id == organization_id,
            AuditLog.apply_job_id == apply_job_id,
            AuditLog.event_type == "bulk_edit_field_write",
            AuditLog.result_status == "success",
            AuditLog.entity_id.in_(listing_ids),
        )
    )
    audit_after: dict[str, dict[str, Any]] = {}
    for entity_id, field_name, extra_data in audit_q.all():
        if not field_name:
            continue
        audit_after.setdefault(entity_id, {})[field_name] = (extra_data or {}).get("after")

    preview_q = await db.execute(
        select(BulkEditPreviewItem).where(
            BulkEditPreviewItem.bulk_edit_session_id == bulk_edit_session_id,
            BulkEditPreviewItem.listing_id.in_(listing_ids),
        )
    )
    preview_by_listing: dict[str, BulkEditPreviewItem] = {p.listing_id: p for p in preview_q.scalars().all()}

    result: dict[str, tuple[dict[str, Any], set[str]]] = {}
    for listing_id in listing_ids:
        listing_audit_after = audit_after.get(listing_id, {})
        preview_item = preview_by_listing.get(listing_id)
        diff = (preview_item.diff or {}) if preview_item else {}

        changed_fields = set(listing_audit_after.keys()) | set(diff.keys())
        expected_after: dict[str, Any] = {}
        for field in changed_fields:
            if field in listing_audit_after:
                expected_after[field] = listing_audit_after[field]
            elif isinstance(diff.get(field), dict) and "after" in diff[field]:
                expected_after[field] = diff[field]["after"]
        result[listing_id] = (expected_after, changed_fields)
    return result


def detect_revert_conflict(
    expected_after: dict[str, Any],
    changed_fields: set[str],
    current_etsy_data: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compares the live current Etsy value for each field this apply
    actually changed against that field's captured AFTER value from the
    apply job being reverted (see build_expected_after_values() — never the
    local Listing row). A mismatch, or a changed field this check can't
    verify, is a conflict — never assumed safe by default. Returns a
    JSON-safe dict, no secrets."""
    if current_etsy_data is None:
        return {
            "has_conflict": True,
            "conflicting_fields": [],
            "unverified_fields": ["*"],
            "reason": "Could not read the listing's current Etsy state to verify it hasn't changed.",
        }

    if not changed_fields:
        return {
            "has_conflict": True,
            "conflicting_fields": [],
            "unverified_fields": ["*"],
            "reason": (
                "Cannot verify the expected post-apply value for this field, so automatic "
                "revert is blocked to avoid overwriting newer work. (no captured after-value "
                "found for this apply job — likely an older job predating the write audit trail)"
            ),
        }

    conflicting: list[str] = []
    unverified: list[str] = []
    price = current_etsy_data.get("price") or {}

    for field in changed_fields:
        if field not in expected_after:
            unverified.append(field)
            continue
        expected = expected_after[field]
        if field in _CONFLICT_CHECK_TEXT_FIELDS:
            actual = _normalize_text_for_conflict_check(current_etsy_data.get(field))
            if _normalize_text_for_conflict_check(expected) != actual:
                conflicting.append(field)
        elif field == "price_amount":
            if expected != price.get("amount"):
                conflicting.append(field)
        elif field == "quantity":
            if expected != current_etsy_data.get("quantity"):
                conflicting.append(field)
        else:
            unverified.append(field)

    if conflicting:
        reason = f"This listing changed after the original apply (field(s): {', '.join(conflicting)}). Reverting may overwrite newer work."
    elif unverified:
        reason = (
            f"Cannot verify the expected post-apply value for field(s) {', '.join(unverified)}, "
            "so automatic revert is blocked to avoid overwriting newer work."
        )
    else:
        reason = None

    return {
        "has_conflict": bool(conflicting or unverified),
        "conflicting_fields": conflicting,
        "unverified_fields": unverified,
        "reason": reason,
    }


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

    Check order is deliberate: org-scoped lookup (404) first so a cross-org
    job id never leaks existence, then status/success-count/duplicate-revert
    (400/409) -- an already-reverted job must report "already reverted", not
    "plan blocked" -- and only then, last, the can_use_magic_revert plan gate
    (403). No RevertJob row is created and no Etsy call is made until every
    check here has passed.
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

    if job.success_count <= 0:
        raise HTTPException(
            status_code=400,
            detail="This apply job has no successfully changed items to revert.",
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

    from app.core.plans import get_effective_plan, get_plan_limits

    effective_plan = await get_effective_plan(db, organization_id)
    if not get_plan_limits(effective_plan).get("can_use_magic_revert", False):
        raise HTTPException(
            status_code=403,
            detail="Magic Revert is not available on your current plan.",
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

    # M06.03: per-listing (expected_after, changed_fields) for the
    # changed-since-apply conflict check -- see build_expected_after_values()
    # for the source priority. Batched once here, not per-listing in the loop.
    expected_after_map = await build_expected_after_values(
        db, organization_id, apply_job_id, apply_job.bulk_edit_session_id, listing_ids,
    )

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

        # M06.03: refuse to revert if the listing appears to have changed
        # since the original apply — read-only Etsy GET, no write attempted
        # for a conflicted item. Compares against THIS apply job's own
        # captured after-values, never the local Listing row — see
        # build_expected_after_values()/detect_revert_conflict() docstrings.
        try:
            current_etsy_data = await fetch_current_listing_for_conflict_check(access_token, listing.etsy_listing_id)
        except Exception as exc:
            logger.warning("Conflict check GET failed for listing %s: %s", listing.etsy_listing_id, exc)
            current_etsy_data = None
        expected_after, expected_changed_fields = expected_after_map.get(listing.id, ({}, set()))
        conflict = detect_revert_conflict(expected_after, expected_changed_fields, current_etsy_data)
        if conflict["has_conflict"]:
            skipped_count += 1
            rr.status = "conflict"
            rr.error_message = conflict["reason"]
            rr.response_payload = {
                "conflicting_fields": conflict["conflicting_fields"],
                "unverified_fields": conflict["unverified_fields"],
            }
            rr.completed_at = datetime.now(timezone.utc)
            await db.flush()
            continue

        # Step 1: revert text/bool fields (listing PATCH)
        listing_resp: Any = None
        if standard_payload and shop:
            try:
                listing_resp = await patch_etsy_listing(
                    access_token=access_token,
                    shop_etsy_id=shop.etsy_shop_id,
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

        # Step 2: revert price/quantity (fetch-patch-put inventory tree)
        inventory_resp: Any = None
        if inventory_payload and shop:
            try:
                inventory_resp = await apply_single_listing_price_quantity(
                    access_token=access_token,
                    shop_etsy_id=shop.etsy_shop_id,
                    listing_etsy_id=listing.etsy_listing_id,
                    price_amount=snapshot_data.get("price_amount") if "price_amount" in snapshot_data else None,
                    quantity=snapshot_data.get("quantity") if "quantity" in snapshot_data else None,
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

    # M06.04: link the per-field write audit trail to this revert's outcome
    # -- "audit record updates after Magic Revert" -- rather than creating a
    # second, disconnected set of rows for the same fields.
    await db.execute(
        update(AuditLog)
        .where(
            AuditLog.apply_job_id == apply_job_id,
            AuditLog.event_type == "bulk_edit_field_write",
            AuditLog.organization_id == organization_id,
        )
        .values(revert_job_id=revert_job.id, revert_status=revert_job.status)
    )

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


async def get_revert_eligibility_map(
    db: AsyncSession,
    organization_id: str,
    apply_jobs: list[BulkEditApplyJob],
) -> dict[str, dict[str, Any]]:
    """
    Batch, read-only version of validate_apply_job_revertable()'s rules, for
    decorating an apply-job history list with can_revert/revert_status
    without one eligibility query per row (N+1) or ever raising. Mirrors the
    exact same rule set that function actually enforces, in the same
    precedence order: job status, at least one successful item, no existing
    completed/completed_with_errors/running revert for that apply job, and
    the can_use_magic_revert plan gate -- checked last, so a job that is
    already reverted (or already in progress) reports that, not "plan
    blocked". Effective plan is resolved once per call (not per job) to
    avoid N+1 queries.
    """
    if not apply_jobs:
        return {}

    from app.core.plans import get_effective_plan, get_plan_limits

    effective_plan = await get_effective_plan(db, organization_id)
    plan_allows_magic_revert = get_plan_limits(effective_plan).get("can_use_magic_revert", False)

    job_ids = [j.id for j in apply_jobs]
    existing_q = await db.execute(
        select(RevertJob)
        .where(
            RevertJob.apply_job_id.in_(job_ids),
            RevertJob.organization_id == organization_id,
        )
        .order_by(RevertJob.created_at.desc())
    )
    # Most recent revert job per apply_job_id (first one seen, since ordered desc)
    latest_revert_by_apply_job: dict[str, RevertJob] = {}
    for rj in existing_q.scalars().all():
        latest_revert_by_apply_job.setdefault(rj.apply_job_id, rj)

    result: dict[str, dict[str, Any]] = {}
    for job in apply_jobs:
        latest_revert = latest_revert_by_apply_job.get(job.id)
        revert_status = latest_revert.status if latest_revert else None
        revert_job_id = latest_revert.id if latest_revert else None

        if job.status not in ("completed", "completed_with_errors"):
            can_revert, reason = False, "Apply job did not complete."
        elif job.success_count <= 0:
            can_revert, reason = False, "No successful items to revert."
        elif revert_status in ("completed", "completed_with_errors", "running"):
            can_revert, reason = False, (
                "Revert already in progress." if revert_status == "running" else "Already reverted."
            )
        elif not plan_allows_magic_revert:
            can_revert, reason = False, "Magic Revert is not available on your current plan."
        else:
            can_revert, reason = True, None

        result[job.id] = {
            "can_revert": can_revert,
            "revert_blocked_reason": reason,
            "revert_job_id": revert_job_id,
            "revert_status": revert_status,
        }
    return result


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
