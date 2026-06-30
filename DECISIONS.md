# DECISIONS.md — Architecture and Product Decisions

Format: `[DATE] [CATEGORY] Decision — Rationale`

---

## 2026-06-30 (One-click startup reliability)

### [DEVOPS] postgres/redis use `expose:` not `ports:` in docker-compose.yml
Windows Hyper-V/WSL2 dynamic port reservation ranges include common high ports (e.g. 55432). `ports:` causes Docker to bind on the Windows host, which hits ACL restrictions. `expose:` keeps services network-reachable inside Docker only — internal DATABASE_URL/REDIS_URL connectivity unchanged. Optional dev access via `docker-compose.dev-ports.yml` override.

### [DEVOPS] Demo seed file written with WriteAllLines + UTF8Encoding($false) in PowerShell
PowerShell 5.1 default `-Encoding UTF8` on `Set-Content`/`Out-File` adds a UTF-8 BOM (EF BB BF). Python's `open()` with `encoding="utf-8"` preserves the BOM as part of the first key name, causing `_require("FREE_SUPERUSER_EMAIL")` to silently fail. Both ends hardened: writer uses `WriteAllLines` + explicit no-BOM encoding; reader uses `encoding="utf-8-sig"` which strips BOM if present.

### [DEVOPS] verify-demo-logins.ps1 runs after backend readiness (Step 7c in setup-and-start.bat)
Verifying demo login via HTTP POST to `/api/v1/auth/login` is the only safe way to confirm the seed ran and the accounts are usable. Halts setup with a clear error + backend logs tail if either account fails. Avoids silent seed failures reaching users with a broken login screen.

---

## 2026-06-27 (Sprint 25)

### [ARCHITECTURE] Media local upload is frontend-only (Option A) — no backend upload endpoint
`LocalUploadPanel` uses `File API` + `URL.createObjectURL()`. No multipart upload, no S3 presign, no path traversal risk. Thumbnails are object URLs revoked on remove/clear. Rationale: no existing backend upload infrastructure; feature purpose is preview/staging, not permanent storage.

### [UX] Etsy disclaimer in FAQ removed — retained only in shared MarketingFooter
MarketingFooter already renders the full Etsy trademark disclaimer in its legal section. The FAQ-specific indigo block was redundant and inconsistent with other marketing pages that rely on footer-only disclaimer.

### [UX] Shops added to AppShell nav — placed in Workspace section between Dashboard and Listings
Route `/shops` existed (Sprint 4/22) but was not linked in main nav. Added ShopIcon + Shops entry for discoverability. Position between Dashboard and Listings reflects typical onboarding flow.

---

## 2026-06-27 (Sprint 24)

### [ARCHITECTURE] Listing health score is dynamic — no snapshot table
Health scores recalculated on each API request from current listing data. No `listing_health_scores` table. Avoids stale score problem and extra migration complexity.

### [ARCHITECTURE] Cost informational warning excluded from issue_count
`has_cost_data=False` is informational (no penalty). Adding it to `issues` list caused `test_score_perfect_listing` to fail (expected 0 issues). Moved to separate `informational` field in score result. Issue count is only for actionable items with points_lost > 0.

### [API] AI suggestions endpoint safe no-op when AI not configured
`POST /listing-health/listings/{id}/ai-suggestions` returns `{ai_available: false, message: "..."}` when `AI_PROVIDER=mock` or API keys not set. Never raises 500. Never auto-applies suggestions to Etsy.

### [TESTING] @pytest.mark.anyio removed from Sprint 24 tests
Use `asyncio_mode = auto` from pytest.ini instead (matches all other test files in this repo). `@pytest.mark.anyio` causes tests to run under both asyncio and trio backends; trio not installed → 20 errors per file. Simpler to use project convention.

### [TESTING] Auth guard returns HTTP 403, not 401
FastAPI OAuth2PasswordBearer with `auto_error=True` returns 403 Forbidden when no credentials supplied. Sprint 24 auth-gate tests updated to `assert r.status_code in (401, 403)`.

## 2026-06-27 (Sprint 23)

### [DEVOPS] validate_env.py uses ASCII-only output for Windows cp1252 compatibility
Unicode symbols (checkmark, warning, em-dash) are not encodable in Windows cp1252 terminal. Replaced with ASCII PASS/WARN/FAIL labels and regular hyphens. ANSI color codes still used - they render correctly in CI (Linux) and Windows Terminal; older cmd.exe strips them cleanly.

### [DEVOPS] validate_env.py checks ENVIRONMENT var (not APP_ENV) to match config.py
Backend config.py uses `ENVIRONMENT` as the env var name. validate_env.py reads `ENVIRONMENT` as the default for `--env` to stay consistent with the app's own config. CI workflow sets this explicitly.

### [DEVOPS] Production compose example uses health checks with `service_healthy` depends_on
Frontend depends_on backend with `condition: service_healthy`. This prevents frontend from starting before backend is ready, matching the local docker-compose.yml pattern.

### [DEVOPS] docker-compose.prod.example.yml is reference-only; not named docker-compose.override.yml
Naming it `.example.yml` prevents `docker compose up` from accidentally using it without explicit `-f` flag. Teams must consciously copy and adapt it. Keeps the dev workflow (plain `docker compose up`) unchanged.

---

## 2026-06-27 (Sprint 22)

### [SEED] FREE seed user is is_superuser=False; PAID seed user is is_superuser=True
The original `local_seed.py` hardcoded `is_superuser=True` for all seeded users, making local testing of normal-customer UX impossible. Fixed by adding `is_superuser: bool` param to `_upsert_user()` and `seed_superuser()`. `seed_on_startup()` explicitly passes `is_superuser=False` for FREE and `is_superuser=True` for PAID. Default for `seed_superuser()` stays `True` for backward compat with direct callers. All existing tests continue to pass because they call `seed_superuser()` without the param.

