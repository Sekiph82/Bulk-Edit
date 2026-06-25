# Bulk Edit Engine

## Overview

The bulk edit engine accumulates field-level change rules for a set of listings, generates a before/after diff for preview, and (in Sprint 8+) applies changes to Etsy one listing at a time with rate limiting, snapshot backup, and audit logging.

---

## Session State Machine

### Sprint 7 (implemented)
```
draft → preview_ready
      → canceled
```

### Sprint 8+ (planned)
```
preview_ready → applying → applied
              → canceled
```

- `draft`: Session created, changes accumulating. Changes can be added/removed.
- `preview_ready`: Preview generated. Changes can be added (re-preview required).
- `canceled`: Soft-deleted. No further modifications allowed.
- `applying` / `applied`: Sprint 8 — Etsy writes in progress / complete.

---

## Change Operations (implemented Sprint 7)

| Operation | Field Types | Description |
|---|---|---|
| `set` | TEXT, BOOL, NUMBER, ARRAY | Replace entire field value |
| `append` | TEXT | Append string to end of field |
| `prepend` | TEXT | Prepend string to start of field |
| `replace` | TEXT | Find-and-replace substring |
| `add_tag` | ARRAY | Add item without replacing (dedup enforced) |
| `remove_tag` | ARRAY | Remove specific item from array |
| `percentage_change` | NUMBER | Multiply by (1 + value/100) |
| `fixed_amount_change` | NUMBER | Add fixed amount (can be negative) |

### Field Type Registry

```python
TEXT_FIELDS   = {title, description, sku, section_id, taxonomy_id, personalization_instructions}
BOOL_FIELDS   = {is_personalizable, is_customizable, personalization_is_required, has_variations}
NUMBER_FIELDS = {price_amount, quantity, processing_min, processing_max,
                 personalization_char_count_max, item_weight, item_length, item_width, item_height}
ARRAY_FIELDS  = {tags, materials}
```

---

## Preview Generation (implemented Sprint 7)

`POST /bulk-edit/sessions/{id}/preview` — reads listings from DB, applies changes in-memory, validates, computes diff, writes `BulkEditPreviewItem` rows (upsert on UNIQUE session+listing).

```
For each listing_id in session.selected_listing_ids:
  1. Load Listing row from DB
  2. build_before_data(listing) → dict of all editable fields
  3. For each BulkEditChange in session (ordered by created_at):
       after_data = apply_change_to_listing_data(before_data or after_data, change)
  4. validate_listing_data(after_data) → {status, messages}
  5. compute_diff(before_data, after_data) → {field: {before, after}} for changed fields only
  6. UPSERT BulkEditPreviewItem (session_id, listing_id)
7. Set session.status = preview_ready
8. Return summary: {valid_count, warning_count, invalid_count}
```

Preview is read-only. No Etsy API calls. No `listings` rows modified.

### Validation Rules

| Rule | Severity |
|---|---|
| title is empty | invalid |
| title > 140 chars | invalid |
| title < 20 chars | warning |
| description < 50 chars | warning |
| tags count > 13 | invalid |
| any tag > 20 chars | invalid |
| duplicate tags | invalid |
| tags count = 0 | warning |
| price_amount < 0 | invalid |
| price_amount = 0 | warning |
| quantity < 0 | invalid |
| processing_min > processing_max | invalid |
| personalization_char_count_max < 0 | invalid |
| personalization_is_required=True + is_personalizable=False | warning |

---

## Apply Flow (Sprint 8 — planned)

```
For each listing in preview_items (order by listing_id):
  1. Take snapshot: INSERT INTO listing_snapshots (before_data)
  2. Check subscription gate (bulk_edits_used limit)
  3. Build Etsy API PATCH payload from after_data diff
  4. Call Etsy PATCH /v3/application/listings/{etsy_listing_id}
  5. On success:
     - Update listings table fields
     - Increment usage_counters.bulk_edits_used
     - Write audit_log entry (action='bulk_edit.apply')
  6. On failure:
     - Log error, store in preview_item.validation_messages
     - Continue to next listing (no abort)
  7. Set session.status = applied / canceled (partial)
```

Apply endpoint in Sprint 7 returns 409 intentionally: `"Etsy write operations start in Sprint 8. This endpoint is intentionally disabled."`

---

## Rate Limiting (Sprint 8 — planned)

- Max 10 Etsy API requests per second
- Sequential processing with `asyncio.sleep(0.1)` between listings
- On 429: exponential backoff, retry up to 3 times
- On persistent 429: pause session, notify user

---

## Concurrency (Sprint 8 — planned)

- One Celery worker per organization (Redis lock: `celery:bulk_edit_lock:{org_id}`)
- Multiple organizations can run concurrent sessions

---

## Snapshot Format (Sprint 9 — planned)

```json
{
  "listing_id": "uuid",
  "etsy_listing_id": 12345678,
  "title": "...",
  "description": "...",
  "price_amount": 29.99,
  "quantity": 5,
  "tags": ["tag1", "tag2"],
  "materials": ["material1"],
  "is_personalizable": false,
  "snapshot_timestamp": "2026-06-25T12:00:00Z"
}
```

Stored as JSON in `listing_snapshots.snapshot_data` (Sprint 9 model).
