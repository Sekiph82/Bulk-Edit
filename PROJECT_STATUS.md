# PROJECT_STATUS.md

## Current Phase

**Production is LIVE (bulk-edit-prod-api / bulk-edit-prod-web) under Private Beta gate. Etsy developer app status escalated from "pending review" to BANNED (2026-07-13) — no reason given by Etsy. A full Etsy compliance + production-readiness audit and correction pass was completed on branch `etsy-compliance-production-readiness` (NOT merged or deployed — awaiting owner review). Stripe Live checkout was previously validated and PASSED (2026-07-10). Private Beta correctly stays enabled until Etsy responds to the appeal.**

## Status

`Stripe Live: products/prices/env fully configured and validated end-to-end (2026-07-10) — Basic Monthly Live Checkout Session created via a controlled internal test account, $19 USD confirmed, production success/cancel URLs confirmed, one live customer created, zero charges/subscriptions. All four price mappings confirmed via Stripe Price lookups.`

`Etsy: app status escalated from "pending review" to "Banned" with no explanation. Full compliance audit completed 2026-07-13 (see ETSY_COMPLIANCE_AUDIT.md) — found and fixed: OAuth granted-scope storage bug, disconnect not deleting tokens, no AI-data authorization gate, no snapshot retention limit, public site pre-launch/beta framing contradicting a live product, and several other items (full list in ETSY_FEATURE_MATRIX.md). A second owner-review validation pass (same day, real Postgres, no delegated write access) additionally found and fixed two real account-deletion bugs invisible to SQLite tests — a SQLAlchemy relationship-cascade crash, and 9 tables missing `organization_id` foreign keys entirely (meaning "deleted" accounts left Etsy shop/token/listing data orphaned) — migration 0025, full detail in ETSY_DATA_RETENTION.md §4a. A third session (same day) implemented the owner's decision on the one remaining item: account deletion is now blocked (HTTP 409) while an organization has an active or billable Stripe subscription — never auto-canceled — via a new local-only eligibility check (`assert_account_deletion_billing_safe`, ETSY_DATA_RETENTION.md §4b), with a minimal deletion UI added to the existing `/billing` page. No new migration needed; head remains 0025. Frontend (tsc/lint/build, 82 routes) and backend (**975/975 tests**) verified clean via a full independent run, including 2 additional real-Postgres end-to-end scenarios for the new billing gate. Not committed, not deployed. No open items remain from the owner's blocker list. Next action: owner does final review of the audit + diff, then either merges/deploys the fixes and/or submits the Etsy appeal (ETSY_APPEAL_CHECKLIST.md, ETSY_SUPPORT_QUESTIONS.md draft). Private Beta (NEXT_PUBLIC_PRIVATE_BETA_MODE=true) remains enabled. Stripe webhook endpoint existence/events still unverifiable via the Stripe MCP connector — same limitation as the prior session.`

## Last Updated