### [UX] OnboardingChecklist hides when all steps complete
The checklist renders `null` when `completedCount === steps.length`. This avoids an empty card flash. Steps 3 and 4 (try bulk edit, explore paid features) are permanently `done: false` — they are prompts, not completion-trackable actions. Only shop connection and listing sync are derived from API counts.

### [UX] Dashboard fetches shop/listing counts on mount; checklist gated on both resolving
Used two independent `fetch` calls so a slow listings endpoint doesn't block the checklist from showing at all. `showChecklist` is only true when both counts are non-null. If either fetch fails, the corresponding count defaults to 0 (shows step as incomplete — safe conservative default).

---

## 2026-06-27 (Sprint 20)

### [SECURITY] CSP uses 'unsafe-inline' for scripts — nonce hardening deferred to Sprint 21
The anti-flash theme script in `app/layout.tsx` uses `dangerouslySetInnerHTML` (inline script). CSP without `'unsafe-inline'` would block it and cause a white flash before React hydrates. Chose pragmatic CSP with `'unsafe-inline'` for initial launch. Sprint 21: implement nonce-based CSP via Next.js middleware (inject nonce into both the script tag and the CSP header per-request).

### [SECURITY] Rate limiter is in-memory (not Redis) by default
Chose custom in-memory limiter over slowapi to avoid adding a new package dependency. Memory limiter is per-process and resets on restart — not suitable for multi-instance production. `RATE_LIMIT_BACKEND=redis` is documented as the production setting. Sprint 21: implement Redis-backed limiting via `aioredis` or `slowapi` when Celery workers are deployed.

### [SECURITY] RATE_LIMIT_ENABLED defaults False
Rate limiting defaults to disabled to prevent test suite instability (429s from rapid test execution). Production must set `RATE_LIMIT_ENABLED=true` in environment. CI workflow explicitly sets `RATE_LIMIT_ENABLED=false`.

### [DEVOPS] Playwright seeded-user tests use PLAYWRIGHT_RUN_SEEDED_TESTS=1 env var
Seeded-user E2E tests require a running Docker stack with seeded users. CI has no backend running during frontend checks job. Used an explicit opt-in env var (`PLAYWRIGHT_RUN_SEEDED_TESTS=1`) rather than `CI` env check to allow running them locally even when other env vars are set.

### [DEVOPS] GitHub Actions backend job uses SQLite tests (via conftest.py)
The test suite uses `sqlite+aiosqlite` in-memory DB (set in `conftest.py`). The CI postgres:16 service is available for future migration testing but current tests don't use it. The `alembic upgrade head` step runs against the postgres service to validate migrations. Test suite runs against SQLite as before.

---

## 2026-06-26 (Sprint 19)

### [PRODUCT] Projected MRR labeled as "Expected — not guaranteed cash"
The `estimated_monthly_revenue` field in `AdminBillingSummary` uses per-plan fixed monthly rates ($9 basic_monthly, $29 pro_monthly, $7.50 basic_yearly/12, $20.83 pro_yearly/12). This is a projection based on DB plan counts — not actual Stripe collected revenue. The field is named `estimated_monthly_revenue` (not `collected_revenue`) and the frontend displays it with sub-label "Expected — not guaranteed cash". Stripe collected revenue is not available without a live Stripe API call.

### [SECURITY] Admin nav item hidden client-side + backend enforces superuser gate server-side
The Admin nav link in AppShell is hidden when `is_superuser === false` (from `/me` response). This is UI convenience only — the backend still enforces `require_superuser` on every admin endpoint. A user who manually navigates to `/admin` will hit the 403 page (API returns 403, UI shows the access-denied screen). Defense in depth: both layers protect the resource.

### [API] `/api/v1/admin/audit-log` duplicates `/api/v1/admin/events`
Sprint 19 adds `/admin/audit-log` as a distinct endpoint (same backing service as `/events`). Rationale: business dashboard uses a tab called "Audit Log" for the System tab, while `/events` is used in the original admin CRUD panel section. Having two named endpoints clarifies intent and avoids breaking the existing admin panel.

### [FRONTEND] AdminUsageSummary added to api.ts (was only in backend schema)
The existing `/api/v1/admin/usage` endpoint lacked a TypeScript type in `lib/api.ts`. Sprint 19 adds `AdminUsageSummary` interface and `adminListUsage()` helper to support the new Usage tab.

---

## 2026-06-26 (Sprint 18)

### [SECURITY] FastAPI HTTPBearer returns 403 (not 401) for missing credentials
FastAPI's `HTTPBearer` scheme returns HTTP 403 when no Authorization header is present (`auto_error=True` default). This is a known FastAPI behavior — 401 would be more semantically correct per RFC 7235 (Unauthorized = no credentials; Forbidden = credentials present but insufficient). Security tests accept `in (401, 403)` to be accurate. A future sprint can configure `HTTPBearer(auto_error=False)` and raise 401 manually.

### [SECURITY] Security test assertions use `in (401, 403)` for unauthenticated access
All 11 "no token" security tests assert `status_code in (401, 403)`. Rationale: FastAPI's bearer scheme returns 403 for missing token. Both codes correctly block access — the distinction is semantic. Keeping this as-is avoids modifying auth middleware and risking regressions.

### [TESTING] Org isolation tests assert `r.json() == []` for flat-list endpoints
`/api/v1/bulk-edit/sessions`, `/api/v1/csv/jobs`, `/api/v1/dynamic-pricing/jobs`, `/api/v1/scheduled-jobs/jobs` all return plain JSON arrays (not paginated `{"total": n, "items": [...]}` objects). Security isolation tests use `== []` assertions for these endpoints.

