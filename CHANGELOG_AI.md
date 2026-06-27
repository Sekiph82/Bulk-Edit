# CHANGELOG_AI.md — AI Session Log

Append one entry per session. Format: `## [DATE] Sprint N — Summary`

---

## 2026-06-27 Sprint 20 — Launch QA, CI/CD, E2E, Rate Limiting, CSP

**Skills active:** 06 backend-api, 20 testing-qa, 22 devops

**What was done:**
- `.github/workflows/ci.yml` — GitHub Actions CI pipeline: 3 jobs (backend-tests with postgres:16+redis:7 services, frontend-checks, docker-compose-validate). No real secrets in CI. RATE_LIMIT_ENABLED=false in CI env.
- `playwright.config.ts` + `e2e/*.spec.ts` — Playwright smoke tests for public pages, theme (anti-flash + light/dark), auth flow (dashboard gating). Seeded-user tests skip unless `PLAYWRIGHT_RUN_SEEDED_TESTS=1`. 11/13 pass locally; 2 seeded tests skipped.
- `app/core/rate_limit.py` — In-memory rate limiter. No new package dependency (avoids slowapi). `RATE_LIMIT_ENABLED` defaults `False` so tests never hit 429. Login 10/min, register 5/min per IP.
- `app/core/security_headers.py` + `app/main.py` — SecurityHeadersMiddleware on all FastAPI responses: X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy: strict-origin-when-cross-origin, Permissions-Policy.
- `apps/frontend/next.config.mjs` — Full security header suite + CSP on all frontend routes. CSP uses 'unsafe-inline' for scripts (required by anti-flash theme script). Nonce-based hardening deferred to Sprint 21.
- `data-testid` attributes on Admin nav link, admin access-denied div, admin dashboard main.
- `tests/test_rate_limiting.py` (3 tests) + `tests/test_security_headers.py` (3 tests) — 6 new tests, all pass.
- `docs/operations/LAUNCH_CHECKLIST.md` — NEW: 10-section production launch checklist (infrastructure, env vars, Stripe, Etsy, AI, admin, security, E2E, go/no-go, post-launch).

**Test results:** 595/595 backend tests pass (+12 from Sprint 20). Playwright: 11 passed, 2 skipped. Build: 22 routes, 0 errors.

---

## 2026-06-26 Sprint 19 — Internal Admin Business Dashboard

**Skills active:** 05 frontend-component, 06 backend-api, 20 testing-qa

**What was done:**
- `apps/backend/app/schemas/admin.py` — added `AdminBillingSummary`, `AdminStripeSummary`, `AdminProductUsage`, `AdminSystemHealth` Pydantic schemas. All exclude secrets (no stripe_secret_key, no password_hash, no Etsy tokens).
- `apps/backend/app/services/admin.py` — added `get_billing_summary()` (plan counts, projected MRR using $PLAN_MRR dict), `get_stripe_summary()` (stripe customer metrics from Subscription model), `get_product_usage()` (7 aggregate counts), `get_system_health()` (DB status + fail counts). Added `BillingEvent` import.
- `apps/backend/app/api/v1/admin.py` — added 5 new endpoints all gated on `require_superuser`: `GET /admin/billing-summary`, `/stripe-summary`, `/product-usage`, `/system-health`, `/audit-log`.
- `apps/frontend/components/ui/AppShell.tsx` — refactored NAV to `NAV_BASE` + `ADMIN_NAV_ITEM`. Added `isSuperuser` state, reads `d.user.is_superuser` from `/me`. Admin nav item only appended when `isSuperuser === true`. Normal customers never see Admin link.
- `apps/frontend/lib/api.ts` — added 5 new TypeScript interfaces + `adminListUsage` + 5 new API helper functions targeting the new backend endpoints.
- `apps/frontend/app/(app)/admin/page.tsx` — full rewrite. 6 tabs: Overview (overview cards + billing KPIs), Users (user table + org table), Billing (plan distribution + stripe summary + subscriptions table), Etsy (shops + scheduled jobs), Usage (product usage stats + usage counters table), System (health cards + audit log). Improved 403 page with shield icon.
- `apps/backend/tests/test_admin_dashboard.py` — 17 new tests: auth gate (403 for regular user, 403 for unauthenticated), response shape validation for all 5 endpoints, MRR field name is `estimated_monthly_revenue` not `collected_revenue`, no stripe secrets in response, `is_superuser` exposed in `/me` as false for users and true for superusers, no `password_hash` in /me response.

**Test results:** 17/17 new tests pass. 59/59 total admin tests pass. TypeScript: 0 errors. Build: 20 routes.

**Security:** All 5 new endpoints require superuser. `estimated_monthly_revenue` labeled as projected (not guaranteed cash). No stripe secrets, no password_hash, no Etsy tokens in any response.

---

## 2026-06-26 Sprint 18 — Security Hardening, Deployment Readiness, Polish

**Skills active:** 20 testing-qa, 08 security, 01 documentation-handoff, 05 frontend-component

**What was done:**
- `apps/backend/app/api/v1/health.py` — added `GET /api/v1/health/ready` readiness probe (DB check, returns 200/503)
- `apps/backend/tests/test_security_hardening.py` — 45 new security tests: auth gates (11 endpoints, 401/403 without token), JWT tampering (tampered signature, empty bearer, wrong scheme), superuser gate (4 admin endpoints return 403 for regular users), no-secrets-in-responses (password_hash, stripe_secret, access_token_enc), org isolation (6 resource types), SQL injection in query params (title/tag/sort_by), path traversal, oversized IDs, input validation (XSS email, short password, duplicate email), stack trace safety
- `apps/frontend/app/(app)/listings/page.tsx` — fixed mojibake × (U+00D7) close button (line 103) and delete-view button (line 469); added `type="button"` and `aria-label` attributes
- `apps/frontend/app/(app)/pricing-rules/page.tsx` — fixed mojibake ✕ dismiss-error button (line 310) + 4 JSX comment lines with box-drawing chars; added `type="button"` and `aria-label`
- `docs/operations/ENVIRONMENT.md` — NEW: full environment variable reference (required/optional, secrets rotation, local superuser seed, environment hierarchy)
- `docs/operations/TESTING.md` — full rewrite: current test counts (566 total), test DB setup, key fixtures, security test coverage summary, CI/CD workflow skeleton
- All project docs updated: TASKS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md

**Test results:** 566/566 PASSED (521 baseline + 45 new)

---

## 2026-06-26 Sprint 17.5 — Marketing Polish

**Skills active:** 05 frontend-component, 19 marketing-copy, 01 documentation-handoff

**What was done:**
- `globals.css` — full `.be-*` design system (gradient primary button, secondary button, card hover-lift, FAQ accordion, contact card, hero bg, section accent, reduced-motion guard)
- `MarketingNav` — sticky nav, active link detection via `usePathname`, Features/FAQ/Contact/Pricing + Sign in + Get started
- `MarketingFooter` — 4-column footer, Etsy legal disclaimer in both footer and page-level banner
- `/features` page — 11-feature grid, 6-step workflow, safety checklist, AnimatedListingVisual, motion FadeUp + whileHover
- `/faq` page — animated accordion (AnimatePresence height expand/collapse), 6 categories, 17 Q&As covering General/Etsy/Safety/Billing/AI/CSV
- `/contact-us` page — 4 contact cards with motion, demo form with 800ms submit simulation + success state, FAQ cross-link
- Home page — MarketingNav + MarketingFooter, FadeUp hero animations, feature tease section, workflow strip uses `.be-step`
- Pricing page — MarketingNav + MarketingFooter, removed inline logo, preserved all billing/checkout logic
- 521/521 backend tests. 22 routes build clean (0 errors, 3 warnings pre-existing).

---

## 2026-06-26 Sprint 16 — Scheduled Jobs

**Skills active:** 06 database-modeling, 07 backend-api, 20 testing-qa, 05 frontend-component, 01 documentation-handoff

