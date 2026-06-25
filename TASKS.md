# TASKS.md — Phased Roadmap

Legend: `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

---

## Sprint 0: Project Memory and Operating System

**Status:** `[x] COMPLETE`

- [x] Create CLAUDE.md
- [x] Create TASKS.md
- [x] Create SKILLS.md
- [x] Create PROJECT_STATUS.md
- [x] Create HANDOFF.md
- [x] Create DECISIONS.md
- [x] Create ARCHITECTURE.md
- [x] Create LIMIT_PROTOCOL.md
- [x] Create SECURITY.md
- [x] Create CHANGELOG_AI.md
- [x] Create ROADMAP.md
- [x] Create README.md
- [x] Create .env.example
- [x] Create .claude/commands/continue.md
- [x] Create .claude/commands/checkpoint.md
- [x] Create .claude/commands/finish-session.md
- [x] Create .claude/commands/plan-next.md
- [x] Create .claude/commands/skill-select.md
- [x] Create .claude/commands/audit.md
- [x] Create docs/product/PRODUCT_REQUIREMENTS.md
- [x] Create docs/product/FEATURES.md
- [x] Create docs/product/PRICING.md
- [x] Create docs/product/USER_FLOWS.md
- [x] Create docs/technical/DATABASE_SCHEMA.md
- [x] Create docs/technical/API_SPEC.md
- [x] Create docs/technical/ETSY_INTEGRATION.md
- [x] Create docs/technical/STRIPE_BILLING.md
- [x] Create docs/technical/BULK_ENGINE.md
- [x] Create docs/technical/AI_TOOLS.md
- [x] Create docs/technical/MEDIA_LIBRARY.md
- [x] Create docs/technical/SECURITY_MODEL.md
- [x] Create docs/operations/DEPLOYMENT.md
- [x] Create docs/operations/TESTING.md
- [x] Create docs/operations/RELEASE_CHECKLIST.md
- [x] Commit and push to GitHub

---

## DevOps Utilities

**Status:** `[x] COMPLETE`

- [x] Create `start-dev.bat` — Windows double-click startup (Docker check, .env copy, down + up --build, logs, pause)
- [x] Create `start-dev-clean.bat` — Windows full reset with volume deletion (confirmation required)
- [x] Create `setup-and-start.bat` — Windows one-click friend/reviewer setup (installs Git + Docker via winget, clones repo, builds, opens browser)
- [x] Create `setup-and-start-clean.bat` — Same as above with DB volume reset (YES confirmation gate)
- [x] Update README.md Windows Quick Start and One-Click Friend Setup sections
- [x] Update docs/operations/DEPLOYMENT.md Windows startup and one-click sections
- [x] Commit and push

---

## Sprint 1: Monorepo Skeleton

**Status:** `[x] COMPLETE`

- [x] Initialize monorepo structure: `apps/frontend`, `apps/backend`, `packages/`
- [x] Scaffold Next.js 14 frontend (TypeScript, App Router, Tailwind CSS)
- [x] Scaffold FastAPI backend (Python 3.12, uvicorn)
- [x] Configure PostgreSQL with Docker Compose (host port 55432)
- [x] Configure Redis with Docker Compose (host port 56379)
- [x] Set up Alembic migrations
- [x] Set up SQLAlchemy base models
- [x] Add health check endpoints: `GET /api/v1/health`, `GET /api/v1/health/db`, `GET /api/v1/health/redis`
- [x] Add root `docker-compose.yml` with custom host ports (3100, 8100, 55432, 56379)
- [x] Add root `Makefile` with common commands
- [x] Add root `.gitignore`
- [x] Align `.env.example` with all services and custom ports
- [x] Update README with local setup instructions and correct ports
- [x] Add landing page `/` and dashboard placeholder `/dashboard`
- [x] Fix BACKEND_CORS_ORIGINS to accept plain string (pydantic-settings v2 compatibility)
- [x] CORS origins validator: handles plain string, comma-separated, JSON array
- [x] Run pytest — 4/4 tests pass, zero warnings
- [x] Commit and push

---

## Sprint 2: Auth + Organization

**Status:** `[x] COMPLETE`

- [x] Design User, Organization, OrganizationMember models
- [x] Implement user registration endpoint (POST /api/v1/auth/register)
- [x] Implement user login endpoint (POST /api/v1/auth/login — JWT access + refresh)
- [x] Implement token refresh endpoint (POST /api/v1/auth/refresh — rotation)
- [x] Implement logout (POST /api/v1/auth/logout — revoke refresh token in DB)
- [x] Implement GET /api/v1/auth/me — returns user + memberships
- [x] Build frontend auth pages: /register, /login (Tailwind forms)
- [x] Update dashboard with auth state + logout button
- [x] Add auth middleware to FastAPI (HTTPBearer + get_current_user dep)
- [x] RefreshToken model with SHA-256 token_hash
- [x] SQLite + aiosqlite test fixtures (override get_db per test)
- [x] Write auth tests — 14/14 PASSED
- [x] Commit and push

---

## Sprint 3: Stripe Billing and Feature Gates

**Status:** `[x] COMPLETE`

- [x] Design Subscription, BillingEvent, UsageCounter models
- [x] Alembic migration 0002 for all three tables
- [x] Plan limits config (app/core/plans.py) — free, basic_monthly, pro_monthly, basic_yearly, pro_yearly
- [x] GET /api/v1/billing/plans — returns all plan configs
- [x] GET /api/v1/billing/subscription — creates free sub if none exists
- [x] POST /api/v1/billing/checkout — Stripe checkout session (503 when not configured)
- [x] POST /api/v1/billing/portal — Stripe customer portal (503 when not configured)
- [x] POST /api/v1/billing/webhook — Stripe webhook with signature verification
- [x] GET /api/v1/billing/usage — usage counters + plan limits
- [x] Feature gate service: can_use_feature, check_usage_limit, increment_usage
- [x] get_current_org_id FastAPI dependency
- [x] Webhook: checkout.session.completed, subscription.updated/deleted, invoice.payment_failed
- [x] Webhook idempotency on duplicate stripe_event_id
- [x] Frontend /pricing page — 5-plan grid with limits and upgrade buttons
- [x] Frontend /billing page — current plan, portal button, success/canceled banners
- [x] Dashboard updated with Pricing/Billing links
- [x] 26 billing tests — 26/26 PASS; full suite 44/44 PASS
- [x] Commit and push

---

## Sprint 4: Etsy OAuth

**Status:** `[x] COMPLETE`

- [x] Add ENCRYPTION_KEY, ETSY_CLIENT_ID, ETSY_REDIRECT_URI, ETSY_SCOPES to config.py + is_etsy_configured()
- [x] Create app/core/encryption.py — Fernet encrypt_token/decrypt_token with dev fallback key
- [x] Create EtsyShop model (organization_id, etsy_shop_id UNIQUE, shop_name, is_connected, last_synced_at)
- [x] Create EtsyToken model (etsy_shop_id FK UNIQUE, access_token_enc, refresh_token_enc, expires_at, scopes)
- [x] Create EtsyOAuthState model (state UNIQUE, code_verifier, organization_id, user_id, expires_at, consumed_at)
- [x] Update app/models/__init__.py — import 3 new models
- [x] Alembic migration 0003 — etsy_shops, etsy_tokens, etsy_oauth_states tables
- [x] Create app/schemas/etsy.py — EtsyAuthorizeResponse, EtsyShopResponse, EtsyShopsResponse, EtsyDisconnectResponse
- [x] Create app/services/etsy.py — PKCE helpers, create_authorization_session, handle_oauth_callback, exchange_code_for_token, fetch_etsy_shop, list_connected_shops, disconnect_shop, refresh_etsy_token
- [x] Create app/api/v1/etsy.py — 4 endpoints: GET /etsy/authorize, GET /etsy/callback, GET /etsy/shops, DELETE /etsy/shops/{id}
- [x] Update app/api/v1/router.py — include etsy_router
- [x] Create tests/test_etsy.py — 15 tests (encryption, PKCE, authorize, callback, shops, disconnect)
- [x] Update conftest.py — shared-memory SQLite URI for cross-fixture data visibility
- [x] Create frontend app/shops/page.tsx — shop list, connect button, disconnect, OAuth redirect
- [x] Update frontend app/dashboard/page.tsx — add Etsy Shops link
- [x] 15/15 etsy tests PASS; full suite 59/59 PASS
- [x] Commit and push

---

## Sprint 5: Listing Sync

**Status:** `[x] COMPLETE`

- [x] Create Listing model (org-scoped, etsy_shop_id FK, etsy_listing_id + full field set)
- [x] Create ListingImage model (listing_id FK, etsy_image_id, URLs, rank)
- [x] Create ListingVideo model (listing_id FK, etsy_video_id, video_url, thumbnail_url)
- [x] Create ListingVariation model (listing_id FK, etsy_product_id, property/value, price, qty)
- [x] Create SyncJob model (org-scoped, etsy_shop_id FK, status, progress counters)
- [x] Update app/models/__init__.py — all 5 new models
- [x] Alembic migration 0004 — listings, listing_images, listing_videos, listing_variations, sync_jobs
- [x] Create app/schemas/listings.py — SyncJobResponse, ListingListItemResponse, ListingDetailResponse, ListingPageResponse, ListingImageResponse, ListingVideoResponse, ListingVariationResponse
- [x] Create app/services/etsy_sync.py — get_valid_etsy_access_token, fetch_shop_listings, fetch_listing_images, fetch_listing_videos, fetch_listing_inventory, upsert_*, sync_shop_listings
- [x] Create app/api/v1/shops.py — POST /shops/{shop_id}/sync, GET /shops/{shop_id}/sync-status
- [x] Create app/api/v1/listings.py — GET /listings, GET /listings/{id}, /images, /videos, /variations
- [x] Update app/api/v1/router.py — include shops_router and listings_router
- [x] max_listings plan gate enforced in sync_shop_listings
- [x] Create tests/test_listings.py — 16 tests
- [x] Create frontend app/listings/page.tsx — shop selector, sync button, filtered table, pagination
- [x] Update frontend app/dashboard/page.tsx — Listings link added
- [x] 16/16 listing tests PASS; full suite 75/75 PASS
- [x] Commit and push

---

## Sprint 6: Listings Grid

**Status:** `[x] COMPLETE`

- [x] Add 10 new backend filters: tag, has_variations, price_min/max, quantity_min/max, section_id, taxonomy_id, is_personalizable, is_customizable
- [x] VALID_SORT_COLS whitelist + 400 on invalid sort_by / sort_dir
- [x] Batch thumbnail fetch (2 queries per page, no N+1)
- [x] thumbnail_url, sku, etsy_updated_at added to ListingListItemResponse
- [x] filters metadata field added to ListingPageResponse
- [x] 18 new filter/sort tests — full suite 93/93 PASS
- [x] Create apps/frontend/lib/api.ts — typed API client with all helpers
- [x] Rewrite apps/frontend/app/listings/page.tsx — state tabs, advanced filter panel, column visibility (localStorage), multi-select checkboxes, sort controls, thumbnail preview, detail sidebar, saved views (localStorage), summary cards
- [x] Commit and push

---

## Sprint 7: Bulk Edit Preview Engine

**Status:** `[x] COMPLETE`

- [x] BulkEditSession model (organization_id, created_by_user_id, name, status, selected_listing_ids JSON, selected_count, change_count, preview_generated_at, applied_at, canceled_at)
- [x] BulkEditChange model (session FK, listing FK nullable, field_name, operation, old/new/operation_value JSON, validation_status, validation_message)
- [x] BulkEditPreviewItem model (session FK, listing FK, listing_title, before_data/after_data/diff JSON, validation_status/messages; UNIQUE session+listing)
- [x] Alembic migration 0005 — bulk_edit_sessions, bulk_edit_changes, bulk_edit_preview_items
- [x] app/schemas/bulk_edit.py — 8 schemas
- [x] app/services/bulk_edit.py — apply_change_to_listing_data, validate_listing_data, compute_diff, create/list/get/cancel session, add/remove change, generate preview, get preview page, apply stub (409)
- [x] app/api/v1/bulk_edit.py — 9 endpoints under /api/v1/bulk-edit
- [x] 38 new tests (21 unit + 17 API) — full suite 131/131 PASS
- [x] apps/frontend/lib/api.ts — bulk edit types + 9 API helpers added
- [x] apps/frontend/app/bulk-edit/page.tsx — 3-phase UX: listing selector, change editor, diff preview table
- [x] apps/frontend/app/listings/page.tsx — Bulk Edit button enabled: saves IDs to localStorage, navigates to /bulk-edit
- [x] Apply endpoint returns 409 + "Etsy write operations start in Sprint 8" — no Listing rows modified
- [x] Commit and push

---

## Sprint 8: Etsy Write + Backup

**Status:** `[x] COMPLETE`

- [x] ListingBackupSnapshot model (org-scoped, session FK, listing FK, snapshot_data JSON, snapshot_type)
- [x] BulkEditApplyJob model (status machine: pending/running/completed/completed_with_errors/failed, counters)
- [x] BulkEditApplyResult model (per-listing result: status, request/response payload, backup_snapshot_id FK)
- [x] AuditLog model (org-scoped, event_type, entity_type/id, extra_data JSON)
- [x] Alembic migration 0006 — all 4 new tables
- [x] app/schemas/bulk_edit_apply.py — ApplyJobOut, ApplyResultOut, BackupSnapshotOut, ApplyJobWithResultsOut
- [x] app/services/etsy_write.py — build_etsy_patch_payload, patch_etsy_listing (PATCH /v3/application/listings/{id})
- [x] app/services/bulk_edit_apply.py — apply_bulk_edit_session (safety gates + orchestration), get/list apply jobs, get results, list backups
- [x] Updated app/api/v1/bulk_edit.py — real POST apply (202), 4 new endpoints (apply-jobs, apply-job detail, backups)
- [x] 22 new tests in test_bulk_edit_apply.py — 153/153 PASS (was 131)
- [x] apps/frontend/lib/api.ts — 4 new types + 4 new helpers (applyBulkEditSession, listApplyJobs, getApplyJobDetail, listBackupSnapshots)
- [x] apps/frontend/app/bulk-edit/page.tsx — confirmation modal, apply result display, real apply call
- [x] Safety: preview_ready gate, no-invalid-items gate, Etsy configured gate, plan limit gate, pre-write backup, local update only after Etsy success, audit log
- [x] Commit and push

---

## Sprint 9: Magic Revert

**Status:** `[x] COMPLETE`

- [x] RevertJob model (org-scoped, apply_job_id FK, session FK, status machine, counters)
- [x] RevertResult model (per-listing: status, backup_snapshot_id FK nullable, request/response payload, error)
- [x] Alembic migration 0007 — revert_jobs + revert_results tables
- [x] app/schemas/bulk_edit_revert.py — RevertJobOut, RevertResultOut, RevertJobWithResultsOut, RevertResultPageOut
- [x] app/services/bulk_edit_revert.py — full revert orchestration with safety gates, build_etsy_revert_payload, update_local_listing_from_snapshot, validate_apply_job_revertable, get/list revert jobs + results
- [x] app/api/v1/bulk_edit.py — 4 new endpoints: POST revert/202, GET revert-jobs list, GET revert-job detail, GET paginated results
- [x] 28 new tests in test_bulk_edit_revert.py — 181/181 PASS (was 153)
- [x] apps/frontend/lib/api.ts — 4 new types (RevertJob, RevertResult, RevertJobWithResults, RevertResultPage) + 4 new helpers (revertApplyJob, listRevertJobs, getRevertJob, getRevertResults)
- [x] apps/frontend/app/bulk-edit/page.tsx — Magic Revert button (visible after apply with completed/completed_with_errors status), REVERT text confirmation modal, revert result card
- [x] Safety: Etsy configured gate, apply job must be completed, no double-revert (409), only success apply results reverted, local Listing updated ONLY after Etsy write, backup snapshots never deleted, audit logs on start + finish
- [x] Commit and push

---

## Sprint 10: Etsy Inventory Writes (Price / Quantity)

**Status:** `[x] COMPLETE`

- [x] `build_etsy_inventory_payload(listing, after_data)` in `etsy_write.py` — change detection vs current listing values, variation skip, currency_code guard
- [x] `patch_etsy_listing_inventory(access_token, shop_etsy_id, listing_etsy_id, payload)` in `etsy_write.py` — PUT /v3/application/shops/{s}/listings/{l}/inventory
- [x] `bulk_edit_apply.py` — dual-write: listing PATCH then inventory PUT; structured request/response payloads; local price/qty update gated on inventory write success; variation skip with reason
- [x] `bulk_edit_revert.py` — inventory revert from snapshot_data; same dual-write pattern; local price/qty restore gated on inventory revert success
- [x] `tests/test_bulk_edit_inventory.py` — 19 tests (9 unit + 10 integration); 200/200 PASS
- [x] Frontend: removed "price/qty not reverted" warning from revert modal; added variation listing skip notice in preview
- [x] Commit and push

---

## Sprint 11: Photo / Video Bulk Editor

**Status:** `[x] COMPLETE`

- [x] BulkEditMediaJob model (org-scoped, operation_type, operation_payload JSON, listing_ids JSON, status machine, counters)
- [x] BulkEditMediaResult model (per-listing: status, before_media/after_media JSON, request/response payload, error)
- [x] ListingMediaBackupSnapshot model (org-scoped, images_snapshot/videos_snapshot/raw_snapshot JSON, etsy_shop_id FK)
- [x] Alembic migration 0008 — bulk_edit_media_jobs, bulk_edit_media_results, listing_media_backup_snapshots
- [x] app/services/etsy_media_write.py — fetch/upload/delete Etsy images (multipart URL-download pattern); video stubs raise 501
- [x] app/schemas/bulk_edit_media.py — MediaJobCreate (validated), MediaJobOut, MediaResultOut, MediaResultPageOut, MediaBackupSnapshotOut, MediaJobWithResultsOut
- [x] app/services/bulk_edit_media.py — create_media_job, apply_media_job (add/replace/delete_image implemented; video/reorder stubs), backup snapshot before every write, audit logs, partial failure support
- [x] app/api/v1/bulk_edit_media.py — 6 endpoints: POST jobs, GET jobs, GET jobs/{id}, POST jobs/{id}/apply, GET jobs/{id}/results, GET jobs/{id}/backups
- [x] app/models/__init__.py — 3 new model imports
- [x] app/api/v1/router.py — bulk_edit_media_router included
- [x] tests/test_bulk_edit_media.py — 25 tests; 225/225 full suite PASS
- [x] apps/frontend/lib/api.ts — 4 new types (MediaJob, MediaResult, MediaResultPage, MediaBackupSnapshot) + 6 helpers
- [x] apps/frontend/app/media/page.tsx — listing selector, operation picker, image URL/rank/alt-text form, backup warning, APPLY MEDIA confirmation modal, job history table, results panel
- [x] apps/frontend/app/dashboard/page.tsx — Media Library link updated to /media ✓
- [x] Commit and push

---

## Sprint 12: Variation Editor

**Status:** `[ ] TODO`

- [ ] Implement bulk variation price edit
- [ ] Implement bulk variation quantity edit
- [ ] Implement bulk variation SKU edit
- [ ] Build variation editor UI
- [ ] Write variation tests
- [ ] Commit and push

---

## Sprint 13: AI Tools

**Status:** `[ ] TODO`

- [ ] Implement AI title optimizer endpoint
- [ ] Implement AI description writer endpoint
- [ ] Implement AI tag generator endpoint
- [ ] Implement AI alt text generator endpoint
- [ ] Implement AI SEO scorer endpoint
- [ ] Implement AI category suggester endpoint
- [ ] Build AI tools panel UI (preview before apply)
- [ ] Add AI output approval flow
- [ ] Write AI tool tests
- [ ] Commit and push

---

## Sprint 14: CSV Import / Export

**Status:** `[ ] TODO`

- [ ] Design CSVJob model
- [ ] Implement CSV export of listings
- [ ] Implement CSV import with validation
- [ ] Build import preview (diff before apply)
- [ ] Build frontend CSV import/export UI
- [ ] Write CSV tests
- [ ] Commit and push

---

## Sprint 15: Dynamic Pricing

**Status:** `[ ] TODO`

- [ ] Design PricingRule model
- [ ] Implement rule-based price calculation engine
- [ ] Implement bulk price preview with rules applied
- [ ] Build pricing rule editor UI
- [ ] Write dynamic pricing tests
- [ ] Commit and push

---

## Sprint 16: Scheduled Jobs

**Status:** `[ ] TODO`

- [ ] Design ScheduledJob model
- [ ] Implement job scheduler (Celery Beat)
- [ ] Implement scheduled listing sync
- [ ] Implement scheduled bulk edit
- [ ] Build job scheduler UI
- [ ] Write scheduler tests
- [ ] Commit and push

---

## Sprint 17: Admin Panel

**Status:** `[ ] TODO`

- [ ] Build admin user management page
- [ ] Build admin subscription management page
- [ ] Build admin audit log viewer
- [ ] Build admin system health page
- [ ] Add admin-only API routes with role gate
- [ ] Write admin tests
- [ ] Commit and push

---

## Sprint 18: Tests, Deployment, Security Hardening, Polish

**Status:** `[ ] TODO`

- [ ] Achieve >80% backend test coverage
- [ ] Achieve >70% frontend test coverage
- [ ] Run OWASP security audit
- [ ] Fix all critical/high findings
- [ ] Configure GitHub Actions CI/CD pipeline
- [ ] Write production Docker Compose / Kubernetes configs
- [ ] Configure SSL, rate limiting, CORS, CSP headers
- [ ] Performance audit and optimization
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Final QA pass
- [ ] Write release checklist
- [ ] Tag v1.0.0
- [ ] Commit and push

---

## Backlog / Future

- [ ] Shopify integration
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Affiliate program
- [ ] Public API for integrations
