# CHANGELOG_AI.md — AI Session Log

Append one entry per session. Format: `## [DATE] Sprint N — Summary`

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