**Completed:**
- `app/models/scheduled_job.py` — ScheduledJob model (String(36) IDs/FKs)
- `app/models/scheduled_job_run.py` — ScheduledJobRun model
- `app/models/__init__.py` — added new models
- `alembic/versions/0013_create_scheduled_job_tables.py` — migration with indexes
- `app/core/plans.py` — added `max_scheduled_jobs` (free=0, basic=3, pro=25)
- `app/services/schedule_calculator.py` — validate_schedule, calculate_next_run, should_run_now; timezone-aware via zoneinfo; min interval 60 min; day_of_month 1–28
- `app/services/scheduled_jobs.py` — full service: create/list/get/update/pause/resume/disable/run_now/find_due/run_due/execute; 4 job type executors (etsy_sync read-only, bulk_edit_draft creates draft only, dynamic_pricing_preview creates preview only, csv_export_snapshot returns metadata only); never calls etsy_write or bulk_edit_apply
- `app/schemas/scheduled_jobs.py` — ScheduledJobCreate/Out/Update, ScheduledJobRunOut, RunDueResponse
- `app/api/v1/scheduled_jobs.py` — 11 endpoints under /api/v1/scheduled-jobs
- `app/api/v1/router.py` — registered scheduled_jobs_router
- `apps/frontend/lib/api.ts` — ScheduledJob + ScheduledJobRun types, all API helpers
- `apps/frontend/app/scheduled/page.tsx` — safety banner, create form, jobs table, run history
- `apps/frontend/app/dashboard/page.tsx` — Scheduled Jobs card added
- `apps/frontend/app/billing/page.tsx` — fixed "You are on the Free plan" for paid local users

**Safety guarantee:** no scheduled Etsy writes. etsy_sync reads only. bulk_edit_draft creates status="draft". dynamic_pricing_preview never converts. csv_export_snapshot returns metadata only.

**Tests:** 479/479 suite passing (41 new tests for Sprint 16)

**Frontend:** 18 routes, zero lint errors, zero build errors

---

## 2026-06-26 Docker Fix — FK Type Mismatch + bcrypt Compat

**Skills active:** 06 database-modeling, 07 backend-api, 20 testing-qa, 01 documentation-handoff

**Completed:**
- `apps/backend/requirements.txt` — pinned `bcrypt==4.0.1` (passlib 1.7.4 incompatible with bcrypt 5.x; `__about__.__version__` removed in 5.x)
- `apps/backend/alembic/versions/0008–0012` — confirmed using `sa.String(36)` throughout (was pre-modified)
- **43 ORM model files** — bulk replaced `Uuid(as_uuid=False)` → `String(36)`, removed `Uuid` and `PG_UUID` imports. Root cause: asyncpg renders `Uuid(as_uuid=False)` as `$1::UUID` bind type in SQL; DB columns from migrations are `VARCHAR(36)`; PostgreSQL rejects `VARCHAR = UUID` comparison at runtime.
- Docker from clean volumes: all 12 Alembic migrations pass, no FK errors
- Backend health verified: HTTP 200 `{"status":"ok","service":"bulk-edit-api"}`
- Frontend verified: HTTP 200, valid HTML
- Local superuser seed verified: both users created, access_token returned on login, wrong password → 401
- `.local-superusers.env` confirmed gitignored, not staged

**Tests:** 438/438 suite passing on host (7 new tests from sprint model files)

---

## 2026-06-26 Local Dev Reliability — Superuser Seed + Startup Readiness

**Skills active:** 07 backend-api, 06 database-modeling, 20 testing-qa, 01 documentation-handoff

**Completed:**
- `.gitignore` — added explicit `apps/backend/.local-superusers.env`, `.local-superusers.env`, `*.local-superusers.env` entries
- `apps/backend/.local-superusers.env.example` — committed example with placeholder values only
- `apps/backend/app/services/local_seed.py` — async seed service: `load_seed_config`, `seed_superuser`, `run_seed`. Idempotent. No password in output. Reads `.local-superusers.env` from backend root (works both on host and in Docker via volume mount)
- `apps/backend/scripts/seed_local_superusers.py` — thin CLI wrapper using asyncio.run(). Prints email/org/plan/status only
- `start-dev.bat` — changed to `-d --build`, added backend health poll + frontend poll (PowerShell Invoke-WebRequest, 5s/180s), optional seed prompt, browser open after readiness, then logs -f
- `start-dev-clean.bat` — same changes as start-dev.bat
- `setup-and-start.bat` — changed to `-d --build`, added backend + frontend readiness checks, browser opens after readiness only
- `setup-and-start-clean.bat` — same changes as setup-and-start.bat
- `apps/backend/tests/test_seed_local_superusers.py` — 15 tests: missing file error/instructions, config parsing, user/org/member/subscription creation, free plan, pro plan, idempotency, password hashing, no password in output, gitignore coverage
- `apps/backend/tests/test_windows_batch_readiness.py` — 13 tests: all .bat files exist, ASCII-only, no chcp 65001, no box drawing, docker info before compose, backend health wait present, frontend wait present, browser after readiness, no fixed-delay browser open, project name isolation, no hardcoded credentials, developer scripts have seed prompt

**Tests:** 431/431 suite passing (28 new tests)

---

## 2026-06-26 Sprint 15 — Dynamic Pricing

**Skills active:** 07 backend-api, 06 database-modeling, 20 testing-qa, 01 documentation-handoff

**Completed:**
- `app/models/dynamic_pricing_job.py` — DynamicPricingJob model (status machine: draft → preview_ready → converted/failed; counts: row, recommended, skipped, warning, invalid)
- `app/models/dynamic_pricing_recommendation.py` — DynamicPricingRecommendation model (per-listing: status, current/recommended/reference price, diff, margin, guardrail warnings)
- `app/models/usage_counter.py` — added `dynamic_pricing_jobs_used` mapped column
- `app/core/plans.py` — added `dynamic_pricing_jobs_per_month` (free/basic: 0, pro: 100)
- `app/services/billing.py` — added limit key mapping for dynamic_pricing_jobs_used
- `alembic/versions/0012_create_dynamic_pricing_tables.py` — migration: adds column + creates 2 tables
- `app/schemas/dynamic_pricing.py` — 6 schemas (JobCreate, JobOut, RecommendationOut, RecommendationPageOut, ConvertResponse, SummaryOut)
- `app/services/dynamic_pricing.py` — full engine: apply_rounding_rule (ending_99/95/nearest_50/nearest_100), apply_margin_floor (Decimal), apply_price_cap, calculate_recommendation_for_listing (4 rule types + reference modes), create_job, generate_preview, accept/reject/accept_all, convert (creates BulkEditSession draft + scoped BulkEditChange, NEVER updates Listing.price_amount)
- `app/api/v1/dynamic_pricing.py` — 10 REST endpoints under /api/v1/dynamic-pricing
- `app/api/v1/router.py` — includes dynamic_pricing_router
- `tests/test_dynamic_pricing.py` — 50 tests (unit + API, all passing)
- `app/pricing-rules/page.tsx` — 3-step UI: listing selector, rule builder (4 rule types + reference modes), safety guardrails (margin/price floor/cap/rounding), preview with summary cards + per-row accept/reject, convert modal requiring "CONVERT PRICES" confirmation, job history
- `lib/api.ts` — DP types + 10 API helpers appended
- `app/dashboard/page.tsx` — Dynamic Pricing card added

**Tests:** 403/403 suite passing (50 new DP tests)
**Build:** 16 routes, zero errors

**Safety:** Dynamic Pricing NEVER writes to Etsy. Convert creates BulkEditSession(status="draft") + BulkEditChange(target_listing_ids=[listing_id]). Listing.price_amount untouched. Pro billing gate enforced.

---

## 2026-06-26 Sprint 14 — CSV Import / Export

**Skills active:** 07 backend-api, 06 database-modeling, 20 testing-qa, 01 documentation-handoff