---

## 2026-06-26 (Sprint 16)

### [SPRINT-16] Scheduled jobs never write to Etsy and never auto-apply changes
All 4 job type executors are read-only from Etsy's perspective: `etsy_sync` calls the read-only sync service. `bulk_edit_draft` creates a `BulkEditSession(status="draft")` only. `dynamic_pricing_preview` creates a preview-only DynamicPricingJob. `csv_export_snapshot` returns metadata only. None of these trigger etsy_write.py or bulk_edit_apply.py. User action required before any Etsy write.

### [SPRINT-16] min interval 60 minutes, day_of_month 1–28
Minimum scheduled interval is 60 minutes to prevent runaway API calls. Monthly day_of_month is capped at 28 to avoid month-end edge cases (Feb has 28 days in non-leap years). These are enforced at validation time in schedule_calculator.py.

### [SPRINT-16] No Celery for MVP scheduled job execution
Celery background execution is deferred. Sprint 16 implements service-layer execution + run-due endpoint pattern. Calling POST /run-due executes all due jobs for the current user's organization. For production, a cron job or Celery Beat calls this endpoint. FastAPI has no infinite background loops.

### [SPRINT-16] Active job count excludes paused/disabled/completed jobs for plan gate
Plan limit `max_scheduled_jobs` counts only `status="active"` jobs. Paused, disabled, and completed jobs do not count. Rationale: a user who paused old jobs should not be penalized — they are not consuming scheduled resources.

---

## 2026-06-26 (Docker Fix)

### [DB] All model ID and FK columns must use String(36), not Uuid(as_uuid=False)
Migration 0001 creates `users` and `organizations` with `VARCHAR(36)` primary keys (via `sa.String(36)`). All sprint migrations must use `sa.String(36)` for FK columns referencing these tables. ORM model files must also use `String(36)` (not `Uuid(as_uuid=False)`). Reason: asyncpg renders `Uuid(as_uuid=False)` as `$1::UUID` type cast; PostgreSQL cannot compare `UUID = VARCHAR(36)`, rejecting every WHERE clause using those columns. Converting the DB to native UUID type is not done — would require dropping and recreating all tables with data.

### [DEPS] bcrypt must be pinned to 4.0.1
passlib 1.7.4 (the last stable release) is not compatible with bcrypt 5.x. bcrypt 5.0.0 removed `__about__.__version__`, which passlib uses for backend detection. This causes `AttributeError` on startup and `password cannot be longer than 72 bytes` on every hash call. Pin `bcrypt==4.0.1` in requirements.txt. Upgrade only when passlib publishes a 5.x-compatible release.

---

## 2026-06-26 (Local Dev Reliability)

### [LOCAL-DEV] Seed script runs via docker compose exec, not on host
The seed script (scripts/seed_local_superusers.py) runs inside the Docker backend container via `docker compose exec backend python scripts/seed_local_superusers.py`. The backend volume mount (./apps/backend:/app) makes the script and the .local-superusers.env file available inside the container. The container's DATABASE_URL env var already points to the internal postgres service. No host Python installation required.

### [LOCAL-DEV] Subscription status is "active" not "free" for all seeded users
Existing code creates subscriptions with status="free" as default. Seeded users always get status="active" so plan gates read correctly. The billing service uses subscription.plan (not status) for feature checks, so this is cosmetically correct.

### [LOCAL-DEV] .bat scripts now run docker compose -d then poll health before browser open
Previously scripts ran `docker compose up --build` (foreground) and opened browser after a fixed 12-second delay. Changed to: run `-d --build` (detached), poll backend health and frontend via PowerShell Invoke-WebRequest (5s intervals, 180s timeout), then open browser. Browser never opens if either service fails readiness. Ctrl+C stops log streaming, not the services.

### [LOCAL-DEV] setup-and-start scripts do not include seed prompt
Seed prompt added only to start-dev.bat and start-dev-clean.bat (developer scripts). setup-and-start.bat and setup-and-start-clean.bat are friend/reviewer scripts — they don't have .local-superusers.env or Python access expectations, so seed prompt is excluded to keep the experience simple.

---

## 2026-06-26 (Sprint 15)

### [SPRINT-15] Dynamic Pricing converts to BulkEditSession draft, never writes Etsy
Approved recommendations create BulkEditSession(status="draft") + BulkEditChange(target_listing_ids=[listing_id]). Listing.price_amount is never updated. Rationale: must respect same Etsy write safety protocol as all other features — user must preview and apply in Bulk Edit before anything publishes.

### [SPRINT-15] Variation listings skipped in dynamic pricing
Listings with has_variations=True get status="skipped" and are not processed. Rationale: variation price structure is complex (per-offering); flat price_amount does not represent the listing correctly. Deferred to future sprint.

### [SPRINT-15] Rounding rule ending_99: exact dollars go down
apply_rounding_rule(2500, "ending_99") → 2499 (not 2599). Distance from 2500 to 2499 is 1; distance to 2599 is 99 → nearest wins. Rationale: consistent with retail psychology (price tags ending .99 are typically just below a round dollar).

### [SPRINT-15] Margin floor uses Decimal arithmetic
required_price = cost / (1 - margin_pct/100) computed with Decimal to avoid float rounding errors on price calculations. Rationale: price calculations are money — float arithmetic produces incorrect values.

### [SPRINT-15] Convert modal requires "CONVERT PRICES" typed confirmation
Frontend modal requires user to type exact string "CONVERT PRICES" before convert button activates. Rationale: convert is irreversible (creates draft session); confirmation prevents accidental conversion.

---

## 2026-06-26

