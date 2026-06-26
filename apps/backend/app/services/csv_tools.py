"""
CSV Import / Export service.

Safety rule: CSV import NEVER writes to Etsy directly.
Import creates BulkEditSession + BulkEditChange rows only.
User must run existing bulk edit preview/apply flow to publish changes.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bulk_edit_change import BulkEditChange
from app.models.bulk_edit_session import BulkEditSession
from app.models.csv_job import CSVJob
from app.models.csv_row import CSVRow
from app.models.listing import Listing

MAX_IMPORT_ROWS = 5_000

# ── field definitions ─────────────────────────────────────────────────────────

IDENTITY_COLUMNS = {"listing_id", "etsy_listing_id", "shop_id", "shop_name"}

EDITABLE_FIELDS = {
    "title", "description", "tags", "materials",
    "price_amount", "quantity", "sku",
    "section_id", "taxonomy_id",
    "is_personalizable", "is_customizable",
    "personalization_instructions", "personalization_is_required",
    "processing_min", "processing_max",
    "state",
}

EXPORT_ONLY_FIELDS = {
    "etsy_listing_id", "listing_id", "shop_name", "currency_code",
    "has_variations", "created_at", "updated_at", "last_synced_at",
}

ALL_KNOWN_COLUMNS = IDENTITY_COLUMNS | EDITABLE_FIELDS | EXPORT_ONLY_FIELDS

EXPORT_HEADERS = [
    "listing_id", "etsy_listing_id", "shop_name",
    "title", "description", "tags", "materials",
    "price_amount", "currency_code", "quantity", "sku",
    "section_id", "taxonomy_id",
    "is_personalizable", "is_customizable",
    "personalization_instructions", "personalization_is_required",
    "processing_min", "processing_max",
    "state", "has_variations",
    "created_at", "updated_at", "last_synced_at",
]

BOOL_FIELDS = {"is_personalizable", "is_customizable", "personalization_is_required"}
INT_FIELDS = {"price_amount", "quantity", "processing_min", "processing_max"}
ID_INT_FIELDS = {"section_id", "taxonomy_id"}
ARRAY_FIELDS = {"tags", "materials"}


class CSVToolsError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ── normalizers ────────────────────────────────────────────────────────────────

def normalize_pipe_array(value: str) -> list[str]:
    if not value or not str(value).strip():
        return []
    parts = [p.strip() for p in str(value).split("|")]
    seen: set[str] = set()
    result: list[str] = []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            result.append(p)
    return result


def parse_bool(value: str) -> bool | None:
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in ("true", "yes", "1", "y"):
        return True
    if v in ("false", "no", "0", "n"):
        return False
    return None


def parse_int(value: str) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def normalize_csv_value(field_name: str, raw_value: str) -> Any:
    if raw_value is None or str(raw_value).strip() == "":
        return None
    v = str(raw_value).strip()
    if field_name in BOOL_FIELDS:
        return parse_bool(v)
    if field_name in INT_FIELDS:
        return parse_int(v)
    if field_name in ID_INT_FIELDS:
        return str(parse_int(v)) if parse_int(v) is not None else None
    if field_name in ARRAY_FIELDS:
        return normalize_pipe_array(v)
    return v


# ── export ─────────────────────────────────────────────────────────────────────

def _listing_to_csv_row(listing: Listing, shop_name: str = "") -> dict[str, str]:
    def fmt_array(v) -> str:
        if not v:
            return ""
        if isinstance(v, list):
            return "|".join(str(x) for x in v)
        return str(v)

    def fmt_bool(v) -> str:
        if v is None:
            return ""
        return "true" if v else "false"

    def fmt_dt(v) -> str:
        if v is None:
            return ""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return str(v)

    return {
        "listing_id": listing.id,
        "etsy_listing_id": listing.etsy_listing_id or "",
        "shop_name": shop_name,
        "title": listing.title or "",
        "description": listing.description or "",
        "tags": fmt_array(listing.tags),
        "materials": fmt_array(listing.materials),
        "price_amount": str(listing.price_amount) if listing.price_amount is not None else "",
        "currency_code": listing.currency_code or "",
        "quantity": str(listing.quantity) if listing.quantity is not None else "",
        "sku": listing.sku or "",
        "section_id": listing.section_id or "",
        "taxonomy_id": listing.taxonomy_id or "",
        "is_personalizable": fmt_bool(listing.is_personalizable),
        "is_customizable": fmt_bool(listing.is_customizable),
        "personalization_instructions": listing.personalization_instructions or "",
        "personalization_is_required": fmt_bool(listing.personalization_is_required),
        "processing_min": str(listing.processing_min) if listing.processing_min is not None else "",
        "processing_max": str(listing.processing_max) if listing.processing_max is not None else "",
        "state": listing.state or "",
        "has_variations": fmt_bool(listing.has_variations),
        "created_at": fmt_dt(listing.created_at),
        "updated_at": fmt_dt(listing.updated_at),
        "last_synced_at": fmt_dt(listing.last_synced_at),
    }


async def export_listings_to_csv(
    db: AsyncSession,
    organization_id: str,
    shop_id: str | None = None,
    state: str | None = None,
    listing_ids: list[str] | None = None,
) -> str:
    from app.models.etsy_shop import EtsyShop

    q = select(Listing).where(Listing.organization_id == organization_id)
    if shop_id:
        q = q.where(Listing.etsy_shop_id == shop_id)
    if state:
        q = q.where(Listing.state == state)
    if listing_ids:
        q = q.where(Listing.id.in_(listing_ids))
    q = q.order_by(Listing.created_at.desc())

    result = await db.execute(q)
    listings = result.scalars().all()

    shop_names: dict[str, str] = {}
    shop_ids = {l.etsy_shop_id for l in listings}
    if shop_ids:
        sr = await db.execute(select(EtsyShop).where(EtsyShop.id.in_(shop_ids)))
        for s in sr.scalars().all():
            shop_names[s.id] = s.shop_name or ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_HEADERS, extrasaction="ignore")
    writer.writeheader()
    for listing in listings:
        writer.writerow(_listing_to_csv_row(listing, shop_names.get(listing.etsy_shop_id, "")))

    return output.getvalue()


def csv_template() -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_HEADERS, extrasaction="ignore")
    writer.writeheader()
    return output.getvalue()


# ── import ─────────────────────────────────────────────────────────────────────

def parse_csv_upload(file_bytes: bytes, filename: str = "") -> tuple[list[dict[str, str]], list[str]]:
    """
    Parse CSV bytes. Returns (rows, ignored_columns).
    Strips UTF-8 BOM. Raises CSVToolsError on fatal errors.
    """
    if not file_bytes or not file_bytes.strip():
        raise CSVToolsError("Uploaded file is empty.", 400)
    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise CSVToolsError("CSV has no headers.", 400)
    headers = [h.strip() for h in reader.fieldnames]
    ignored = sorted(set(headers) - ALL_KNOWN_COLUMNS)
    rows: list[dict[str, str]] = []
    for row in reader:
        clean = {k.strip(): v for k, v in row.items() if k is not None}
        rows.append(clean)
        if len(rows) > MAX_IMPORT_ROWS:
            raise CSVToolsError(
                f"CSV exceeds {MAX_IMPORT_ROWS} row limit. Split into smaller files.", 400
            )
    return rows, ignored


def _build_diff(before: dict, normalized: dict) -> dict:
    diff: dict = {}
    for field, after_val in normalized.items():
        if field not in EDITABLE_FIELDS:
            continue
        if after_val is None:
            continue
        before_val = before.get(field)
        if before_val != after_val:
            diff[field] = {"before": before_val, "after": after_val}
    return diff


def _validate_raw_row(
    row: dict[str, str],
    listing: Listing | None,
    row_number: int,
) -> tuple[dict | None, list[str], list[str]]:
    """
    Validate and normalize one CSV row.
    Returns (normalized_data, errors, warnings). normalized_data=None if identity invalid.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if listing is None:
        errors.append("Listing not found or does not belong to your organization.")
        return None, errors, warnings

    normalized: dict[str, Any] = {}

    for field in EDITABLE_FIELDS:
        raw = row.get(field)
        if raw is None or str(raw).strip() == "":
            continue
        v = normalize_csv_value(field, raw)

        if field == "price_amount":
            if v is None:
                errors.append(f"price_amount: invalid integer '{raw}'")
                continue
            if v < 0:
                errors.append("price_amount must be >= 0")
                continue

        if field == "quantity":
            if v is None:
                errors.append(f"quantity: invalid integer '{raw}'")
                continue
            if v < 0:
                errors.append("quantity must be >= 0")
                continue

        if field in ("processing_min", "processing_max"):
            if v is None:
                errors.append(f"{field}: invalid integer '{raw}'")
                continue

        if field in BOOL_FIELDS:
            if v is None:
                errors.append(f"{field}: invalid boolean '{raw}' — use true/false/yes/no/1/0")
                continue

        if field == "title" and v is not None:
            if not str(v).strip():
                errors.append("title cannot be empty")
                continue
            if len(str(v)) > 140:
                errors.append(f"title too long ({len(str(v))} chars, max 140)")
                continue

        if field in ARRAY_FIELDS and isinstance(v, list):
            if len(v) > 13 and field == "tags":
                errors.append(f"tags: too many tags ({len(v)}, max 13)")
                continue
            for tag in v:
                if len(str(tag)) > 20 and field == "tags":
                    errors.append(f"tags: tag '{tag}' exceeds 20 chars")
                    break

        if field in ("price_amount", "quantity") and listing.has_variations:
            warnings.append(
                f"{field}: listing has variations — price/quantity managed per variation, "
                "not at listing level. Change will be included but may have no effect."
            )

        if v is not None:
            normalized[field] = v

    pmin = normalized.get("processing_min")
    pmax = normalized.get("processing_max")
    if pmin is not None and pmax is not None and pmin > pmax:
        errors.append("processing_min must be <= processing_max")

    return normalized, errors, warnings


