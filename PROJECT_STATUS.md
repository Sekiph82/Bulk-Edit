# PROJECT_STATUS.md

Single current-state source of truth. For history, see `CHANGELOG.md` (product/release) and `CHANGELOG_AI.md` (full engineering session log, Sprint 0 onward). For the next session's exact resume point, see `HANDOFF.md`. For durable architecture/product decisions, see `DECISIONS.md`.

## Current Phase

Post-credential-issuance / Private Beta operations. Production is **LIVE** under Private Beta (new sign-ups paused) since 2026-07-06. Etsy lifted the ban and granted Personal Use access for `bulk-edit-app` (credentials configured since 2026-07-31, rate limit 5 QPS / 5000 QPD). A live read-only OAuth test was attempted 2026-08-07: authorize-URL generation confirmed correct again, but Etsy's consent page rejected the redirect ("The requested redirect URL is not permitted") — the callback URL is not yet registered in the Etsy Developer Console. **Blocked on owner action**, not our code/config. All planned sprints (0-27) are complete — see `CHANGELOG_AI.md` for the full build history.

## Production Status

| Component | Status |
|---|---|
| Backend (`bulk-edit-prod-api`) | LIVE, healthy |
| Frontend (`bulk-edit-prod-web`) | LIVE, healthy |
| PostgreSQL | Connected |
| Redis | Connected |
| Alembic revision | `0025` (single head) — reconfirmed after PR #64 (no migration files changed; pre-deploy `migrate` job applied no pending upgrades) |
| Private Beta (`app.bulkeditapp.com`) | **Enabled** — new sign-ups paused, 307 → `/private-beta` on all app routes |
| Retention cleanup | **Option A live** — DO Scheduled Job `retention-cleanup`, `30 3 * * *` (03:30 UTC daily). First run succeeded 2026-07-15; **second consecutive run succeeded 2026-07-16** (03:31:12–03:31:33 UTC, invocation `ad207ee4-f05c-4038-b244-6e54bf9fd13a`). |
| Stripe | Live products/prices/env configured, validated end-to-end 2026-07-10 (controlled test account, zero real charges) |
| Etsy developer app | Ban lifted, Personal Use access granted for `bulk-edit-app`. Credentials configured on `bulk-edit-prod-api` as encrypted `SECRET` env vars since 2026-07-31. Production OAuth URL generation re-verified working 2026-08-07 (masked keystring `qvmj...fh33`, callback/scopes/PKCE all correct). **Live OAuth blocked**: Etsy's consent page rejects the redirect — callback URL not yet registered in Etsy Developer Console. Needs owner action (see Manual Owner Actions Required) before retry. |
| Public website | Aligned with the submitted appeal as of PR #64 (merge `6be4046`) — public AI/marketing wording neutralized, Privacy/Terms updated, feature/health public routes not exposed, sitemap clean. |

## Environment Status

- Backend tests: **982 passed**, 0 failed (unchanged by PR #64 — no backend files touched).
- Frontend: `tsc --noEmit` clean, `next lint` 0 errors, `next build` clean (verified again on PR #64).
- Hosting: DigitalOcean App Platform + Cloudflare (see `docs/operations/DIGITALOCEAN_DEPLOY.md`, `CLOUDFLARE_DNS.md`).
- AI: `ALLOW_ETSY_DATA_TO_AI` defaults `false` (not overridden in production); `AI_PROVIDER=mock` in production, so no live AI provider call is possible right now regardless of the flag.
- Pricing (live, confirmed correct): Free $0/mo · Basic $19/mo ($180/yr) · Pro $49/mo ($468/yr).

## Known Blockers

- **Live Etsy OAuth blocked by Etsy Developer Console config (2026-08-07).** Etsy's consent page returns "The requested redirect URL is not permitted" — `https://api.bulkeditapp.com/api/v1/etsy/callback` is not yet in the app's registered Redirect URI allowlist. Confirmed our side (env + code) is correct; no production change made since nothing here was proven wrong. Owner must add the callback URL in Etsy's console before any further live OAuth/read/write testing can happen. See `TASKS.md` → Owner Action.
- Email-delivery domain verification (Resend, `bulkeditapp.com`) status not re-checked this session — see `docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md` if this becomes relevant again.

## Manual Owner Actions Required

1. **Register the callback URL in the Etsy Developer Console**: https://www.etsy.com/developers/your-apps → `bulk-edit-app` → Redirect URI(s) → add `https://api.bulkeditapp.com/api/v1/etsy/callback` exactly (no trailing slash) → save. Currently blocking the live OAuth test.
2. **Then retry the live read-only OAuth test** (connect one owner-controlled test Etsy shop, no writes) per `TASKS.md` → Owner Action.

## Current Next Action

**Await owner confirmation that the Etsy Developer Console redirect URI is registered**, then generate a fresh production OAuth URL and retry. Do not create a new Etsy developer app, do not disable Private Beta, do not enable Etsy-derived external AI processing, do not perform any Etsy write, and do not submit another appeal. Once the redirect succeeds: verify callback/token exchange/shop connection, do read-only shop/listing fetch.

## Last Updated

2026-08-07
