# CHANGELOG_AI.md — AI Session Log

Append one entry per session. Format: `## [DATE] Sprint N — Summary`

---

## 2026-07-14 (sixth session) Retention cleanup: Option B → Option A, confirmed live

**Trigger:** Owner instruction to merge the pending docs-only PR #57, then convert retention cleanup from "script deployed, no schedule" to a real production scheduler — smallest reliable option, explicitly no Celery/Redis-queue/separate-worker — with a safe dry-run mode verified locally before touching production, plus a final (not-submitted) Etsy appeal package.

**PR #57:** merged (`8345de4`) after confirming factual accuracy and CI green. Retriggered both prod apps' auto-deploy (push-triggered, not path-filtered); both reconfirmed `ACTIVE` with health/DB/Redis/Private-Beta/migration-0025 unaffected.

**Dry-run support:** `count_expired_snapshots()` added to `app/services/retention_cleanup.py`, sharing one `_RETENTION_MODELS` tuple with the real delete so the two queries can't drift apart. `scripts/run_retention_cleanup.py` gained `--dry-run` via `argparse`. Both paths print aggregate per-table + total counts only — no record content. 7 new tests in `tests/test_retention_cleanup.py`, all passing against the SQLite test DB.

**Scheduler discovery:** DigitalOcean App Platform's job `kind` for time-based execution is `SCHEDULED`, not `CRON` — found by testing directly against the live API (`doctl apps propose`, which validates without applying): `kind: CRON` was rejected outright as an unknown enum value; `kind: SCHEDULED` + `schedule: { cron: "..." }` validated cleanly. No `timezone` field exists on `schedule` — DO Scheduled Jobs are UTC-only, confirmed by testing one and having it rejected as an unknown field, which conveniently is exactly what was needed (03:30 UTC).

**Spec built:** `ops/app-specs/bulk-edit-prod-api.yaml` — the existing prod-api spec (reused an already-cached copy rather than re-pulling in full) plus a new `retention-cleanup` job mirroring the existing `migrate` job's build config exactly, single instance, smallest size, no public route/domain. Re-validated the whole modified spec against the real prod-api app via `propose` — passed. `SECRET`-type env vars are DigitalOcean's `EV[...]` encrypted placeholders, round-tripped unchanged, never decrypted or re-exposed.

**Local Postgres verification (real DB, not SQLite):** seeded 4 expired + 4 unexpired rows across all 4 tables in an isolated `retention_verify` database (after resolving the recurring Windows Hyper-V host-port issue by using port 45432). Dry-run reported exactly 4 candidates with a `ROLLBACK` (no writes); the real run deleted exactly 4 and a direct SQL count confirmed the 4 unexpired rows remained; a second real run deleted 0.

**Verification, PR, merge:** full backend suite **982 passed** (975 + 7 new), 0 failed; frontend tsc/lint/build clean; `git diff --check` and secret scan clean. Committed in the 3 specified logical groups, opened **PR #58**, all 6 required checks passed. Pre-merge production checks: DB backup current, health OK, migration unaffected (no schema change), and a pre-merge production dry-run via direct read-only query — **0 expired candidates**. Merged (`5f0cdb8`); both prod apps auto-rebuilt and reconfirmed healthy (rebuild alone doesn't add new components).

**Job registered:** ran `doctl apps update bulk-edit-prod-api --spec ops/app-specs/bulk-edit-prod-api.yaml --wait` (additive-only, preserves every existing setting) to actually add the new component — `deploy_on_push` alone only rebuilds components already in the spec. Confirmed directly against the live app (narrow, filtered query): `retention-cleanup`, `kind: SCHEDULED`, cron `30 3 * * *`, correct command, 1 instance, no public route. A final post-deploy production dry-run again showed **0** across all 4 tables, well below the anomaly thresholds — did not manually trigger the real cleanup to prove it works; the first real execution is left to the 03:30 UTC scheduled run and had not happened yet as of this session.

**Not yet done:** confirming the first real scheduled execution actually ran and succeeded (next session or later). `ETSY_FINAL_APPEAL_DRAFT.md` not yet written. Nothing submitted to Etsy.

---

## 2026-07-14 (fifth session) Etsy compliance — merged PR #56 and deployed directly to production

**Trigger:** Owner instruction to merge the already-open PR #56 (`etsy-compliance-production-readiness` → `main`) and deploy the approved Etsy compliance / legal / billing-safety / account-deletion changes directly to production, with no staging step, subject to an extensive list of hard safety rules (no live Etsy/Stripe writes, no DNS changes, never disable Private Beta, fail closed on CI or orphan-data problems, never print secrets).

**CI fix (blocking the merge):** `gh pr checks 56` showed the `CodeQL` check failing. Two real findings: `apps/backend/app/services/etsy_http.py` raised a statically-`Optional[Exception]` at two call sites (CodeQL: "Illegal raise"); `apps/backend/scripts/run_retention_cleanup.py` had a `noqa`-suppressed unused import. Fixed both — the raise sites now fall back to a descriptive `RuntimeError` if `last_exc` is somehow `None`, and the import is given a real syntactic use via `assert app.models`. Full backend suite run twice from scratch: **975/975 passed** both times. Pushed as commit `6e0a1f0`. All 6 required checks (`Analyze (python)`, `Analyze (javascript-typescript)`, `Backend Tests`, `CodeQL`, `Docker Compose Validate`, `Frontend Lint & Build`) green.

**Pre-merge safety review:** full diff read for secrets, staging URLs, invented legal facts, false public claims. None found. Live pricing source re-confirmed correct (Free $0, Basic $19/mo, Pro $49/mo, $180/$468 yearly — old $9/$29 absent). AI public-marketing pages confirmed removed while the server-side `ALLOW_ETSY_DATA_TO_AI` gate stays wired. `terms_accepted` confirmed enforced server-side (Pydantic validator), not just client-side.

