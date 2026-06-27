# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-27
**Task:** Sprint 25 — Promote Health & Profit Features + Media Local Upload — COMPLETE
**Commit:** feat: surface optimization features and add media upload (Sprint 25)

**What was built:**
- `apps/frontend/app/faq/page.tsx` — removed standalone Etsy disclaimer `<div className="bg-indigo-50 border-t border-indigo-100">` block. MarketingFooter still shows disclaimer.
- `apps/frontend/app/features/page.tsx` — added Listing Health Score + Profit Calculator to FEATURES array (icon, title, desc, color, href). Updated grid to render optional href as "Open →" link. Updated subtitle to "Thirteen tools".
- `apps/frontend/app/page.tsx` — added "Optimize listings. Protect your margin." section with 2 cards (health + profit). Fixed `it's` → `it&apos;s` apostrophe.
- `apps/frontend/app/pricing/page.tsx` — added 4 FeatureRow entries after existing rows: Listing Health Score (always true), Profit Calculator (always true), AI listing suggestions (not free), Multiple cost profiles (pro only).
- `apps/frontend/components/ui/AppShell.tsx` — added Shops nav item + ShopIcon SVG between Dashboard and Listings in NAV_BASE Workspace section.
- `apps/frontend/app/(app)/listings/page.tsx` — green tip banner linking to /listing-health.
- `apps/frontend/app/(app)/listing-health/page.tsx` — violet cross-link banner to /profit after header.
- `apps/frontend/app/(app)/profit/page.tsx` — green cross-link banner to /listing-health after header.
- `apps/frontend/app/(app)/media/page.tsx` — `LocalUploadPanel` component: drag-drop + click-to-upload, MIME type + extension dual validation (JPG/PNG/WEBP), 10 MB per file, 20 files max, URL.createObjectURL() thumbnails, URL.revokeObjectURL() cleanup, rejection messages, Copy URL button, per-file + clear-all remove. Preview-only (not uploaded to Etsy).
- `apps/frontend/e2e/faq.spec.ts` — 2 tests: loads without crash, no mid-page indigo disclaimer.
- `apps/frontend/e2e/media-upload.spec.ts` — 2 tests: loads without crash, redirect if unauth.

**Tests:** 673/673 backend pass. 25/25 Playwright pass (base + seeded). 0 lint errors. 24 routes build clean. 13/13 smoke checks. 16 dev env warnings 0 errors. No mojibake.

## Next Task

**Sprint 26 suggestion:** Listing Bulk Edit Performance — virtual scroll for large listing grids, lazy loading, and optimistic updates in the bulk editor.

**Or:** Real Etsy sync integration — wire the existing /shops OAuth flow to a live Etsy sandbox shop and test actual listing sync. Requires `ETSY_CLIENT_ID` + `ETSY_REDIRECT_URI` in .env.

**Next prompt template:**
```
You are working inside: C:\Users\sekip\Desktop\Bulk-Edit
Start Sprint 26: [task name]
[spec here]
```

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 24 — Listing Health Score + Profit & Cost Calculator — COMPLETE
**Commit:** feat: add listing health score and profit calculator modules (Sprint 24)