### [SPRINT-12] Fetch-patch-put for variation inventory writes
Always GET current Etsy inventory tree before writing. Never construct tree from local `ListingVariation` data alone — local rows may be stale or incomplete (missing offering IDs, property IDs, etc.). Patch in memory, then PUT full tree back. Rationale: Etsy's inventory API requires the full tree on PUT; partial updates not supported.

### [SPRINT-12] Status gate before Etsy config gate in apply_variation_job
`job.status != "preview_ready"` check fires before `settings.is_etsy_configured()` check. Rationale: status check is a logical precondition (should return 400); Etsy config is an infrastructure requirement (503). Discovered as bug during testing — original code returned 503 for a draft job instead of 400.

### [SPRINT-12] Dual-source preview vs apply
Preview generated from local `ListingVariation` rows (fast, no Etsy calls, shows user what will change). Apply fetches fresh Etsy inventory tree per listing (authoritative, current). Rationale: preview must be cheap and offline-capable; apply must be correct.

### [SPRINT-12] VALID_OPERATION_TYPES defined in schema, not imported from service
Defined independently in `schemas/bulk_edit_variation.py` to avoid circular imports (schema → service would create a cycle). Kept in sync manually. Rationale: simpler than restructuring imports for a small constant set.

### [SPRINT-12] Variation revert deferred to Sprint 13
Backup snapshots (both `local_variations_snapshot` and `etsy_inventory_snapshot`) are created in Sprint 12 to enable Sprint 13 revert. The revert logic itself is deferred. Rationale: MVP scope; Sprint 12 focused on write safety, not undo.

### [SPRINT-12] Warning items do not block apply; invalid items do
`validation_status="invalid"` (e.g., listing has `has_variations=False`) blocks apply. `validation_status="warning"` (no local variations or no selector match) does not block — those listings produce skip results. Rationale: invalid means the operation is logically wrong; warning means it will have no effect (safe to skip).

---

## 2026-06-25

### [STACK] Frontend: Next.js 14 with App Router
Next.js 14 App Router chosen for SSR, file-based routing, server components, and strong TypeScript support. Aligns with modern React patterns. Alternative considered: Remix (rejected — smaller ecosystem).

### [STACK] Backend: FastAPI (Python 3.12)
FastAPI chosen for async-first design, automatic OpenAPI docs, Pydantic validation, and strong ecosystem for AI/ML integrations. Alternative considered: Node.js/Express (rejected — weaker AI library ecosystem).

### [STACK] Database: PostgreSQL 16
PostgreSQL chosen for JSONB support (listing metadata), full-text search, strong relational guarantees, and wide hosting support. Alternative considered: MySQL (rejected — weaker JSONB support).

### [STACK] ORM: SQLAlchemy 2.x + Alembic
SQLAlchemy 2.x async support with Alembic migrations. Industry standard for Python/PostgreSQL. No alternatives seriously considered.

### [STACK] Cache / Queue: Redis 7
Redis used for both caching and Celery broker. Single dependency serving two purposes. Alternative considered: RabbitMQ as broker (rejected — adds complexity for no gain at this scale).

### [STACK] Task Queue: Celery
Celery with Redis broker for background jobs. Mature, well-documented, integrates with FastAPI. Alternative considered: ARQ (rejected — smaller community, fewer features).

### [STACK] Auth: JWT (access + refresh)
JWT with short-lived access tokens (15 min) and rotating refresh tokens (7 days). Token blacklist in Redis. No server-side sessions to keep backend stateless.

### [STACK] Storage: S3-compatible
MinIO for local development, AWS S3 (or compatible) for production. Presigned URLs for direct client uploads. No media stored on application servers.

### [STACK] AI: OpenAI GPT-4o + Anthropic Claude
Dual-provider AI support. OpenAI GPT-4o for primary AI tools. Anthropic Claude as fallback and for specific use cases. Both require preview before apply.

### [PRODUCT] Subscription Tiers: Free, Monthly, Yearly
Three tiers: Free (limited features), Monthly Pro, Yearly Pro (discounted). No per-seat pricing at v1. Decision can be revisited after launch.

### [PRODUCT] Monorepo Structure
All code in single repo: `apps/frontend`, `apps/backend`, `packages/shared`. Simplifies CI/CD and type sharing at the cost of slightly more complex repo management.

### [SAFETY] External Write Protocol: 6-Step
All Etsy writes require: preview → user confirmation → snapshot → permission check → subscription gate → audit log. Non-negotiable. Rationale: Etsy write mistakes can cause seller revenue loss and are hard to reverse without our Magic Revert system.

---

## 2026-06-25 (Sprint 1)

### [BACKEND] Async SQLAlchemy engine pool config
Set `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`. Sufficient for initial load. Can tune in Sprint 18 based on observed connection patterns.

### [BACKEND] Health endpoints at /api/v1/health (not /health)
Chose `/api/v1/health` prefix to stay consistent with API versioning. All future endpoints under `/api/v1/`.

### [BACKEND] pydantic-settings model_config over inner Config class
Used Pydantic v2 `model_config` dict syntax instead of deprecated inner `Config` class. Avoids deprecation warnings with Pydantic 2.x.

### [INFRA] Custom local host ports to avoid conflict with other projects
Frontend host port: 3100 (container: 3000, mapping 3100:3000)
Backend host port: 8100 (container: 8000, mapping 8100:8000)
PostgreSQL host port: 55432 (container: 5432, mapping 55432:5432)
Redis host port: 56379 (container: 6379, mapping 56379:6379)
Rationale: avoids collision with another active local project using ports 3000, 8000, 5432, 6379. Production uses standard ports (80/443). Docker Compose internal traffic uses standard container ports (service-to-service).

