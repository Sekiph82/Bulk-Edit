# Bulk Edit Engine

## Overview

The bulk edit engine accumulates field-level changes for a set of listings, generates a before/after diff for preview, and applies changes to Etsy one listing at a time with rate limiting, rollback on failure, and audit logging.

---

## Session State Machine

```
draft → previewing → applying → complete
                              → failed (partial)
```

- `draft`: Session created, changes accumulating
- `previewing`: Preview generated and sent to frontend
- `applying`: Background job running Etsy writes
- `complete`: All changes applied (some may have failed)
- `failed`: Job crashed before completing

---

## Edit Modes

| Mode | Description | Applicable Fields |
|---|---|---|
| `set` | Replace entire field value | title, description, price, quantity, etc |
| `find_replace` | Find substring, replace with new | title, description, tags |
| `append` | Append text to end of field | title, description |
| `prepend` | Prepend text to start of field | title, description |
| `add_item` | Add to array without replacing | tags, materials |
| `remove_item` | Remove specific item from array | tags, materials |
| `multiply` | Multiply numeric value by factor | price |
| `add_fixed` | Add fixed amount to numeric | price |

---

## Preview Generation

For each listing in the session:
1. Load current field values from `listings` table
2. Apply staged changes in memory (do not write to DB yet)
3. Compute diff: `{ field, old_value, new_value }`
4. Return array of per-listing diffs

Preview is read-only. No Etsy API calls during preview.

---

## Apply Flow (per listing)

```
For each BulkEditChange in session:
  1. Take snapshot: INSERT INTO listing_snapshots
  2. Check subscription gate
  3. Build Etsy API PATCH payload from new_value
  4. Call Etsy API PATCH /listings/{etsy_listing_id}
  5. On success:
     - Update listings table with new value
     - Mark BulkEditChange.status = 'applied'
     - Write audit_log entry
  6. On failure:
     - Mark BulkEditChange.status = 'failed'
     - Store error_message
     - Log error
     - Continue to next listing (do not abort entire batch)
  7. Update bulk_edit_sessions counters
```

---

## Rate Limiting

- Max 10 Etsy API requests per second
- Celery task processes listings sequentially with `asyncio.sleep(0.1)` between requests
- On 429 from Etsy: pause 5 seconds, retry up to 3 times
- On persistent 429: mark session as paused, notify user

---

## Concurrency

- One Celery worker processes one bulk edit session at a time per organization
- Multiple organizations can have concurrent sessions
- Lock key: `celery:bulk_edit_lock:{organization_id}` in Redis (expires in 1 hour)

---

## Partial Failure Handling

- A session is `complete` even if some listings failed
- `bulk_edit_sessions.failed_count` tracks failures
- User sees per-listing status in results view
- Failed listings can be retried individually

---

## Snapshot Format

```json
{
  "listing_id": "uuid",
  "etsy_listing_id": 12345,
  "title": "...",
  "description": "...",
  "price": "29.99",
  "quantity": 5,
  "tags": ["tag1", "tag2"],
  "materials": [...],
  "images": [{ "etsy_image_id": ..., "rank": 0, "url": "...", "alt_text": "..." }],
  "variations": [...],
  "snapshot_timestamp": "2026-06-25T..."
}
```

Stored as JSONB in `listing_snapshots.snapshot_data`.