**What was built:**
- `app/services/listing_health.py` — rule-based listing health score engine. Score 0-100, grade (excellent/good/needs_work/critical), priority, per-category issues (title, tags, description, media, pricing). Points deducted per rule violation. Informational cost warning (no penalty) stored separately.
- `app/services/profit.py` — Decimal-precision profit calculator. Etsy transaction fee (6.5%), payment fee (3% + $0.25), listing fee ($0.20), optional offsite ads (15%). Returns gross_revenue, net_profit, margin_percent, break_even_price, recommended_min_price, roi_percent.
- `apps/backend/alembic/versions/0014_create_profit_calculator_tables.py` — creates `cost_profiles` + `listing_costs` tables. Migration applied.
- `app/models/cost_profile.py` + `app/models/listing_cost.py` — SQLAlchemy ORM models with Numeric(10,4) for money.
- `app/schemas/listing_health.py` + `app/schemas/profit.py` — Pydantic v2 schemas for all endpoints.
- `app/api/v1/listing_health.py` — 5 endpoints: summary, paginated list (filter by grade/priority/search/sort), detail, AI suggestions (safe no-op when AI_PROVIDER=mock), recalculate.
- `app/api/v1/profit.py` — 7 endpoints: summary, paginated list, detail, upsert listing costs, list/create/update cost profiles.
- `apps/frontend/lib/api.ts` — 13 new API helpers + TypeScript interfaces for both modules.
- `apps/frontend/app/(app)/listing-health/page.tsx` — health score page with summary cards, grade/priority/sort filters, score badges, AI suggestions inline panel (never auto-applied disclaimer).
- `apps/frontend/app/(app)/profit/page.tsx` — profit page with fee rate warning banner, summary cards, profit/loss/missing-costs status badges, inline cost editor per listing.
- `apps/frontend/components/ui/AppShell.tsx` — added Listing Health + Profit nav items after Listings with HeartIcon + DollarIcon.
- `apps/frontend/app/(app)/dashboard/page.tsx` — health + profit summary widgets fetched in parallel.
- `e2e/listing-health.spec.ts` + `e2e/profit.spec.ts` — 4 Playwright tests (2 auth-redirect + 2 seeded).
- `tests/test_listing_health.py` + `tests/test_profit.py` — 52 tests total; all pass.

**Tests:** 673/673 backend tests pass (52 new). Build: 24 routes clean. Migration 0014 applied.

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 23 — Production Deployment Readiness Kit — COMPLETE
**Commit:** chore: add production deployment readiness kit (Sprint 23)

**What was built:**
- `apps/backend/scripts/validate_env.py` — standalone env validator. 20+ checks across Database, Redis, Security, CORS, Stripe, Etsy, AI, Rate Limiting, Observability. Masks all secret values. Hard-fails (exit 1) in production mode for missing/placeholder required vars. Warns in development/staging. CORS wildcard check, weak JWT_SECRET detection, Stripe test key in production warning.
- `scripts/smoke_test_deployment.ps1` — PowerShell smoke test. Checks /health, /health/ready, 11 frontend routes. Exit 0 on all pass. 13/13 passed locally.
- `scripts/smoke_test_deployment.sh` — Bash equivalent for Linux/Mac/CI.
- `docker-compose.prod.example.yml` — reference production compose. Health checks, restart policies, commented Celery worker/beat. No secrets hardcoded. Notes: prefer managed DB + Redis. No .local-superusers.env volume.
- `docs/operations/MIGRATIONS.md` — Alembic commands, migration table (0001-0013), zero-downtime migration notes, post-migration smoke test.
- `docs/operations/BACKUP_AND_ROLLBACK.md` — pg_dump, managed platform options, Redis considerations, Docker image rollback, emergency checklist.
- `docs/operations/STAGING_DEPLOYMENT.md` — staging architecture, env var table, step-by-step deploy procedure, promotion criteria.
- `docs/operations/DNS_SSL.md` — domain structure, DNS records, HSTS, CORS config, OAuth/webhook URLs, common mistake table.
- `docs/operations/PROVIDER_SETUP.md` — Stripe setup (products/keys/webhook), Etsy app (scopes, PKCE), OpenAI/Anthropic, email options, Sentry.
- `docs/operations/LAUNCH_READINESS_REPORT.md` — fill-in launch template with test/infra/security/provider/go-no-go sections.
- `.github/workflows/ci.yml` — added `validate_env.py --env development` step before backend tests. Uses CI env vars, exits 0 (warnings only), so CI doesn't break.

**Tests:** 621/621 backend tests pass. Smoke test 13/13. Routes 19/19. Security headers present frontend + backend.

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 22 — First-Run Onboarding, Non-Superuser Seed, Etsy Connection UX — COMPLETE
**Commit:** feat: add first-run onboarding and customer seed flow (Sprint 22)

