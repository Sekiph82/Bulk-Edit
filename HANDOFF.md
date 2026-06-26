# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-26
**Task:** Local Dev Reliability — Superuser Seed + Startup Readiness — COMPLETE
**Completed:** .gitignore updated. .local-superusers.env.example created. local_seed.py service (async, idempotent, no password output). scripts/seed_local_superusers.py thin CLI wrapper. All 4 .bat files updated: run compose -d, poll backend health (8100/api/v1/health) + frontend (3100) via PowerShell Invoke-WebRequest before opening browser. start-dev.bat + start-dev-clean.bat have optional seed prompt. 28 new tests (seed + bat readiness). 431/431 full suite.

## Previous Session

**Date:** 2026-06-26
**Sprint:** Sprint 15 — Dynamic Pricing — COMPLETE
**Completed:** DynamicPricingJob + DynamicPricingRecommendation models (alembic 0012). dynamic_pricing_jobs_used on UsageCounter. Pro plan gate (can_use_dynamic_pricing, 100 jobs/month). Full calculation engine: percentage_adjustment, fixed_amount_adjustment, set_price, reference_price. Safety guardrails: margin floor (Decimal math), price floor, price cap, rounding (ending_99/95/nearest_50/nearest_100). accept/reject/accept-all/convert endpoints. Convert creates BulkEditSession draft + scoped BulkEditChange (target_listing_ids=[listing_id]) — NEVER writes to Etsy. 50 tests. /pricing-rules page (listing selector, rule builder, guardrails, preview table with per-row accept/reject, convert modal with "CONVERT PRICES" confirmation). Dashboard DP card. 403/403 full suite passing. Build: 16 routes, zero errors.

## Previous Session

**Date:** 2026-06-26
**Sprint:** Sprint 14 — CSV Import / Export — COMPLETE
**Completed:** CSVJob + CSVRow models (alembic 0011). Added target_listing_ids to BulkEditChange. 6 CSV endpoints under /api/v1/csv. Import converts to BulkEditSession only — never writes to Etsy directly. 49 CSV tests pass. /csv page. Dashboard CSV card. 353/353 suite passing.

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

## Current State (Sprint 15 additions)

**Backend (`apps/backend/`):**
- `app/models/dynamic_pricing_job.py` — DynamicPricingJob model (status: draft → preview_ready → converted/failed)
- `app/models/dynamic_pricing_recommendation.py` — DynamicPricingRecommendation model (per-listing: status, diff, margin, guardrail warnings)
- `app/models/usage_counter.py` — added `dynamic_pricing_jobs_used` column
- `app/core/plans.py` — added `dynamic_pricing_jobs_per_month` (free/basic: 0, pro: 100)
- `app/services/billing.py` — added `dynamic_pricing_jobs_used` → `dynamic_pricing_jobs_per_month` to limit key mapping
- `alembic/versions/0012_create_dynamic_pricing_tables.py` — migration (adds column + creates 2 tables)
- `app/schemas/dynamic_pricing.py` — 6 schemas
- `app/services/dynamic_pricing.py` — full engine: rule calculation, safety guardrails, accept/reject/accept-all/convert
- `app/api/v1/dynamic_pricing.py` — 10 REST endpoints under /api/v1/dynamic-pricing
- `app/api/v1/router.py` — includes dynamic_pricing_router
- `tests/test_dynamic_pricing.py` — 50 tests (all passing)

**Frontend (`apps/frontend/`):**
- `app/pricing-rules/page.tsx` — 3-step page: Setup (listing selector + rule builder + guardrails), Preview (summary cards + rec table with accept/reject + convert modal), History
- `lib/api.ts` — DynamicPricingJob, DynamicPricingRecommendation, DynamicPricingSummary, DynamicPricingConvertResponse types + 10 helpers
- `app/dashboard/page.tsx` — Dynamic Pricing card

## Safety Gates (Sprint 15)

Dynamic Pricing enforces:
1. Billing gate: can_use_dynamic_pricing must be True (Pro plan); dynamic_pricing_jobs_per_month limit checked
2. Variation listings skipped (has_variations=True) — not processed
3. Listings with no price_amount → status="invalid"
4. Negative recommended price → status="invalid"
5. Safety guardrails: margin floor (Decimal), price floor, price cap applied in order
6. Convert requires job.status == "preview_ready" AND at least 1 accepted recommendation
7. Convert creates BulkEditSession(status="draft") + BulkEditChange(target_listing_ids=[listing_id]) only
8. Listing.price_amount is NEVER updated by dynamic pricing
9. Convert modal requires user to type "CONVERT PRICES" before proceeding

## Next Task

**Sprint 16: Scheduled Jobs**

Implement Celery Beat scheduler for recurring listing sync and bulk edits.

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: 403/403 tests passing. Sprint 15 (Dynamic Pricing) is COMPLETE.

Start Sprint 16 per TASKS.md.
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