**Completed:**
- `app/models/csv_job.py` — CSVJob model (status: processing → preview_ready → converted/failed; counts: row, valid, invalid, changed, unchanged, ignored)
- `app/models/csv_row.py` — CSVRow model (per-row: listing_id, etsy_listing_id, raw_data, normalized_data, diff, status, validation_errors, validation_warnings)
- `app/models/bulk_edit_change.py` — added `target_listing_ids` JSON nullable; backward compat: null = apply to all
- `alembic/versions/0011_create_csv_import_export_tables.py` — adds column, creates 2 tables
- `app/schemas/csv_tools.py` — 6 schemas
- `app/services/csv_tools.py` — export (streaming CSV), template, parse_csv_upload (BOM-strip, 5000 row limit), create_csv_import_job (validate all rows, diff compute), get_csv_preview (paginated, status filter), convert_csv_job_to_bulk_edit_session (creates BulkEditSession + per-field BulkEditChange with target_listing_ids)
- `app/services/bulk_edit.py` — preview engine: `if targets is None or lid in targets: apply_change()`
- `app/api/v1/csv_tools.py` — 6 REST endpoints under /api/v1/csv
- `app/api/v1/router.py` — csv_router added
- `tests/test_csv_tools.py` — 49 tests: parsers, export, template, import, validation, row status, preview, convert, org isolation, backward compat
- `apps/frontend/lib/api.ts` — CSV types + 7 helpers (importCSV uses FormData; exportCSV returns URL for direct download)
- `apps/frontend/app/csv/page.tsx` — 3-tab page: Export (download CSV/template), Import (upload → summary stats → row preview table → convert button), Job History
- `apps/frontend/app/dashboard/page.tsx` — CSV Import / Export card
- Full suite: 353/353 PASSED; build: 15 routes, zero errors

**Key decisions:**
- `target_listing_ids` on BulkEditChange solves per-row different values: null = all (existing), [id] = specific listing (CSV)
- Import → convert creates BulkEditSession with status=draft; user must run existing bulk edit preview+apply flow; no direct Etsy write in this sprint
- Max 5,000 rows enforced at parse time
- Pipe-separated arrays in CSV (tags, materials) normalized to lists
- Both listing_id and etsy_listing_id supported for row identity resolution; cross-org rejected

---

## 2026-06-26 Sprint 13 — AI Tools

**Skills active:** 07 backend-api, 06 database-modeling, 20 testing-qa, 01 documentation-handoff

**Completed:**
- `app/services/ai_provider.py` — MockProvider / OpenAIProvider / AnthropicProvider abstraction; `get_provider()` factory reads `AI_PROVIDER` env var; default = mock; no real API calls in CI
- `app/services/ai_prompts.py` — 5 prompt builders (title, description, tags, alt_text, seo_score)
- `app/models/ai_session.py`, `ai_suggestion.py`, `ai_usage_log.py` — 3 new models
- `alembic/versions/0010_create_ai_tools_tables.py` — migration for 3 tables
- `app/schemas/ai.py` — AISessionCreate, AISessionOut, AISuggestionOut, AISessionPageOut, AIUsageOut, ConvertToSessionOut
- `app/services/ai_tools.py` — full service layer: create_ai_session, run_ai_session, accept/reject, convert_to_bulk_edit (creates BulkEditSession+BulkEditChange — AI never writes to Etsy), get_ai_usage; billing gate: paid plan required before any AI run
- `app/api/v1/ai.py` — 9 endpoints under /api/v1/ai
- `app/api/v1/router.py` — ai_router added
- `app/core/config.py` — 6 new env vars: AI_PROVIDER, OPENAI_API_KEY, OPENAI_MODEL, ANTHROPIC_API_KEY, ANTHROPIC_MODEL, AI_REQUEST_TIMEOUT_SECONDS
- `requirements.txt` — added openai==1.57.0, anthropic==0.40.0
- `apps/frontend/lib/api.ts` — AI types + 9 helpers
- `apps/frontend/app/ai/page.tsx` — full AI tools page: usage card, listing selector, tool picker, suggestions panel with accept/reject, convert to bulk edit, session history
- `apps/frontend/app/dashboard/page.tsx` — AI Optimizer card added
- `tests/test_ai_tools.py` — 32 tests, all mocked
- Full suite: 304/304 PASSED; build: 15 routes, zero errors

**Key decisions:**
- AI billing gate requires paid plan (not just non-zero credits) — sprint spec: "Pro plan minimum"
- Convert-to-bulk-edit creates BulkEditSession with status=draft; user must still run existing bulk edit preview + apply flow
- seo_score tool: accept/reject not surfaced (read-only scoring tool)

---

## 2026-06-26 Landing Animation Sprint — AnimatedProductDemo

**Skills active:** 08 frontend-ui, 24 ux-polish

**Completed:**
- Installed `motion` v12 (`npm install motion`) — added to apps/frontend dependencies
- Created `apps/frontend/components/AnimatedProductDemo.tsx` (client component, ~220 lines)
  - 5-phase animation loop (idle → select → edit panel → preview → safety strip)
  - Phase durations: 1.2s / 2.2s / 2.8s / 2.8s / 4.0s → total ~13s loop
  - `useReducedMotion` from `motion/react`: if true, jumps to phase 4 (static final state), no loop
  - Sliding edit panel (absolute positioned, `x: "100%"` → `x: 0`) — no layout shift
  - Row highlighting via animated `backgroundColor` (indigo-50 when selected)
  - Animated checkboxes (border + bg color + SVG check fade-in)
  - Preview panel (amber bg, before/after rows, `opacity+y` fade-up)
  - Safety strip (green "Backup snapshot created", "Magic Revert ready", "Apply safely" button)
  - All mock data static — zero API calls, zero external assets
  - `aria-hidden="true"` on entire demo (decorative)
  - Easing: `easeOut` only. No bounce, no spring.
- Rewrote `apps/frontend/app/page.tsx`:
  - Two-column desktop layout (`lg:grid-cols-2`): left = headline+CTAs+trust strip, right = demo
  - Mobile: stacked (demo below hero text)
  - New headline: "Bulk editing for Etsy sellers, without the spreadsheet chaos."
  - Trust strip (4-item grid with SVG checks): Preview every change / Backup snapshots / Magic Revert / Built for Etsy sellers
  - Workflow strip below hero: Connect → Sync → Edit → Preview → Apply → Revert
- Updated `DESIGN.md` — added Motion section with animation rules for homepage only
- Updated `design-system/pages/home.md` — documented two-column layout + AnimatedProductDemo behavior

**Customer-facing text check:** Zero `Sprint` / `API Endpoints` / `Backend API` / `roadmap` strings in app/ or components/.

**Lint:** Zero errors (pre-existing warnings unchanged).
**Build:** 14 routes, zero errors. Homepage: 43.7kB (motion library). Zero type errors.
**Backend:** Not touched.

---

## 2026-06-26 Productization UI Sprint — Design System Prep

**Skills active:** 08 frontend-ui, 24 ux-polish, 01 documentation-handoff

**Completed:**
- Installed Impeccable v3.1.0 project-locally via `npx impeccable install --providers=claude --scope=project` → .claude/skills/impeccable/ (24 reference files + scripts)
- Installed UI UX Pro Max v2.2.3 globally (`npm install -g uipro-cli`) + project-locally (`uipro init --ai claude`) → .claude/skills/ui-ux-pro-max/ (Python scripts + CSV data files)
- Generated design system via UI UX Pro Max: indigo primary, flat design style, Plus Jakarta Sans / Inter, for SaaS dashboard + etsy seller tool
- Created page-specific design systems in design-system/bulk-edit/pages/ (home, dashboard, listings, bulk-edit, media, variations) via `uipro init --persist`
- Created PRODUCT.md (Impeccable context: register=product, users=Etsy sellers, principles: safety is visible / data density / zero roadmap language)
- Created DESIGN.md (full visual system: color tokens, Inter type scale, spacing, card/button/badge/table/modal/form styles, motion rules)
- Created design-system/MASTER.md (canonical design reference for Next.js + Tailwind, all component styles, absolute bans, copywriting rules)
- Created design-system/pages/ with 6 page-specific overrides
- Created docs/design/PRODUCT_UI_DIRECTION.md (page-by-page direction, anti-patterns inventory)
- Created docs/design/UI_AUDIT.md (audit score 8/20, P0: sprint labels/API debug/disabled roadmap cards; P1: no focus states, no form labels, emoji icons, no loading states)
- Light cleanup (Part G): removed sprint badge + API debug card + "Sprint 2" copy from homepage; removed disabled roadmap cards + API endpoint debug panel from dashboard
- Grep confirmed: zero sprint labels or API endpoint strings remaining in customer-facing .tsx files

**Key design decisions:**
- Register = product (tool-first, design serves task)
- Color strategy = Restrained (indigo accent, neutral surfaces, semantic states only)
- Impeccable installed project-local; UI UX Pro Max installed global+project-local (CLI requires global for `uipro` command)
- Full UI redesign deferred to Productization UI Sprint (not this task)
- Design system created at design-system/MASTER.md (project root) + design-system/bulk-edit/ (uipro persist output)
- Backend tests NOT run (no backend files touched)