async def create_csv_import_job(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    filename: str,
    raw_rows: list[dict[str, str]],
    ignored_columns: list[str],
) -> CSVJob:
    job = CSVJob(
        organization_id=organization_id,
        user_id=user_id,
        job_type="import",
        status="validating",
        filename=filename,
        original_filename=filename,
        row_count=len(raw_rows),
        ignored_column_count=len(ignored_columns),
        ignored_columns=ignored_columns or None,
    )
    db.add(job)
    await db.flush()

    counts = {"valid": 0, "invalid": 0, "unchanged": 0, "warning": 0}

    for i, raw in enumerate(raw_rows, start=1):
        listing, errors_id = await _resolve_listing(db, organization_id, raw, i)

        normalized, errors_field, warnings = _validate_raw_row(raw, listing, i)
        errors = errors_id + errors_field

        diff: dict = {}
        etsy_id = raw.get("etsy_listing_id") or (listing.etsy_listing_id if listing else None)
        title = listing.title if listing else None

        if not errors and normalized is not None and listing is not None:
            before = _listing_before(listing)
            diff = _build_diff(before, normalized)
            if not diff and not warnings:
                row_status = "unchanged"
            elif errors:
                row_status = "invalid"
            elif warnings:
                row_status = "warning"
            else:
                row_status = "valid"
        else:
            row_status = "invalid"

        counts[row_status] = counts.get(row_status, 0) + 1

        csv_row = CSVRow(
            organization_id=organization_id,
            csv_job_id=job.id,
            row_number=i,
            listing_id=listing.id if listing else None,
            etsy_listing_id=etsy_id,
            listing_title=title,
            raw_data=dict(raw),
            normalized_data=normalized,
            diff=diff if diff else None,
            status=row_status,
            validation_errors=errors if errors else None,
            validation_warnings=warnings if warnings else None,
        )
        db.add(csv_row)

    job.valid_row_count = counts.get("valid", 0) + counts.get("warning", 0)
    job.invalid_row_count = counts.get("invalid", 0)
    job.changed_row_count = counts.get("valid", 0) + counts.get("warning", 0)
    job.unchanged_row_count = counts.get("unchanged", 0)
    job.status = "preview_ready"
    job.completed_at = datetime.now(timezone.utc)
    job.summary = {
        "total": len(raw_rows),
        "valid": counts.get("valid", 0),
        "warning": counts.get("warning", 0),
        "invalid": counts.get("invalid", 0),
        "unchanged": counts.get("unchanged", 0),
        "ignored_columns": ignored_columns,
    }

    await db.commit()
    await db.refresh(job)
    return job


