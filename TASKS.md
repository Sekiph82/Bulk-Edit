# TASKS.md — Phased Roadmap

Legend: `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

---

## Etsy Compliance + Production Readiness Audit (2026-07-13)

**Status:** `[x] MERGED TO MAIN AND LIVE IN PRODUCTION (2026-07-14, merge commit 435a1aa) — Private Beta remains enabled; Etsy appeal still not submitted`

Branch: `etsy-compliance-production-readiness`. Trigger: Etsy developer app "bulk-edit-app" status changed from "pending review" to **Banned**, no reason given.

- [x] Full repo audit — 7 docs (`ETSY_COMPLIANCE_AUDIT.md`, `ETSY_FEATURE_MATRIX.md`, `ETSY_PRODUCTION_READINESS.md`, `ETSY_DATA_RETENTION.md`, `ETSY_OAUTH_SCOPES.md`, `ETSY_APPEAL_CHECKLIST.md`, `ETSY_SUPPORT_QUESTIONS.md`)
- [x] Fixed OAuth scopes-storage bug, `disconnect_shop` token deletion, token auto-refresh wiring
- [x] Gated Etsy-data→AI-provider pathway behind `ALLOW_ETSY_DATA_TO_AI` (default off)
- [x] 30-day snapshot/CSV-job retention + cleanup script; retention window now configurable (`ETSY_DERIVED_DATA_RETENTION_DAYS`)
- [x] Terms/Privacy acceptance checkbox + backend enforcement + migration + tests
- [x] Self-service account deletion endpoint
- [x] Removed founding-access/pre-launch marketing language; removed public Listing Health Score / AI Optimization marketing claims (features stay live in-app)
- [x] Fixed Etsy-replacement language, trademark disclaimer placement, legal-entity-name invention
- [x] **Owner-review validation pass (second session, real Postgres, no delegated write access):** consolidated official-policy citation table added (`ETSY_COMPLIANCE_AUDIT.md` §6b); real local Postgres migration testing — clean upgrade, 0022→head with pre-existing data, downgrade/re-upgrade round trip, all verified for migrations 0023/0024/0025; found and fixed 2 real account-deletion bugs (SQLAlchemy relationship cascade crash; 9 tables missing `organization_id` foreign keys entirely) via live testing against real Postgres, not just reading code — see `ETSY_DATA_RETENTION.md` §4a; new migration `0025_add_missing_org_fk_constraints.py`; 3 new account-deletion regression tests.
- [x] Verification (second session): frontend `tsc`/lint/build clean (82 routes), backend full suite **971/971 passed** (964 original baseline + 4 from first review pass + 3 new account-deletion tests) — confirmed via a full independent from-scratch run
- [x] Secret scan: no candidates found in the diff
- [x] **Owner decision implemented (third session):** account deletion now blocks (HTTP 409, `ACTIVE_SUBSCRIPTION_MUST_BE_CANCELED` / `BILLING_PORTAL_UNAVAILABLE`) while an organization has an active or billable Stripe subscription — never auto-canceled. New `assert_account_deletion_billing_safe()` in `app/services/billing.py` (local-DB-only, no live Stripe call, fail-closed on any unrecognized status). Minimal deletion UI added to the existing `/billing` page — no new page. 14 new tests (11 owner-specified scenarios + 3 supporting), plus 2 real-Postgres end-to-end scenarios. No new migration — head unchanged at `0025`. See `ETSY_DATA_RETENTION.md` §4b.
- [x] Final verification (third session): frontend `tsc`/lint/build clean (82 routes, no new route), backend full suite **975/975 passed** (971 + 4 new billing-gate tests) — confirmed via a full independent from-scratch run. Alembic single-head confirmed: `0025`.
- [x] **PR #56 prepared and opened (fourth session)** — 6 logical commits, clean diff, no secrets.
- [x] **CodeQL CI failure found and fixed (fifth session):** `etsy_http.py` illegal-raise-of-`None` guard, `run_retention_cleanup.py` unused-import fix. Full backend suite re-confirmed **975/975 passed** (twice) before committing the fix. All 6 required PR checks green.
- [x] **Final pre-merge production-safety diff review (fifth session):** no secrets, no staging URLs, no invented legal entity, correct live pricing ($0/$19/$49/mo, $15/$39/mo yearly-equivalent = $180/$468/yr), server-side terms-acceptance enforcement, server-side `ALLOW_ETSY_DATA_TO_AI` gate confirmed wired.
- [x] **PR #56 merged to `main`** (merge commit `435a1aa`, non-squash, non-force) and **deployed directly to production** — no staging step, per owner instruction. Auto-deploy-on-push fired for both `bulk-edit-prod-api` and `bulk-edit-prod-web` immediately after merge; both prerequisite safety gates (DB backup confirmed, 0-orphan preflight) had already passed before that auto-deploy began.
- [x] Production orphan-data preflight: **0 orphan rows** across all 9 tables gaining FK constraints — safe to migrate.
- [x] Production migration `0025` applied cleanly (confirmed via `alembic_version` = `0025` and all 9 `fk_*_organization_id` constraints present with `ON DELETE CASCADE` on the live DB).
- [x] Production verification: backend health/readiness/redis all `ok`; Private Beta gate still enforced (307 → `/private-beta` on all `app.bulkeditapp.com/*` routes); AI public-marketing pages 404 as intended; live pricing bundle confirmed correct; terms/privacy/trademark copy live; registration blocked behind Private Beta (expected).
- [x] Cleanup-scheduler readiness: **Option B** — `run_retention_cleanup.py` is deployed with the backend image but has no `CRON`-kind DO job wired; scheduling remains manual until a real worker exists.
- [ ] Submit Etsy appeal using `ETSY_APPEAL_CHECKLIST.md` + `ETSY_SUPPORT_QUESTIONS.md` draft
- [ ] Manual verification once Etsy access restored (see `ETSY_PRODUCTION_READINESS.md` MANUAL/BLOCKED items — live OAuth, live video upload, email delivery)
- [ ] Wire retention cleanup script into a real scheduled job (DO `CRON` job kind, or a Celery beat schedule once a worker exists)

---

## Production Activation (2026-07-10)

**Status:** `[~] IN PROGRESS — blocked on Etsy (status escalated from "pending review" to "Banned" — see Etsy Compliance Audit above)`

- [x] Stripe Live checkout validated end-to-end (controlled internal account, no charge/subscription created)
- [x] All four Stripe price mappings confirmed correct
- [!] Etsy OAuth validation — **blocked: Etsy Developer app is now Banned** (was "pending review" as of 2026-07-10; status changed since). Waiting on Etsy appeal response; no workaround exists on our side. See HANDOFF.md for exact resume steps.
- [ ] Disable Private Beta (blocked on the Etsy item above passing)
- [ ] Post-activation app + marketing smoke tests

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
- [x] Fix Windows Docker port conflict — postgres/redis use `expose:` not `ports:` (commit e7d5111)
- [x] Fix demo login seed BOM issue — WriteAllLines no-BOM + utf-8-sig reader + verify-demo-logins.ps1 (commit 32c0e49)
- [x] Rewrite start-dev.bat as thin wrapper; ASCII-clean setup-and-start.bat (commit aa93aee)

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

**Status:** `[x] COMPLETE`

- [x] BulkEditVariationJob model (org-scoped, operation_type, operation_payload JSON, selected_listing_ids JSON, status machine, preview/success/failure/skipped counters)
- [x] BulkEditVariationPreviewItem model (per-listing: before_variations/after_variations/diff JSON, validation_status, unique constraint on job+listing)
- [x] BulkEditVariationResult model (per-listing: status, request/response payload JSON, error_message, attempted_at/completed_at)
- [x] ListingVariationBackupSnapshot model (org-scoped, local_variations_snapshot + etsy_inventory_snapshot JSON, etsy_shop_id FK, snapshot_type)
- [x] Alembic migration 0009 — bulk_edit_variation_jobs, bulk_edit_variation_preview_items, bulk_edit_variation_results, listing_variation_backup_snapshots
- [x] app/services/etsy_variation_write.py — fetch_etsy_listing_inventory, put_etsy_listing_inventory, normalize_etsy_inventory_tree, patch_inventory_tree_for_variation_operation (8 ops), _product_matches_selector, extract_local_variation_snapshot; EtsyVariationWriteError; fetch-patch-put pattern
- [x] app/schemas/bulk_edit_variation.py — VariationJobCreate (validated), VariationJobOut, VariationPreviewItemOut, VariationPreviewPageOut, VariationResultOut, VariationResultPageOut, VariationBackupSnapshotOut
- [x] app/services/bulk_edit_variation.py — create_variation_job, generate_variation_preview, apply_variation_job (safety gates: status check before Etsy config check, no invalid items, backup snapshot before write, local update only on success, partial failure, audit logs), list/get/preview/results/backups query helpers
- [x] app/api/v1/bulk_edit_variations.py — 8 endpoints: POST /jobs, GET /jobs, GET /jobs/{id}, POST /jobs/{id}/preview, GET /jobs/{id}/preview, POST /jobs/{id}/apply, GET /jobs/{id}/results, GET /jobs/{id}/backups
- [x] app/models/__init__.py — 4 new model imports
- [x] app/api/v1/router.py — bulk_edit_variations_router included
- [x] tests/test_bulk_edit_variation.py — 47 tests (unit: normalize/patch/selector/validate/preview; API: auth/validation/create/preview/apply gates/apply flow/org isolation/audit); 272/272 full suite PASS
- [x] apps/frontend/lib/api.ts — 6 new types (VariationJob, VariationPreviewItem, VariationPreviewPage, VariationResult, VariationResultPage, VariationBackupSnapshot) + 8 helpers
- [x] apps/frontend/app/variations/page.tsx — listing selector filtered to has_variations=true, 8-operation picker, selector inputs (property_name/value_name), preview button + before/after table, APPLY VARIATIONS confirm modal, results panel, job history
- [x] apps/frontend/app/dashboard/page.tsx — Variation Editor card added linking to /variations
- [x] Commit and push

---

## Productization UI Sprint (Design System)

**Status:** `[x] COMPLETE`

- [x] Install Impeccable (project-local, .claude/skills/impeccable/) via `npx impeccable install --providers=claude --scope=project`
- [x] Install UI UX Pro Max (global uipro-cli + project-local skill files in .claude/skills/ui-ux-pro-max/)
- [x] Run UI UX Pro Max design system generation for Bulk-Edit (SaaS etsy seller tool)
- [x] Generate page-specific design systems: dashboard, listings, bulk-edit, media, variations, home
- [x] Create PRODUCT.md (Impeccable context, register: product)
- [x] Create DESIGN.md (color palette, typography scale, component styles, motion rules)
- [x] Create design-system/MASTER.md (canonical design system for Next.js + Tailwind)
- [x] Create design-system/pages/ (home, dashboard, listings, bulk-edit, media, variations)
- [x] Create docs/design/PRODUCT_UI_DIRECTION.md (page-by-page direction, anti-patterns list)
- [x] Create docs/design/UI_AUDIT.md (full audit: 8/20 score, P0/P1/P2/P3 findings)
- [x] Light cleanup: remove sprint labels from homepage, remove disabled roadmap cards from dashboard, remove API debug panel
- [x] Full Productization UI Sprint — apply design system to all customer-facing pages
  - [x] npm install + lint + build baseline
  - [x] Fix tsconfig.json target (ES2017) — pre-existing Set spread type error
  - [x] Fix billing/page.tsx Suspense boundary for useSearchParams
  - [x] Remove emoji from shops/page.tsx and listings/page.tsx empty states
  - [x] Remove sprint labels from media/page.tsx operation labels and error messages
  - [x] Replace emoji check/cross in pricing/page.tsx with SVG icons
  - [x] Add loading="lazy" to all listing thumbnail img tags
  - [x] Add focus:outline-none focus:ring-2 to all interactive elements across all pages
  - [x] Human-readable operation labels in variations job history
  - [x] Human-readable operation name in media confirm modal
  - [x] Build passes — 14 routes, zero errors

---

## Landing Animation Sprint

**Status:** `[x] COMPLETE`

- [x] Install `motion` v12 (`npm install motion` in apps/frontend)
- [x] Create `apps/frontend/components/AnimatedProductDemo.tsx` — 5-phase animated mock product demo
  - [x] Phase 0: listing grid idle
  - [x] Phase 1: 3 rows selected (checkbox + row highlight animation)
  - [x] Phase 2: edit panel slides in (title append, tag add, price +10%)
  - [x] Phase 3: preview panel (before/after amber rows)
  - [x] Phase 4: safety strip (backup snapshot badge, magic revert badge, apply button)
  - [x] Reduced motion: `useReducedMotion` → static phase 4, no loop
  - [x] `aria-hidden="true"` on component (decorative)
  - [x] Zero API calls, zero external assets
- [x] Rewrite `apps/frontend/app/page.tsx` — 2-column hero layout
  - [x] New headline: "Bulk editing for Etsy sellers, without the spreadsheet chaos."
  - [x] Trust strip: Preview every change / Backup snapshots / Magic Revert / Built for Etsy sellers
  - [x] Workflow strip below hero: Connect → Sync → Edit → Preview → Apply → Revert
- [x] Update DESIGN.md — motion rules for homepage animation
- [x] Update design-system/pages/home.md — 2-column layout + demo docs
- [x] Lint clean, build 14 routes zero errors

---

## Sprint 13: AI Tools

**Status:** `[x] COMPLETE`

- [x] Provider abstraction (Mock/OpenAI/Anthropic) — default mock for local/CI
- [x] Prompt builders: title, description, tags, alt_text, seo_score
- [x] AISession, AISuggestion, AIUsageLog models
- [x] Alembic migration 0010_create_ai_tools_tables.py
- [x] Billing gate: paid plan required; credits counted per run
- [x] Service layer: create, run, accept, reject, convert_to_bulk_edit
- [x] 9 endpoints under /api/v1/ai
- [x] Frontend AI tools page (/ai): listing selector, tool picker, suggestions with accept/reject, convert to bulk edit, usage card, session history
- [x] Dashboard updated with AI Optimizer card
- [x] 32 tests, all mocked — 304/304 full suite pass
- [x] Build: 15 routes, zero errors
- [x] Commit and push

---

## Sprint 14: CSV Import / Export

**Status:** `[x] COMPLETE`

- [x] Design CSVJob + CSVRow models (alembic 0011)
- [x] Add target_listing_ids to BulkEditChange (alembic 0011)
- [x] Implement CSV export of listings
- [x] Implement CSV template download
- [x] Implement CSV import with validation (parse, normalize, diff)
- [x] Build import preview endpoint (paginated, status filter)
- [x] Build convert endpoint: CSV → BulkEditSession + BulkEditChange (NEVER writes to Etsy)
- [x] Update bulk edit preview engine for target_listing_ids scoping
- [x] Frontend: /csv page (export tab, import tab, job history tab)
- [x] Dashboard card: CSV Import / Export
- [x] 49 CSV tests pass, 353 total pass
- [x] Commit and push

---

## Sprint 15: Dynamic Pricing

**Status:** `[x] COMPLETE`

- [x] Design DynamicPricingJob + DynamicPricingRecommendation models (alembic 0012)
- [x] Add dynamic_pricing_jobs_used to UsageCounter
- [x] Add dynamic_pricing_jobs_per_month to plan limits (Pro: 100, free/basic: 0)
- [x] Implement calculation engine: percentage_adjustment, fixed_amount_adjustment, set_price, reference_price
- [x] Implement safety guardrails: margin floor, price floor, price cap, rounding rules
- [x] Build preview engine: per-listing DynamicPricingRecommendation rows with status/diff/warnings
- [x] Billing gate: can_use_dynamic_pricing (Pro only), dynamic_pricing_jobs_per_month limit
- [x] accept/reject/accept-all/convert endpoints
- [x] convert → BulkEditSession + BulkEditChange (target_listing_ids scoped, NEVER writes to Etsy)
- [x] 10 REST endpoints under /api/v1/dynamic-pricing
- [x] Frontend types + API helpers in lib/api.ts
- [x] Frontend: /pricing-rules page (listing selector, rule builder, guardrails, preview, rec table, convert modal)
- [x] Dashboard card: Dynamic Pricing
- [x] 50 dynamic pricing tests pass, 403 total pass
- [x] lint clean, build clean
- [x] Commit and push

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

**Status:** `[x] COMPLETE`

- [x] `app/schemas/admin.py` — 16 schemas, no secrets (no password_hash, no Etsy tokens, no Stripe secrets)
- [x] `app/services/admin.py` — paginated queries for all 14 entity types + 4 safe actions
- [x] `app/api/v1/admin.py` — 20 endpoints all gated on `require_superuser`
- [x] Router registered in `app/api/v1/router.py`
- [x] `tests/test_admin_panel.py` — 42 tests (auth gates, security, pagination, actions, not-found)
- [x] `apps/frontend/lib/api.ts` — admin types + 11 API helpers appended
- [x] `apps/frontend/app/admin/page.tsx` — full admin UI (overview cards, 6 sections, pagination, actions)
- [x] Dashboard card added for Admin Panel
- [x] 521/521 total tests passing
- [x] Frontend build clean, `/admin` route included
- [x] Commit and push

---

## Sprint 17.5: Marketing Website, FAQ, Contact, Footer Disclaimer, Theme Polish

**Status:** `[x] COMPLETE`

- [x] `apps/frontend/app/globals.css` — full `.be-*` design system (gradient buttons, hover-lift cards, FAQ accordion, contact card, hero bg, section accent, reduced-motion guard)
- [x] `apps/frontend/components/marketing/MarketingNav.tsx` — sticky nav, active link highlighting, Features/FAQ/Contact/Pricing
- [x] `apps/frontend/components/marketing/MarketingFooter.tsx` — 4-column footer, Etsy legal disclaimer
- [x] `apps/frontend/app/features/page.tsx` — 11-feature grid, 6-step workflow, safety checklist, animated listing visual
- [x] `apps/frontend/app/faq/page.tsx` — animated accordion, 6 categories (17 Q&As), safety/billing/AI/CSV coverage
- [x] `apps/frontend/app/contact-us/page.tsx` — 4 contact cards, demo form with success state, FAQ cross-link
- [x] Home page — MarketingNav + MarketingFooter, FadeUp hero, feature tease section
- [x] Pricing page — MarketingNav + MarketingFooter, billing logic unchanged
- [x] Etsy legal disclaimer on all marketing pages
- [x] 521/521 backend tests pass
- [x] 22 routes build clean
- [x] Commit and push

---

## Sprint 18: Tests, Deployment, Security Hardening, Polish

**Status:** `[x] COMPLETE`

- [x] Part A: Baseline verification — 521/521 tests, lint, build, mojibake scan, Docker, 22 routes
- [x] Part B: Security audit + `tests/test_security_hardening.py` (45 tests: auth gates, JWT tampering, org isolation, SQL injection, no-secrets, stack trace safety)
- [x] Part C: Add `GET /api/v1/health/ready` readiness probe endpoint
- [x] Part D: Create `docs/operations/ENVIRONMENT.md`, update `TESTING.md`, `DEPLOYMENT.md`
- [x] Part E: Mojibake fix — additional × and ✕ close buttons in listings + pricing-rules pages; JSX comment line clean-up
- [x] Part F: Frontend accessibility — `type="button"` + `aria-label` on icon-only close/delete buttons
- [x] Part G: No PII/secrets in responses verified (covered by security tests)
- [x] Part H: Full test suite — 566/566 passed (521 baseline + 45 new security tests)
- [x] Part I: Update TASKS.md, PROJECT_STATUS.md, HANDOFF.md, CHANGELOG_AI.md, DECISIONS.md, SECURITY.md, README.md
- [x] Part J: Confirm `.local-superusers.env` and `.env` NOT staged; commit + push

---

## Sprint 19: Internal Admin Business Dashboard

**Status:** `[x] COMPLETE`

- [x] Part A: Hide Admin nav link from non-superusers in AppShell; expose `is_superuser` in `/api/v1/auth/me` (already present in UserResponse schema)
- [x] Part B: Add `/api/v1/admin/billing-summary` endpoint (plan distribution, projected MRR labeled as "Expected")
- [x] Part C: Add `/api/v1/admin/stripe-summary`, `/api/v1/admin/product-usage`, `/api/v1/admin/system-health`, `/api/v1/admin/audit-log` endpoints
- [x] Part D: Rewrite `apps/frontend/app/(app)/admin/page.tsx` as full business dashboard (6 tabs: Overview, Users, Billing, Etsy, Usage, System)
- [x] Part E: Add new admin types + API helpers to `apps/frontend/lib/api.ts`
- [x] Part F: Friendly 403 page for non-superusers visiting /admin (improved design)
- [x] Part O: `tests/test_admin_dashboard.py` — 17 tests, all passing
- [x] Build: 20 routes, 0 errors. TypeScript: 0 errors.

---

## Sprint 20: Launch QA, CI/CD, E2E, Rate Limiting, CSP

**Status:** `[x] COMPLETE`

- [x] Part A: Baseline verification — 595/595 tests, lint, build, mojibake scan, Docker, 22 routes
- [x] Part B: GitHub Actions CI — `.github/workflows/ci.yml` (backend tests + postgres:16 + redis:7 services, frontend lint+build, docker-compose validate)
- [x] Part C: Playwright E2E — `playwright.config.ts` + 3 spec files (public-pages, theme, auth-flow); 11 pass / 2 skipped (seeded tests need `PLAYWRIGHT_RUN_SEEDED_TESTS=1`)
- [x] Part D: Backend rate limiting — `app/core/rate_limit.py` (in-memory, disabled by default; `RATE_LIMIT_ENABLED` env var); login 10/min, register 5/min per IP
- [x] Part E: CSP + frontend security headers via `next.config.mjs` (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, Content-Security-Policy)
- [x] Part F: Backend security headers middleware (`app/core/security_headers.py` — SecurityHeadersMiddleware on all API responses)
- [x] Part G: data-testid attributes for E2E selectors (`admin-nav-link`, `admin-access-denied`, `admin-dashboard`)
- [x] Part H: Launch checklist — `docs/operations/LAUNCH_CHECKLIST.md` (10 sections, 60+ checkboxes)
- [x] Part O: `tests/test_rate_limiting.py` (3 tests) + `tests/test_security_headers.py` (3 tests) — all 6 pass
- [x] Build: 22 routes, 0 errors. TypeScript: 0 errors. 595/595 backend tests pass.

---

## Sprint 21: Production Monitoring, Redis Rate Limiting, Sentry, Celery Readiness

**Status:** `[x] COMPLETE`

- [x] Part A: Upgrade rate limiter to Redis-backed dual backend (memory fallback on Redis unavailability) — `app/core/rate_limit.py`
- [x] Part B: Add `RATE_LIMIT_REDIS_URL`, `RATE_LIMIT_CONTACT_PER_HOUR`, `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE` to config
- [x] Part C: Sentry backend integration — `_init_sentry()` no-op when DSN absent; `_scrub_sentry_event()` redacts sensitive keys; FastApiIntegration + SqlalchemyIntegration
- [x] Part D: Upgrade `AdminSystemHealth` schema with 6 new monitoring fields: `redis_status`, `rate_limit_backend`, `rate_limit_enabled`, `sentry_configured`, `worker_status`, `csp_mode`
- [x] Part E: `_check_redis_health()` service — probes Redis with 2s timeout; never exposes Redis URL in response
- [x] Part F: Remove `unsafe-eval` from production CSP; add HSTS for `NODE_ENV=production`; document sha256 for future nonce CSP
- [x] Part G: Add `sentry-sdk[fastapi]==2.19.2` to requirements.txt
- [x] Part H: Expand `tests/test_rate_limiting.py` to 9 tests (was 3) — includes Redis config fields, Sentry config, disabled bypass
- [x] Part I: Expand `tests/test_security_headers.py` to 10 tests (was 3) — includes monitoring fields, Redis URL not exposed, Sentry DSN not exposed, worker status
- [x] Part J: `docs/operations/MONITORING.md` — health endpoints, Sentry, rate limiting, Stripe, Etsy, scheduled jobs, admin checks, daily checklist
- [x] Part K: `docs/operations/RUNBOOK.md` — 14 incident scenarios + rollback + secret rotation
- [x] Part L: `docs/operations/WORKERS.md` — inline scheduler docs + future Celery architecture
- [x] Part M: `.github/workflows/e2e.yml` — manual Playwright workflow with artifact upload
- [x] Build: 22 routes, 0 errors. TypeScript: 0 errors. 617/617 backend tests pass.

---

## Sprint 22: First-Run Onboarding, Non-Superuser Seed, Etsy Connection UX

**Status:** `[x] COMPLETE`

- [x] Fix `local_seed.py`: FREE seed user `is_superuser=False`, PAID seed user `is_superuser=True`
- [x] Add 4 new seed role tests (621/621 total)
- [x] `OnboardingChecklist.tsx` — 4-step progress bar, hides when all complete, dark-mode safe
- [x] Dashboard fetches shop count + listing count; shows checklist for new users
- [x] Shops empty state: Etsy® trademark note + OAuth explanation
- [x] `e2e/onboarding.spec.ts` — 2 always-run + 2 seeded-user E2E tests (Playwright 13/13 pass, 4 skipped)
- [x] Live Docker seed verified: `test@example.com is_superuser=False`, `test-su@example.com is_superuser=True`

---

## Sprint 23: Production Deployment Readiness Kit

**Status:** `[x] COMPLETE`

- [x] Part A: Baseline verification — 621/621 tests, 19/19 routes 200, Docker 4/4 up, seed roles correct
- [x] Part B: `apps/backend/scripts/validate_env.py` — production env validation (20+ checks, masks secrets, hard-fail in production, warn in dev/staging)
- [x] Part C: `scripts/smoke_test_deployment.ps1` + `.sh` — cross-platform smoke tests (13/13 pass against local Docker)
- [x] Part D: `docker-compose.prod.example.yml` — reference production compose (health checks, restart policies, no secrets)
- [x] Part E: `docs/operations/MIGRATIONS.md` — Alembic commands, migration table 0001-0013, safety rules
- [x] Part F: `docs/operations/BACKUP_AND_ROLLBACK.md` — pg_dump, managed platforms, emergency checklist
- [x] Part G: `docs/operations/STAGING_DEPLOYMENT.md` — staging architecture, env vars, promotion criteria
- [x] Part H: `docs/operations/DNS_SSL.md` — domain structure, DNS records, HSTS, CORS, common mistakes
- [x] Part I: `docs/operations/PROVIDER_SETUP.md` — Stripe, Etsy, OpenAI/Anthropic, email, Sentry
- [x] Part J: `docs/operations/LAUNCH_READINESS_REPORT.md` — fill-in launch template
- [x] Part K: `.github/workflows/ci.yml` — added `validate_env.py` dev-mode step before tests
- [x] Part L: Final verification — 621/621 backend tests, 13/13 smoke test, 19/19 routes, security headers, seed roles, no mojibake
- [x] Part M: Safety check + commit + push

---

## Sprint 24: Listing Health Score + Profit & Cost Calculator

**Status:** `[x] COMPLETE`

- [x] Part A: Baseline verification — 621/621 tests, 21/21 routes build
- [x] Part B: `app/services/listing_health.py` — rule-based score engine (0-100, grades, priorities, issue categories)
- [x] Part C: `app/services/profit.py` — Decimal arithmetic profit calculator with Etsy fee profile
- [x] Part D: Alembic migration 0014 — `cost_profiles` + `listing_costs` tables
- [x] Part E: `app/models/cost_profile.py` + `app/models/listing_cost.py` — new ORM models
- [x] Part F: `app/schemas/listing_health.py` + `app/schemas/profit.py` — Pydantic schemas
- [x] Part G: `app/api/v1/listing_health.py` — 5 endpoints (summary, list, detail, AI suggestions safe no-op, recalculate)
- [x] Part H: `app/api/v1/profit.py` — 7 endpoints (summary, list, detail, upsert costs, list/create/update cost profiles)
- [x] Part I: Router registration (`app/api/v1/router.py`)
- [x] Part J: `tests/test_listing_health.py` — 28+ tests, 52/52 Sprint 24 tests pass
- [x] Part K: `tests/test_profit.py` — 22+ unit + API tests
- [x] Part L: `apps/frontend/lib/api.ts` — 13 new API helpers + type interfaces
- [x] Part M: `apps/frontend/app/(app)/listing-health/page.tsx` — full health score page (summary cards, filters, table, AI suggestions inline)
- [x] Part N: `apps/frontend/app/(app)/profit/page.tsx` — full profit page (warning banner, summary cards, table, inline cost editor)
- [x] Part O: `apps/frontend/components/ui/AppShell.tsx` — added Listing Health + Profit nav items with icons
- [x] Part P: `apps/frontend/app/(app)/dashboard/page.tsx` — health + profit summary widgets
- [x] Part Q: `e2e/listing-health.spec.ts` + `e2e/profit.spec.ts` — 2+2 Playwright tests
- [x] Part R: 673/673 backend tests pass (52 new Sprint 24); build 24 routes clean; migration 0014 applied
- [x] Part S: Safety check + commit + push

---

## Sprint 25: Promote Health & Profit Features + Media Local Upload

**Status:** `[x] COMPLETE`

- [x] Part A: Remove mid-page Etsy disclaimer block from `/faq` page (footer disclaimer retained)
- [x] Part B: Add Listing Health Score + Profit Calculator to `/features` FEATURES array with optional href
- [x] Part C: Update `/features` subtitle from "Eleven" to "Thirteen tools"
- [x] Part D: Add optimization section (2 new cards) to homepage `/`; fix apostrophe entity
- [x] Part E: Add 4 FeatureRow entries to `/pricing` (Listing Health, Profit, AI suggestions, multiple profiles)
- [x] Part F: Add Shops nav item + ShopIcon SVG to AppShell between Dashboard and Listings
- [x] Part G: Cross-links — Listings → Listing Health (green tip banner), Listing Health → Profit, Profit → Listing Health
- [x] Part H: `LocalUploadPanel` component in `/media` page (drag-drop, MIME+extension validation, 10 MB / 20 files limits, thumbnail grid, Copy URL, clear all, URL.revokeObjectURL cleanup)
- [x] Part I: `e2e/faq.spec.ts` + `e2e/media-upload.spec.ts` — 4 new Playwright tests
- [x] Part J: 673/673 backend tests pass; 25/25 Playwright tests pass; 0 lint errors; build 24 routes clean
- [x] Part K: 13/13 smoke test checks; 16 dev env warnings 0 errors
- [x] Part L: Docs updated, safety check, commit + push

---

---

## Owner Console Subdomain Rebuild + Contact Persistence

**Status:** `[~] CODE COMPLETE, NOT MERGED` (branch `feature/owner-console-subdomain-rebuild`)

- [x] Audit: confirmed backend admin endpoints properly `require_superuser`-gated; found + fixed real bug (dashboard showed "Admin Panel" card to all users, not just superusers)
- [x] `apps/frontend/app/owner/*` — 11 pages (Dashboard, Users, Organizations, Shops, Jobs, Contact Submissions, Emails, Audit Logs, System Health, Feature Flags, Content) + `OwnerShell`/`OwnerUI` shared components
- [x] `middleware.ts` — `owner.bulkeditapp.com` host rewrite to `/owner/*`, noindex, no new DO app
- [x] `/admin` rebuilt as compat shim (404 for non-superusers, redirect to `/owner` for superusers)
- [x] `contact_submissions` table (migration 0020) — contact form persists every submission regardless of email delivery
- [x] `GET /api/v1/admin/contact-submissions` + `GET /api/v1/admin/feature-flags` (both `require_superuser`)
- [x] Backend 875/875 tests, frontend `tsc`/`next build` clean, `e2e/auth-flow.spec.ts` updated
- [x] Docs: `DECISIONS.md`, `PRODUCTION_LAUNCH_FOLLOWUPS.md` §8/§9, `HANDOFF.md`, `CHANGELOG_AI.md`
- [ ] Commit + push branch, open PR into `staging`, CI/CodeQL green, squash-merge, pull staging
- [ ] Attach `owner.bulkeditapp.com` to existing staging frontend DO app + Cloudflare CNAME (separate step, report exact record first)
- [ ] Cloudflare Access policy for `owner.bulkeditapp.com` (needs explicit allow-list confirmation)
- [ ] Follow-up (not this PR): `email_events` persistence table so `/owner/emails` shows real history instead of a static explanation

## Resend Outbound Email Domain Verification (bulkeditapp.com)

**Status:** `[ ] BLOCKED ON USER` — waiting for exact DNS records pasted from the Resend dashboard (Domain Verification/DKIM + Enable Sending/SPF/return-path + optional DMARC only — explicitly not inbound/MX; "Enable Receiving" confirmed disabled)

- [x] Resend SMTP env vars applied to staging backend
- [x] Diagnosed real failure via backend logs: `550 The bulkeditapp.com domain is not verified`
- [ ] Add exact DNS records to Cloudflare zone (DNS-only, never proxied)
- [ ] Click "Verify DNS Records" in Resend dashboard
- [ ] Retest staging email end-to-end (health, forgot-password known/unknown, contact form to both `SUPPORT_EMAIL` recipients)

## Backlog / Future
- [ ] Shopify integration
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Affiliate program
- [ ] Public API for integrations
