# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-26
**Task:** Sprint 19 — Internal Admin Business Dashboard — COMPLETE
**Commit:** feat: add internal admin business dashboard (Sprint 19)

**What was built:**
- `apps/backend/app/schemas/admin.py` — added `AdminBillingSummary`, `AdminStripeSummary`, `AdminProductUsage`, `AdminSystemHealth` schemas
- `apps/backend/app/services/admin.py` — added `get_billing_summary`, `get_stripe_summary`, `get_product_usage`, `get_system_health` service functions + `BillingEvent` import
- `apps/backend/app/api/v1/admin.py` — added 5 new endpoints: `GET /admin/billing-summary`, `/stripe-summary`, `/product-usage`, `/system-health`, `/audit-log`; all require superuser
- `apps/frontend/components/ui/AppShell.tsx` — Admin nav item now hidden from non-superusers; reads `is_superuser` from `/me` response
- `apps/frontend/lib/api.ts` — added `AdminUsageSummary`, `AdminBillingSummary`, `AdminStripeSummary`, `AdminProductUsage`, `AdminSystemHealth` types + 6 new API helpers
- `apps/frontend/app/(app)/admin/page.tsx` — full rewrite as 6-tab business dashboard (Overview, Users, Billing, Etsy, Usage, System)
- `apps/backend/tests/test_admin_dashboard.py` — 17 new tests: auth gates, response shape, MRR field name safety, is_superuser in /me

**Tests:** 17/17 new tests pass. 59/59 total admin tests pass. Build: 20 routes, 0 errors. TypeScript: 0 errors.

## Next Task

**Sprint 20** — CI/CD pipeline, production Docker, rate limiting, CSP headers, Playwright E2E tests.

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: Sprint 19 COMPLETE. Admin business dashboard live. 20 routes, 0 TS errors.

Start Sprint 20 per TASKS.md.
```

## Previous Last Session

**What was built:**
- `apps/frontend/app/globals.css` — `.be-btn-primary`, `.be-btn-secondary`, `.be-card`, `.be-contact-card`, `.be-faq-item`, `.be-faq-trigger`, `.be-hero-bg`, `.be-section-accent`, `.be-icon-ring`, `.be-step`. Gradient buttons, hover-lift cards, reduced-motion guard.
- `apps/frontend/components/marketing/MarketingNav.tsx` — sticky nav with active link highlighting, mobile-safe, links to /features /faq /contact-us /pricing.
- `apps/frontend/components/marketing/MarketingFooter.tsx` — 4-col footer, legal Etsy disclaimer.
- `apps/frontend/app/features/page.tsx` — 11-feature grid, 6-step workflow, safety checklist, CTA, animated listing preview visual.
- `apps/frontend/app/faq/page.tsx` — animated accordion, 6 categories (General, Etsy Connection, Safety, Billing, AI Tools, CSV & Dynamic Pricing), 17 Q&As.
- `apps/frontend/app/contact-us/page.tsx` — 4 contact cards, demo form with success state, FAQ cross-link.
- `apps/frontend/app/page.tsx` — replaced inline nav with MarketingNav, added MarketingFooter, motion FadeUp animations, feature tease section.
- `apps/frontend/app/pricing/page.tsx` — added MarketingNav + MarketingFooter, removed inline logo.
- Build: 22 routes, 0 errors. 521/521 backend tests pass.

## Previous Last Session

**What was built:**
- `app/schemas/admin.py` — 16 Pydantic schemas. No password_hash, no Etsy tokens, no Stripe secret keys, no raw billing event payload.
- `app/services/admin.py` — `_paginate()` generic helper + 14 list functions + 4 safe action functions (disable/enable user, pause/resume job).
- `app/api/v1/admin.py` — 20 endpoints all gated on `require_superuser` from deps.py. Prefix: `/api/v1/admin`.
- Router registered in `app/api/v1/router.py`.
- `tests/test_admin_panel.py` — 42 tests: auth gates, 403 for non-superuser, no secrets in responses, pagination, user disable/enable, job pause/resume, not-found handling.
- `apps/frontend/lib/api.ts` — admin types + 11 API helpers appended at end.
- `apps/frontend/app/admin/page.tsx` — admin UI: 8 overview cards, 6 section tabs (users, orgs, subs, shops, scheduled jobs, events), paginated tables, inline disable/enable and pause/resume actions, 403 handled cleanly.
- Dashboard card added: "Admin Panel" → /admin.
- 521/521 tests pass. Build clean.

**Security verified:**
- All endpoints → 403 without superuser role
- No password_hash in any user response
- No Etsy access_token/refresh_token in any shop response
- No stripe_subscription_id or stripe_price_id in any subscription response
- No destructive delete operations
- Cannot disable own account (400)

**Root Cause:**
1. Sprint migrations 0008-0012 originally used `postgresql.UUID`/`sa.UUID` for FK columns while parent tables (`organizations`, `users`, `listings`, etc.) have `VARCHAR(36)` IDs (from migration 0001+). PostgreSQL rejects FK constraints across incompatible types.
2. All parent-table ORM models (`organization.py`, `user.py`, `listing.py`, and 21 others) declared columns as `Uuid(as_uuid=False)`. With asyncpg, this generates `$1::UUID` bind type in SQL. PostgreSQL rejects `VARCHAR = UUID` comparisons.
3. `bcrypt==5.0.0` (unpinned transitive dep) broke `passlib==1.7.4` — `__about__.__version__` removed, causing seed hash failure.

**Fixes:**
- Migrations 0008-0012: already fixed to use `sa.String(36)` (were in unstaged changes)
- **ALL 43 model files**: replaced `Uuid(as_uuid=False)` → `String(36)`, removed `Uuid` imports (bulk PowerShell replace across 24 files)
- `requirements.txt`: pinned `bcrypt==4.0.1` (last compatible with passlib 1.7.4)

**Verified:**
- `alembic upgrade head` from clean DB: all 12 migrations pass, no FK errors
- Backend health: HTTP 200 `{"status":"ok","service":"bulk-edit-api"}`
- Frontend: HTTP 200, valid HTML
- Local superuser seed: `test@example.com (free, created) | test-su@example.com (pro_monthly, created)` — no errors
- Login: both users return `access_token`; wrong password → 401
- `.local-superusers.env` gitignored, not staged
- **438/438 tests pass on host**

## Previous Session — Sprint 16

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

**Sprint 18: Tests, Deployment, Security Hardening, Polish**

CI/CD pipeline, production Docker config, OWASP security audit, >80% backend test coverage, accessibility.

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: 521/521 tests passing. Sprints 1-17 all COMPLETE.

Start Sprint 18 per TASKS.md.
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