def _listing_before(listing: Listing) -> dict:
    return {
        "title": listing.title,
        "description": listing.description,
        "tags": list(listing.tags) if isinstance(listing.tags, list) else [],
        "materials": list(listing.materials) if isinstance(listing.materials, list) else [],
        "price_amount": listing.price_amount,
        "quantity": listing.quantity,
        "sku": listing.sku,
        "section_id": listing.section_id,
        "taxonomy_id": listing.taxonomy_id,
        "is_personalizable": listing.is_personalizable,
        "is_customizable": listing.is_customizable,
        "personalization_instructions": listing.personalization_instructions,
        "personalization_is_required": listing.personalization_is_required,
        "processing_min": listing.processing_min,
        "processing_max": listing.processing_max,
        "state": listing.state,
    }


async def _resolve_listing(
    db: AsyncSession,
    organization_id: str,
    raw: dict[str, str],
    row_number: int,
) -> tuple[Listing | None, list[str]]:
    errors: list[str] = []
    lid = raw.get("listing_id", "").strip()
    eid = raw.get("etsy_listing_id", "").strip()

    listing_by_id: Listing | None = None
    listing_by_etsy: Listing | None = None

    if lid:
        r = await db.execute(
            select(Listing).where(Listing.id == lid, Listing.organization_id == organization_id)
        )
        listing_by_id = r.scalar_one_or_none()
        if not listing_by_id:
            errors.append(f"listing_id '{lid}' not found or does not belong to your organization.")
            return None, errors

    if eid:
        r = await db.execute(
            select(Listing).where(
                Listing.etsy_listing_id == eid,
                Listing.organization_id == organization_id,
            )
        )
        listing_by_etsy = r.scalar_one_or_none()

    if listing_by_id and listing_by_etsy and listing_by_id.id != listing_by_etsy.id:
        errors.append(
            f"listing_id and etsy_listing_id point to different listings — row is invalid."
        )
        return None, errors

    if listing_by_id:
        return listing_by_id, errors
    if listing_by_etsy:
        return listing_by_etsy, errors

    if not lid and not eid:
        errors.append("Row must have listing_id or etsy_listing_id to identify the listing.")
        return None, errors

    if eid and not listing_by_etsy:
        errors.append(f"etsy_listing_id '{eid}' not found in your organization.")
        return None, errors

    return None, errors


