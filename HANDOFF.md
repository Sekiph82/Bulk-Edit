# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-25
**Sprint:** 8 — Etsy Write + Backup — COMPLETE
**Completed:** 4 new models (ListingBackupSnapshot, BulkEditApplyJob, BulkEditApplyResult, AuditLog), migration 0006, etsy_write.py service, bulk_edit_apply.py service with full safety gate chain, 5 new API endpoints (replace apply stub + apply-jobs + apply-job detail + backups), 22 new tests (153/153 pass), frontend apply confirmation modal + result display, api.ts helpers. Committed and pushed.

## Current State

**Backend (`apps/backend/`):**
- `app/models/listing_backup_snapshot.py` — pre-write snapshot before any Etsy write
- `app/models/bulk_edit_apply_job.py` — job tracker with status + counters
- `app/models/bulk_edit_apply_result.py` — per-listing result with request/response payloads
- `app/models/audit_log.py` — immutable event log (extra_data JSON column, named "metadata" in DB)
- `app/schemas/bulk_edit_apply.py` — ApplyJobOut, ApplyResultOut, BackupSnapshotOut, ApplyJobWithResultsOut
- `app/services/etsy_write.py` — build_etsy_patch_payload (excludes price/qty), patch_etsy_listing (PATCH v3)
- `app/services/bulk_edit_apply.py` — apply_bulk_edit_session (full orchestration with 5 safety gates)
- `app/api/v1/bulk_edit.py` — 14 endpoints total (9 Sprint 7 + 5 Sprint 8: apply/202, apply-jobs list, apply-job detail, backups)
- `alembic/versions/0006_create_bulk_edit_apply_tables.py`
- `tests/test_bulk_edit_apply.py` — 22 tests

**Frontend (`apps/frontend/`):**
- `lib/api.ts` — added ApplyJob, ApplyResult, ApplyJobWithResults, BackupSnapshot types + 4 helpers (applyBulkEditSession, listApplyJobs, getApplyJobDetail, listBackupSnapshots)
- `app/bulk-edit/page.tsx` — confirmation modal + real apply call + result status display

**What NOT implemented in Sprint 8 (by design):**
- Price/quantity writes (deferred to Sprint 9 — needs Etsy inventory endpoint)
- Photo/video writes (deferred to Sprint 11)
- Magic Revert UI (snapshots exist in DB, revert API deferred to Sprint 9)
- Celery async apply (inline/synchronous for MVP)

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Next Task

**Sprint 9: Magic Revert**

Implement the ability to revert applied bulk edit changes using the backup snapshots created in Sprint 8.

Implement:
- `RevertJob` model (org-scoped, apply_job_id FK, session_id FK, status, counters, started/finished_at)
- `RevertResult` model (per-listing result: status, snapshot_id FK, request/response payload, error)
- Alembic migration 0007 for revert tables
- `POST /api/v1/bulk-edit/apply-jobs/{job_id}/revert` — create a revert job: for each success result in the apply job, load the backup snapshot, PATCH Etsy with snapshot_data values, update local Listing row
- `GET /api/v1/bulk-edit/revert-jobs/{revert_job_id}` — get revert job with per-listing results
- Safety rules:
  - Cannot revert an already-reverted apply job
  - Skip listings where backup snapshot is missing
  - Write audit log on revert start + finish
  - Never modify local Listing rows unless Etsy write succeeds
  - Subscription gate check (same as apply)
- Frontend: add "Revert" button next to apply result display (only visible after apply, only if job status is completed or completed_with_errors)
- Frontend: revert result modal showing per-listing success/failure
- 15+ backend tests in `test_bulk_edit_revert.py`
- Price/quantity inventory write (Etsy PATCH /v3/application/shops/{shop_id}/listings/{listing_id}/inventory) deferred to Sprint 10
- No full "Magic Revert" UI (history browser) in Sprint 9 — just direct revert of a specific apply job

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Start Sprint 9: Magic Revert — implement revert of a completed bulk edit apply job using
the ListingBackupSnapshot records created in Sprint 8. POST revert endpoint, RevertJob/RevertResult
models, Alembic migration 0007, safety gates identical to Sprint 8 apply (no write without
preview check, subscription gate, audit log), frontend Revert button + result display.
15+ tests. No price/quantity writes yet.

Active skills: 07 backend-api, 06 database-modeling, 08 frontend-ui, 20 testing-qa, 01 documentation-handoff.
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

- Etsy access token auto-refresh not implemented. Logs warning but uses token. Full refresh deferred to Sprint 9+.
- `fetch_listing_videos` is best-effort — returns empty list on 404/405.
- Sync runs inline in HTTP thread. Celery background task deferred to Sprint 9.
- Frontend npm not installed — `node_modules/` absent. Run `npm install` inside `apps/frontend` or `docker compose up`.
- Price/quantity writes NOT supported in Sprint 8 — Etsy inventory endpoint required (Sprint 9).
- Photo/video writes NOT supported — deferred to Sprint 11.
- AuditLog model uses `extra_data` attribute in Python (SQLAlchemy reserved `metadata` name), stored as `metadata` column in DB.

## Push Status

Pushed successfully to: https://github.com/Sekiph82/Bulk-Edit (main)
Commit: feat: add safe etsy write and backups (Sprint 8)
