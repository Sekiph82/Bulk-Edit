# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-26
**Task:** Fix local superuser workflow — seed on backend startup — COMPLETE
**Commit:** `23e1520` — `chore: seed local superusers on backend startup`
**Completed:**
- `app/main.py` — FastAPI lifespan hook calls `seed_on_startup` on startup
- `app/services/local_seed.py` — `seed_on_startup(db, env_path=None)` async fn: silent if file absent, logs warning on error, never crashes backend
- `start-dev.bat` + `start-dev-clean.bat` — removed Y/N seed prompt and `seed_local_superusers.py` invocation entirely
- `tests/test_seed_local_superusers.py` — rewritten: 23 tests including startup hook tests and login endpoint tests (fixed `.test` TLD rejection — changed to `@example.com`)
- `tests/test_windows_batch_readiness.py` — replaced `test_start_dev_bat_has_seed_prompt` with `test_start_dev_bat_no_seed_prompt` (seed strings must be ABSENT)
- 431/431 full suite passes

**How seeding works now:**
1. Backend starts → FastAPI lifespan fires `seed_on_startup`
2. If `.local-superusers.env` absent → silent, backend continues normally
3. If present → creates/updates free + paid superusers in DB (idempotent)
4. Users log in normally via unchanged `/api/v1/auth/login` endpoint
5. No Y/N prompt. No bat file involvement. No login bypass.

## Previous Session

**Date:** 2026-06-26
**Task:** Local Dev Reliability — Superuser Seed + Startup Readiness — COMPLETE
**Commit:** `d0fc2c8` — `chore: add local superusers and startup readiness checks`
**Completed:** `.gitignore` updated. `.local-superusers.env.example` created. `local_seed.py` service (async, idempotent, no password output). `scripts/seed_local_superusers.py` thin CLI wrapper. All 4 .bat files updated: run compose -d, poll backend health (8100/api/v1/health) + frontend (3100) via PowerShell Invoke-WebRequest before opening browser. 431/431 full suite.

## Previous Session

**Date:** 2026-06-26
**Sprint:** Sprint 15 — Dynamic Pricing — COMPLETE
**Commit:** `3286787` — `feat: add dynamic pricing workflow (Sprint 15)`
**Completed:** DynamicPricingJob + DynamicPricingRecommendation models (alembic 0012). `dynamic_pricing_jobs_used` on UsageCounter. Pro plan gate (`can_use_dynamic_pricing`, 100 jobs/month). Full calculation engine: percentage_adjustment, fixed_amount_adjustment, set_price, reference_price. Safety guardrails: margin floor (Decimal math), price floor, price cap, rounding (ending_99/95/nearest_50/nearest_100). accept/reject/accept-all/convert endpoints. Convert creates BulkEditSession draft + scoped BulkEditChange (`target_listing_ids=[listing_id]`) — NEVER writes to Etsy. 50 tests. `/pricing-rules` page (listing selector, rule builder, guardrails, preview table with per-row accept/reject, convert modal with "CONVERT PRICES" confirmation). Dashboard DP card. 403/403 full suite passing. Build: 16 routes, zero errors.

## Current State

**Backend (`apps/backend/`):**

**Local Seed Service (`app/services/local_seed.py`):**
- `seed_on_startup(db, env_path=None)` — async startup hook. Reads `.local-superusers.env`, upserts free + paid superuser. Silent if file missing. Warning log on error. Never raises.
- `seed_superuser(db, email, password, full_name, org_name, plan)` — idempotent upsert: user + org + member + subscription. Returns summary dict (no password). status = "created" or "updated".
- `load_seed_config(path)` — parses KEY=value env file, raises `SeedConfigError` if file missing
- `_require(config, key)` — raises `SeedConfigError` if key absent
- `run_seed(env_path)` — CLI fn for manual use via `scripts/seed_local_superusers.py`

**ENV_FILE_PATH:** resolves to `apps/backend/.local-superusers.env` on host, `/app/.local-superusers.env` inside Docker (volume mount `./apps/backend:/app`)