### [BACKEND] BACKEND_CORS_ORIGINS stored as str, not List[str]
pydantic-settings v2 pre-parses `List[str]` fields as JSON before field validators run. Storing as `str` avoids this. `settings.get_cors_origins()` method handles parsing (plain string, comma-separated, or JSON array). `main.py` calls `settings.get_cors_origins()` when configuring CORS middleware.

### [DEPS] anyio 4.6.2 yanked warning
`anyio==4.6.2` in requirements-dev.txt is yanked on PyPI (mistagged 4.5.2 code). Still functional. Will update when `anyio>=4.7.0` is stable and compatible with pytest-asyncio 0.24.x.

### [FRONTEND] No shadcn/ui in Sprint 1
shadcn/ui setup deferred to Sprint 2 when auth pages will benefit from its form components. Sprint 1 uses raw Tailwind only.

### [SAFETY] AI Output: Preview-Only
AI output must never be applied directly to listings. Always goes through preview → user approval flow. Rationale: AI output quality varies; seller is responsible for their listing content.

---

## 2026-06-25 (Sprint 2)

### [AUTH] Refresh token stored as SHA-256 hash in DB (not Redis, not plaintext)
SHA-256 hash (64 hex chars) stored in `refresh_tokens.token_hash`. SHA-256 is sufficient for random tokens because the token itself is already cryptographically random (secrets.token_urlsafe(64)). bcrypt rejected — designed for passwords (intentionally slow), overkill for random tokens. Redis rejected — tokens should survive Redis restart without forcing all users to re-login.

### [AUTH] Refresh token rotation on every use
Each use of a refresh token revokes the old one (`revoked=True`) and issues a new one. Provides refresh token rotation as a security measure against token theft. Old token cannot be reused after one rotation.

### [AUTH] JWT access token 15 min, refresh token 7 days
15 min access token limits damage window if token is intercepted. 7 day refresh provides good UX (users stay logged in). Both configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` and `JWT_REFRESH_TOKEN_EXPIRE_DAYS` in settings.

### [AUTH] User creates Organization on register
Each user gets an Organization with `role=owner` on registration. Organization name defaults to `{full_name}'s workspace` if not provided. Enforces multi-tenancy model from day one.

### [AUTH] SQLite + aiosqlite for tests
Tests use SQLite in-memory DB via `aiosqlite`. PostgreSQL-specific features (e.g., native UUID type) avoided in models by using `Uuid(as_uuid=False)` (stored as VARCHAR(36) on SQLite). TimestampMixin uses Python-side `default=lambda` in addition to `server_default=func.now()` so tests don't require DB round-trips.

### [AUTH] UUIDs stored as String(36) / Uuid(as_uuid=False)
`Uuid(as_uuid=False)` used instead of native PostgreSQL UUID type. SQLAlchemy renders as VARCHAR(36) on SQLite and UUID on PostgreSQL. Avoids test compatibility issues without sacrificing production correctness.

### [DEPS] PyJWT 2.9.0 downgraded from 2.13.0
Pinned to 2.9.0 per requirements.txt spec. Existing 2.13.0 was uninstalled. No breaking API changes for our usage (encode/decode). Pin exists for reproducibility.

---

## 2026-06-25 (Sprint 3)

### [BILLING] Stripe configured detection via key prefix, not env var name
`is_stripe_configured()` checks if `STRIPE_SECRET_KEY` starts with `sk_test_` or `sk_live_`. Placeholder value `"stripe_secret_key_placeholder"` fails this check, returning 503. Avoids complex env var presence checking.

### [BILLING] Webhook configured check via whsec_ prefix
`is_stripe_webhook_configured()` checks if `STRIPE_WEBHOOK_SECRET` starts with `whsec_`. Default placeholder `"webhook_secret_placeholder"` fails, returning 503 for all webhook calls. Real Stripe secrets always start with `whsec_`.

### [BILLING] UsageCounter in database (not Redis)
Sprint 3 spec requires a UsageCounter DB model with `period_key=YYYY-MM`. Redis-based counters remain in design docs for Sprint 18 as a higher-performance alternative. DB approach is simpler and sufficient for MVP.

### [BILLING] Webhook idempotency via unique stripe_event_id + early return
BillingEvent table has UNIQUE constraint on `stripe_event_id`. `process_webhook_event` checks for existing record before processing. Duplicate events are silently ignored without error. Safe for Stripe's at-least-once delivery guarantee.

### [BILLING] Free plan subscription row created on first GET /billing/subscription
Rather than creating subscription on register, we create it lazily on first billing endpoint call. Reduces SQL writes at registration. Organization always gets free plan if no subscription exists.

### [BILLING] Sync Stripe API calls in async FastAPI handlers
Stripe Python SDK is synchronous. Calls run in the event loop thread directly. Acceptable for MVP — latency is typically <300ms. `anyio.to_thread.run_sync` wrappers deferred to Sprint 18 hardening to keep Sprint 3 testable without extra mocking complexity.

### [BILLING] Mocking pydantic-settings in tests via module-level ref patch
pydantic-settings instances are frozen; attribute patching fails. Solution: `patch("app.api.v1.billing.settings", MagicMock(...))` replaces the full settings object in the billing module scope. Used only for the `test_webhook_400_invalid_signature` test that needs a configured-but-invalid-sig scenario.

### [BILLING] Stripe price ID validity check includes "placeholder" string detection
`get_stripe_price_id(plan)` returns None if the configured price ID contains "placeholder". This ensures the endpoint returns 503 without making a live Stripe call, even if the key format passes the prefix check.

### [BILLING] basic_yearly/pro_yearly share limits with basic_monthly/pro_monthly
Yearly plans have identical feature limits; only pricing differs (lower monthly rate with annual commitment). Yearly variants reference the same dict in PLAN_LIMITS to avoid duplication.

---

## 2026-06-25 (Sprint 4)