---

## 2026-06-26 Sprint 12 — Variation Editor

**Skills active:** 07 backend-api, 06 database-modeling, 20 testing-qa, 01 documentation-handoff

**Completed:**
- 4 new SQLAlchemy models: `BulkEditVariationJob`, `BulkEditVariationPreviewItem`, `BulkEditVariationResult`, `ListingVariationBackupSnapshot`
- Alembic migration `0009` — 4 new tables
- `etsy_variation_write.py` — `fetch_etsy_listing_inventory`, `put_etsy_listing_inventory`, `normalize_etsy_inventory_tree` (strips deleted/read-only), `patch_inventory_tree_for_variation_operation` (8 operations with optional selector), `_product_matches_selector` (case-insensitive), `extract_local_variation_snapshot`; `EtsyVariationWriteError`; `MAX_SKU_LENGTH=32`
- `schemas/bulk_edit_variation.py` — 7 Pydantic v2 schemas with field_validators; `VALID_OPERATION_TYPES` defined locally (not imported to avoid circular)
- `services/bulk_edit_variation.py` — `create_variation_job` (org-scoped listing validation, payload validation), `generate_variation_preview` (clears old, generates new preview items using local ListingVariation data), `apply_variation_job` (safety gates: status → Etsy config → no invalid items → fetch Etsy tree → backup → normalize → patch → PUT → local update on success → audit), 5 query helpers
- `api/v1/bulk_edit_variations.py` — 8 REST endpoints under `/api/v1/bulk-edit/variations`
- `models/__init__.py` + `router.py` updated with 4 new model imports and variations router
- 47 new tests in `test_bulk_edit_variation.py` — 272/272 full suite PASS (was 225)
- 1 bug fixed during testing: `apply_variation_job` checked Etsy config before job status — reordered gates so status check fires first (returns 400 not 503 when job not preview_ready)
- Frontend: `app/variations/page.tsx` (listing selector filtered to `has_variations=true`, 8-op picker, selector inputs, Preview button, before/after table, APPLY VARIATIONS confirm modal, results panel, job history); `lib/api.ts` (6 types + 8 helpers); dashboard card added

**Key design decisions:**
- Fetch-patch-put: always GET current Etsy inventory tree before patching; never construct from local data alone
- Preview uses local `ListingVariation` rows; apply uses fresh Etsy inventory tree (dual-source design)
- Two selector functions: `_product_matches_selector()` on Etsy tree; `_selector_matches()` on local ListingVariation rows
- Invalid preview items (listing has `has_variations=False`) block apply (400) — user must fix selection
- Warning items (no local variations, no selector match) do NOT block apply — they create skip results
- Backup stores both `local_variations_snapshot` AND `etsy_inventory_snapshot` to enable Sprint 13 variation revert
- Revert for variations explicitly deferred to Sprint 13

---

## 2026-06-26 Productization UI Sprint — Apply Design System

**Skills active:** 08 frontend-ui, 24 ux-polish, 01 documentation-handoff

**Completed:**
- `npm install` in apps/frontend — first-time dependency install (390 packages)
- Fixed tsconfig.json: added `"target": "ES2017"` — pre-existing type error on `[...Set]` spread with ES3 target
- Fixed `apps/frontend/app/billing/page.tsx`: wrapped in Suspense (useSearchParams requires it for static prerender)
- Removed emoji from empty states: shops/page.tsx (🏪) and listings/page.tsx (📦)
- `media/page.tsx`: removed sprint references from operation labels ("not available in Sprint 11" → "coming soon"); fixed unescaped apostrophe lint error; fixed error message ("This operation is not available in Sprint 11" → "This operation is not yet available")
- `pricing/page.tsx`: replaced emoji ✓/✗ in FeatureRow with inline Heroicon SVGs (green check / gray X)
- `listings/page.tsx`: added `loading="lazy"` to both thumbnail img tags (table row + detail sidebar)
- All pages: added `focus:outline-none focus:ring-2 focus:ring-indigo-300` to buttons missing focus rings (bulk-edit, media, variations, shops, listings)
- `variations/page.tsx`: job history now shows human-readable label from OPERATION_OPTIONS instead of snake_case operation_type; added focus rings to Preview/Apply/Cancel buttons
- `media/page.tsx`: confirm modal shows human-readable label; job stats changed from emoji (✓✗) to text (ok/err/skip)
- Build: 14 routes, zero errors, zero type errors

**Key decisions:**
- Did not rewrite entire pages (all functionality retained)
- Used targeted edits only (focus rings, lazy loading, text fixes, svg replacements)
- billing/page.tsx Suspense fix was a pre-existing bug surfaced by first build run

---

## 2026-06-25 Sprint 11 — Photo / Video Bulk Editor

**Skills active:** 07 backend-api, 06 database-modeling, 20 testing-qa, 01 documentation-handoff

**Completed:**
- 3 new SQLAlchemy models: `BulkEditMediaJob`, `BulkEditMediaResult`, `ListingMediaBackupSnapshot`
- Alembic migration `0008` — 3 new tables
- `etsy_media_write.py` — `fetch_etsy_listing_images`, `upload_etsy_listing_image` (httpx download → multipart POST), `delete_etsy_listing_image` (404=success); video upload/delete raise `EtsyMediaWriteError(not_implemented=True, status_code=501)`
- `schemas/bulk_edit_media.py` — 6 Pydantic v2 schemas with field_validators
- `services/bulk_edit_media.py` — `create_media_job` (org-scoped listing validation), `apply_media_job` (backup-before-write, add/replace/delete_image implemented, video/reorder stubs skip-with-reason, audit logs, partial failure), 4 query helpers
- `api/v1/bulk_edit_media.py` — 6 REST endpoints under `/api/v1/bulk-edit/media`
- `models/__init__.py` + `router.py` updated with 3 new model imports and media router
- 25 new tests in `test_bulk_edit_media.py` — 225/225 full suite PASS (was 200)
- Frontend: `app/media/page.tsx` (listing selector, operation picker, APPLY MEDIA confirm modal, backup warning, job history, results panel); `lib/api.ts` (4 types + 6 helpers); dashboard card updated

**Key design decisions:**
- Image upload pattern: download bytes from `image_url` via httpx → POST multipart to Etsy (Etsy has no URL-based image upload)
- Video operations: explicit stubs (not partial), raise 501; skipped with clear reason in result rows
- Image reorder: stub only — Etsy has no atomic reorder endpoint; delete-all + re-upload too destructive for MVP
- Backup created per-listing per-job, never deleted
- Local ListingImage rows updated ONLY after Etsy write success (failure leaves local unchanged)
- 404 on image delete = success (image already deleted — safe behavior)

---

## 2026-06-25 Sprint 10 — Etsy Inventory Writes (Price / Quantity)

**Skills active:** 07 backend-api, 20 testing-qa, 01 documentation-handoff

**Completed:**
- `build_etsy_inventory_payload(listing, after_data)` in `etsy_write.py` — change detection via value comparison (not diff key), variation skip (return None), currency_code guard
- `patch_etsy_listing_inventory(access_token, shop_etsy_id, listing_etsy_id, payload)` in `etsy_write.py` — PUT /v3/application/shops/{s}/listings/{l}/inventory with JSON body
- `bulk_edit_apply.py` rewritten with dual-write: listing PATCH first, inventory PUT second; structured request/response payloads `{"listing_patch": {...}, "inventory_patch": {...}}`; variation skip detection; local price/qty updated ONLY after inventory PUT success
- `bulk_edit_revert.py` updated with inventory revert from snapshot_data; same dual-write pattern; local price/qty restore gated on inventory revert success; `shop.etsy_shop_id` lookup for endpoint
- `tests/test_bulk_edit_inventory.py` — 19 tests (9 unit, 10 integration); 200/200 full suite PASS (was 181)
- Frontend: revert modal warning updated to "price and quantity now included"; variation listing skip notice shown in preview when has_variations=True and price_amount/quantity in diff

**Key design decisions:**
- Change detection: `new_price != listing.price_amount` (works for both apply and revert)
- Partial write caveat: listing PATCH success + inventory PUT failure → Etsy has new text, not new price; local DB not updated; next sync resolves
- Backward compat: request_payload uses flat format for text-only changes, structured format only when inventory involved

