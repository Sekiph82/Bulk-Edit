# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-25
**Sprint:** 10 — Etsy Inventory Writes (Price / Quantity) — COMPLETE
**Completed:** `build_etsy_inventory_payload` + `patch_etsy_listing_inventory` in `etsy_write.py`, dual-write in `bulk_edit_apply.py` (listing PATCH → inventory PUT, structured payloads, local price/qty gated on inventory success), inventory revert in `bulk_edit_revert.py` (snapshot → revert PUT, local restore gated), 19 new tests (200/200 pass), frontend revert modal warning updated + variation listing skip notice. Committed and pushed.

## Current State

**Backend (`apps/backend/`):**
- `app/services/etsy_write.py` — `build_etsy_inventory_payload`, `patch_etsy_listing_inventory` (Sprint 10)
- `app/services/bulk_edit_apply.py` — dual-write apply (listing PATCH + inventory PUT), structured request/response payloads, variation skip detection
- `app/services/bulk_edit_revert.py` — dual-write revert (listing PATCH + inventory revert PUT), local price/qty restore only after inventory revert success
- `tests/test_bulk_edit_inventory.py` — 19 tests (9 unit for `build_etsy_inventory_payload`, 6 apply integration, 3 revert integration, 1 structured payload)
- All prior Sprint 9 files unchanged (revert_job, revert_result models, migration 0007, schemas, 28 revert tests)

**Frontend (`apps/frontend/`):**
- `app/bulk-edit/page.tsx` — revert modal: updated warning ("price and quantity now included"), variation listing notice in preview when `after_data.has_variations=true` and price_amount/quantity in diff

**What NOT implemented in Sprint 10 (by design):**
- Variation-level inventory (multiple SKU offerings per listing) — deferred to Sprint 12
- Photo/video writes — deferred to Sprint 11
- Celery async apply/revert — inline/synchronous for MVP

## Partial Write Caveat (documented)

If listing PATCH succeeds but inventory PUT fails: Etsy has new text but not new price. Local DB is not updated (next sync resolves). Same applies to revert. This is accepted behavior — logged as warning.

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Next Task

**Sprint 11: Photo / Video Bulk Editor**

Implement bulk photo operations using Etsy's image API endpoints.

Context:
- Etsy API: `GET /v3/application/shops/{shop_id}/listings/{listing_id}/images` — list images
- Etsy API: `POST /v3/application/shops/{shop_id}/listings/{listing_id}/images` — upload image
- Etsy API: `DELETE /v3/application/shops/{shop_id}/listings/{listing_id}/images/{listing_image_id}` — delete
- `fetch_listing_images` already exists in `etsy_sync.py` (Sprint 5) — images stored as JSONB in `listing.images`
- `fetch_listing_videos` already exists in `etsy_sync.py` — videos stored in `listing.videos`
- Photo bulk operations: replace all photos, reorder photos, add a photo to all listings, remove a photo by position
- Video: assign/replace listing video

Implement:
- New model `BulkEditMediaJob` (similar to `BulkEditApplyJob`) or extend apply to handle media ops
- Media write safety: preview → confirm → backup → write → audit log (same safety contract)
- `etsy_media_write.py` service for image/video API calls
- Wire to bulk edit session: new media-specific change types (`replace_image`, `add_image`, `remove_image`, `set_video`)
- 15+ tests in `test_bulk_edit_media.py`
- Frontend: media operation UI in bulk edit session (upload + preview photo before applying)
- Deferred: AI alt text for photos (Sprint 13)

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Start Sprint 11: Photo/Video Bulk Editor — implement bulk photo operations (replace, add, remove, reorder)
using Etsy's image API endpoints. Wire into existing bulk edit session flow with full safety gate chain.
Video support: assign/replace listing video. 15+ tests. Single image per operation (no batch upload in this sprint).

Active skills: 07 backend-api, 06 database-modeling, 20 testing-qa, 01 documentation-handoff.
```

## Dev Startup Scripts

Four Windows batch files at project root:

| File | Who uses it | What it does |
|---|---|---|
| `setup-and-start.bat` | Friend / reviewer | Installs Git + Docker if missing, clones repo, starts app, opens browser at http://localhost:3100 |
| `setup-and-start-clean.bat` | Friend / reviewer | Same as above + destroys DB volumes (requires YES confirmation) |
| `start-dev.bat` | Developer (already cloned) | Stops old containers, rebuilds, streams logs — no tool install |
| `start-dev-clean.bat` | Developer (already cloned) | Same + destroys DB volumes (requires YES confirmation) |

**ASCII-only scripts:** all .bat files must remain plain ASCII. No Unicode, no box-drawing chars, no long dashes, no chcp 65001.

**Docker Desktop auto-start:** all scripts automatically start Docker Desktop and poll `docker info` every 5 seconds (max 180s) before running any compose command.

**Docker project isolation:** all scripts force `docker compose -p bulk-edit` to prevent accidental interference with other Docker Compose projects.

## Known Issues

- Etsy access token auto-refresh not implemented. Logs warning but uses token. Full refresh deferred to Sprint 10+.
- `fetch_listing_videos` is best-effort — returns empty list on 404/405.
- Sync runs inline in HTTP thread. Celery background task deferred to a future sprint.
- Frontend npm not installed — `node_modules/` absent. Run `npm install` inside `apps/frontend` or `docker compose up`.
- Variation inventory writes NOT supported — variation listings with price/quantity changes are skipped (deferred to Sprint 12).
- Photo/video writes NOT supported — deferred to Sprint 11.
- AuditLog model uses `extra_data` attribute in Python (SQLAlchemy reserved `metadata` name), stored as `metadata` column in DB.
- RevertResult.backup_snapshot_id is nullable — skipped items (no listing, no snapshot, no token, empty payload) store NULL.
- Partial write caveat: if listing PATCH succeeds but inventory PUT fails, Etsy has new text but not new price. Next sync resolves. Local DB not updated.

## Push Status

Pushed successfully to: https://github.com/Sekiph82/Bulk-Edit (main)
Commit: feat: add etsy inventory writes (Sprint 10)
