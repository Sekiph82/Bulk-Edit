# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-25
**Sprint:** 11 — Photo / Video Bulk Editor — COMPLETE
**Completed:** 3 new models (BulkEditMediaJob, BulkEditMediaResult, ListingMediaBackupSnapshot), Alembic migration 0008, etsy_media_write.py (image fetch/upload-from-URL/delete; video stubs 501), bulk_edit_media.py orchestration service, 6 API endpoints, 25 new tests (225/225 pass), frontend /media page, api.ts types + helpers, dashboard link updated. Committed and pushed.

## Current State

**Backend (`apps/backend/`):**
- `app/models/bulk_edit_media_job.py` — job status machine + counters
- `app/models/bulk_edit_media_result.py` — per-listing result with before/after_media JSON
- `app/models/listing_media_backup_snapshot.py` — images_snapshot + videos_snapshot JSON
- `alembic/versions/0008_create_bulk_edit_media_tables.py` — migration for 3 tables
- `app/services/etsy_media_write.py` — fetch images (GET), upload image (download-then-multipart-POST), delete image; video stubs raise EtsyMediaWriteError(not_implemented=True)
- `app/schemas/bulk_edit_media.py` — MediaJobCreate, MediaJobOut, MediaResultOut, MediaResultPageOut, MediaBackupSnapshotOut, MediaJobWithResultsOut
- `app/services/bulk_edit_media.py` — create_media_job, apply_media_job (add/replace/delete implemented; video/reorder skip-with-reason), _create_media_backup_snapshot, audit logs, partial failure support
- `app/api/v1/bulk_edit_media.py` — 6 endpoints under /api/v1/bulk-edit/media
- `tests/test_bulk_edit_media.py` — 25 tests

**Frontend (`apps/frontend/`):**
- `app/media/page.tsx` — listing selector, operation picker, image URL/rank/alt-text inputs, backup warning, APPLY MEDIA confirm modal, job history table, results panel
- `lib/api.ts` — MediaJob, MediaResult, MediaResultPage, MediaBackupSnapshot types + 6 helpers (createMediaJob, listMediaJobs, getMediaJob, applyMediaJob, getMediaResults, getMediaBackups)
- `app/dashboard/page.tsx` — Media Library card now links to /media

**What NOT implemented in Sprint 11 (by design):**
- Video upload/delete (requires server-side direct file upload; S3 deferred)
- Image reorder (Etsy has no atomic reorder endpoint; delete-all + re-upload deferred)
- AI alt text generation — Sprint 13
- Celery async apply — inline/synchronous MVP

## Safety Gates (Sprint 11)

All enforced in `apply_media_job()`:
1. `ETSY_CLIENT_ID` must be configured
2. Job must belong to organization (404 if not)
3. Job must be `pending` (400 if already running/completed)
4. Per-listing: backup snapshot created BEFORE any Etsy write
5. Local ListingImage rows updated ONLY after Etsy write success
6. Audit log on job start + job finish
7. Partial failure supported — each listing gets its own BulkEditMediaResult row
8. Backup snapshots never deleted

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Next Task

**Sprint 12: Variation Editor**

Implement bulk variation price/quantity/SKU editing across multiple listings.

Context:
- `ListingVariation` model exists (Sprint 5): `etsy_product_id`, `sku`, `property_name`, `value_name`, `price_amount`, `price_divisor`, `currency_code`, `quantity`, `is_available`
- Inventory write to Etsy: `PUT /v3/application/shops/{shop_id}/listings/{listing_id}/inventory` with full variation tree
- Listings with `has_variations=true` were skipped in Sprint 10 price/quantity writes (with skip reason logged)
- Need: bulk update variation price by % or fixed amount, bulk update variation quantity, bulk SKU rename

Implement:
- New model `BulkEditVariationJob` (similar pattern to media jobs)
- Variation write safety: preview → confirm → backup → write → audit log
- `etsy_variation_write.py` service (fetch variation tree, patch, PUT back)
- Variation change types: `set_variation_price`, `adjust_variation_price_pct`, `set_variation_quantity`, `set_variation_sku`
- 20+ tests in `test_bulk_edit_variation.py`
- Frontend: variation editor panel showing variation tree per listing before/after

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Start Sprint 12: Variation Editor — implement bulk variation price/quantity/SKU editing for Etsy listings with has_variations=true. Use Etsy's PUT inventory endpoint with full variation tree. Same safety gate chain as Sprints 8-11. 20+ tests. No AI in this sprint.

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

- Etsy access token auto-refresh not implemented. Logs warning but uses token. Full refresh deferred to future sprint.
- `fetch_listing_videos` is best-effort — returns empty list on 404/405.
- Sync runs inline in HTTP thread. Celery background task deferred to a future sprint.
- Frontend npm not installed — `node_modules/` absent. Run `npm install` inside `apps/frontend` or `docker compose up`.
- Variation inventory writes NOT supported in bulk edit sessions (Sprint 10 price/qty) — variation listings skipped. Deferred to Sprint 12.
- Video upload/delete NOT supported — Etsy requires direct file upload; URL-based not available. Stubs return 501. Deferred to Sprint 13+.
- Image reorder NOT supported — Etsy has no atomic reorder endpoint. Deferred.
- AuditLog model uses `extra_data` attribute in Python (SQLAlchemy reserved `metadata` name), stored as `metadata` column in DB.
- `anyio==4.6.2` in requirements-dev.txt is yanked — works fine, upgrade when 4.7.0 stable.

## Push Status

Pushed successfully to: https://github.com/Sekiph82/Bulk-Edit (main)
Commit: feat: add photo video bulk editor (Sprint 11)
