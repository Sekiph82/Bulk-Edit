# TASKS.md — Active Work

Legend: `[ ]` todo · `[~]` in progress · `[x]` done

Full sprint-by-sprint build history (Sprint 0 through Sprint 27, all DevOps fixes, the Vercel/Render → DigitalOcean hosting migration) lives in `CHANGELOG_AI.md` — not repeated here. This file tracks only what's currently active, blocked, or pending.

---

## Current Phase

Post-launch production QA. All planned feature sprints are complete, Etsy OAuth is fully live and confirmed working (WearYourStoriesCom, 210/210 listings synced under `sekiphayit1982@gmail.com`, `pro_monthly` comp grant). Sprint 1 Core QA (PR #89) deployed but only partially fixed the owner's 5 problems on manual verification. Current focus: **Sprint 1 Follow-up QA** (branch `fix/sprint-1-followup-qa`, issue #90) — code-complete as of 2026-08-28, pending PR/CI/merge/deploy.

## In Progress

- **Sprint 1 Follow-up QA — PR/CI/merge/deploy** — 4 fixes code-complete and test-verified on `fix/sprint-1-followup-qa` (see Recently Completed below and issue #90). Next: commit, push, open PR, wait for CI, merge, verify prod health, get owner to manually re-verify hover/decode/remove-change. **Do not retry the live Bulk Edit apply** — owner approval required first. See `HANDOFF.md` for exact resume steps.

## Recently Completed

- **Sprint 1 Follow-up QA (2026-08-28)** — issue #90, after owner manually verified PR #89 in production and found 4 of 5 items still broken: (1) hover preview was clipped by the table wrapper's `overflow-hidden` — fixed with a `createPortal`-based fixed-position preview; (2) HTML entities still visible for already-synced rows — added frontend `decodeEntities()` defense-in-depth across listings/bulk-edit/promote, wrote (not run) a DB backfill script for existing rows; (3) Bulk Edit remove-change failed with a false-negative error — `apiFetch()` was calling `res.json()` on empty `204` responses, fixed once in the shared helper (also fixes 4 other `204` endpoints); (4) **the real Bulk Edit write bug** — `patch_etsy_listing_inventory()` used a wrong URL (`/shops/{shop_id}/listings/{listing_id}/inventory`) when Etsy's real endpoint is listing-scoped only (`/listings/{listing_id}/inventory`), proven via the already-working read counterpart; same bug also fixed in the unexercised variation-write sibling. No live Etsy write performed — root cause diagnosed from code only. Full detail: `CHANGELOG_AI.md`, `DECISIONS.md`, `2026-08-28` Sprint 1 follow-up entries.
- **Sprint 1 Core QA (2026-08-28)** — issue #88, PR #89 merged `309cff0`: (1) Billing page now shows effective plan (Pro via comp grant) instead of raw "Free"; (2) added `property_values` to the inventory payload (necessary but, per the follow-up above, not sufficient — a second bug remained) and wired the previously-unused apply-job-detail endpoint into the UI so failed items show a reason; (3) HTML entities (`&#39;` etc.) now decoded at the Etsy sync layer for new syncs; (4) listing table thumbnails 80×80 (hover preview shipped broken, fixed in the follow-up above); (5) footer now credits "Akilta" with a link to `https://www.akilta.com`. No live Etsy write performed. Full detail: `CHANGELOG_AI.md`, `DECISIONS.md`, `2026-08-28` Sprint 1 entries.
- **Etsy listing sync "25 of 210" — root cause fixed (2026-08-28)** — was correctly diagnosed as a working-as-designed Free-plan cap, not a pagination bug (see below), but the owner's chosen fix (comp grant) didn't take effect until two further bugs were found and fixed: `promote_superuser.py`/`create_admin_user.py` used the raw `DATABASE_URL` instead of the app's asyncpg-rewritten `settings.DATABASE_URL` (PR #86), and `sync_shop_listings()` never actually checked comp grants — only raw `Subscription.plan` (PR #87, added `get_effective_plan()` to `app/core/plans.py`). Confirmed fixed: sekiphayit1982@gmail.com now syncs all 210 listings.
- **Etsy listing sync "25 of 210" investigated — not a bug (2026-08-28)** — pagination loop in `sync_shop_listings()` already correct; the cap is `PLAN_LIMITS["free"]["max_listings"]=25`, a deliberate feature gate, confirmed the test account is on the Free plan. Declined to implement the originally-requested "pagination fix" — it would have bypassed a paid-plan gate (`CLAUDE.md` rule 8). Owner chose to upgrade the test account's plan via the existing admin comp-grant mechanism instead of a code change. No code changed, no new GitHub issue filed (would have been factually wrong). See `CHANGELOG_AI.md` / `DECISIONS.md`, `2026-08-28` entries.

- **Private Beta allows sign-in (2026-08-27)** — `fix/private-beta-allow-signin`: Private Beta now blocks only registration (`/register`, `/signup`, `/get-started`); sign-in and the authenticated app pass through, and the Etsy OAuth callback's `/shops?connected=true`/`?error=...` result is no longer masked by the beta gate. See `CHANGELOG_AI.md` for full detail.
- **Etsy OAuth callback safe categorized logging (2026-08-27)** — `fix/etsy-oauth-safe-callback-logging`: the previously-bare `except Exception` in `/etsy/callback` now logs one of 11 safe categories (`etsy_oauth_state_not_found`, `_token_exchange_failed`, `_shop_not_found`, etc.) with no code/state/token values. Browser-visible behavior unchanged (`?connected=true` / `?error=etsy_connect_failed`).
- **doctl auth restored (2026-08-27)** — token re-supplied from `deploy-production.local.env` directly into doctl's local config, never printed/argv'd. `doctl account get` confirmed working.
- **Etsy OAuth root cause found + defensive hardening shipped (2026-08-27)** — production logs showed `etsy_oauth_shop_lookup_failed`, Etsy's shop-lookup endpoint returning 403 after a successful token exchange. Diagnosed at the time as likely a Personal Use access-tier restriction (issue #80) — `user_id` derivation confirmed correct against Etsy's own docs. Shipped `fix/etsy-oauth-user-id-validation` anyway: validates `user_id` is present/numeric before calling Etsy, new category `etsy_oauth_user_id_missing_or_invalid`. Superseded by the finding below.
- **Etsy x-api-key header format fix (2026-08-27)** — `fix/etsy-oauth-shop-lookup-x-api-key`, merged `9336c53`, deployed, **confirmed working** (the 403 is gone on the next retry). Every `/v3/application/*` request now sends `x-api-key: "<keystring>:<shared_secret>"`. Used the already-configured `ETSY_CLIENT_SECRET` — no new production secret needed.
- **Etsy shop-lookup response parsing fix (2026-08-27)** — `fix/etsy-shop-lookup-single-shop-response`, **PR open, not merged**: after the x-api-key fix, OAuth still failed with `etsy_oauth_shop_not_found` — owner confirmed an active shop exists (WearYourStoriesCom, 210 listings). Root cause: `fetch_etsy_shop()` parsed the response as `{count, results: [...]}`, but this endpoint (`getShopByOwnerUserId`) returns a single `Shop` object per Etsy's own OpenAPI spec — `results` was always empty regardless of whether a shop existed. Fixed to parse the single object directly. Do not retry OAuth until this PR is merged and deployed.

## Blocked Externally (owner approval, not Etsy)

- **Live Etsy write verification** (bulk-edit apply, revert, media, variations, including the Sprint 1 follow-up's inventory-URL fix) — code-verified and mocked-test-covered only; a live write against production Etsy needs explicit owner go-ahead per session, per `CLAUDE.md` rule 2. The owner's two live attempts so far (pre- and post-PR-#89) both failed — a controlled single-listing retry should only happen after the owner explicitly asks, per the follow-up's constraints.
- **Etsy listing-video-upload endpoint** — implemented per documented endpoint shape, never tested against a live shop (see `DECISIONS.md`, "[MEDIA] Etsy listing video upload/delete implemented for real").
- **Etsy-derived external AI processing guidance** — `ALLOW_ETSY_DATA_TO_AI` stays off by default; still pending explicit written Etsy confirmation, independent of the credential issuance (see `ETSY_FINAL_APPEAL_DRAFT.md` §F, question 1).
- **Social republishing guidance** (Pinterest/Instagram auto-post) — deliberately stubbed pending the same confirmation (§F, question 4).

## Owner Action

None pending.

## Deferred

- **Enabling external AI processing for Etsy-derived data** (`ALLOW_ETSY_DATA_TO_AI=true`) — deferred pending Etsy's written confirmation that sending Etsy-derived listing content to a third-party AI provider is permitted (`ETSY_FINAL_APPEAL_DRAFT.md` §F, question 1).
- **Disabling Private Beta** — deferred until Etsy responds and live OAuth is re-verified; not an engineering decision (see `DECISIONS.md`, "[LAUNCH] Private Beta gate stays enabled until Etsy's ban is resolved").
- **Pinterest/Instagram cross-posting** (live `POST` calls) — deliberately stubbed pending Etsy's confirmation that republishing synced listing content to a third-party marketing platform is permitted (§F, question 4).
- **Stripe webhook endpoint existence/events verification** — the Stripe MCP connector has no webhook-endpoint API access; unverifiable from this tooling. Needs a manual Stripe Dashboard check.
- **Real Celery worker** — not needed at current volume; retention cleanup runs as a DO Scheduled Job instead (see `DECISIONS.md`, "[OPS] Retention scheduling uses a DO App Platform `SCHEDULED` job, not Celery"). Revisit if background-task volume grows.
- **Migration 0023 backfill precision** — pre-existing snapshot rows got a retention window measured from migration-deploy-time rather than true `created_at`; documented, not fixed (makes retention more conservative, never less) — see `ETSY_DATA_RETENTION.md` §2.
- **Old Dependabot PRs / dependency bumps** — not merged unless separately requested by the owner.

## Recently Completed

- **Etsy production credential configuration (2026-07-31):** Etsy-issued Keystring + Shared Secret for `bulk-edit-app` configured as encrypted `SECRET` env vars on `bulk-edit-prod-api` via `doctl apps update --spec` (existing `ops/app-specs/bulk-edit-prod-api.yaml` structure reused as the source of truth). Rate limit (5 QPS/5000 QPD) and OAuth scopes already matched existing code defaults exactly — no code change, no PR. Local `apps/backend/.env` synced from `deploy-production.local.env` (git-ignored, never committed, never printed). Production OAuth URL generation verified end-to-end via the live `/api/v1/etsy/authorize` endpoint. Live OAuth completion deliberately not performed — see Owner Action above. Mid-task: caught and fixed a `[regex]::Replace` count-arg bug in a helper script that had triple-duplicated env entries across the api service and both jobs; fixed with a YAML-aware Python pass and re-verified before trusting the deploy. Full detail: `CHANGELOG_AI.md`, `DECISIONS.md`.
- **Post-appeal public copy alignment (2026-07-16):** PR #64 (`fix/current-public-copy-appeal-alignment`, merge `6be4046`) neutralized remaining public AI wording (homepage hero/pricing preview, `/pricing`, `/features` metadata + safety line, FAQ, feature registry) and updated Privacy/Terms for current AI-safeguard and retention/account-deletion behavior. CI green (6/6), merged, both prod apps redeployed to `ACTIVE`, live site verified. No authenticated in-app functionality removed.
- **Post-PR-#64 production health re-verification (2026-07-16):** API health, DB connectivity, Redis connectivity, retention scheduler config/cron/command, and latest retention invocation (`ad207ee4-f05c-4038-b244-6e54bf9fd13a`, SUCCEEDED — second consecutive successful daily run) all confirmed read-only, no production changes made.
- **Documentation full-sync (2026-07-15):** consolidated `PROJECT_STATUS.md`/`TASKS.md`/`HANDOFF.md` to current-state-only; synchronized all Etsy compliance docs and the appeal draft to the confirmed-live retention scheduler and 982-test count; fixed stale Vercel/Render-as-current-hosting claims in `docs/operations/DEPLOYMENT.md`/`DNS_SSL.md`/`PRODUCTION_SMOKE_TEST.md` (now correctly point to DigitalOcean + Cloudflare, with the old plan marked superseded); merged PR #61 (retention-monitoring command fix) and PR #62 (finalized appeal draft).
- **Retention cleanup Option A (2026-07-14/15):** DO Scheduled Job live, first real execution succeeded 2026-07-15 (0 rows deleted, no errors) — see `ETSY_DATA_RETENTION.md` §2, `docs/operations/WORKERS.md`.
- **Etsy compliance + production-readiness pass (2026-07-13/14):** full audit, OAuth scope-storage bug fix, AI-data gate (`ALLOW_ETSY_DATA_TO_AI`), 30-day configurable retention, terms/privacy acceptance, self-service account deletion with a Stripe billing-safety gate (block, don't auto-cancel), 9 missing FK constraints fixed (migration `0025`), public-site marketing corrections. Merged to `main` (`435a1aa`) and deployed directly to production. Full detail: `ETSY_COMPLIANCE_AUDIT.md`, `ETSY_FEATURE_MATRIX.md`, `ETSY_PRODUCTION_READINESS.md`, `ETSY_DATA_RETENTION.md`.
- **Production Activation (2026-07-06/10):** Private Beta gate live; Stripe Live checkout validated end-to-end (zero real charges); all four price mappings confirmed. Etsy OAuth validation was blocked by app review status at the time (later escalated to Banned — see above).
- All 27 feature sprints (monorepo skeleton through Promote/Media/Video polish) — see `CHANGELOG_AI.md` for full detail per sprint.

## Backlog / Future

- Shopify integration
- Multi-language support
- Mobile app
- Affiliate program
- Public API for integrations