### [ETSY] EtsyOAuthState consumed via timestamp, not deleted
`consumed_at` timestamp set instead of deleting the row on callback. Preserves audit trail — can detect replay attacks and analyze OAuth flow metrics. State is checked for `consumed_at is None` before processing.

### [ETSY] Callback endpoint always redirects, never raises HTTPException
`GET /etsy/callback` catches all errors and redirects to `{FRONTEND_URL}/shops?error=etsy_connect_failed`. Never raises HTTPException. Rationale: OAuth callbacks are browser redirects — a JSON error response breaks the UX flow and may expose internal errors.

### [ETSY] Dev Fernet fallback key is deterministic, documented
`base64.urlsafe_b64encode(b"dev_encryption_key_placeholder!!")` = `ZGV2X2VuY3J5cHRpb25fa2V5X3BsYWNlaG9sZGVyISE=`. Used when ENCRYPTION_KEY is missing/placeholder. Warning documented in encryption.py — production must set a real key.

### [ETSY] is_etsy_configured() checks for "placeholder" in ETSY_CLIENT_ID
Mirrors is_stripe_configured() pattern. `GET /etsy/authorize` returns 503 `"Etsy is not configured."` if ETSY_CLIENT_ID is placeholder. Prevents OAuth flow from starting with invalid credentials.

---

## 2026-06-25 (Sprint 7)

### [BULK-EDIT] Session-level changes, not per-listing changes
One `BulkEditChange` row per rule (field + operation) scoped to the session, not duplicated per listing. At preview-generation time the service fans out: one change is applied to each selected listing in memory. Rationale: seller edits the same rule across all selected listings; duplicating the change row N times would make edits (e.g., correcting a typo in the operation value) require updating N rows. Session-level model is simpler and correct.

### [BULK-EDIT] apply_change_to_listing_data is a pure function (copy.deepcopy)
`apply_change_to_listing_data(before_data, change)` returns a new dict and never mutates `before_data`. Enables safe sequential application of multiple changes: call the function N times, threading the output of each as input to the next. Rationale: mutation would make debugging and testing brittle; pure functions compose cleanly.

### [BULK-EDIT] apply endpoint is a 409 stub in Sprint 7
`POST /bulk-edit/sessions/{id}/apply` raises `HTTPException(409, "Etsy write operations start in Sprint 8. This endpoint is intentionally disabled.")`. Returns 409 (Conflict) rather than 503 (Service Unavailable) because the resource exists and the action is understood — it is deliberately blocked pending Sprint 8, not a configuration failure. No `listings` rows are modified.

### [BULK-EDIT] UniqueConstraint on (session, listing) for preview items
`BulkEditPreviewItem` has `UniqueConstraint("bulk_edit_session_id", "listing_id")`. `generate_bulk_edit_preview` checks for an existing preview item per listing and updates it in-place (upsert). Rationale: sellers can regenerate the preview after editing changes without accumulating duplicate rows or hitting DB integrity errors.

### [BULK-EDIT] Status machine: draft → preview_ready → canceled (applied deferred)
Sprint 7 status values: `draft`, `preview_ready`, `canceled`. `applied` status is intentionally absent — the apply flow (including snapshot, Etsy write, audit log) is Sprint 8 work. Keeping `applied` out of the Sprint 7 schema avoids having a status value with no corresponding code path.

### [BULK-EDIT] Field type registry drives operation validation
`TEXT_FIELDS`, `BOOL_FIELDS`, `NUMBER_FIELDS`, `ARRAY_FIELDS` sets in the service determine which operations are accepted per field. `add_bulk_edit_change` rejects unknown fields (400) and incompatible operation+field combinations (400) before persisting. Rationale: catching errors at change-creation time gives better UX than silently creating noop changes.

### [FRONTEND] localStorage for selected listing IDs passthrough
`/listings` page writes `localStorage.setItem("bulk_edit_selected_listing_ids", JSON.stringify([...selected]))` and navigates to `/bulk-edit`. `/bulk-edit` reads and clears this key on mount. Avoids URL length limits for large selections and avoids a server-side session concept for a single-page navigation. Can be replaced with a real session store if cross-tab or cross-device sync is needed.

---

## 2026-06-25 (Sprint 6)

### [BACKEND] Batch thumbnail fetch: 2 queries per page, not N+1
`GET /listings` needs thumbnail_url (first image) for each listing on the page. Fetching images per-listing = N+1 queries. Solution: collect listing IDs from page result, run one `SELECT listing_id, url_570xN FROM listing_images WHERE listing_id IN (...)` ordered by rank ASC, build dict keyed by listing_id, inject via `model_copy(update={"thumbnail_url": ...})`. Total: 3 queries per page request (count, listings, thumbnails).

### [BACKEND] sort_by whitelist VALID_SORT_COLS + 400 on invalid
`getattr(Listing, sort_by)` would expose any SQLAlchemy column attribute including internal ones. Fixed with explicit `VALID_SORT_COLS` set. Returns 400 with readable error listing allowed values. Same pattern for sort_dir (asc/desc only).

### [BACKEND] Cross-DB JSON tag search: cast to String + ILIKE
`Listing.tags` is a JSON column. To search for a tag substring across SQLite and PostgreSQL without native JSONB operators: `cast(Listing.tags, String).ilike(f"%{tag}%")`. Works because SQLite stores JSON as text and PostgreSQL's cast to TEXT gives the JSON representation. Not semantically correct (could match substrings in keys), acceptable for MVP tag filter.

### [FRONTEND] Column visibility and saved views in localStorage (not DB)
At MVP scale, column preferences and saved filter views are user-device-specific and low-stakes. localStorage avoids a DB migration and API endpoint. Can migrate to DB-backed user preferences in Sprint 17 (admin/settings sprint) if multi-device sync becomes a requirement.

