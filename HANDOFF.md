# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-25
**Sprint:** 9 — Magic Revert — COMPLETE
**Completed:** 2 new models (RevertJob, RevertResult), migration 0007, bulk_edit_revert.py service with full safety gate chain, 4 new API endpoints (POST revert/202, GET revert-jobs list, GET revert-job detail, GET paginated results), 28 new tests (181/181 pass), frontend Magic Revert button + REVERT text confirmation modal + result card, api.ts 4 new types + 4 helpers. Committed and pushed.

## Current State

**Backend (`apps/backend/`):**
- `app/models/revert_job.py` — RevertJob (org-scoped, apply_job_id FK, status, counters)
- `app/models/revert_result.py` — RevertResult (per-listing, backup_snapshot_id nullable FK SET NULL)
- `app/schemas/bulk_edit_revert.py` — RevertJobOut, RevertResultOut, RevertJobWithResultsOut, RevertResultPageOut
- `app/services/bulk_edit_revert.py` — full revert orchestration with 10 safety gates
- `app/api/v1/bulk_edit.py` — 18 endpoints total (+4 Sprint 9: POST revert, GET revert-jobs, GET revert-job detail, GET paginated results)
- `alembic/versions/0007_create_bulk_edit_revert_tables.py`
- `tests/test_bulk_edit_revert.py` — 28 tests
- All prior Sprint 8 files remain unchanged

**Frontend (`apps/frontend/`):**
- `lib/api.ts` — added RevertJob, RevertResult, RevertJobWithResults, RevertResultPage types + 4 helpers (revertApplyJob, listRevertJobs, getRevertJob, getRevertResults)
- `app/bulk-edit/page.tsx` — Magic Revert button (visible after successful apply), REVERT text confirmation modal, revert result status card

**What NOT implemented in Sprint 9 (by design):**
- Price/quantity writes (deferred to Sprint 10 — needs Etsy inventory endpoint)
- Photo/video revert (deferred to Sprint 11)
- Celery async revert (inline/synchronous for MVP)
- Per-field selective revert (full listing restore only)

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Next Task

**Sprint 10: Etsy Inventory Writes (Price / Quantity)**

Implement price and quantity bulk edit writes using the Etsy inventory endpoint.

Context:
- Sprint 8 explicitly excluded price/quantity from `build_etsy_patch_payload()` — they are in `EXCLUDED_FIELDS`
- The Etsy API requires a separate endpoint for price/quantity: `PUT /v3/application/shops/{shop_id}/listings/{listing_id}/inventory`
- Existing `BulkEditPreviewItem` already computes price_amount and quantity diffs but they are not written

Implement:
- `patch_etsy_listing_inventory(access_token, shop_etsy_id, listing_etsy_id, payload)` in `etsy_write.py`
- Payload format: `{"products": [{"sku": ..., "offerings": [{"price": {"amount": ..., "divisor": ...}, "quantity": ...}]}]}`
- Wire up to `apply_bulk_edit_session()` — if diff contains price_amount or quantity, call inventory endpoint after text PATCH
- Wire up to `revert_apply_job()` — if snapshot contains price_amount or quantity, call inventory endpoint during revert
- Add inventory fields to `build_etsy_revert_payload()` logic
- 15+ new tests in `test_bulk_edit_inventory.py`
- Update `test_bulk_edit_apply.py` — add test: inventory write called when price_amount in diff
- Deferred (Sprint 10 out of scope): Variation-level price/quantity (multiple sku offerings per listing)

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Start Sprint 10: Etsy Inventory Writes — implement price and quantity bulk edit writes using
the Etsy inventory endpoint (PUT /v3/application/shops/{shop_id}/listings/{listing_id}/inventory).
Wire into existing apply and revert flows. 15+ tests. Single-sku per listing only (no variation
multi-sku in this sprint).

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
- Sync runs inline in HTTP thread. Celery background task deferred to Sprint 10.
- Frontend npm not installed — `node_modules/` absent. Run `npm install` inside `apps/frontend` or `docker compose up`.
- Price/quantity writes NOT supported in Sprints 8/9 — Etsy inventory endpoint required (Sprint 10).
- Photo/video revert NOT supported — deferred to Sprint 11.
- AuditLog model uses `extra_data` attribute in Python (SQLAlchemy reserved `metadata` name), stored as `metadata` column in DB.
- RevertResult.backup_snapshot_id is nullable — skipped items (no listing, no snapshot, no token, empty payload) store NULL.

## Push Status

Pushed successfully to: https://github.com/Sekiph82/Bulk-Edit (main)
Commit: feat: add magic revert (Sprint 9)