**Merge and deploy:** merged via a normal merge commit (`435a1aa`), no squash, no force-push. Local `main` fast-forwarded. Production DB backup confirmed current (same-day automated backup, DO managed backups). Orphan-data preflight across the 9 tables gaining FK constraints in migration `0025`: **0 orphans**, verified via a read-only `asyncpg` script. Both `bulk-edit-prod-api` and `bulk-edit-prod-web` have `deploy_on_push: true`, so both auto-deployed the moment the merge landed — both prerequisite gates (backup + orphan check) had already passed before that happened, so no rule was violated, but future sessions should treat the merge as the deploy trigger and run those checks *before* merging.

**Post-deploy verification (all read-only / non-destructive):** production `alembic_version` = `0025`, all 9 `fk_*_organization_id` constraints present with `ON DELETE CASCADE`. Backend health/readiness/redis all `ok`. Private Beta gate fully intact — every `app.bulkeditapp.com/*` route still `307`s to `/private-beta`. `/features/ai-listing-optimization` and `/features/listing-health-score` `404` live as intended. Live pricing bundle fetched directly (`/_next/static/chunks/app/pricing/page-*.js`, since prices are client-rendered) and confirmed correct. `AI_PROVIDER=mock` and `ALLOW_ETSY_DATA_TO_AI` unset (safe default) in production — no live AI calls possible right now. Retention cleanup script (`run_retention_cleanup.py`) is deployed but not scheduled — no `CRON`-kind job wired (Option B).