---

## 2026-06-25 (Sprint 5)

### [SYNC] Inline sync for MVP, Celery deferred to Sprint 8
POST /shops/{id}/sync runs sync_shop_listings() inline in the HTTP request. Acceptable for MVP because sync is read-only and typically <10 seconds for free/basic plan listing counts. Comment added for future Celery task dispatch.

### [SYNC] max_listings gate enforced by results[:remaining] slice
Service requests `min(PAGE_LIMIT, remaining)` items per page from Etsy. Additionally, results are sliced to `remaining` before processing to guard against Etsy returning more than requested. Ensures plan limit is always honored even with mock data.

### [SYNC] raw_data JSON column on all listing models
Every Listing/ListingImage/ListingVideo/ListingVariation stores the full API response JSON. Defensive design: Etsy API response fields change without notice. raw_data preserves full fidelity for future field additions without requiring migrations.

### [SYNC] Video sync is best-effort, returns empty on 404/405
Not all Etsy shops have video listings. fetch_listing_videos() returns empty list on 404 or 405 instead of failing sync. Documented as known limitation in HANDOFF.md.

### [SYNC] Token expiry check logs warning but continues
If EtsyToken.expires_at is within TOKEN_REFRESH_BUFFER_SECONDS (300s), logs a warning but uses the token anyway. Etsy access tokens often remain valid briefly after expiry. Full auto-refresh deferred to Sprint 8. Users are shown a reconnect recommendation in that edge case.

### [TEST] Shared-memory SQLite URI for cross-fixture data visibility
Changed TEST_DB_URL from `sqlite+aiosqlite:///:memory:` to `sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true`. Named shared-memory DB required when both `client` (with overridden get_db) and `db_session` fixtures are used in the same test — they now share the same SQLite in-memory database across connections.

---

## Sprint 8 Decisions

### [MODEL] AuditLog.metadata renamed to extra_data
SQLAlchemy DeclarativeBase reserves the class attribute `metadata` (maps to `MetaData`). Using `metadata` as a column attribute name raises `InvalidRequestError: Attribute name 'metadata' is reserved`. Solution: use `extra_data` as the Python attribute with `mapped_column(JSON, name="metadata")` so the DB column is still named `metadata` for SQL compatibility.

### [APPLY] Price and quantity writes excluded from Sprint 8
Etsy PATCH /v3/application/listings/{id} does NOT support price or quantity fields. These require PATCH /v3/application/shops/{shop_id}/listings/{listing_id}/inventory (a separate endpoint). Deferred to Sprint 9. `build_etsy_patch_payload()` explicitly excludes `price_amount` and `quantity` from all payloads.

### [APPLY] Local Listing row updated only after Etsy write succeeds
Safety invariant: local DB must always reflect what Etsy actually has. If Etsy PATCH fails, local row is NOT updated. `apply_bulk_edit_session()` sets Listing attrs only inside the success branch after `patch_etsy_listing()` returns without raising `EtsyWriteError`.

### [TEST] Patch settings.is_etsy_configured via module-level mock
Pydantic v2 Settings objects block `__setattr__` on non-field names. Cannot use `patch("app.core.config.settings.is_etsy_configured")`. Correct approach: `patch("app.services.bulk_edit_apply.settings", MagicMock())` which replaces the module-level name reference without touching the singleton. `MagicMock().is_etsy_configured.return_value = True` satisfies the check.

## Sprint 9 Decisions

### [REVERT] RevertResult.backup_snapshot_id is nullable (SET NULL)
Skip cases (listing not found in DB, no snapshot ID on apply result, snapshot row deleted, no valid access token, empty patch payload) must produce a `RevertResult` row for full audit trail but cannot have a valid FK value. Changed from `Mapped[str]` / RESTRICT to `Mapped[str | None]` / SET NULL. Alembic migration 0007 updated to match.

### [REVERT] Price/quantity revert deferred to Sprint 10
Same reason as apply exclusion: Etsy PATCH /v3/application/listings/{id} does not accept price/quantity. Revert of these fields requires PATCH /v3/application/shops/{shop_id}/listings/{listing_id}/inventory. `build_etsy_revert_payload()` inherits the exclusion from `build_etsy_patch_payload()`.

### [REVERT] Only "success" apply results are iterated during revert
Failed and skipped apply results should not be reverted — they represent listings that were never written to Etsy, so there is nothing to undo. Iterating only `status == "success"` apply results ensures revert only touches listings that were actually modified.

### [REVERT] 409 on duplicate revert (not 400)
A second revert request on an already-reverted apply job is a conflict, not a bad request — the apply job itself is valid, but a concurrent/completed revert job already exists. 409 (Conflict) is semantically correct. The check queries for `status IN ("completed", "completed_with_errors", "running")` to also block concurrent reverts in progress.

---

## Sprint 10 Decisions

### [INVENTORY] Change detection via value comparison, not diff key presence
`build_etsy_inventory_payload(listing, after_data)` uses `new_price != listing.price_amount` to detect change, not `"price_amount" in diff`. Reason: `after_data` always contains `price_amount` (from `build_before_data`), so presence check would always trigger an inventory write. Value comparison works correctly for both apply (listing has old value, after_data has new) and revert (listing has applied value, snapshot has original).

### [INVENTORY] Partial write caveat: accepted, documented, not recovered
If listing PATCH succeeds but inventory PUT fails: Etsy has new text but not new price. This is a partial external write. Decision: do NOT update local DB for that listing (treating failure as atomic). Next listing sync will resolve the text/price mismatch. Alternative considered: revert the text PATCH on inventory failure (double complexity, another potential failure). Accepted caveat documented in module docstring and HANDOFF.md.

