# PROJECT_STATUS.md

## Current Phase

**Sprint 8 — Etsy Write + Backup — COMPLETE**

## Status

`Sprint 8 COMPLETE — Ready for Sprint 9`

## Last Updated

2026-06-25

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
- Etsy access token auto-refresh not fully implemented. Partial: logs warning but uses token anyway. Full auto-refresh deferred to Sprint 9+.
- `fetch_listing_videos` best-effort: returns empty list on 404/405.
- Inline sync blocks HTTP thread. Celery background task deferred to Sprint 9.
- Price/quantity Etsy writes NOT implemented — deferred to Sprint 9 (requires Etsy inventory endpoint).
- Photo/video Etsy writes NOT implemented — deferred to Sprint 11.
- Magic Revert UI not implemented — snapshots exist in DB, revert API deferred to Sprint 9.

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
| **Full suite `pytest`** | **153/153 PASSED** |

## Sprint 8 — New Files

| File | Description |
|---|---|
| `app/models/listing_backup_snapshot.py` | Pre-write snapshot of listing data |
| `app/models/bulk_edit_apply_job.py` | Apply job with status + counters |
| `app/models/bulk_edit_apply_result.py` | Per-listing result with request/response payload |
| `app/models/audit_log.py` | Immutable event log |
| `alembic/versions/0006_create_bulk_edit_apply_tables.py` | Migration for 4 new tables |
| `app/schemas/bulk_edit_apply.py` | ApplyJobOut, ApplyResultOut, BackupSnapshotOut |
| `app/services/etsy_write.py` | Etsy PATCH wrapper + payload builder |
| `app/services/bulk_edit_apply.py` | Full apply orchestration with all safety gates |
| `tests/test_bulk_edit_apply.py` | 22 tests (unit + API) |

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
| Sprints complete | 8 / 18 |
| Backend Python files | 82+ |
| Frontend TypeScript files | 24 |
| Total tests | 153 |
| Open blockers | 0 |

## Next Action

Begin Sprint 9: Magic Revert. See HANDOFF.md for exact prompt.