---

## 2026-06-25 DevOps — Fixed Windows Batch Scripts to ASCII-Only CMD-Safe Syntax

**Skills active:** 01 documentation-handoff

**Problem:** Scripts contained Unicode box-drawing characters (e.g., `:: ── 1. Check Docker CLI ─────────`) and `chcp 65001` which caused CMD errors on double-click: `'EADY' is not recognized as an internal or external command`, `The syntax of the command is incorrect`.

**Root cause:** Unicode comment separators parsed as commands. `chcp 65001` changes code page but the .bat file itself was saved with characters CMD could not parse at the default code page, causing label/goto resolution to break.

**Completed:**
- All 4 .bat files fully rewritten as plain ASCII-only Windows CMD batch files
- Removed all Unicode box-drawing characters (U+2500 range), long dashes, fancy quotes, decorative separators
- Removed `chcp 65001` from all scripts
- Comment lines use only `::` with plain ASCII text
- Labels simplified: `:WAIT_FOR_DOCKER`, `:DOCKER_READY`, `:DOCKER_NOT_READY`
- Verified with PowerShell regex `[^\x00-\x7F]` — 0 non-ASCII chars in all 4 files
- Docker engine wait loop retained: polls every 5s, max 180s, exits cleanly on timeout
- Updated README.md, DEPLOYMENT.md, HANDOFF.md

---

## 2026-06-25 DevOps — Auto-Start Docker Desktop in Windows Scripts

**Skills active:** 01 documentation-handoff

**Problem:** User had to manually open Docker Desktop before double-clicking start-dev.bat. Script would fail immediately if Docker engine was not already running.

**Completed:**
- All 4 batch scripts updated with Docker Desktop auto-start section:
  1. `start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"` — launches Desktop silently
  2. Loop: `docker info >nul 2>&1` every 5 seconds, up to 180 seconds total
  3. Clear progress output: `Waiting 5 seconds... 10/180`
  4. On timeout: detailed error with WSL2/restart instructions + `pause + exit /b 1`
  5. On success: `[OK] Docker engine is ready.` then continues
- Docker Compose version check moved to after engine is confirmed ready
- No `docker compose` commands run before Docker engine is up
- Updated README.md, DEPLOYMENT.md, HANDOFF.md

**Max wait time:** 180 seconds (3 minutes), polling every 5 seconds

---

## 2026-06-25 DevOps — Docker Compose Project Isolation Fix

**Skills active:** 01 documentation-handoff

**Problem:** Double-clicking start-dev.bat was opening/starting the old `fmcg-erp-system-main` ERP project because plain `docker compose` without a project name falls back to the folder name or leftover state.

**Completed:**
- All 4 batch scripts updated to use `docker compose -p bulk-edit` instead of bare `docker compose`
- All 4 scripts: added `findstr /i "COMPOSE_PROJECT_NAME" .env` check — appends `COMPOSE_PROJECT_NAME=bulk-edit` if missing
- All 4 scripts: added safe ERP project stop before Bulk-Edit startup: `docker compose -p fmcg-erp-system-main down --remove-orphans >nul 2>&1` (errors suppressed, does not stop script, no `-v` so ERP volumes preserved)
- Added `COMPOSE_PROJECT_NAME=bulk-edit` to `.env.example`
- Removed obsolete `version: "3.9"` top-level line from `docker-compose.yml`
- Updated README.md, DEPLOYMENT.md, HANDOFF.md, PROJECT_STATUS.md

**Docker Compose project name:** `bulk-edit` (enforced via `-p bulk-edit` flag AND `COMPOSE_PROJECT_NAME` env var)

---

## 2026-06-25 DevOps — Windows One-Click Friend Setup Scripts

**Skills active:** 01 documentation-handoff

**Completed:**
- Created `setup-and-start.bat` — full friend/reviewer setup: checks winget, installs Git via winget if missing, installs Docker Desktop via winget if missing, starts Docker Desktop, waits for engine (with manual pause fallback), clones repo to `%USERPROFILE%\Desktop\Bulk-Edit` (or pulls if exists), copies `.env.example` to `.env`, runs `docker compose down --remove-orphans`, spawns background cmd to open browser after 12s delay, runs `docker compose up --build` in foreground.
- Created `setup-and-start-clean.bat` — same as above but with WARNING banner + `set /p CONFIRM` YES gate + `docker compose down -v --remove-orphans` before rebuild.
- Updated `README.md` — "One-click Windows setup for a friend" section added above developer quick start.
- Updated `docs/operations/DEPLOYMENT.md` — Windows One-Click Setup section with table and Docker Desktop restart warning.
- Updated `HANDOFF.md` — 4-file scripts table with who uses each.
- Updated `TASKS.md` — task added and marked complete.
- Updated `PROJECT_STATUS.md` — reviewer note added.

**Decisions made:**
- `%USERPROFILE%\Desktop\Bulk-Edit` as clone target — works for any Windows user without knowing their username; Desktop is universally accessible.
- Browser opened via `start "" cmd /c "timeout /t 12 /nobreak >nul && start http://localhost:3100"` in background so main window keeps streaming Docker logs.
- Non-destructive on existing non-git folder: prints error, does NOT delete folder, exits safely.
- `chcp 65001` for UTF-8 encoding to avoid Turkish character issues in CMD.

---

## 2026-06-25 DevOps — Windows Dev Startup Scripts

**Skills active:** 01 documentation-handoff

**Completed:**
- Created `start-dev.bat` — Windows batch file: checks Docker, creates .env from .env.example if missing, runs `docker compose down --remove-orphans`, runs `docker compose up --build`, keeps CMD window open. No volume deletion.
- Created `start-dev-clean.bat` — Same checks + explicit WARNING banner + `set /p CONFIRM` gate (requires typing YES) + `docker compose down -v --remove-orphans` before rebuild. Destroys DB volumes.
- Updated `README.md` — Windows Quick Start section added above Docker Compose manual section
- Updated `docs/operations/DEPLOYMENT.md` — Windows Startup Scripts subsection with table and behavior description
- Updated `HANDOFF.md` — Dev Startup Scripts section added to Known Issues area
- Updated `TASKS.md` — task marked complete under DevOps Utilities
- Updated `PROJECT_STATUS.md` — note added under local development

**Decisions made:**
- foreground mode by default (no -d flag) — user needs to see logs/errors
- no `docker compose down -v` in normal script — protects DB data
- UTF-8 via `chcp 65001` — avoids Turkish character encoding issues
- `cd /d "%~dp0"` — script always runs from its own directory regardless of launch method

---

## 2026-06-25 Sprint 7 — Bulk Edit Preview Engine

**Skills active:** 06 database-modeling, 07 backend-api, 08 frontend-ui, 20 testing-qa, 01 documentation-handoff

**Completed:**
- Created `app/models/bulk_edit_session.py` — BulkEditSession (org-scoped, status: draft/preview_ready/canceled, selected_listing_ids JSON, selected_count, change_count, preview_generated_at, applied_at, canceled_at)
- Created `app/models/bulk_edit_change.py` — BulkEditChange (session FK CASCADE, listing FK SET NULL nullable, field_name, operation, old/new/operation_value JSON, validation_status, validation_message)
- Created `app/models/bulk_edit_preview_item.py` — BulkEditPreviewItem (session+listing FKs CASCADE, listing_title, before/after/diff JSON, validation_status/messages; UNIQUE session+listing)
- Updated `app/models/__init__.py` — imported 3 new models
- Created `alembic/versions/0005_create_bulk_edit_tables.py` — migration for 3 tables (down_revision=0004)
- Created `app/schemas/bulk_edit.py` — 8 Pydantic schemas: BulkEditSessionCreateRequest, BulkEditSessionResponse, BulkEditChangeCreateRequest, BulkEditChangeResponse, BulkEditPreviewSummary, BulkEditPreviewGenerateResponse, BulkEditPreviewItemResponse, BulkEditPreviewPageResponse, BulkEditSessionDetailResponse
- Created `app/services/bulk_edit.py` — pure functions (apply_change_to_listing_data, validate_listing_data, compute_diff, build_before_data) + async DB functions (create/list/get/cancel session, add/remove change, generate preview, get preview page, apply stub → 409)
- Created `app/api/v1/bulk_edit.py` — 9 endpoints under /api/v1/bulk-edit
- Updated `app/api/v1/router.py` — include bulk_edit_router
- Created `tests/test_bulk_edit.py` — 38 tests: 21 pure function unit tests + 17 API integration tests
- Updated `apps/frontend/lib/api.ts` — 6 new TS types + 9 bulk edit API helpers appended
- Created `apps/frontend/app/bulk-edit/page.tsx` — 3-phase flow: listing selector (reads localStorage), change editor (dynamic op list by field type), diff preview table (before/after per field, validation badges)
- Updated `apps/frontend/app/listings/page.tsx` — Bulk Edit Selected button now active: saves IDs to localStorage, navigates to /bulk-edit