**Sprint 14 additions (CSV Import / Export):**
- `app/models/csv_job.py` — CSVJob model (status machine: processing → preview_ready → converted/failed)
- `app/models/csv_row.py` — CSVRow model (per-row: listing_id, etsy_listing_id, raw_data, normalized_data, diff, status, errors, warnings)
- `app/models/bulk_edit_change.py` — added `target_listing_ids` JSON nullable column
- `alembic/versions/0011_create_csv_import_export_tables.py` — migration
- `app/schemas/csv_tools.py` — 6 schemas
- `app/services/csv_tools.py` — full service: export, template, parse, validate, import job, preview, convert to BulkEditSession
- `app/api/v1/csv_tools.py` — 6 REST endpoints under /api/v1/csv
- `app/services/bulk_edit.py` — preview engine updated: `if targets is None or lid in targets: apply_change()`
- `tests/test_csv_tools.py` — 49 tests

**Sprint 15 additions (Dynamic Pricing):**
- `app/models/dynamic_pricing_job.py` — DynamicPricingJob model
- `app/models/dynamic_pricing_recommendation.py` — DynamicPricingRecommendation model
- `app/models/usage_counter.py` — added `dynamic_pricing_jobs_used`
- `app/core/plans.py` — added `dynamic_pricing_jobs_per_month`
- `alembic/versions/0012_create_dynamic_pricing_tables.py` — migration
- `app/schemas/dynamic_pricing.py` — 6 schemas
- `app/services/dynamic_pricing.py` — full engine
- `app/api/v1/dynamic_pricing.py` — 10 REST endpoints
- `tests/test_dynamic_pricing.py` — 50 tests

**Frontend (`apps/frontend/`):**
- `app/pricing-rules/page.tsx` — Dynamic Pricing 3-step page
- `app/csv/page.tsx` — CSV 3-tab page
- `lib/api.ts` — all types + helpers for DP and CSV
- `app/dashboard/page.tsx` — DP + CSV cards

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Dev Startup Scripts

| File | Who | What |
|---|---|---|
| `setup-and-start.bat` | Friend / reviewer | Installs Git + Docker if missing, clones repo, starts app, opens browser |
| `setup-and-start-clean.bat` | Friend / reviewer | Same + destroys DB volumes (requires YES) |
| `start-dev.bat` | Developer | Stops old containers, rebuilds, polls readiness, opens browser, streams logs |
| `start-dev-clean.bat` | Developer | Same + destroys DB volumes (requires YES) |

**ASCII-only scripts.** Docker Desktop auto-start via `docker info` poll (5s, 180s max). Project isolation: `docker compose -p bulk-edit`.

## Safety Gates Active

- Seeded users authenticate via unchanged `/api/v1/auth/login` — no bypass
- `.local-superusers.env` gitignored — never committed
- `seed_on_startup` swallows all exceptions — bad env file never crashes backend
- No passwords logged or printed

## Next Task

**Sprint 16: Scheduled Jobs**

Implement Celery Beat scheduler for recurring listing sync and periodic bulk edits.

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: 431/431 tests passing. Sprints 1-15 + local dev reliability all COMPLETE.

Start Sprint 16 per TASKS.md.
```

## Known Issues

- Etsy access token auto-refresh not implemented. Logs warning but uses token.
- `fetch_listing_videos` is best-effort — returns empty list on 404/405.
- Sync runs inline in HTTP thread. Celery background task deferred to Sprint 16.
- Frontend npm not installed — run `npm install` inside `apps/frontend` or `docker compose up`.
- Video upload/delete NOT supported — Etsy requires direct file upload. Stubs return 501.
- Image reorder NOT supported — Etsy has no atomic reorder endpoint.
- Variation revert NOT implemented — backup snapshots created; revert deferred.
- AuditLog model uses `extra_data` in Python, stored as `metadata` column in DB.
- `anyio==4.6.2` in requirements-dev.txt is yanked — works fine.

## Push Status

Last pushed: `23e1520` — chore: seed local superusers on backend startup
Branch: main