**What was built:**
- `apps/backend/app/services/local_seed.py` — `_upsert_user()` now takes `is_superuser: bool = False`; `seed_superuser()` takes `is_superuser: bool = True`; `seed_on_startup()` calls FREE with `is_superuser=False`, PAID with `is_superuser=True`; `run_seed()` updated same way
- `apps/backend/tests/test_seed_local_superusers.py` — 4 new tests: `test_free_user_is_not_superuser`, `test_paid_user_is_superuser`, `test_seed_on_startup_free_user_is_not_superuser`, `test_seed_on_startup_paid_user_is_superuser` (27 total in file, 621 total backend)
- `apps/frontend/components/onboarding/OnboardingChecklist.tsx` — NEW: 4-step checklist (connect shop, sync listings, try bulk edit, explore paid features), progress bar, hides when all complete, dark mode safe via `be-card`, `data-testid="onboarding-checklist"`
- `apps/frontend/app/(app)/dashboard/page.tsx` — fetches `/api/v1/etsy/shops` (shopCount) and `/api/v1/listings?limit=1` (listingCount); shows `OnboardingChecklist` above feature cards when counts loaded
- `apps/frontend/app/(app)/shops/page.tsx` — empty state: added Etsy trademark note + OAuth explanation; button text changed to "Redirecting to Etsy..."
- `apps/frontend/e2e/onboarding.spec.ts` — NEW: 2 always-run tests (unauthenticated dashboard, shops no-crash) + 2 seeded-user tests (checklist visible, trademark note)
- Live seed verification: `test@example.com is_superuser=False` ✓, `test-su@example.com is_superuser=True` ✓

**Tests:** 621/621 backend tests pass. Playwright: 13 passed, 4 skipped. Build: 22 routes, 0 TS errors.

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 21 — Production Monitoring, Redis Rate Limiting, Sentry, Celery Readiness — COMPLETE
**Commit:** chore: add production monitoring redis rate limiting sentry and celery readiness (Sprint 21)

**What was built:**
- `apps/backend/app/core/rate_limit.py` — upgraded to Redis+memory dual backend; IP-only key for login (Pydantic already consumed body); memory fallback on Redis unavailability; `contact_rate_limit` dependency added
- `apps/backend/app/core/config.py` — added RATE_LIMIT_REDIS_URL, RATE_LIMIT_CONTACT_PER_HOUR, SENTRY_DSN, SENTRY_ENVIRONMENT, SENTRY_TRACES_SAMPLE_RATE
- `apps/backend/app/main.py` — `_init_sentry()` + `_scrub_sentry_event()` (scrubs password, tokens, keys); safe no-op when DSN absent
- `apps/backend/requirements.txt` — added `sentry-sdk[fastapi]==2.19.2`
- `apps/backend/app/schemas/admin.py` — AdminSystemHealth upgraded: redis_status, rate_limit_backend, rate_limit_enabled, sentry_configured, worker_status, csp_mode
- `apps/backend/app/services/admin.py` — `_check_redis_health()` probe; `get_system_health()` returns all new fields; never exposes Redis URL
- `apps/frontend/next.config.mjs` — removed `unsafe-eval` in production; added HSTS for production (NODE_ENV=production); sha256 hash documented as comment
- `apps/backend/tests/test_rate_limiting.py` — 9 tests (up from 3)
- `apps/backend/tests/test_security_headers.py` — 10 tests (up from 3); system-health monitoring field tests, no-Redis-URL, no-Sentry-DSN, worker_status
- `docs/operations/MONITORING.md` — NEW: health endpoints, Sentry, rate limits, Stripe, Etsy, scheduled jobs, Redis, admin checks, daily checklist
- `docs/operations/RUNBOOK.md` — NEW: 14 incident scenarios + rollback + secret rotation procedures
- `docs/operations/WORKERS.md` — NEW: current inline scheduler docs + future Celery architecture
- `.github/workflows/e2e.yml` — NEW: manual workflow_dispatch for Playwright E2E with artifact upload

