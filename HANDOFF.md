# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-26
**Sprint:** Sprint 14 — CSV Import / Export — COMPLETE
**Completed:** CSVJob + CSVRow models (alembic 0011). Added target_listing_ids to BulkEditChange so per-row values scope to specific listings. 6 CSV endpoints under /api/v1/csv (export, template, import, jobs, preview, convert). Import converts to BulkEditSession only — never writes to Etsy directly. 49 CSV tests pass. Frontend /csv page (export tab, import tab with preview table and convert, job history tab). Dashboard CSV card. 353/353 full suite passing. Build: 15 routes, zero errors.

## Previous Session

**Date:** 2026-06-26
**Sprint:** Sprint 13 — AI Tools — COMPLETE
**Completed:** Provider abstraction (mock/openai/anthropic). 5 prompt builders. AISession, AISuggestion, AIUsageLog models (alembic 0010). 9 endpoints under /api/v1/ai. Billing gate: paid plan required. Accept/reject suggestions per field. Convert accepted → BulkEditSession (draft only, never writes Etsy). 32 tests. /ai page. Dashboard AI card.

## Current State

**Backend (`apps/backend/`):**

**Sprint 14 additions (CSV Import / Export):**
- `app/models/csv_job.py` — CSVJob model (status machine: processing → preview_ready → converted/failed)
- `app/models/csv_row.py` — CSVRow model (per-row: listing_id, etsy_listing_id, raw_data, normalized_data, diff, status, errors, warnings)
- `app/models/bulk_edit_change.py` — added `target_listing_ids` JSON nullable column
- `alembic/versions/0011_create_csv_import_export_tables.py` — migration (adds column + creates 2 tables)
- `app/schemas/csv_tools.py` — 6 schemas (CSVJobOut, CSVRowOut, CSVPreviewPageOut, CSVConvertRequest, CSVConvertResponse, CSVImportSummaryOut)
- `app/services/csv_tools.py` — full service: export, template, parse, validate, import job, preview, convert to BulkEditSession
- `app/api/v1/csv_tools.py` — 6 REST endpoints under /api/v1/csv
- `app/api/v1/router.py` — includes csv_router
- `app/services/bulk_edit.py` — preview engine updated: `if targets is None or lid in targets: apply_change()`
- `tests/test_csv_tools.py` — 49 tests (all passing)

**Frontend (`apps/frontend/`):**
- `app/csv/page.tsx` — 3-tab page: Export (download CSV/template), Import (upload → summary → preview → convert), Job History
- `lib/api.ts` — CSVJob, CSVRow, CSVPreviewPage, CSVImportSummary, CSVConvertResult types + 7 helpers
- `app/dashboard/page.tsx` — CSV Import / Export card

## Safety Gates (Sprint 14)

CSV import enforces:
1. Only .csv extension and csv content types accepted
2. Max 5,000 rows (MAX_IMPORT_ROWS)
3. Each row must resolve to a listing by listing_id OR etsy_listing_id — cross-org rejects
4. Identity column mismatch (both provided but don't resolve to same listing) → invalid row
5. Convert blocks if any invalid rows (unless ignore_invalid=True)
6. Convert creates BulkEditSession with status="draft" — NEVER writes to Etsy
7. Each BulkEditChange gets target_listing_ids=[row.listing_id] — scope to specific listing
8. Preview engine: if targets is None → apply to all (existing behavior); if targets set → skip non-targets

## target_listing_ids Architecture

When `BulkEditChange.target_listing_ids` is:
- `None` → change applies to ALL selected listings (existing bulk edit behavior, backward compat)
- `[listing_id]` → change applies ONLY to that one listing (CSV import behavior)

This allows per-row different values in a single BulkEditSession without breaking existing bulk edit sessions.

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Next Task

**Sprint 15: Dynamic Pricing**

Implement rules-based price adjustments: percentage markup/markdown, rounding rules, competitor-based pricing.

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: 353/353 tests passing. Sprint 14 (CSV Import/Export) is COMPLETE.

Start Sprint 15 per TASKS.md.
```

## Dev Startup Scripts

Four Windows batch files at project root:

| File | Who uses it | What it does |
|---|---|---|
| `setup-and-start.bat` | Friend / reviewer | Installs Git + Docker if missing, clones repo, starts app, opens browser at http://localhost:3100 |
| `setup-and-start-clean.bat` | Friend / reviewer | Same as above + destroys DB volumes (requires YES confirmation) |
| `start-dev.bat` | Developer (already cloned) | Stops old containers, rebuilds, streams logs — no tool install |
| `start-dev-clean.bat` | Developer (already cloned) | Same + destroys DB volumes (requires YES confirmation) |

**ASCII-only scripts:** all .bat files must remain plain ASCII. No Unicode, no box-drawing chars.
**Docker Desktop auto-start:** scripts poll `docker info` every 5 seconds (max 180s).
**Docker project isolation:** all scripts force `docker compose -p bulk-edit`.

## Known Issues

- Etsy access token auto-refresh not implemented. Logs warning but uses token.
- `fetch_listing_videos` is best-effort — returns empty list on 404/405.
- Sync runs inline in HTTP thread. Celery background task deferred to future sprint.
- Frontend npm not installed — run `npm install` inside `apps/frontend` or `docker compose up`.
- Video upload/delete NOT supported — Etsy requires direct file upload. Stubs return 501.
- Image reorder NOT supported — Etsy has no atomic reorder endpoint.
- Variation revert NOT implemented — backup snapshots created; revert deferred.
- AuditLog model uses `extra_data` in Python, stored as `metadata` column in DB.
- `anyio==4.6.2` in requirements-dev.txt is yanked — works fine.

## Push Status

Last pushed: Sprint 14 — CSV Import / Export
Branch: main