**Test results:** 131/131 PASSED (38 new + 93 existing)

**Decisions made:**
- Session-level changes (one BulkEditChange per session, not per listing) — apply fan-out at preview time
- apply_change_to_listing_data uses copy.deepcopy — pure function, no mutation
- Apply stub returns 409 with "Etsy write operations start in Sprint 8" — no Listing rows modified
- UniqueConstraint(session+listing) on preview items — upsert on re-generate
- localStorage passthrough: listings page → /bulk-edit for selected IDs

**Blockers:** None

**Next:** Sprint 8 — Safe Etsy Write Pipeline

---

## 2026-06-25 Sprint 6 — Listings Grid UX

**Skills active:** 07 backend-api, 08 frontend-ui, 20 testing-qa, 01 documentation-handoff

**Completed:**
- Updated `app/schemas/listings.py` — added `thumbnail_url`, `sku`, `etsy_updated_at` to `ListingListItemResponse`; `filters: dict[str, Any] | None` to `ListingPageResponse`; `personalization_is_required`, `personalization_char_count_max` to `ListingDetailResponse`
- Rewrote `app/api/v1/listings.py` — `VALID_SORT_COLS` whitelist, 400 on invalid sort_by/sort_dir, 10 new query filters (tag, has_variations, price_min/max, quantity_min/max, section_id, taxonomy_id, is_personalizable, is_customizable), batch thumbnail fetch (one IN query per page), `model_copy(update={"thumbnail_url": ...})` injection, `active_filters` metadata in response
- Extended `tests/test_listings.py` — 18 new tests: all 10 new filters, sort_by asc/desc, invalid sort 400, filters metadata, no-filters null. Full suite: 93/93 PASSED
- Created `apps/frontend/lib/api.ts` — typed API client: `ApiError`, `apiFetch`, `getShops`, `getListings`, `getListing`, `getListingImages`, `getListingVideos`, `getListingVariations`, `syncShop`, `logoutLocalSession`; full TypeScript types for all response shapes
- Rewrote `apps/frontend/app/listings/page.tsx` — state tabs (All/Active/Inactive/Draft/Expired), advanced filter panel (collapsible, 10 filter fields), saved views (localStorage), column visibility dropdown (localStorage-persisted), multi-select checkboxes with select-all, sortable column headers with ↑↓ indicator, thumbnail preview (9×9 rounded image), detail sidebar (slide-in, full listing detail + tags + description + Etsy link), summary cards (total page, selected, active, out-of-stock)

**Test results:** 93/93 PASSED (18 new + 75 existing)

**Decisions made:**
- Batch thumbnail: 2 queries per page (count + images IN), no N+1 — see DECISIONS.md
- Cross-DB JSON tag search via `cast(Listing.tags, String).ilike(...)` — works SQLite + PostgreSQL
- Column visibility and saved views stored in localStorage (no DB table needed at MVP scale)
- Bulk Edit button disabled placeholder in grid — actual flow wired in Sprint 7

**Blockers:** None

**Next:** Sprint 7 — Bulk Edit Preview Engine

---

## 2026-06-25 Sprint 5 — Etsy Listing Sync

**Skills active:** 11 etsy-integration, 06 database-modeling, 07 backend-api, 08 frontend-ui, 14 background-jobs, 10 billing-stripe, 20 testing-qa, 01 documentation-handoff

**Completed:**
- Created 5 new SQLAlchemy models: Listing, ListingImage, ListingVideo, ListingVariation, SyncJob
- Updated `app/models/__init__.py` — all 10+ models imported
- Created `alembic/versions/0004_create_listing_sync_tables.py` — migration for 5 tables
- Created `app/schemas/listings.py` — 7 response schemas (SyncJobResponse, ListingListItemResponse, ListingDetailResponse, ListingPageResponse, ListingImageResponse, ListingVideoResponse, ListingVariationResponse)
- Created `app/services/etsy_sync.py` — full sync pipeline: token retrieval (decrypt, expiry check), paginated fetch (PAGE_LIMIT=100), upsert_listing/images/videos/variations, SyncJob lifecycle (pending→running→completed/failed), max_listings plan gate, best-effort video/variation sync
- Created `app/api/v1/shops.py` — POST /shops/{id}/sync (inline, Celery placeholder comment), GET /shops/{id}/sync-status
- Created `app/api/v1/listings.py` — GET /listings (org-scoped, shop/state/search filters, pagination, sort), GET /listings/{id}, /images, /videos, /variations
- Updated `app/api/v1/router.py` — include shops_router + listings_router
- Created `tests/test_listings.py` — 16 tests
- Created `apps/frontend/app/listings/page.tsx` — shop selector, sync button, state/search filters, paginated table, loading/empty/error states
- Updated `apps/frontend/app/dashboard/page.tsx` — Listings card + feature grid links

**Test results:** 75/75 PASSED (16 new + 59 existing)

**Bug fixes:**
- `_setup_connected_shop` uses org-based unique `etsy_shop_id` to avoid SQLite UNIQUE constraint conflicts across tests sharing the same in-memory DB
- `sync_shop_listings` caps `results[:remaining]` to enforce max_listings even when mock returns more than requested

**Decisions made:**
- Inline sync (not Celery) for Sprint 5 MVP — Celery task deferred to Sprint 8
- Results capped to `remaining = max_listings - total_fetched` before processing (guards against Etsy returning more than requested)
- Video sync is best-effort: 404/405 returns empty list, not error
- Listing model stores `raw_data` JSON for defensive future field access

---

## 2026-06-25 Sprint 4 — Etsy OAuth2 PKCE Flow

**Skills active:** 11 etsy-integration, 06 database-modeling, 07 backend-api, 08 frontend-ui, 20 testing-qa, 21 security-audit

**Completed:**
- Added ENCRYPTION_KEY, ETSY_CLIENT_ID, ETSY_REDIRECT_URI, ETSY_SCOPES to `app/core/config.py` + `is_etsy_configured()` method
- Created `app/core/encryption.py` — Fernet `encrypt_token`/`decrypt_token` with documented dev fallback key (`ZGV2X2VuY3J5cHRpb25fa2V5X3BsYWNlaG9sZGVyISE=`)
- Created `app/models/etsy_shop.py` — EtsyShop model (org-scoped, etsy_shop_id UNIQUE)
- Created `app/models/etsy_token.py` — EtsyToken model (etsy_shop_id FK UNIQUE, encrypted tokens, expires_at)
- Created `app/models/etsy_oauth_state.py` — EtsyOAuthState (PKCE state storage with consumed_at for single-use)
- Updated `app/models/__init__.py` — imports all 10 models
- Created `alembic/versions/0003_create_etsy_tables.py` — migration for 3 new tables
- Created `app/schemas/etsy.py` — EtsyAuthorizeResponse, EtsyShopResponse, EtsyShopsResponse, EtsyDisconnectResponse
- Created `app/services/etsy.py` — PKCE helpers (generate_code_verifier, generate_code_challenge), create_authorization_session, handle_oauth_callback, exchange_code_for_token, fetch_etsy_shop, list_connected_shops, disconnect_shop, refresh_etsy_token (placeholder)
- Created `app/api/v1/etsy.py` — GET /etsy/authorize, GET /etsy/callback (always redirects), GET /etsy/shops, DELETE /etsy/shops/{id}
- Updated `app/api/v1/router.py` — include etsy_router
- Created `tests/test_etsy.py` — 15 tests covering encryption, PKCE, authorize 503/401/200, callback redirect cases, success flow, shops list, disconnect 404
- Updated `tests/conftest.py` — shared-memory SQLite URI (`file:testdb?mode=memory&cache=shared&uri=true`) for cross-fixture data sharing
- Created `apps/frontend/app/shops/page.tsx` — shops list, connect button (OAuth redirect), disconnect, banners
- Updated `apps/frontend/app/dashboard/page.tsx` — Etsy Shops link added

