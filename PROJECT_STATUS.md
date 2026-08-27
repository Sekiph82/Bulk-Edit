# PROJECT_STATUS.md

Single current-state source of truth. For history, see `CHANGELOG.md` (product/release) and `CHANGELOG_AI.md` (full engineering session log, Sprint 0 onward). For the next session's exact resume point, see `HANDOFF.md`. For durable architecture/product decisions, see `DECISIONS.md`.

## Current Phase

Post-credential-issuance / Private Beta operations. Production is **LIVE** under Private Beta (new sign-ups paused) since 2026-07-06. Etsy issued new developer-app credentials for `bulk-edit-app` on 2026-07-31 (owner received Keystring + Shared Secret directly, rate limit 5 QPS / 5000 QPD); credentials are now configured in production and OAuth URL generation is verified working. **Live OAuth completion (connecting a real shop) has not yet been performed** — pending explicit owner approval. All planned sprints (0-27) are complete — see `CHANGELOG_AI.md` for the full build history. Current work is credential configuration and verification, not feature development.

## Production Status

| Component | Status |
|---|---|
| Backend (`bulk-edit-prod-api`) | LIVE, healthy |
| Frontend (`bulk-edit-prod-web`) | LIVE, healthy |
| PostgreSQL | Connected |
| Redis | Connected |
| Alembic revision | `0025` (single head) — reconfirmed after PR #64 (no migration files changed; pre-deploy `migrate` job applied no pending upgrades) |
| Private Beta (`app.bulkeditapp.com`) | **Enabled** — registration paused (`/register`, `/signup`, `/get-started` → `/private-beta`). Sign-in and the rest of the authenticated app pass through as of `fix/private-beta-allow-signin` (2026-08-27) — see `CHANGELOG_AI.md`. |
| Retention cleanup | **Option A live** — DO Scheduled Job `retention-cleanup`, `30 3 * * *` (03:30 UTC daily). First run succeeded 2026-07-15; **second consecutive run succeeded 2026-07-16** (03:31:12–03:31:33 UTC, invocation `ad207ee4-f05c-4038-b244-6e54bf9fd13a`). |
| Stripe | Live products/prices/env configured, validated end-to-end 2026-07-10 (controlled test account, zero real charges) |
| Etsy developer app | **Credentials received from Etsy 2026-07-31** (`bulk-edit-app`, rate limit 5 QPS / 5000 QPD), configured on `bulk-edit-prod-api` as encrypted `SECRET` env vars. Production OAuth URL generation verified. **Two root causes found and fixed 2026-08-27:** (1) `x-api-key` header was sent as `<keystring>` alone instead of Etsy's documented `<keystring>:<shared_secret>` — fixed, merged `9336c53`, **confirmed working** (next retry no longer 403'd). (2) After that fix, `etsy_oauth_shop_not_found` on retry despite owner confirming an active shop (WearYourStoriesCom, 210 listings) — traced to `fetch_etsy_shop()` parsing the response as a paginated list when Etsy's `getShopByOwnerUserId` actually returns a single `Shop` object. Fix (`fix/etsy-shop-lookup-single-shop-response`, **PR open, not yet merged**). No shop connected yet (`total_shops=0`). **Do not retry OAuth until this PR is merged and deployed.** |
| Public website | Aligned with the submitted appeal as of PR #64 (merge `6be4046`) — public AI/marketing wording neutralized, Privacy/Terms updated, feature/health public routes not exposed, sitemap clean. |

## Environment Status

- Backend tests: **982 passed**, 0 failed (unchanged by PR #64 — no backend files touched).
- Frontend: `tsc --noEmit` clean, `next lint` 0 errors, `next build` clean (verified again on PR #64).
- Hosting: DigitalOcean App Platform + Cloudflare (see `docs/operations/DIGITALOCEAN_DEPLOY.md`, `CLOUDFLARE_DNS.md`).
- AI: `ALLOW_ETSY_DATA_TO_AI` defaults `false` (not overridden in production); `AI_PROVIDER=mock` in production, so no live AI provider call is possible right now regardless of the flag.
- Pricing (live, confirmed correct): Free $0/mo · Basic $19/mo ($180/yr) · Pro $49/mo ($468/yr).

## Known Blockers

- **Live Etsy OAuth completion not yet performed.** Credentials are configured and the authorize-URL step is verified in production, but no real shop has been connected — needs explicit owner approval per `TASKS.md` → Owner Action before the connect flow, live reads, or the never-tested-live video-upload endpoint can be exercised.
- Email-delivery domain verification (Resend, `bulkeditapp.com`) status not re-checked this session — see `docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md` if this becomes relevant again.

## Manual Owner Actions Required

1. **Approve a live OAuth test** (connect one real test Etsy shop, read-only — no writes) when ready, per `TASKS.md` → Owner Action. Confirm first that the callback URL registered in the Etsy Developer Console exactly matches `https://api.bulkeditapp.com/api/v1/etsy/callback`.
2. Nothing else is currently blocking.

## Current Next Action

**Await owner approval for a live OAuth test.** Do not create a new Etsy developer app, do not disable Private Beta, do not enable Etsy-derived external AI processing, do not perform any Etsy write, and do not submit another appeal. Once approved: connect one test shop, verify token exchange, re-verify live reads.

## Last Updated

2026-07-31