**Tests:** 609/609 backend tests pass. Build: 22 routes, 0 errors.

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 20 — Launch QA, CI/CD, E2E, Rate Limiting, CSP — COMPLETE
**Commit:** chore: add launch qa ci e2e rate limiting and security headers (Sprint 20)

**What was built:**
- `.github/workflows/ci.yml` — GitHub Actions CI: backend tests + postgres:16 + redis:7 services, Alembic migration, pytest; frontend lint+build; docker-compose config validate
- `apps/frontend/playwright.config.ts` — Playwright config targeting localhost:3100
- `apps/frontend/e2e/public-pages.spec.ts` — 7 tests: 5 marketing pages + 2 auth pages
- `apps/frontend/e2e/theme.spec.ts` — 3 tests: anti-flash script, light mode, dark mode
- `apps/frontend/e2e/auth-flow.spec.ts` — 1 test (dashboard loads) + 2 seeded-user tests (skipped without `PLAYWRIGHT_RUN_SEEDED_TESTS=1`)
- `apps/backend/app/core/rate_limit.py` — in-memory rate limiter; login 10/min, register 5/min per IP; disabled by default (`RATE_LIMIT_ENABLED=false`)
- `apps/backend/app/core/security_headers.py` — `SecurityHeadersMiddleware` adding 4 headers to all API responses
- `apps/backend/app/main.py` — imports + registers SecurityHeadersMiddleware
- `apps/backend/app/core/config.py` — added RATE_LIMIT_ENABLED, RATE_LIMIT_BACKEND, RATE_LIMIT_LOGIN_PER_MINUTE, RATE_LIMIT_REGISTER_PER_MINUTE
- `apps/backend/app/api/v1/auth.py` — added `Depends(login_rate_limit)` / `Depends(register_rate_limit)` to login + register
- `apps/frontend/next.config.mjs` — CSP + X-Content-Type-Options + X-Frame-Options + Referrer-Policy + Permissions-Policy + X-DNS-Prefetch-Control on all routes
- `apps/frontend/components/ui/AppShell.tsx` — `data-testid="admin-nav-link"` on Admin link
- `apps/frontend/app/(app)/admin/page.tsx` — `data-testid="admin-access-denied"` + `data-testid="admin-dashboard"`
- `apps/backend/tests/test_rate_limiting.py` — 3 tests
- `apps/backend/tests/test_security_headers.py` — 3 tests
- `docs/operations/LAUNCH_CHECKLIST.md` — NEW: 10-section production launch checklist
- TASKS.md, PROJECT_STATUS.md, HANDOFF.md, CHANGELOG_AI.md, DECISIONS.md, SECURITY.md updated

**Tests:** 595/595 backend tests pass. Playwright: 11 passed, 2 skipped. Build: 22 routes, 0 errors.

## Next Task

**Sprint 24** — Options: (1) CSP nonce hardening via Next.js middleware (remove unsafe-inline), (2) Celery task workers (real background jobs), (3) Email delivery integration (contact form + billing notifications), (4) Etsy token auto-refresh. Choose from TASKS.md backlog.

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: Sprint 23 COMPLETE. Production deployment readiness kit shipped: validate_env.py, smoke_test_deployment scripts, docker-compose.prod.example.yml, 6 ops docs (MIGRATIONS, BACKUP_AND_ROLLBACK, STAGING_DEPLOYMENT, DNS_SSL, PROVIDER_SETUP, LAUNCH_READINESS_REPORT), CI validate_env step. 621/621 backend tests. 19/19 routes.

Start Sprint 24 per TASKS.md backlog.
```

## Next Prompt (legacy Sprint 21 — DONE)

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: Sprint 20 COMPLETE. CI/CD live, Playwright E2E added, rate limiting + security headers active. 595/595 tests. 22 routes. 0 errors.

Start Sprint 21: CSP nonce hardening, Celery production workers, monitoring, post-launch ops.
```

## Previous Last Session

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
