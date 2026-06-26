# PROJECT_STATUS.md

## Current Phase

**Sprint 13: AI Tools — COMPLETE**

## Status

`AI listing optimizer live (/ai). Provider abstraction (mock/openai/anthropic), 9 endpoints, 32 tests. Sprint 14 (CSV) is next.`

## Last Updated

2026-06-26

## Active Skills

None (between sprints)

## Completed Sprints

- Sprint 0: Project Memory and Operating System ✓
- Sprint 1: Monorepo Skeleton ✓
- Sprint 2: Auth + Organization ✓
- Sprint 3: Stripe Billing and Feature Gates ✓
- Sprint 4: Etsy OAuth2 PKCE Flow ✓
- Sprint 5: Etsy Listing Sync ✓
- Sprint 6: Listings Grid UX ✓
- Sprint 7: Bulk Edit Preview Engine ✓
- Sprint 8: Etsy Write + Backup ✓
- Sprint 9: Magic Revert ✓
- Sprint 10: Etsy Inventory Writes (Price/Quantity) ✓
- Sprint 11: Photo / Video Bulk Editor ✓
- Sprint 12: Variation Editor ✓
- Productization UI Sprint ✓ (Design system installed, all 9 customer-facing pages polished, build passing)
- Landing Animation Sprint ✓ (AnimatedProductDemo + 2-column hero, motion v12, build passing)
- Sprint 13: AI Tools ✓ (provider abstraction, 9 endpoints, 32 tests, /ai page, 304/304 suite)

## Local Development (Windows)

**For developers (already have Docker + repo cloned):**
- `start-dev.bat` — double-click to start all services (preserves volumes, streams logs)
- `start-dev-clean.bat` — full reset including volume deletion (requires typing YES to confirm)

**For friend / reviewer (no developer tools needed):**
- `setup-and-start.bat` — double-click; installs Git + Docker Desktop via winget if missing, clones repo to Desktop, builds, starts, opens browser at http://localhost:3100
- `setup-and-start-clean.bat` — same with volume reset (requires YES confirmation)

All scripts: check Docker, auto-create `.env` from `.env.example` if missing, enforce `docker compose -p bulk-edit` project name, safely stop old `fmcg-erp-system-main` ERP containers before starting.

## Blockers

None

## Known Issues

- `anyio==4.6.2` in requirements-dev.txt is yanked. Works fine. Upgrade when 4.7.0 stable.
- Frontend `npm install` not run — node_modules absent. Run `npm install` or `docker compose up`.
- Etsy access token auto-refresh not fully implemented. Partial: logs warning but uses token anyway. Full auto-refresh deferred to Sprint 10+.
- `fetch_listing_videos` best-effort: returns empty list on 404/405.
- Inline sync blocks HTTP thread. Celery background task deferred to Sprint 10.
- Price/quantity Etsy writes implemented (Sprint 10). Variation listings handled in Sprint 12 variation editor.
- Photo/video Etsy writes implemented (Sprint 11). Video upload/delete/reorder stubs only — requires direct file upload or S3 (Sprint 12+).
- Variation inventory writes implemented (Sprint 12). Revert for variations deferred to Sprint 13 — backup snapshots created to enable it.
- AuditLog model uses `extra_data` attribute in Python (SQLAlchemy reserved `metadata` name), stored as `metadata` column in DB.

## Test Results

| Test File | Result |
|---|---|
| `pytest tests/test_health.py` | 4/4 PASSED |
| `pytest tests/test_auth.py` | 14/14 PASSED |
| `pytest tests/test_billing.py` | 26/26 PASSED |
| `pytest tests/test_etsy.py` | 15/15 PASSED |
| `pytest tests/test_listings.py` | 34/34 PASSED |
| `pytest tests/test_bulk_edit.py` | 38/38 PASSED |
| `pytest tests/test_bulk_edit_apply.py` | 22/22 PASSED |
| `pytest tests/test_bulk_edit_revert.py` | 28/28 PASSED |
| `pytest tests/test_bulk_edit_inventory.py` | 19/19 PASSED |
| `pytest tests/test_bulk_edit_media.py` | 25/25 PASSED |
| `pytest tests/test_bulk_edit_variation.py` | 47/47 PASSED |
| `pytest tests/test_ai_tools.py` | 32/32 PASSED |
| **Full suite `pytest`** | **304/304 PASSED** |