**Test results:** 59/59 PASSED (15 new + 44 existing)

**Decisions made:**
- EtsyOAuthState consumed via `consumed_at` timestamp (not delete) — audit trail preserved
- Callback always returns 302 redirect, never raises HTTPException — OAuth security requirement
- Dev Fernet key computed from `base64.urlsafe_b64encode(b"dev_encryption_key_placeholder!!")` — deterministic, documented warning
- Shared-memory SQLite URI needed when `client` + `db_session` fixtures used in same test

---

## 2026-06-25 Sprint 3 — Stripe Billing and Feature Gates

**Skills active:** 10 billing-stripe, 06 database-modeling, 07 backend-api, 08 frontend-ui, 20 testing-qa, 21 security-audit, 01 documentation-handoff

**Completed:**
- Added `stripe==15.3.0` to requirements.txt
- Added Stripe env vars to `app/core/config.py` (STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_*); helper methods `is_stripe_configured()`, `is_stripe_webhook_configured()`, `get_stripe_price_id(plan)`
- Created `app/core/plans.py` — plan limits dict for free/basic_monthly/pro_monthly/basic_yearly/pro_yearly
- Created `app/models/subscription.py`, `billing_event.py`, `usage_counter.py`
- Updated `app/models/__init__.py` — imports all 7 models for Alembic autogenerate
- Created `alembic/versions/0002_create_billing_tables.py` — migration for subscriptions, billing_events, usage_counters
- Created `app/schemas/billing.py` — PlanLimitsResponse, PlansResponse, SubscriptionResponse, CheckoutRequest/Response, PortalResponse, UsageResponse
- Created `app/services/billing.py` — ensure_subscription_exists, can_use_feature, check_usage_limit, increment_usage, create_checkout_session, create_portal_session, process_webhook_event + sub-handlers
- Updated `app/core/deps.py` — added `get_current_org_id` dependency
- Created `app/api/v1/billing.py` — 6 endpoints: GET plans, GET subscription, POST checkout, POST portal, POST webhook, GET usage
- Updated `app/api/v1/router.py` — includes billing router
- Created `apps/frontend/app/pricing/page.tsx` — 5-plan grid with limits, upgrade buttons, BACKEND_URL integration
- Created `apps/frontend/app/billing/page.tsx` — subscription status, portal button, success/canceled query params
- Updated `apps/frontend/app/dashboard/page.tsx` — Pricing/Billing quick-links
- Created `tests/test_billing.py` — 26 tests

**Test results:** 44/44 PASSED (4 health + 14 auth + 26 billing), 0 warnings

**Decisions made:**
- Webhook secret detection: `whsec_` prefix check (not placeholder detection)
- Stripe configured detection: `sk_test_` or `sk_live_` prefix check
- Webhook event idempotency: unique constraint on `stripe_event_id` + early-return check
- UsageCounter: DB model with `period_key=YYYY-MM` (not Redis) per sprint spec
- Sync Stripe calls in async routes: acceptable for Sprint 3, fix in Sprint 18
- Mocking pydantic-settings in tests: patch full module-level `settings` ref (not instance attribute)

**Blockers:** None

**Next:** Sprint 4 — Etsy OAuth

---

## 2026-06-25 Sprint 2 — Auth + Organization

**Skills active:** 09 auth-security, 06 database-modeling, 07 backend-api, 08 frontend-ui, 20 testing-qa

**Completed:**
- Added `passlib[bcrypt]==1.7.4`, `PyJWT==2.9.0`, `email-validator==2.2.0` to requirements.txt
- Added `aiosqlite==0.20.0` to requirements-dev.txt
- Added JWT settings to `app/core/config.py` (JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15, JWT_REFRESH_TOKEN_EXPIRE_DAYS=7)
- Updated `app/db/base.py` TimestampMixin: added Python-side `default=lambda` for SQLite test compat
- Created `app/core/security.py`: bcrypt hash/verify, JWT access token, SHA-256 refresh token hash
- Created `app/core/deps.py`: get_current_user, require_active_user, require_superuser (HTTPBearer)
- Created `app/models/user.py`, `organization.py`, `organization_member.py`, `refresh_token.py`
- Updated `app/models/__init__.py`: imports all 4 models for Alembic autogenerate
- Created `app/schemas/auth.py`: all Pydantic request/response schemas
- Created `app/services/auth.py`: register_user, login_user, refresh_tokens, logout_user, _issue_tokens, AuthError
- Created `app/api/v1/auth.py`: 5 endpoints (register 201, login 200, refresh 200, logout 204, me 200)
- Updated `app/api/v1/router.py`: includes auth router
- Created `alembic/versions/0001_create_auth_tables.py`: hand-written migration for users, organizations, organization_members, refresh_tokens
- Updated `tests/conftest.py`: SQLite+aiosqlite engine per test, get_db override
- Created `tests/test_auth.py`: 14 tests covering all scenarios
- Created `apps/frontend/app/register/page.tsx`: client form, localStorage token storage
- Created `apps/frontend/app/login/page.tsx`: client form, localStorage token storage
- Updated `apps/frontend/app/dashboard/page.tsx`: auth state display, logout button

**Test results:** 18/18 PASSED (4 health + 14 auth), 0 warnings

**Decisions made:**
- Refresh tokens: SHA-256 hash in DB (not Redis, not bcrypt)
- Refresh token rotation on every use
- UUIDs as Uuid(as_uuid=False) / VARCHAR(36) for SQLite compat
- Organization created on user registration with owner role

**Blockers:** None

**Next:** Sprint 3 — Stripe Billing and Feature Gates

---

## 2026-06-25 Sprint 1 (rev 2) — Custom Ports Applied + CORS Fix

**Skills active:** 05 repo-setup, 04 system-architect, 07 backend-api, 22 devops-deployment, 01 documentation-handoff