**Process note:** briefly pulled a full deployment-status JSON blob that included `EV[1:...]`-format encrypted placeholders for `SECRET`-type env vars (DigitalOcean's standard non-reversible ciphertext representation, not plaintext) — switched to narrower field-filtered queries for every subsequent check.

**Not done:** Etsy appeal still not submitted. Retention cleanup still not on a real schedule. No live Etsy/Stripe actions performed. Staging untouched.

---

## 2026-07-13 (third session) Etsy compliance — Stripe account-deletion safety gate

**Trigger:** Owner decision on the second session's one open item — a paying user could delete their Bulk Edit App account while their Stripe subscription stayed active, with no remaining self-service cancel path. Owner decision: do not auto-cancel Stripe subscriptions on deletion; block deletion instead until the subscription is safely non-billable.

**Backend:**
- `app/services/billing.py` — new `AccountDeletionBillingStatus` enum, `AccountDeletionBillingCheck` dataclass, `assert_account_deletion_billing_safe(org_id, db)`: the single authoritative eligibility check. Local-DB-only (no live Stripe call), explicit allowlist, fail-closed. Safe only when: no `Subscription` row exists; plan is free with no `stripe_subscription_id`; or status is `canceled` with `current_period_end` already past. Every other state blocks, including `active` with `cancel_at_period_end=true` (not yet actually ended) and any Stripe status not explicitly recognized.
- `app/services/auth.py::delete_account()` — runs the check for every organization the user owns, before any row is touched; raises `AuthError(..., 409, code=...)` if any organization is unsafe. Nothing is deleted if any check fails — trivially transactional, no partial deletion possible.
- `app/api/v1/auth.py::delete_me` — surfaces the code in a structured `{"code": ..., "message": ...}` 409 body. No Stripe IDs or billing metadata in the response.

**Frontend:**
- `apps/frontend/app/(app)/billing/page.tsx` — minimal "Danger zone" section added to the existing billing page (no new page). Password-confirmed deletion; on block, shows the owner's exact required copy plus a "Manage Subscription" button routed through the existing `/billing/portal` endpoint.

**Tests:** 14 new in `tests/test_auth.py` — one table-driven test covering all 11 owner-specified scenarios, plus 3 supporting tests (portal-unavailable edge case, blocked-leaves-data-untouched, safe-deletion-still-cascades).

**Real-Postgres verification (local Docker only, zero live Stripe calls):** Scenario A — active subscription inserted directly, live API call → 409, confirmed user/org/subscription unchanged. Scenario B — subscription updated to canceled-and-ended, Etsy shop added, retried → 200, confirmed zero rows remain in any table.

**Verification:** Backend **975/975 passed** (971 + 4 new), full independent run. Frontend `tsc`/lint/build clean, 82 routes (no new route). Alembic single head confirmed unchanged: `0025` — no new migration needed.

**Not done:** not committed, not pushed, no PR, not merged, not deployed. No real Stripe API action performed anywhere in this session.

---

## 2026-07-13 (second session) Etsy compliance — owner-review validation pass

**Trigger:** Owner asked for a rigorous final validation of the existing `etsy-compliance-production-readiness` branch before merge — real Postgres testing, independent policy-citation verification, full change inventory, hygiene/secret scans, explicit decision matrix. No delegated write access to subagents this session.

**Found and fixed — 2 real bugs invisible to the SQLite test suite:**
- `DELETE /api/v1/auth/me` crashed (500) whenever the user had an active refresh token or org membership. Root cause: `Organization.members` / `User.memberships` / `User.refresh_tokens` relationships had no `passive_deletes=True`, so SQLAlchemy tried to NULL out NOT NULL foreign keys instead of letting Postgres's own `ON DELETE CASCADE` run. Fixed in `app/models/organization.py` + `app/models/user.py`.
- 9 tables (`etsy_shops`, `listings`, `cost_profiles`, `listing_costs`, `social_connections`, `social_oauth_states`, `etsy_oauth_states`, `sync_jobs`, `video_renders`) had `organization_id` with no foreign key at the database level at all — pre-existing since early sprints. Account deletion could never actually cascade to them. Added `ForeignKey(..., ondelete="CASCADE")` to all 9 models + new migration `apps/backend/alembic/versions/0025_add_missing_org_fk_constraints.py`.
- Both reproduced live against real Postgres (actual tracebacks), both fixed, both re-verified end-to-end (register → connect shop/listing/snapshot → delete → 0 rows remain anywhere, confirmed via direct SQL, not just a 200 response). 3 new tests in `tests/test_auth.py`.

**Real Postgres migration testing (all 3 required scenarios):** clean `alembic upgrade head` on a fresh DB (single head, `0025`); upgrade from a 0022 snapshot with representative pre-existing data (verified: no data loss, correct `expires_at` backfill, existing users NOT retroactively marked as accepting terms); full downgrade/re-upgrade round trip. Also found and documented (not fixed — it only makes retention more conservative, never less): migration 0023's backfill computes `expires_at` from migration-run-time, not each row's true `created_at`.

**Other additions:** consolidated official Etsy policy citation table (`ETSY_COMPLIANCE_AUDIT.md` §6b, sourced only from `developers.etsy.com`/`developer.etsy.com`/`etsy.com/legal`, explicit A–E classification so conservative choices are never described as Etsy mandates); `ETSY_DERIVED_DATA_RETENTION_DAYS` config (default 30, range 1-365, no new migration needed); full grouped 69-file change inventory with per-deleted-file justification; secret scan (clean) and hygiene scan (clean) across the whole diff.

**Flagged, not fixed — needs an owner decision:** `delete_account()` never touches Stripe. A paying user who deletes their account keeps an active, un-cancelable Stripe subscription. See `ETSY_PRODUCTION_READINESS.md` §27b.

**Verification:** Backend **971/971 passed** (964 + 4 from the first pass + 3 new this pass), confirmed via a full independent run. Frontend `tsc`/build re-confirmed clean (82 routes) after the backend model changes.

**Not done:** not committed, not pushed, no PR, not merged, not deployed. Etsy appeal not sent.

---

## 2026-07-13 (first session) Etsy compliance + production readiness audit (branch `etsy-compliance-production-readiness`)

**Trigger:** Etsy developer app "bulk-edit-app" marked Banned, no reason given. Full audit + correction pass, not deployed.

### Audit docs (new)
`ETSY_COMPLIANCE_AUDIT.md`, `ETSY_FEATURE_MATRIX.md`, `ETSY_PRODUCTION_READINESS.md`, `ETSY_DATA_RETENTION.md`, `ETSY_OAUTH_SCOPES.md`, `ETSY_APPEAL_CHECKLIST.md`, `ETSY_SUPPORT_QUESTIONS.md`.

### Most likely ban causes found
Etsy-synced listing content sent to OpenAI/Anthropic with no Etsy authorization (`ai_tools.py`, `listing_health.py`); OAuth `scopes` column bug (stored `token_type` not granted `scope`); public site "founding access"/pre-launch language contradicting a live, feature-complete app; `disconnect_shop` not actually deleting tokens (contradicted the Privacy Policy); no snapshot retention limit.

### Backend fixes
- `etsy.py`: fixed scopes-storage bug; `disconnect_shop` now deletes `EtsyToken` + pauses related `ScheduledJob` rows.
- `etsy_sync.py`: wired the already-existing `refresh_etsy_token()` into the read path (was previously logged-and-ignored); revoked-grant now surfaces a clean 401.
- New `etsy_http.py`: shared GET retry/backoff (429/5xx, `Retry-After`), wired into `etsy_sync.py` + `etsy_variation_write.py`'s inventory fetch.
- New `ALLOW_ETSY_DATA_TO_AI` flag (default False) hard-gates the Etsy-data→AI-provider pathway in `ai_tools.py` and `listing_health.py`, independent of `AI_PROVIDER`.
- New `expires_at` (30-day) on `ListingBackupSnapshot`/`ListingMediaBackupSnapshot`/`ListingVariationBackupSnapshot`/`CSVJob` + `retention_cleanup.py` + `scripts/run_retention_cleanup.py`. Migrations `0023`, `0024`.
- New `TermsAcceptance` model + `POST /api/v1/auth/register` terms_accepted enforcement (frontend + backend + service layer) + `terms_acceptances` table.
- New self-service `DELETE /api/v1/auth/me` (password-confirmed account deletion, cascades via existing FK `ondelete=CASCADE`).
- `bulk_edit.py`: preview summary now reports `stale_listing_count` (Etsy sync >6h old) — surfaced as a frontend warning banner before apply.
- `config.py`: added `ALLOW_ETSY_DATA_TO_AI`, `LEGAL_ENTITY_NAME/ADDRESS/COUNTRY/CONTACT_EMAIL`, `TERMS_VERSION`, `PRIVACY_VERSION`.

### Frontend fixes
- Removed "Founding access"/pre-launch marketing (`FoundingAccessSection.tsx` → `TrustSection.tsx`); rewrote `/private-beta` to state the real reason (Etsy verification pending) instead of "opening access gradually."
- Fixed "Your Etsy control panel"/"Everything you need to manage your Etsy shop" Etsy-replacement language; added the required primary positioning statement + "complements Etsy's seller tools" line to the homepage.
- Removed public marketing for Listing Health Score / AI Listing Optimization (features grid, pricing rows, comparison/blog copy, `/features/[slug]` entries) pending Etsy clarification — features remain live in-app.
- Added full Etsy trademark disclaimer near the always-visible Connect Etsy Shop button on `/shops` (previously only in the empty state).
- `MarketingFooter`/`Terms`: legal entity name now `LEGAL_ENTITY_NAME`-driven (no invented "LLC" — falls back to "© 2026 Bulk Edit App").
- `register/page.tsx`: required Terms/Privacy checkbox, unchecked by default, blocks submit client-side too.
- `terms/page.tsx`: added Etsy API developer disclaimer section. `privacy/page.tsx`: retention section now states the real 30-day/6-hour/immediate-token-deletion policy.
- `README.md`: removed stale "Sprint 1 — Monorepo Skeleton" claim.

### Verification
Frontend: `tsc --noEmit` clean, `next lint` 0 errors (pre-existing warnings only), `next build` clean (82 routes). Backend: delegated test-payload fix (terms_accepted added across 23 test files + 3 new auth tests) — full suite 964/964 passed, confirmed independently twice.

Independent verification pass (same session, before presenting to owner) found and fixed 3 real gaps the delegated work had missed: `docs/operations/WORKERS.md` was claimed-but-not-actually updated with the retention-cleanup cron hook (fixed); `ETSY_OAUTH_SCOPES.md` described a nonexistent `EtsyReauthRequiredError` exception class and wrong HTTP status (corrected to match the real `SyncError`/401 code); and none of this branch's own compliance-critical fixes (scope-storage bug, disconnect token deletion, token auto-refresh/revoked-grant handling) had regression tests. Added 4 tests to `tests/test_etsy.py` covering all three — full suite now 968/968 passed (964 baseline + 4 new, confirmed by a full independent run, 13m38s). Also flagged: two subagents each independently believed themselves to be "the main thread" mid-session and one disregarded scoping instructions; since both share one working tree, the landed result is a single coherent diff, confirmed by direct file-by-file review rather than trusting either agent's self-report. See `ETSY_COMPLIANCE_AUDIT.md` §6a for full detail.

### Not deployed
Per task instruction — audit, fixes, and test report only. Owner reviews before any deploy.

## 2026-07-10 Final controlled activation phase — Stripe PASSED, Etsy BLOCKED (Etsy app pending review)

**No code changes this session** — validation + ops only.

### Preflight
- Confirmed API/DB/Redis healthy, migration stayed at 0022, all Etsy/Stripe/email env var keys present in `bulk-edit-prod-api` (names only checked, never values).

### Controlled internal test account
- Created `sekiphayit1982+internal-test@gmail.com` via `POST /api/v1/auth/register` directly against production. Credentials appended to gitignored `deploy-production.local.env` (`INTERNAL_TEST_ACCOUNT_EMAIL`/`_PASSWORD`), never printed to transcript.

### Stripe checkout validation — PASSED
- `POST /api/v1/billing/checkout {"plan":"basic_monthly"}` with the test account's bearer token returned a Live Mode Checkout Session (`cs_live_...`).
- Verified via Stripe MCP: Price `price_1TrcNUHwWcsILCcPaBpeX4UP` = $19.00 USD (Basic Monthly); the other three prices (Basic Yearly $180, Pro Monthly $49, Pro Yearly $468) all confirmed active/correct via read-only Price lookups — no additional checkout sessions created for those three, per the task's own "read-only mapping check" instruction.
- One live Stripe customer created (`cus_UrMfFr80ISI59r`) for the test account; confirmed via Stripe search: zero charges, zero subscriptions.
- Confirmed `FRONTEND_URL=https://app.bulkeditapp.com` in the deployed spec, so checkout success/cancel URLs are production, not staging/localhost.
- Webhook signing secret present and code validates signatures, but the Stripe MCP connector has no webhook-endpoint API surface at all (list/create/retrieve all return empty across every resource name tried) — endpoint/event existence still unverifiable from this session.

### Etsy OAuth validation — BLOCKED
- `GET /api/v1/etsy/authorize` returned a structurally correct URL: production `redirect_uri`, correct scopes, PKCE `code_challenge` + `state`.
- User opened it; Etsy returned "application not recognized." Owner checked Etsy Developer Console: app status is **pending review**.
- Ruled out a config sync bug: sha256-hashed the local `ETSY_CLIENT_ID` and the value embedded in the live authorization URL — identical, so DO and local are in sync. The failure is Etsy-side app review status, not our infra.
- Stopped per the task's own Etsy-failure protocol: Private Beta remains enabled, no further Etsy testing possible until Etsy approves the app.

### Private Beta
- Remains enabled (`NEXT_PUBLIC_PRIVATE_BETA_MODE=true`) — correctly not disabled since the activation checklist requires both Etsy and Stripe to pass, and Etsy hasn't.

**Next session:** once the Etsy app clears review, resume from re-generating the OAuth URL and completing the callback/token/read-only-shop checks (see HANDOFF.md), then proceed to disabling Private Beta (requires a frontend **rebuild**, not just an env update, since `NEXT_PUBLIC_PRIVATE_BETA_MODE` is inlined at Next.js build time in `middleware.ts`) and the post-activation smoke tests.

## 2026-06-30 Fix: Port conflict + demo login seeding for one-click startup

**Commits:** e7d5111, aa93aee, 32c0e49

### Task 1 — Windows Docker port conflict (e7d5111)
- Root cause: Windows Hyper-V/WSL2 dynamic port reservation blocks port 55432
- `docker-compose.yml`: changed postgres+redis from `ports:` to `expose:` (internal Docker only)
- New `docker-compose.dev-ports.yml` optional override for dev host access
- `start-dev-clean.bat`: removed ERP shutdown + removed dead host port lines from URL display
- `start-dev.bat`: rewritten as 3-line thin wrapper to setup-and-start.bat
- Runtime verified: `docker compose ps` shows `5432/tcp` not bound — no ACL error

### Task 2 — Rewrite Windows one-click launcher (aa93aee)
- `setup-and-start.bat`: replaced Unicode box-drawing chars (`──` U+2500) with ASCII `-`; added Step 7c demo login verification; added Step 5 demo seed creation before compose up

### Task 3 — Demo login seeding (32c0e49)
- Root cause: PowerShell 5.1 `Set-Content -Encoding UTF8` writes UTF-8 BOM (EF BB BF). Python `open(path, encoding="utf-8")` keeps the BOM, making first key `﻿FREE_SUPERUSER_EMAIL` which `_require()` can't find. `seed_on_startup` catches `SeedConfigError` silently → users never created.
- `create-seed.ps1`: rewrote to use `WriteAllLines` + `UTF8Encoding($false)` — no BOM
- `local_seed.py`: `open(path, encoding="utf-8-sig")` — strips BOM if present
- New `scripts/windows/verify-demo-logins.ps1`: POSTs to `/api/v1/auth/login` for both demo accounts after readiness; exits 1 if either fails (bat halts + shows logs)
- 45/45 tests pass (batch readiness + seed tests)

---

## 2026-06-27 Social Connect + Product Sharing UX — COMPLETE

**Skills active:** 04 backend-router, 07 frontend-page
**Commit:** 13421bd fix: complete social connect and product sharing UX

- Popup OAuth flow for Pinterest and Instagram (window.open + postMessage)
- Callbacks return HTML page (not redirect) — postMessage never includes token
- SocialConnection model: +status, +account_name, +username, +external_account_id, +disconnected_at
- Migration 0018: add 5 columns, make access_token_encrypted nullable
- Status endpoints: return connected bool + account_name + username
- GET /promote/listings: org-isolated, 50 active listings, empty state
- POST /promote/pinterest/share + /instagram/share: deferred=true (no fake success)
- config-status now public (no auth), includes missing_vars lists
- Frontend: popup OAuth, SocialConnectionCard 4 states, PromoteListingCard grid, ShareModal
- Instagram Business/Creator + Facebook Page requirement always shown
- 797/797 backend tests passing; frontend build 0 errors

## 2026-06-27 Sprint 26 follow-up — Real Video Rendering + Social OAuth Account Connection

**Skills active:** 04 backend-router, 06 backend-service, 07 frontend-page
**Commit:** 430eaa6 feat: enable video rendering and social account connections

- Added ffmpeg to Dockerfile (apt-get)
- New `video_renderer` service: check_ffmpeg() 3-state, render_slideshow_mp4() ffmpeg subprocess arg-list
- New VideoRender model + migration 0015
- Rewrote video_generator.py: 5 endpoints, background task render with httpx image download, FileResponse download (auth + org isolation, file_path never in response)
- New SocialConnection + SocialOAuthState models + migration 0016
- Rewrote promote.py: Pinterest + Instagram OAuth (CSRF: state_value → SHA256 → store; single-use + expiry; Fernet-encrypted tokens; 4-state platform status)
- Rewrote video-generator frontend: 3-state + polling + download
- Rewrote promote frontend: 4-state per platform + connect/disconnect + query-param toast
- 617/617 backend tests pass. TypeScript: 0 errors.

---

## 2026-06-27 Sprint 26 — Growth, Insights, Credits, Media Reorder, Social Promote, Action Queue, Video Generator, Bulk Create

**Skills active:** 07 frontend-page, 05 frontend-component, 04 backend-router
**Commit:** 864e104 feat: add insights credits promote action queue video generator and bulk create (Sprint 26)
**Tests:** 24 new backend tests pass. 28 frontend routes build clean.

New: sound.ts chime utility, SoundToggle, 6 new feature cards, 8 FAQ entries, listing-health bulk select + Send to Bulk Edit, bulk-edit ?listing_ids= URL preselection, dashboard Action Queue widget, media reorder enabled, scheduled jobs payload hidden under Advanced, AppShell 4 new nav items, 4 new frontend pages (insights, promote, video-generator, bulk-create), 6 new backend endpoints (action_queue, insights, promote, video_generator, usage, bulk_create).

---

## 2026-06-27 Sprint 25 — Promote Health & Profit Features + Media Local Upload

**Skills active:** 07 frontend-page, 05 frontend-component

**What shipped:**
- FAQ: removed standalone Etsy disclaimer block (redundant with MarketingFooter).
- Features page: Listing Health Score + Profit Calculator added to FEATURES array. Grid updated for optional href. Subtitle updated "Eleven" → "Thirteen tools".
- Homepage: "Optimize listings. Protect your margin." section with 2 feature cards. Fixed `it's` → `it&apos;s` ESLint apostrophe error.
- Pricing: 4 new FeatureRow entries (Listing Health, Profit, AI suggestions, multiple profiles).
- AppShell: Shops nav item + ShopIcon SVG added to Workspace section between Dashboard and Listings.
- Cross-links: Listings → Listing Health (green tip banner), Listing Health → Profit (violet banner), Profit → Listing Health (green banner).
- Media page: `LocalUploadPanel` — drag-drop + click, MIME + extension dual validation, 10 MB / 20 files limits, objectURL thumbnail grid, Copy URL, cleanup on remove. No backend call (preview-only).
- E2E: `e2e/faq.spec.ts` (2 tests), `e2e/media-upload.spec.ts` (2 tests).

**Results:** 673/673 backend · 25/25 Playwright (all pass) · 0 lint errors · 24 routes clean · 13/13 smoke · 16 dev env warnings 0 errors.

**Issues fixed:** Spurious `<div style={{display:"none"}}>` artifact in profit/page.tsx cross-link edit removed immediately. ESLint apostrophe in app/page.tsx fixed.

---

## 2026-06-27 Sprint 24 — Listing Health Score + Profit & Cost Calculator

**Skills active:** 06 backend-api, 07 frontend-page, 03 data-model

**What shipped:**
- `app/services/listing_health.py`: rule-based health score engine. Score 0-100. Five categories: title, tags, description, media, pricing. HealthIssue dataclass with severity/category/field/points_lost. Informational cost warning outside issue list. `_grade()` and `_priority()` helpers.
- `app/services/profit.py`: Decimal profit calculator. Default Etsy fee profile (6.5% transaction, 3%+$0.25 payment, $0.20 listing, optional 15% offsite ads). Returns break-even price, recommended min price, ROI. `profit_status()` returns profitable/low_margin/loss.
- Alembic migration 0014: `cost_profiles` table (org-scoped fee profiles, Numeric(6,5) for percentages) + `listing_costs` table (UNIQUE org+listing, FK to cost_profiles SET NULL).
- 5 listing-health API endpoints + 7 profit API endpoints. All org-isolated via `get_current_org_id`. AI suggestions safe no-op when `AI_PROVIDER=mock`.
- Frontend: `/listing-health` page (summary cards, grade/priority/search/sort filters, score badges, AI suggestions inline), `/profit` page (fee disclaimer banner, status badges, inline cost editor). Both pages: auth redirect, parallel data fetch, empty state with shop link.
- AppShell nav: HeartIcon + DollarIcon added. Dashboard: health + profit summary widgets.
- 52 new backend tests (28 health + 24 profit). All pass. Pre-existing failures unchanged.

**Issues fixed:** Cost informational issue moved outside `issues` list (no points_lost; was incorrectly counted). `@pytest.mark.anyio` removed (use `asyncio_mode=auto` from pytest.ini). Auth guard returns 403 not 401 — tests updated to `in (401, 403)`.

## 2026-06-27 Sprint 23 — Production Deployment Readiness Kit

**Skills active:** 22 devops, 06 backend-api

**What shipped:**
- `apps/backend/scripts/validate_env.py`: standalone env validation script. Checks 20+ variables. Masks secrets. Hard-fails in production mode for missing/placeholder values. Warns in development/staging. CORS wildcard check, weak JWT_SECRET check, Stripe test key in production warning. Exit code 0 on warnings, 1 on errors.
- `scripts/smoke_test_deployment.ps1` + `.sh`: cross-platform smoke tests for `/health`, `/health/ready`, and 11 frontend routes. Exit code 0 on all pass.
- `docker-compose.prod.example.yml`: reference production compose config. Health checks, restart policies, commented Celery worker/beat services, no secrets hardcoded. Notes managed DB + Redis preference.
- `docs/operations/MIGRATIONS.md`: Alembic commands, migration table (0001-0013), safety rules, post-migration smoke test, zero-downtime migration notes.
- `docs/operations/BACKUP_AND_ROLLBACK.md`: pg_dump, managed platform options, Redis backup considerations, Docker image rollback, emergency checklist.
- `docs/operations/STAGING_DEPLOYMENT.md`: staging architecture, env var table, step-by-step deploy procedure, promotion criteria checklist.
- `docs/operations/DNS_SSL.md`: domain structure, DNS records, HSTS notes, CORS config, OAuth/webhook URLs, common mistake table.
- `docs/operations/PROVIDER_SETUP.md`: Stripe (products, keys, webhook events), Etsy (app creation, scopes, rate limits), OpenAI/Anthropic setup, Sentry integration.
- `docs/operations/LAUNCH_READINESS_REPORT.md`: fill-in launch template with sections for tests, infra, security, providers, go/no-go, post-launch checks.
- `.github/workflows/ci.yml`: added `validate_env.py --env development` step before tests. Exits 0 in dev mode (warnings only), catches critical issues early.
- Verified: 621/621 backend tests pass. 13/13 smoke test checks pass. 19/19 routes 200. Security headers present. Seed roles correct.

---

## 2026-06-27 Sprint 22 — First-Run Onboarding, Non-Superuser Seed, Etsy Connection UX

**Skills active:** 06 backend-api, 20 testing-qa, frontend-ux

**What shipped:**
- `local_seed.py`: `_upsert_user` + `seed_superuser` now accept `is_superuser` param. FREE seed = `is_superuser=False` (normal customer). PAID seed = `is_superuser=True` (internal admin).
- 4 new backend role tests. 621/621 total.
- `OnboardingChecklist.tsx`: 4-step checklist with progress bar, hides when all steps done, dark-mode safe.
- Dashboard: fetches shop count + listing count; shows checklist above feature cards for new users.
- Shops empty state: Etsy® trademark disclaimer + OAuth explanation added.
- `e2e/onboarding.spec.ts`: 2 always-run + 2 seeded-user tests.
- Live verified: `test@example.com is_superuser=False`, `test-su@example.com is_superuser=True`.
- Playwright: 13 passed, 4 skipped. 0 TS errors.

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

---

## Session: Sprint 21 — Production Monitoring, Redis Rate Limiting, Sentry, Celery Readiness

**Date:** 2026-06-27
**Status:** COMPLETE

**Summary:** Upgraded production readiness infrastructure. Redis-backed rate limiter with automatic memory fallback. Sentry error tracking integration (disabled without DSN; scrubs all sensitive keys). Admin system-health endpoint upgraded with 6 new monitoring fields. Production CSP hardened: removed unsafe-eval, added HSTS. Full operations documentation suite created.

**New files:**
- `docs/operations/MONITORING.md` — health endpoints, Sentry config, rate limiting monitoring, daily checklist
- `docs/operations/RUNBOOK.md` — 14 incident scenarios, rollback, secret rotation
- `docs/operations/WORKERS.md` — inline scheduler docs + future Celery architecture
- `.github/workflows/e2e.yml` — manual Playwright E2E workflow with artifact upload

**Modified files:**
- `apps/backend/app/core/config.py` — 5 new fields: RATE_LIMIT_REDIS_URL, RATE_LIMIT_CONTACT_PER_HOUR, SENTRY_DSN, SENTRY_ENVIRONMENT, SENTRY_TRACES_SAMPLE_RATE
- `apps/backend/app/core/rate_limit.py` — full rewrite: Redis ZSET + memory fallback dual backend; IP-only keys (no email extraction); contact endpoint 1h window
- `apps/backend/app/main.py` — _init_sentry() + _scrub_sentry_event() with 14-key sensitive field set
- `apps/backend/app/schemas/admin.py` — AdminSystemHealth + 6 monitoring fields
- `apps/backend/app/services/admin.py` — _check_redis_health() + updated get_system_health()
- `apps/backend/requirements.txt` — sentry-sdk[fastapi]==2.19.2
- `apps/frontend/next.config.mjs` — remove unsafe-eval in production, HSTS for production
- `apps/backend/tests/test_rate_limiting.py` — 9 tests (was 3)
- `apps/backend/tests/test_security_headers.py` — 10 tests (was 3)

**Test results:** 617/617 PASSED (51 new Sprint 21 tests)

**Frontend build:** 22 routes, 0 TypeScript errors

**Security gates verified:**
- Rate limit 429 response contains no secrets
- system-health never returns Redis URL
- system-health never returns Sentry DSN
- Sentry disabled when DSN absent (no crash, no-op)
- RATE_LIMIT_ENABLED defaults False in test env

**Blockers:** None

**Next:** Sprint 22 — User onboarding flow, empty state polish, first-run wizard, analytics events

---

## Production domain configuration — bulkeditapp.com

**Goal:** Ready the repo for the purchased production domain. Frontend www.bulkeditapp.com; apex bulkeditapp.com redirects to www; backend api.bulkeditapp.com. Local dev preserved (localhost:3100 / :8100).

**Files changed:**
- `.env.example` — fixed Etsy callback path; added PRODUCTION REFERENCE block
- `apps/backend/.env.example` — production reference comments
- `apps/frontend/.env.local.example` — production reference comments
- `docs/operations/ENVIRONMENT.md` — local/prod URL + CORS tables; fixed Etsy row
- `docs/operations/PROVIDER_SETUP.md` — real domain; fixed Etsy redirect (api host + /api/v1/etsy/callback)
- `docs/operations/DNS_SSL.md` — rewritten for www/apex/api model + DNS + callbacks
- `docs/operations/LAUNCH_CHECKLIST.md` — new Domain/DNS section; fixed webhook/Etsy/support URLs
- `docs/operations/DEPLOYMENT.md` — production domain model + provider-neutral notes
- `docs/operations/STAGING_DEPLOYMENT.md`, `LAUNCH_READINESS_REPORT.md` — domain refs
- `apps/backend/tests/test_config_cors.py` — new (5 tests, CORS parsing)

**Verified callback/webhook routes (from code):**
- Etsy: `https://api.bulkeditapp.com/api/v1/etsy/callback`
- Pinterest: `https://api.bulkeditapp.com/api/v1/promote/pinterest/callback`
- Instagram: `https://api.bulkeditapp.com/api/v1/promote/instagram/callback`
- Stripe webhook: `https://api.bulkeditapp.com/api/v1/billing/webhook`

**Results:** CORS tests 5/5 PASSED · frontend lint clean (pre-existing warnings only) · frontend build OK (22 routes) · validate_env.py runs (fails only on absent real secrets, as expected) · no real secrets committed · no `.env` files staged.

**No code behavior changed** — CORS already supported comma-separated origins; all URLs remain env-driven.

---

## Vercel + Render production deployment prep

**Goal:** Ready repo for Vercel (frontend) + Render (backend) deploy of bulkeditapp.com. Local dev preserved.

**Code changes:**
- `apps/backend/app/core/config.py` — `_force_asyncpg_driver` validator normalizes DATABASE_URL scheme (postgres:// / postgresql:// → postgresql+asyncpg://) for managed DBs
- `apps/backend/Dockerfile` — prod CMD → `sh /app/start.sh`; chmod start.sh (was hardcoded port 8000 + --reload)
- `apps/backend/start.sh` — NEW: alembic upgrade head (retry) + uvicorn on ${PORT:-8000}
- `apps/backend/.dockerignore` — NEW: keeps .env/.local-superusers.env/caches/tests out of image
- `render.yaml` — NEW blueprint (Postgres + Redis + Docker web); secrets sync:false, no values
- `apps/backend/tests/test_config_db_url.py` — NEW (4 tests, scheme normalization)

**Docs:**
- `docs/operations/VERCEL_RENDER_DEPLOY.md` — NEW: full Vercel + Render walkthrough, env vars, DNS, callbacks, CI/CD rationale
- `docs/operations/PRODUCTION_SMOKE_TEST.md` — NEW: post-deploy checklist
- `docs/operations/DNS_SSL.md`, `DEPLOYMENT.md` — cross-link provider guide

**Deploy model:** provider Git auto-deploy (Vercel + Render watch main). No custom deploy workflow — deferred.

**Results:** config tests 9/9 PASSED (CORS + DB URL) · normalizer verified live · frontend lint clean · frontend build OK (22 routes) · docker compose config OK (local unaffected) · validate_env runs (fails only on absent real secrets) · no secrets in render.yaml · no .env staged.

---

## Guided Vercel + Render deploy automation

**Goal:** Claude Code runs the deploy after the user fills one gitignored secrets file. No manual copy/PowerShell/CLI.

**Files added:**
- `deploy-secrets.local.env.example` — template (tracked); local `deploy-secrets.local.env` is gitignored
- `scripts/prepare-deploy-secrets.ps1` — create local file from template + open in Notepad
- `scripts/deploy-production.ps1` — validate (present/MISSING only), preflight, git-safety, Vercel deploy + env, Render validate/find/domain/deploy, summary
- `scripts/smoke-production.ps1` — www/apex-redirect/health/ready/CORS PASS-FAIL
- `scripts/output/.gitkeep` — keep dir; contents gitignored
- `.gitignore` — deploy-secrets.local.env, .vercel/, scripts/output/*
- `docs/operations/VERCEL_RENDER_DEPLOY.md` — "Claude Code guided deployment" section

**Verification:** all 3 scripts parse clean (PSParser) · prepare creates local file + opens Notepad · deploy with blank secrets fails safe (exit 2, lists only 4 missing key names, no values) · git check-ignore confirms local secrets/.vercel/output all ignored · no secret file tracked (only .example template).

---

## Phase 0 + Phase 1 scaffolding (DigitalOcean migration)

**Branch:** feature/phase0-1-scaffold (not pushed). staging branch created.

**Phase 0 (guardrails):** .github/dependabot.yml, .github/workflows/codeql.yml, CHANGELOG.md, docs/operations/GIT_WORKFLOW.md, docs/operations/GITHUB_SETUP_CHECKLIST.md.

**Phase 1 (DO staging scaffold):**
- .do/app.staging-frontend.yaml, .do/app.staging-backend.yaml (+ pre-deploy migrate job, PG, Redis), .do/app.production-{frontend,backend}.yaml (design only), .do/README.md
- apps/frontend/middleware.ts (host routing: www->apex 301, app-route bounce to app subdomain, X-Robots-Tag noindex for app/staging; localhost/preview pass-through)
- apps/frontend/app/robots.ts (per-host: marketing allow, app/staging Disallow /)
- apps/frontend/components/StagingBanner.tsx + wired into app/layout.tsx (shows when NEXT_PUBLIC_APP_ENV=staging)
- docs/operations/DIGITALOCEAN_DEPLOY.md, CLOUDFLARE_DNS.md; updated ENVIRONMENT.md + STAGING_DEPLOYMENT.md

**Verification:** frontend lint clean, build OK (robots.txt dynamic, middleware 26.8kB), all .do/*.yaml + dependabot + codeql parse clean, no secrets in any new file. Nothing committed to main; nothing pushed.

---

## Staging provisioning automation (token-driven)

**Branch:** feature/staging-automation (PR into staging).

**Added:**
- deploy-staging.local.env.example (template; local deploy-staging.local.env is gitignored)
- .gitignore: deploy-staging.local.env, *.local.env, *secrets*.env, .doctl/, .cloudflared/, token files
- scripts/prepare-staging-secrets.ps1 (create+open local env)
- scripts/provision-staging.ps1 (validate + refuse prod/live values + generate JWT/Fernet locally +
  doctl app create from .do specs + Cloudflare DNS CNAMEs; secrets never printed)
- scripts/smoke-staging.ps1 (health/ready/db/redis, CORS allow+reject, robots Disallow, X-Robots noindex,
  no prod-API, no sk_live_)
- docs/operations/STAGING_AUTOMATION.md (fill env, tokens/scopes, run order, stop conditions, cost, rollback)

**Verified:** all 3 scripts parse clean; provision safe-fails on blank env (lists missing tokens, no
provisioning, no secrets printed); local env gitignored + untracked; example trackable; no secrets in diff.

---

## Owner console subdomain rebuild + contact submission persistence (2026-07-05)

**Branch:** `feature/owner-console-subdomain-rebuild` (off `staging`, not yet merged).

**Audit findings (reported before any code changed, per instruction):** `/admin` backend endpoints (20, under `/api/v1/admin`) were and remain correctly `require_superuser`-gated. `AppShell.tsx`'s sidebar nav item was correctly hidden from non-superusers. Real bug found: `(app)/dashboard/page.tsx`'s static `activeFeatures` list unconditionally showed an "Admin Panel" card (linking to `/admin`) to every logged-in customer, not just superusers — fixed by removing the card. `/admin` was already absent from sitemap/robots/nav/footer/JSON-LD.

**Added:**
- `apps/frontend/app/owner/*` — 11 pages (Dashboard, Users, Organizations, Shops, Jobs, Contact Submissions, Emails, Audit Logs, System Health, Feature Flags, Content) + `layout.tsx` + shared `components/owner/OwnerShell.tsx` (client-side superuser gate — this app's tokens live in localStorage, so Next middleware cannot check auth server-side) + `components/owner/OwnerUI.tsx` (shared table/badge/pagination helpers).
- `apps/frontend/middleware.ts` — `owner.bulkeditapp.com` host constant; rewrites every request on that host to `/owner/*` (same frontend app, no new DO app); applies `X-Robots-Tag: noindex`.
- `apps/frontend/app/(app)/admin/page.tsx` — rewritten from the old single tabbed dashboard into a thin compat shim: `notFound()` for unauthenticated/non-superuser, same-origin `router.replace("/owner")` for confirmed superusers.
- `apps/backend/app/models/contact_submission.py` + migration `0020_create_contact_submissions.py` — contact form (`app/api/v1/contact.py`) now persists every submission (name/email/subject/message/email_delivered) regardless of send outcome, so an inquiry isn't lost while SUPPORT_EMAIL delivery is failing (live Resend blocker).
- `GET /api/v1/admin/contact-submissions` + `GET /api/v1/admin/feature-flags` — both `require_superuser`; feature-flags is read-only (mirrors `VIDEO_RENDERER_ENABLED`, `RATE_LIMIT_ENABLED`, `EMAIL_CONFIGURED`, `AI_PROVIDER_LIVE` — no functional toggle backend exists, none faked).
- Deliberately NOT built: `email_events` persistence (send_email() only logs, never persists — Emails page states this plainly instead of faking history; documented as a follow-up in `PRODUCTION_LAUNCH_FOLLOWUPS.md` §8).

**Tests:** 875/875 backend (6 new: contact persistence, contact-submissions auth, feature-flags auth). Frontend `tsc --noEmit` clean, `next build` clean (61 routes, incl. 11 new `/owner/*`). Updated `e2e/auth-flow.spec.ts` for the new `/admin` 404/redirect behavior.

**Not done in this branch:** Cloudflare DNS / DO custom-domain attachment for `owner.bulkeditapp.com` (separate step, reported before applying); Cloudflare Access policy for the owner host (needs an explicit allow-list confirmation first); PR/merge into staging.
No provisioning executed. Production untouched.