2026-07-13

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
- Sprint 14: CSV Import / Export ✓ (CSVJob + CSVRow models, 6 endpoints, 49 tests, /csv page, 353/353 suite)
- Sprint 15: Dynamic Pricing ✓ (DynamicPricingJob + DynamicPricingRecommendation models, 10 endpoints, 50 tests, /pricing-rules page, 403/403 suite)
- Local Dev Reliability ✓ (gitignored seed config, local_seed.py service, bat readiness polling, FastAPI lifespan startup hook, 431/431 suite)
- Sprint 16: Scheduled Jobs ✓ (ScheduledJob + ScheduledJobRun models, migration 0013, schedule calculator, 11 API endpoints, plan gates, /scheduled page, 41 tests, 479/479 suite)
- Sprint 17: Admin Panel ✓ (20 endpoints all require_superuser, 16 schemas, paginated service, 42 tests, /admin page, 521/521 suite)
- Sprint 17.5: Marketing Polish ✓ (MarketingNav, MarketingFooter, /features, /faq, /contact-us, motion v12 animations, globals.css design system, Etsy legal disclaimer, 22 routes build clean, 521/521 suite)
- Sprint 17.5-B: Theme System + fmcg Visual Language ✓ (ThemeProvider, ThemeToggle, AppShell, anti-flash script, (app)/ route group, 11 app pages migrated, full dark mode CSS, 22 routes, 521/521 suite)
- Sprint 18: Security Hardening + Deployment Readiness ✓ (45 security tests, /health/ready endpoint, mojibake fix, accessibility, ENVIRONMENT.md, TESTING.md, 566/566 suite)
- Sprint 19: Internal Admin Business Dashboard ✓ (6-tab dashboard, 5 new summary endpoints, Admin nav gated to superusers, 17 new tests, 20 routes, 0 TS errors)
- Sprint 20: Launch QA, CI/CD, E2E, Rate Limiting, CSP ✓ (GitHub Actions CI, Playwright E2E, rate limiting, security headers, CSP, launch checklist, 595/595 tests)
- Sprint 21: Production Monitoring, Redis Rate Limiting, Sentry, Celery Readiness ✓ (Redis rate limiter, Sentry backend, system-health monitoring fields, MONITORING.md, RUNBOOK.md, WORKERS.md, e2e.yml, 609/609 tests)
- Sprint 22: First-Run Onboarding, Non-Superuser Seed, Etsy Connection UX ✓ (seed role fix, OnboardingChecklist, dashboard shop/listing count fetch, Etsy trademark note, 621/621 tests)
- Sprint 23: Production Deployment Readiness Kit ✓ (validate_env.py, smoke_test scripts, docker-compose.prod.example.yml, 6 ops docs, CI validate_env step, 621/621 tests)
- Sprint 24: Listing Health Score + Profit & Cost Calculator ✓ (health score engine, profit calculator, migration 0014, 9 API endpoints, 2 frontend pages, dashboard widgets, 52 new tests, 673/673 total)
- Sprint 25: Promote Health & Profit + Media Local Upload ✓ (FAQ disclaimer removed, features/homepage/pricing updated, Shops nav added, cross-links added, LocalUploadPanel in media, 4 new E2E tests, 673/673 backend, 25/25 Playwright)
- Sprint 26 follow-up: Real ffmpeg rendering + Pinterest/Instagram OAuth ✓
- Sprint 26 polish: Etsy video spec compliance + promote page clarity ✓ (4 aspect ratios, 5-15s validation, 100MB check, etsy_ready checklist, per-state copy, migration 0017, 747/747 tests)

## Local Development (Windows)

**For developers (already have Docker + repo cloned):**
- `start-dev.bat` — double-click to start all services (preserves volumes, streams logs)
- `start-dev-clean.bat` — full reset including volume deletion (requires typing YES to confirm)

**For friend / reviewer (no developer tools needed):**
- `setup-and-start.bat` — double-click; installs Git + Docker Desktop via winget if missing, clones repo to Desktop, builds, starts, opens browser at http://localhost:3100
- `setup-and-start-clean.bat` — same with volume reset (requires YES confirmation)

All scripts: check Docker, auto-create `.env` from `.env.example` if missing, enforce `docker compose -p bulk-edit` project name, safely stop old `fmcg-erp-system-main` ERP containers before starting.

## Blockers

- Etsy developer app "bulk-edit-app" is **Banned** (escalated from "pending review" 2026-07-13, no reason given). Blocks all live Etsy OAuth/API testing. Appeal drafted in `ETSY_SUPPORT_QUESTIONS.md`, not yet sent (requires owner to send from the account that manages the Etsy developer app).

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
| `pytest tests/test_csv_tools.py` | 49/49 PASSED |
| `pytest tests/test_dynamic_pricing.py` | 50/50 PASSED |
| `pytest tests/test_seed_local_superusers.py` | 23/23 PASSED |
| `pytest tests/test_windows_batch_readiness.py` | 12/12 PASSED |
| `pytest tests/test_scheduled_jobs.py` | 41/41 PASSED |
| `pytest tests/test_admin_panel.py` | 42/42 PASSED |
| `pytest tests/test_security_hardening.py` | 45/45 PASSED |
| `pytest tests/test_rate_limiting.py` | 9/9 PASSED |
| `pytest tests/test_security_headers.py` | 10/10 PASSED |
| `pytest tests/test_admin_dashboard.py` | 17/17 PASSED |
| **Full suite `pytest`** | **617/617 PASSED** |

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
| Sprints complete | 21 / 21 (incl. Productization UI, Landing Animation, AI, CSV, DP, local dev, scheduled jobs, admin panel, admin dashboard, CI/CD, monitoring) |
| Backend Python files | 132+ |
| Frontend TypeScript files | 31 |
| Total tests | 617 |
| Open blockers | 0 |

## Next Action

Begin Sprint 22: User onboarding flow, empty state polish, first-run wizard, analytics events. See HANDOFF.md for exact prompt.
