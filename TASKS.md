# TASKS.md — Active Work

Legend: `[ ]` todo · `[~]` in progress · `[x]` done

Full sprint-by-sprint build history (Sprint 0 through Sprint 27, all DevOps fixes, the Vercel/Render → DigitalOcean hosting migration) lives in `CHANGELOG_AI.md` — not repeated here. This file tracks only what's currently active, blocked, or pending.

---

## Current Phase

Post-credential-issuance / Private Beta operations. All planned feature sprints are complete. Etsy issued new developer-app credentials 2026-07-31; they are configured in production and OAuth URL generation is verified. Current focus: awaiting owner approval for a live OAuth test.

## In Progress

None.

## Recently Completed

- **Private Beta allows sign-in (2026-08-27)** — `fix/private-beta-allow-signin`: Private Beta now blocks only registration (`/register`, `/signup`, `/get-started`); sign-in and the authenticated app pass through, and the Etsy OAuth callback's `/shops?connected=true`/`?error=...` result is no longer masked by the beta gate. See `CHANGELOG_AI.md` for full detail.
- **Etsy OAuth callback safe categorized logging (2026-08-27)** — `fix/etsy-oauth-safe-callback-logging`: the previously-bare `except Exception` in `/etsy/callback` now logs one of 11 safe categories (`etsy_oauth_state_not_found`, `_token_exchange_failed`, `_shop_not_found`, etc.) with no code/state/token values. Browser-visible behavior unchanged (`?connected=true` / `?error=etsy_connect_failed`).
- **doctl auth restored (2026-08-27)** — token re-supplied from `deploy-production.local.env` directly into doctl's local config, never printed/argv'd. `doctl account get` confirmed working.
- **Etsy OAuth root cause found + defensive hardening shipped (2026-08-27)** — production logs showed `etsy_oauth_shop_lookup_failed`, Etsy's shop-lookup endpoint returning 403 after a successful token exchange. Diagnosed at the time as likely a Personal Use access-tier restriction (issue #80) — `user_id` derivation confirmed correct against Etsy's own docs. Shipped `fix/etsy-oauth-user-id-validation` anyway: validates `user_id` is present/numeric before calling Etsy, new category `etsy_oauth_user_id_missing_or_invalid`. Superseded by the finding below.
- **Etsy x-api-key header format fix (2026-08-27)** — `fix/etsy-oauth-shop-lookup-x-api-key`, **PR open, not merged**: found the actual documented requirement — every `/v3/application/*` request needs `x-api-key: "<keystring>:<shared_secret>"`, not the keystring alone. Fixed across all 6 call sites (was also silently broken/missing in `etsy_sync.py`'s 4 read calls, never exercised live before). Uses the already-configured `ETSY_CLIENT_SECRET` (live in production since 2026-07-31, never wired into code) — **no new production secret needed**. This is now the leading root-cause candidate, ahead of the access-tier hypothesis. Do not retry OAuth until this PR is merged and deployed.

## Blocked Externally (Etsy, not owner or engineering)

- **Etsy OAuth shop lookup 403 (issue #80)** — `GET /v3/application/users/{user_id}/shops` returns 403 after a successful token exchange. Leading hypothesis as of 2026-08-27: malformed `x-api-key` header (fix above, PR open). Fallback hypothesis if the header fix doesn't resolve it on the next attempt: Personal Use access-tier restriction — needs an Etsy Developer Support answer (message drafted, see issue #80 / `CHANGELOG_AI.md`) or a retry with an Etsy account confirmed to own an active shop. **Do not retry OAuth until the header-fix PR is merged and deployed.**

## Blocked Externally (owner approval, not Etsy)

- **Live Etsy OAuth completion** — credentials configured and authorize-URL generation verified in production 2026-07-31; connecting a real shop needs explicit owner go-ahead (see Owner Action below), not another Etsy response.
- **Live Etsy write verification** (bulk-edit apply, revert, media, variations) — code-verified only, blocked on the same live-OAuth approval above.
- **Etsy listing-video-upload endpoint** — implemented per documented endpoint shape, never tested against a live shop (see `DECISIONS.md`, "[MEDIA] Etsy listing video upload/delete implemented for real").
- **Etsy-derived external AI processing guidance** — `ALLOW_ETSY_DATA_TO_AI` stays off by default; still pending explicit written Etsy confirmation, independent of the credential issuance (see `ETSY_FINAL_APPEAL_DRAFT.md` §F, question 1).
- **Social republishing guidance** (Pinterest/Instagram auto-post) — deliberately stubbed pending the same confirmation (§F, question 4).

## Owner Action

- **Approve a live OAuth test** when ready: confirm the callback URL registered in the Etsy Developer Console exactly matches `https://api.bulkeditapp.com/api/v1/etsy/callback`, confirm a test shop is available, confirm no write action will run — then give explicit go-ahead to connect it (read-only verification only).

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