## Sprint 11 — New Files

| File | Description |
|---|---|
| `app/models/bulk_edit_media_job.py` | Media job tracking (status machine, counters) |
| `app/models/bulk_edit_media_result.py` | Per-listing media write result |
| `app/models/listing_media_backup_snapshot.py` | Pre-write images/videos snapshot |
| `alembic/versions/0008_create_bulk_edit_media_tables.py` | Migration for 3 new tables |
| `app/services/etsy_media_write.py` | Etsy image fetch/upload (multipart URL-download)/delete; video stubs |
| `app/schemas/bulk_edit_media.py` | 6 Pydantic schemas |
| `app/services/bulk_edit_media.py` | Full orchestration: create_media_job, apply_media_job, backup, audit |
| `app/api/v1/bulk_edit_media.py` | 6 REST endpoints |
| `tests/test_bulk_edit_media.py` | 25 tests |
| `apps/frontend/app/media/page.tsx` | Photo & Video Bulk Editor UI |

## Sprint 10 — Modified/New Files

| File | Description |
|---|---|
| `app/services/etsy_write.py` | Added `build_etsy_inventory_payload` + `patch_etsy_listing_inventory` |
| `app/services/bulk_edit_apply.py` | Dual-write: listing PATCH + inventory PUT; structured payloads |
| `app/services/bulk_edit_revert.py` | Inventory revert from snapshot; local price restored only after success |
| `tests/test_bulk_edit_inventory.py` | 19 tests (9 unit + 10 integration) |
| `apps/frontend/app/bulk-edit/page.tsx` | Revert modal warning updated; variation skip notice added |

## Sprint 9 — New Files

| File | Description |
|---|---|
| `app/models/revert_job.py` | Revert job with status + counters |
| `app/models/revert_result.py` | Per-listing revert result (nullable backup_snapshot_id) |
| `alembic/versions/0007_create_bulk_edit_revert_tables.py` | Migration for revert_jobs + revert_results |
| `app/schemas/bulk_edit_revert.py` | RevertJobOut, RevertResultOut, RevertJobWithResultsOut, RevertResultPageOut |
| `app/services/bulk_edit_revert.py` | Full revert orchestration with safety gates |
| `tests/test_bulk_edit_revert.py` | 28 tests (unit + API) |

## Safety Gates (Sprint 9)

All enforced in `revert_apply_job()` before any revert write:
1. `ETSY_CLIENT_ID` must be configured
2. Apply job must belong to organization (404 if not)
3. Apply job must be `completed` or `completed_with_errors`
4. No existing completed/running RevertJob for this apply job (409 if duplicate)
5. Only `success` apply results are iterated (never reverts failed results)
6. Per-listing: uses pre-write backup snapshot as source of truth
7. Local Listing row updated ONLY after Etsy revert write success
8. Backup snapshots never deleted
9. Audit log written on revert start + revert finish
10. Partial failures supported — each listing gets its own RevertResult row

## Safety Gates (Sprint 8)

All enforced in `apply_bulk_edit_session()` before any write:
1. Session must be `preview_ready`
2. Zero `invalid` preview items
3. `ETSY_CLIENT_ID` must be configured (non-placeholder)
4. Plan usage limit not exceeded
5. Per-listing: backup snapshot created BEFORE write
6. Local Listing row updated ONLY after Etsy write success
7. Audit log written on job start + job finish

## Port Configuration

| Service | Host Port | Container Port |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Metrics

| Metric | Value |
|---|---|
| Sprints complete | 15 / 18 (incl. Productization UI Sprint + Landing Animation Sprint + Sprint 13 AI Tools) |
| Backend Python files | 107+ |
| Frontend TypeScript files | 28 |
| Total tests | 304 |
| Open blockers | 0 |

## Next Action

Begin Sprint 14: CSV Import/Export. See HANDOFF.md for exact prompt.