### [INVENTORY] Backward compat: flat vs structured request_payload
`request_payload` on `BulkEditApplyResult` uses flat format `{"title": "New"}` for text-only changes (no inventory). Uses structured format `{"listing_patch": {"title": "New"}, "inventory_patch": {...}}` only when inventory is involved. Reason: existing Sprint 8 tests mock title-only changes and assert on the flat payload. Changing to structured unconditionally would break those tests. The conditional keeps both cases working.

### [INVENTORY] currency_code from listing, not after_data/snapshot
`listing.currency_code` is always used for the inventory payload. It's not in `after_data` or `snapshot_data` (not captured by `build_before_data`). Currency shouldn't change via bulk edit — it's not a patchable field. Reading from the listing object is correct and avoids adding currency to the snapshot schema.

### [INVENTORY] Variation listings: inventory skipped, text fields still applied
When `listing.has_variations=True`, `build_etsy_inventory_payload` returns None. The variation skip reason is recorded in `request_payload["inventory_skip_reason"]`. Text field changes (title, description, etc.) proceed normally through the standard PATCH endpoint. Full variation inventory support deferred to Sprint 12 (Variation Editor).

---

## Sprint 11 Decisions

### [MEDIA] Image upload: URL-download-then-multipart, not direct URL pass-through
Etsy image upload API requires multipart/form-data with binary image bytes. There is no URL-based "upload from link" parameter. Decision: download image bytes from the provided URL via httpx, then POST multipart to Etsy. This means the backend temporarily holds the image bytes in memory (capped at 20MB). Alternative: require users to upload images to S3 first (deferred to Sprint 13+).

### [MEDIA] Video upload: stub only (Sprint 11)
Etsy video upload requires direct server-side file upload. URL-based upload is not supported. S3-based upload infrastructure not ready in Sprint 11. Decision: raise EtsyMediaWriteError(not_implemented=True, status_code=501) from the stub function. Result rows record status="skipped" with a clear reason. No silent failures.

### [MEDIA] Image reorder: stub only (Sprint 11)
Etsy has no atomic image reorder endpoint. Reorder would require delete-all + re-upload in the desired order, which is destructive and error-prone. Decision: stub operation, skip with reason. Deferred to a future sprint when we can safely orchestrate the delete-upload sequence.

### [MEDIA] Separate BulkEditMediaJob table (not reusing BulkEditApplyJob)
Media operations are structurally different from text/inventory operations: they operate on files, not listing fields, and produce before/after media states (not field diffs). A separate job/result table keeps the schemas clean and avoids widening existing tables with nullable media-specific columns.

### [MEDIA] 404 on Etsy image delete = success
If DELETE /images/{image_id} returns 404, the image is already deleted on Etsy. Decision: treat as success (return without error). Rationale: the desired state (image removed) is already achieved. Alternative: raise error (rejected — would cause false failures on retry).

### [MEDIA] Backup snapshot: images only (not videos) in Sprint 11
`ListingMediaBackupSnapshot.videos_snapshot` is stored as NULL in Sprint 11 because video fetch is best-effort and video write operations are stubs. Snapshot schema supports videos for future sprints.

---

## Sprint 21 Decisions

### [RATE_LIMIT] IP-only key for login/register (no email extraction)
FastAPI body is consumed by Pydantic model validation before the rate limit dependency runs. Attempting `await request.json()` in the dependency raises an error (body already consumed). Decision: login and register rate limit keys use IP only: `rl:login:{ip}`. This prevents per-email tracking but is still effective for brute-force protection at the IP level. Comment in code explains why.

### [RATE_LIMIT] Memory fallback on Redis unavailability
If Redis is unavailable (connection error, timeout, or not configured), rate limiter falls back to in-memory dict automatically. Logged as warning. No HTTP error surfaced to users. This ensures rate limiting never takes the app down — a Redis outage degrades to less robust rate limiting, not a service failure.

### [RATE_LIMIT] RATE_LIMIT_ENABLED defaults False
Tests and local dev do not need rate limiting. Defaulting to False avoids flaky test failures from legitimate test login loops. Production must explicitly set RATE_LIMIT_ENABLED=true.

### [SENTRY] No-op when DSN absent or placeholder
_init_sentry() returns early if DSN is empty, contains "placeholder", or starts with "YOUR_". This ensures local dev and CI never accidentally try to connect to Sentry. sentry-sdk is installed (it's a dep) but never initialized.

### [SENTRY] Secrets scrubbed before Sentry send
_scrub_sentry_event() recursively redacts any dict key in _SENSITIVE set (14 keys: password, password_hash, access_token, refresh_token, etsy_access_token, etsy_refresh_token, stripe_secret_key, openai_api_key, anthropic_api_key, secret_key, authorization, cookie, sentry_dsn, redis_url). Applied via before_send hook — Sentry never receives raw values.

### [CSP] unsafe-eval removed in production only
Next.js App Router injects multiple inline scripts per build. These require unsafe-inline (SHA256 approach only covers one specific script). unsafe-eval however is not needed in production — only Next.js dev server hot-reload uses it. Decision: keep unsafe-inline everywhere, remove unsafe-eval in production only (NODE_ENV=production).

### [MONITORING] system-health fields: never expose URLs
_check_redis_health() accepts the URL internally and returns only "ok" | "not_configured" | "error". The response schema has no field for the Redis URL. Test test_system_health_no_redis_url_exposed verifies "redis://" is not in the response body. Same approach for Sentry DSN — sentry_configured is bool only.

### [CELERY] Deferred — inline jobs sufficient for Sprint 21
No Celery worker container added. Scheduled jobs run inline in HTTP thread. Volume doesn't warrant a separate worker process yet. WORKERS.md documents the future Celery architecture (worker.py template, docker-compose service stub, beat scheduler). worker_status field returns "not_configured".