# ── query helpers ──────────────────────────────────────────────────────────────

async def list_csv_jobs(
    db: AsyncSession,
    organization_id: str,
    job_type: str | None = None,
) -> list[CSVJob]:
    q = select(CSVJob).where(CSVJob.organization_id == organization_id)
    if job_type:
        q = q.where(CSVJob.job_type == job_type)
    q = q.order_by(CSVJob.created_at.desc())
    r = await db.execute(q)
    return list(r.scalars().all())


async def get_csv_job(
    db: AsyncSession,
    organization_id: str,
    csv_job_id: str,
) -> CSVJob:
    r = await db.execute(
        select(CSVJob).where(CSVJob.id == csv_job_id, CSVJob.organization_id == organization_id)
    )
    job = r.scalar_one_or_none()
    if not job:
        raise CSVToolsError("CSV job not found", 404)
    return job


async def get_csv_preview(
    db: AsyncSession,
    organization_id: str,
    csv_job_id: str,
    page: int = 1,
    per_page: int = 50,
    status: str | None = None,
) -> tuple[list[CSVRow], int]:
    await get_csv_job(db, organization_id, csv_job_id)
    q = select(CSVRow).where(
        CSVRow.csv_job_id == csv_job_id,
        CSVRow.organization_id == organization_id,
    )
    if status:
        q = q.where(CSVRow.status == status)
    total_r = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_r.scalar_one()
    q = q.order_by(CSVRow.row_number).offset((page - 1) * per_page).limit(per_page)
    r = await db.execute(q)
    return list(r.scalars().all()), total


# ── conversion ─────────────────────────────────────────────────────────────────

async def convert_csv_job_to_bulk_edit_session(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    csv_job_id: str,
    ignore_invalid: bool = False,
) -> tuple[BulkEditSession, int, int]:
    """
    Convert valid CSV rows into BulkEditSession + BulkEditChange rows.
    Returns (session, converted_rows, created_changes).
    NEVER writes to Etsy.
    """
    job = await get_csv_job(db, organization_id, csv_job_id)

    if job.status not in ("preview_ready",):
        raise CSVToolsError(f"Job is not preview_ready (status={job.status})", 400)

    if job.invalid_row_count > 0 and not ignore_invalid:
        raise CSVToolsError(
            f"Job has {job.invalid_row_count} invalid rows. Fix them or set ignore_invalid=true.",
            400,
        )

    valid_rows_r = await db.execute(
        select(CSVRow).where(
            CSVRow.csv_job_id == csv_job_id,
            CSVRow.organization_id == organization_id,
            CSVRow.status.in_(("valid", "warning")),
            CSVRow.listing_id.isnot(None),
        )
    )
    valid_rows = list(valid_rows_r.scalars().all())
    convertible = [r for r in valid_rows if r.diff]

    if not convertible:
        raise CSVToolsError("No convertible rows with changes found.", 400)

    listing_ids = list(dict.fromkeys(r.listing_id for r in convertible))

    bulk_session = BulkEditSession(
        organization_id=organization_id,
        created_by_user_id=user_id,
        name=f"CSV import: {job.original_filename or job.id}",
        status="draft",
        selected_listing_ids=listing_ids,
        selected_count=len(listing_ids),
        change_count=0,
    )
    db.add(bulk_session)
    await db.flush()

    change_count = 0
    for row in convertible:
        if not row.diff or not row.listing_id:
            continue
        for field, delta in row.diff.items():
            new_val = delta.get("after")
            change = BulkEditChange(
                bulk_edit_session_id=bulk_session.id,
                listing_id=row.listing_id,
                field_name=field,
                operation="set",
                new_value=new_val,
                operation_value=new_val,
                validation_status="pending",
                target_listing_ids=[row.listing_id],
            )
            db.add(change)
            change_count += 1

    bulk_session.change_count = change_count
    job.status = "converted"
    job.converted_bulk_edit_session_id = bulk_session.id
    job.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(bulk_session)
    return bulk_session, len(convertible), change_count
