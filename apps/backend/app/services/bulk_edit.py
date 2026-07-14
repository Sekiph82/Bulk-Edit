"""
Bulk Edit Preview Engine — Sprint 7.

All operations are in-memory only. No Etsy API calls.
No Listing rows modified. Apply endpoint is a stub.
"""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bulk_edit_session import BulkEditSession
from app.models.bulk_edit_change import BulkEditChange
from app.models.bulk_edit_preview_item import BulkEditPreviewItem
from app.models.listing import Listing

# ── field type registries ──────────────────────────────────────────────────────

TEXT_FIELDS = {
    "title", "description", "sku", "section_id", "taxonomy_id",
    "personalization_instructions",
}
BOOL_FIELDS = {
    "is_personalizable", "is_customizable",
    "personalization_is_required", "has_variations",
}
NUMBER_FIELDS = {
    "price_amount", "quantity", "processing_min", "processing_max",
    "personalization_char_count_max", "item_weight", "item_length",
    "item_width", "item_height",
}
ARRAY_FIELDS = {"tags", "materials"}
EDITABLE_FIELDS = TEXT_FIELDS | BOOL_FIELDS | NUMBER_FIELDS | ARRAY_FIELDS

TEXT_OPS = {"set", "append", "prepend", "replace"}
BOOL_OPS = {"set"}
NUMBER_OPS = {"set", "percentage_change", "fixed_amount_change"}
ARRAY_OPS = {"set", "add_tag", "remove_tag"}

FIELD_OPS: dict[str, set[str]] = {}
for f in TEXT_FIELDS:
    FIELD_OPS[f] = TEXT_OPS
for f in BOOL_FIELDS:
    FIELD_OPS[f] = BOOL_OPS
for f in NUMBER_FIELDS:
    FIELD_OPS[f] = NUMBER_OPS
for f in ARRAY_FIELDS:
    FIELD_OPS[f] = ARRAY_OPS


# ── helpers ────────────────────────────────────────────────────────────────────