**Completed:**
- Updated `docker-compose.yml`: host ports 3100/8100/55432/56379 (container ports unchanged)
- Updated `.env.example`: FRONTEND_URL=:3100, BACKEND_URL=:8100, BACKEND_CORS_ORIGINS plain string format
- Updated `apps/backend/.env.example`: localhost:55432, localhost:56379
- Updated `apps/frontend/.env.local.example`: NEXT_PUBLIC_BACKEND_URL, NEXT_PUBLIC_APP_URL
- Updated `apps/frontend/app/page.tsx`: env var → NEXT_PUBLIC_BACKEND_URL, default :8100
- Updated `apps/frontend/app/dashboard/page.tsx`: same
- Fixed `app/core/config.py`: BACKEND_CORS_ORIGINS as `str` with `get_cors_origins()` method (pydantic-settings v2 can't use field_validator on List[str] before JSON pre-parse)
- Updated `app/main.py`: CORS middleware uses `settings.get_cors_origins()`
- Updated `Makefile`: health curl targets use :8100
- Updated `README.md`, `docs/operations/DEPLOYMENT.md`: all URLs use custom ports
- Ran pytest: 4/4 PASSED, 0 warnings
- Verified CORS validator: plain string and JSON array both parse correctly

**Decisions made:**
- Custom host ports documented in DECISIONS.md
- BACKEND_CORS_ORIGINS storage strategy documented in DECISIONS.md

**Blockers:** None

**Next:** Sprint 2 — Auth + Organization

---

## 2026-06-25 Sprint 1 — Monorepo Skeleton Created

**Skills active:** 05 repo-setup, 04 system-architect, 07 backend-api, 08 frontend-ui, 06 database-modeling, 22 devops-deployment, 20 testing-qa

**Completed:**
- Created `apps/frontend/` — Next.js 14, App Router, TypeScript, Tailwind CSS, landing page, dashboard placeholder, Dockerfile
- Created `apps/backend/` — FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2 settings, health endpoints (`/api/v1/health`, `/api/v1/health/db`, `/api/v1/health/redis`), Dockerfile, pytest suite (4/4 pass)
- Created `docker-compose.yml` — services: frontend (3000), backend (8000), postgres (5432), redis (6379) with healthchecks
- Created `Makefile` — `make dev`, `make migrate`, `make test`, `make health`
- Created `.gitignore` — Python + Node + Docker volumes
- Updated `.env.example` — Docker Compose alignment, frontend env vars
- Updated `README.md` — full local setup instructions
- Ran pytest: 4/4 PASSED, 0 warnings

**Decisions made:**
- See DECISIONS.md for anyio version note and asyncpg pool config

**Blockers:** None

**Next:** Sprint 2 — Auth + Organization

---

## 2026-06-25 Sprint 0 — Project Operating System Initialized

**Skills active:** 01 documentation-handoff, 05 repo-setup

**Completed:**
- Created all Sprint 0 files (CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, ARCHITECTURE.md, LIMIT_PROTOCOL.md, SECURITY.md, CHANGELOG_AI.md, ROADMAP.md, README.md, .env.example)
- Created all Claude command files (.claude/commands/)
- Created all documentation files (docs/product/, docs/technical/, docs/operations/)
- Initialized git repository and connected to GitHub remote
- Committed and pushed Sprint 0 to main

**Decisions made:**
- See DECISIONS.md — full tech stack and product decisions documented

**Blockers:** None

**Next:** Sprint 1 — Monorepo Skeleton

---

## 2026-06-25 Sprint 9 — Magic Revert

**Skills active:** 07 backend-api, 06 database-modeling, 08 frontend-ui, 20 testing-qa, 01 documentation-handoff

**Completed:**

Models (2 new):
- `RevertJob` — tracks the revert run (org-scoped, apply_job_id FK, status, counters, timestamps)
- `RevertResult` — per-listing revert record (backup_snapshot_id nullable FK SET NULL — handles skip cases)

Migration:
- `0007_create_bulk_edit_revert_tables.py` — revert_jobs + revert_results tables; backup_snapshot_id nullable with SET NULL

Services:
- `bulk_edit_revert.py`:
  - `build_etsy_revert_payload(snapshot_data)` — builds Etsy PATCH body from snapshot; excludes price/qty (same as apply)
  - `update_local_listing_from_snapshot(listing, snapshot_data)` — in-place listing restore
  - `validate_apply_job_revertable(db, org_id, apply_job_id)` — 404 if not found, 400 if not completed, 409 if already reverted
  - `revert_apply_job(db, org_id, user_id, apply_job_id)` — 10 safety gates, only `status=success` apply results iterated, per-listing local update only after Etsy write success, partial failure supported, audit logs on start + finish
  - `get_revert_job`, `list_revert_jobs_for_apply_job`, `get_revert_results` — read endpoints with org isolation

API (4 new endpoints):
- `POST /api/v1/bulk-edit/apply-jobs/{id}/revert` → 202 + RevertJobOut
- `GET /api/v1/bulk-edit/apply-jobs/{id}/revert-jobs` → list jobs
- `GET /api/v1/bulk-edit/revert-jobs/{id}` → job + results
- `GET /api/v1/bulk-edit/revert-jobs/{id}/results` → paginated RevertResultPageOut

Tests: 28 new in `test_bulk_edit_revert.py` (181/181 pass)
- Unit: build_etsy_revert_payload (title, description, section_id, excludes price/qty, empty snapshot)
- API: Etsy not configured 503, apply job not found 404, apply job not completed 400, double-revert 409, wrong org 404, auth 403
- Happy path: creates job 202, restores listing title, ETsy failure does not modify listing, only success results reverted, partial failure statuses, audit logs written, snapshots not deleted
- Read endpoints: list revert jobs, get revert job detail, paginated results, org isolation, auth required

Frontend:
- `lib/api.ts` — 4 new types (RevertJob, RevertResult, RevertJobWithResults, RevertResultPage) + 4 helpers
- `app/bulk-edit/page.tsx` — Magic Revert button (visible after completed/completed_with_errors apply, hidden after revert), REVERT text confirmation modal, revert result status card

**Key decisions:**
- `RevertResult.backup_snapshot_id` nullable (SET NULL) — skipped items (no listing, no snapshot ID, snapshot not found, no token) need a valid DB row but have no valid FK
- Skip cases produce status `"skipped"` RevertResult rows rather than being silently dropped — full audit trail
- Price/quantity revert deferred to Sprint 10 (same reason as apply: inventory endpoint required)

**Blockers:** None

**Next:** Sprint 10 — Etsy Inventory Writes (price/quantity)

---

## 2026-06-25 Sprint 8 — Etsy Write + Backup

**Skills active:** 07 backend-api, 06 database-modeling, 08 frontend-ui, 20 testing-qa, 01 documentation-handoff

**Completed:**

Models (4 new):
- `ListingBackupSnapshot` — pre-write snapshot stored per listing before every Etsy write
- `BulkEditApplyJob` — tracks the apply run (status, counters, timestamps)
- `BulkEditApplyResult` — per-listing record with request payload, response payload, error, and backup reference
- `AuditLog` — immutable event log; Python attr `extra_data` maps to DB column `metadata` (SQLAlchemy `metadata` is reserved)

Migration:
- `0006_create_bulk_edit_apply_tables.py` — 4 new tables

Services:
- `etsy_write.py` — `build_etsy_patch_payload` (maps diff → Etsy PATCH body; excludes price/qty; maps `section_id` → `shop_section_id`), `patch_etsy_listing` (PATCH /v3/application/listings/{id} via httpx)
- `bulk_edit_apply.py` — `apply_bulk_edit_session`: 5 sequential safety gates (preview_ready, no invalid items, Etsy configured, plan limit), per-listing backup → PATCH → local update only on success, audit log on start/finish, usage counter increment

API (5 new endpoints, replaced 409 stub):
- `POST /api/v1/bulk-edit/sessions/{id}/apply` → 202 + ApplyJobOut
- `GET /api/v1/bulk-edit/sessions/{id}/apply-jobs` → list jobs
- `GET /api/v1/bulk-edit/apply-jobs/{job_id}` → job + results
- `GET /api/v1/bulk-edit/sessions/{id}/backups` → backup snapshots

Tests: 22 new in `test_bulk_edit_apply.py` (153/153 pass)
- Unit: payload builder (title, tags, section_id mapping, price/qty exclusion)
- API: safety gate 400/503/422, org isolation 404, success flow, failure-no-modify, backup creation, usage increment

Frontend:
- `lib/api.ts` — 4 new types + 4 new helpers
- `app/bulk-edit/page.tsx` — replaced disabled stub button with confirmation modal + real apply call + result status card

**Key decision:** `metadata` is a reserved SQLAlchemy DeclarativeBase attribute. Used `extra_data` as Python attribute name with `name="metadata"` in `mapped_column` to store in the expected DB column name.

**Blockers:** None

**Next:** Sprint 9 — Magic Revert (revert apply jobs using ListingBackupSnapshot records)

---

## Session 2026-06-26 — Sprint 17: Admin Panel

**Status:** COMPLETE

**New files:**
- `apps/backend/app/schemas/admin.py` — 16 Pydantic schemas. Secrets redacted: no password_hash, no Etsy tokens, no Stripe secret keys.
- `apps/backend/app/services/admin.py` — generic paginator + 14 list queries + 4 safe actions (disable/enable user, pause/resume scheduled job).
- `apps/backend/app/api/v1/admin.py` — 20 endpoints all gated on `require_superuser`.
- `apps/backend/tests/test_admin_panel.py` — 42 tests.
- `apps/frontend/app/admin/page.tsx` — full admin UI with overview cards, 6 section tabs, pagination, and inline actions.

**Modified files:**
- `apps/backend/app/api/v1/router.py` — registered admin router.
- `apps/frontend/lib/api.ts` — appended admin types + 11 API helpers.
- `apps/frontend/app/dashboard/page.tsx` — added "Admin Panel" card.

**Test results:** 521/521 PASSED (42 new admin tests)

**Frontend build:** Clean, /admin route included

**Security gates verified:**
- All 20 endpoints require is_superuser=True → 403 for regular users
- No password_hash in any response
- No Etsy access_token/refresh_token in shop responses
- No stripe_subscription_id or stripe_price_id in subscription responses
- Cannot disable own account (400)
- No destructive deletes

**Blockers:** None

**Next:** Sprint 18 — Tests, Deployment, Security Hardening, Polish
