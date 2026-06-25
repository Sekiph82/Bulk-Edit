# DECISIONS.md — Architecture and Product Decisions

Format: `[DATE] [CATEGORY] Decision — Rationale`

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