def _float_or_none(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def build_before_data(listing: Listing) -> dict:
    return {
        "title": listing.title,
        "description": listing.description,
        "sku": listing.sku,
        "section_id": listing.section_id,
        "taxonomy_id": listing.taxonomy_id,
        "personalization_instructions": listing.personalization_instructions,
        "is_personalizable": listing.is_personalizable,
        "is_customizable": listing.is_customizable,
        "personalization_is_required": listing.personalization_is_required,
        "has_variations": listing.has_variations,
        "price_amount": listing.price_amount,
        "quantity": listing.quantity,
        "processing_min": listing.processing_min,
        "processing_max": listing.processing_max,
        "personalization_char_count_max": listing.personalization_char_count_max,
        "item_weight": _float_or_none(listing.item_weight),
        "item_length": _float_or_none(listing.item_length),
        "item_width": _float_or_none(listing.item_width),
        "item_height": _float_or_none(listing.item_height),
        "tags": list(listing.tags) if isinstance(listing.tags, list) else [],
        "materials": list(listing.materials) if isinstance(listing.materials, list) else [],
    }


# ── pure functions (no DB) ─────────────────────────────────────────────────────

def apply_change_to_listing_data(before_data: dict, change: BulkEditChange) -> dict:
    """Apply one session-level change to listing data dict. Returns new dict (no mutation)."""
    import copy
    data = copy.deepcopy(before_data)
    field = change.field_name
    op = change.operation
    val = change.operation_value

    if field not in EDITABLE_FIELDS:
        return data

    current = data.get(field)

    if op == "set":
        data[field] = val

    elif op == "append" and field in TEXT_FIELDS:
        data[field] = (current or "") + str(val or "")

    elif op == "prepend" and field in TEXT_FIELDS:
        data[field] = str(val or "") + (current or "")

    elif op == "replace" and field in TEXT_FIELDS:
        find = val.get("find", "") if isinstance(val, dict) else ""
        replace = val.get("replace", "") if isinstance(val, dict) else ""
        data[field] = (current or "").replace(find, replace)

    elif op == "add_tag" and field in ARRAY_FIELDS:
        lst = list(current) if isinstance(current, list) else []
        tag = str(val) if val is not None else ""
        if tag and tag not in lst:
            lst.append(tag)
        data[field] = lst

    elif op == "remove_tag" and field in ARRAY_FIELDS:
        lst = list(current) if isinstance(current, list) else []
        tag = str(val) if val is not None else ""
        data[field] = [t for t in lst if t != tag]

    elif op == "percentage_change" and field in NUMBER_FIELDS:
        if current is not None:
            try:
                pct = float(val)
                data[field] = round(current * (1 + pct / 100))
            except (TypeError, ValueError):
                pass

    elif op == "fixed_amount_change" and field in NUMBER_FIELDS:
        if current is not None:
            try:
                data[field] = current + float(val)
            except (TypeError, ValueError):
                pass

    return data


def validate_listing_data(after_data: dict) -> dict:
    """Validate after_data. Returns {"status": "valid"|"warning"|"invalid", "messages": [...]}."""
    messages: list[dict] = []
    worst = "valid"

    def add(level: str, field: str, msg: str):
        nonlocal worst
        messages.append({"level": level, "field": field, "message": msg})
        if level == "invalid":
            worst = "invalid"
        elif level == "warning" and worst == "valid":
            worst = "warning"

    title = after_data.get("title")
    if title is not None:
        if not str(title).strip():
            add("invalid", "title", "Title must not be empty.")
        elif len(str(title)) > 140:
            add("invalid", "title", f"Title too long ({len(str(title))} chars, max 140).")
        elif len(str(title)) < 20:
            add("warning", "title", f"Title is short ({len(str(title))} chars). Consider > 20 for better SEO.")

    desc = after_data.get("description")
    if desc is not None and len(str(desc)) < 50:
        add("warning", "description", "Description is short (< 50 chars).")

    tags = after_data.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            add("invalid", "tags", "Tags must be a list.")
        else:
            if len(tags) > 13:
                add("invalid", "tags", f"Too many tags ({len(tags)}, max 13).")
            if len(tags) != len(set(tags)):
                add("invalid", "tags", "Duplicate tags are not allowed.")
            for t in tags:
                if len(str(t)) > 20:
                    add("invalid", "tags", f"Tag '{t}' exceeds 20 characters.")
                    break
            if len(tags) == 0:
                add("warning", "tags", "No tags — listings with tags rank higher.")

    price = after_data.get("price_amount")
    if price is not None:
        try:
            p = float(price)
            if p < 0:
                add("invalid", "price_amount", "Price must be >= 0.")
            elif p == 0:
                add("warning", "price_amount", "Price is 0.")
        except (TypeError, ValueError):
            add("invalid", "price_amount", "Price must be a number.")

    qty = after_data.get("quantity")
    if qty is not None:
        try:
            q = int(qty)
            if q < 0:
                add("invalid", "quantity", "Quantity must be >= 0.")
        except (TypeError, ValueError):
            add("invalid", "quantity", "Quantity must be an integer.")

    pmin = after_data.get("processing_min")
    pmax = after_data.get("processing_max")
    if pmin is not None and pmax is not None:
        try:
            if int(pmin) > int(pmax):
                add("invalid", "processing_min", "processing_min must be <= processing_max.")
        except (TypeError, ValueError):
            pass

    pcc = after_data.get("personalization_char_count_max")
    if pcc is not None:
        try:
            if int(pcc) < 0:
                add("invalid", "personalization_char_count_max", "personalization_char_count_max must be >= 0.")
        except (TypeError, ValueError):
            pass

    is_req = after_data.get("personalization_is_required")
    is_pers = after_data.get("is_personalizable")
    if is_req and not is_pers:
        add("warning", "personalization_is_required", "personalization_is_required is True but is_personalizable is not True.")

    return {"status": worst, "messages": messages}


def compute_diff(before_data: dict, after_data: dict) -> dict:
    diff: dict = {}
    all_keys = set(list(before_data.keys()) + list(after_data.keys()))
    for key in all_keys:
        b = before_data.get(key)
        a = after_data.get(key)
        if b != a:
            diff[key] = {"before": b, "after": a}
    return diff


# ── service functions (async DB) ───────────────────────────────────────────────

async def create_bulk_edit_session(
    db: AsyncSession,
    organization_id: str,
    user_id: str,
    listing_ids: list[str],
    name: str | None = None,
) -> BulkEditSession:
    if not listing_ids:
        raise HTTPException(status_code=400, detail="listing_ids must not be empty.")
    deduped = list(dict.fromkeys(listing_ids))

    result = await db.execute(
        select(Listing).where(
            Listing.id.in_(deduped),
            Listing.organization_id == organization_id,
        )
    )
    found = result.scalars().all()
    if len(found) != len(deduped):
        raise HTTPException(
            status_code=400,
            detail="One or more listing IDs not found or do not belong to your organization.",
        )

    session = BulkEditSession(
        organization_id=organization_id,
        created_by_user_id=user_id,
        name=name,
        status="draft",
        selected_listing_ids=deduped,
        selected_count=len(deduped),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_bulk_edit_sessions(
    db: AsyncSession,
    organization_id: str,
) -> list[BulkEditSession]:
    result = await db.execute(
        select(BulkEditSession)
        .where(BulkEditSession.organization_id == organization_id)
        .order_by(BulkEditSession.created_at.desc())
    )
    return list(result.scalars().all())


async def get_bulk_edit_session(
    db: AsyncSession,
    session_id: str,
    organization_id: str,
) -> BulkEditSession:
    result = await db.execute(
        select(BulkEditSession).where(
            BulkEditSession.id == session_id,
            BulkEditSession.organization_id == organization_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Bulk edit session not found.")
    return session


async def cancel_bulk_edit_session(
    db: AsyncSession,
    session_id: str,
    organization_id: str,
) -> BulkEditSession:
    session = await get_bulk_edit_session(db, session_id, organization_id)
    session.status = "canceled"
    session.canceled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session


async def add_bulk_edit_change(
    db: AsyncSession,
    session_id: str,
    organization_id: str,
    field_name: str,
    operation: str,
    operation_value,
) -> BulkEditChange:
    session = await get_bulk_edit_session(db, session_id, organization_id)

    if session.status not in ("draft", "preview_ready"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot add changes to a session with status '{session.status}'.",
        )

    if field_name not in EDITABLE_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Field '{field_name}' is not editable. Allowed: {sorted(EDITABLE_FIELDS)}",
        )

    allowed_ops = FIELD_OPS.get(field_name, set())
    if operation not in allowed_ops:
        raise HTTPException(
            status_code=400,
            detail=f"Operation '{operation}' not valid for field '{field_name}'. Allowed: {sorted(allowed_ops)}",
        )

    change = BulkEditChange(
        bulk_edit_session_id=session_id,
        field_name=field_name,
        operation=operation,
        operation_value=operation_value,
        validation_status="pending",
    )
    db.add(change)
    session.status = "draft"
    await db.commit()
    await db.refresh(change)
    return change


async def remove_bulk_edit_change(
    db: AsyncSession,
    session_id: str,
    change_id: str,
    organization_id: str,
) -> None:
    session = await get_bulk_edit_session(db, session_id, organization_id)

    result = await db.execute(
        select(BulkEditChange).where(
            BulkEditChange.id == change_id,
            BulkEditChange.bulk_edit_session_id == session_id,
        )
    )
    change = result.scalar_one_or_none()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found.")
    await db.delete(change)
    await db.commit()


async def generate_bulk_edit_preview(
    db: AsyncSession,
    session_id: str,
    organization_id: str,
) -> dict:
    session = await get_bulk_edit_session(db, session_id, organization_id)

    if session.status == "canceled":
        raise HTTPException(status_code=400, detail="Cannot preview a canceled session.")

    listing_ids: list[str] = list(session.selected_listing_ids or [])
    if not listing_ids:
        raise HTTPException(status_code=400, detail="Session has no selected listings.")

    result = await db.execute(
        select(Listing).where(
            Listing.id.in_(listing_ids),
            Listing.organization_id == organization_id,
        )
    )
    listings = {l.id: l for l in result.scalars().all()}

    # Etsy listing-content freshness: Etsy's own caching rules treat listing
    # content as stale past a few hours — surface a warning before the user
    # reaches final confirmation rather than silently trusting an old sync.
    # See ETSY_DATA_RETENTION.md §1.
    stale_cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
    stale_listing_ids: list[str] = []
    for l in listings.values():
        synced = l.last_synced_at
        if synced is None:
            continue
        if synced.tzinfo is None:
            synced = synced.replace(tzinfo=timezone.utc)
        if synced < stale_cutoff:
            stale_listing_ids.append(l.id)

    changes_result = await db.execute(
        select(BulkEditChange).where(BulkEditChange.bulk_edit_session_id == session_id)
    )
    changes = list(changes_result.scalars().all())

    counts = {"valid": 0, "warning": 0, "invalid": 0}

    for lid in listing_ids:
        listing = listings.get(lid)
        if not listing:
            continue

        before_data = build_before_data(listing)

        after_data = before_data.copy()
        for change in changes:
            targets = change.target_listing_ids
            if targets is None or lid in targets:
                after_data = apply_change_to_listing_data(after_data, change)

        validation = validate_listing_data(after_data)
        vstatus = validation["status"]
        counts[vstatus] = counts.get(vstatus, 0) + 1

        diff = compute_diff(before_data, after_data)

        existing_result = await db.execute(
            select(BulkEditPreviewItem).where(
                BulkEditPreviewItem.bulk_edit_session_id == session_id,
                BulkEditPreviewItem.listing_id == lid,
            )
        )
        item = existing_result.scalar_one_or_none()

        if item:
            item.listing_title = listing.title
            item.before_data = before_data
            item.after_data = after_data
            item.diff = diff
            item.validation_status = vstatus
            item.validation_messages = validation["messages"]
        else:
            item = BulkEditPreviewItem(
                bulk_edit_session_id=session_id,
                listing_id=lid,
                listing_title=listing.title,
                before_data=before_data,
                after_data=after_data,
                diff=diff,
                validation_status=vstatus,
                validation_messages=validation["messages"],
            )
            db.add(item)

    session.status = "preview_ready"
    session.preview_generated_at = datetime.now(timezone.utc)
    session.change_count = len(changes)
    await db.commit()
    await db.refresh(session)

    count_result = await db.execute(
        select(func.count()).select_from(
            select(BulkEditPreviewItem)
            .where(BulkEditPreviewItem.bulk_edit_session_id == session_id)
            .subquery()
        )
    )
    total_items = count_result.scalar_one()

    return {
        "session": session,
        "summary": {
            "selected_count": session.selected_count,
            "preview_items": total_items,
            "valid": counts.get("valid", 0),
            "warning": counts.get("warning", 0),
            "invalid": counts.get("invalid", 0),
            "stale_listing_count": len(stale_listing_ids),
        },
    }


async def get_bulk_edit_preview_page(
    db: AsyncSession,
    session_id: str,
    organization_id: str,
    page: int = 1,
    per_page: int = 50,
    validation_status: str | None = None,
) -> dict:
    await get_bulk_edit_session(db, session_id, organization_id)

    q = select(BulkEditPreviewItem).where(BulkEditPreviewItem.bulk_edit_session_id == session_id)
    if validation_status:
        q = q.where(BulkEditPreviewItem.validation_status == validation_status)

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar_one()

    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = list(result.scalars().all())

    return {"items": items, "page": page, "per_page": per_page, "total": total, "session_id": session_id}


async def apply_bulk_edit_stub(
    db: AsyncSession,
    session_id: str,
    organization_id: str,
) -> None:
    """
    Sprint 7 stub — intentionally disabled.
    Etsy write operations start in Sprint 8.
    """
    await get_bulk_edit_session(db, session_id, organization_id)
    raise HTTPException(
        status_code=409,
        detail="Etsy write operations start in Sprint 8. This endpoint is intentionally disabled.",
    )
