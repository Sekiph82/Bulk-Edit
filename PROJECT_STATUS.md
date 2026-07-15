# PROJECT_STATUS.md

Single current-state source of truth. For history, see `CHANGELOG.md` (product/release) and `CHANGELOG_AI.md` (full engineering session log, Sprint 0 onward). For the next session's exact resume point, see `HANDOFF.md`. For durable architecture/product decisions, see `DECISIONS.md`.

## Current Phase

Post-launch operations. Production is **LIVE** under Private Beta (new sign-ups paused) since 2026-07-06, running the Etsy-compliance deployment since 2026-07-14. All planned sprints (0-27, incl. Productization UI, Landing Animation, CI/CD, monitoring) are complete — see `CHANGELOG_AI.md` for the full build history. Current work is compliance/appeal/documentation, not feature development.

## Production Status

| Component | Status |
|---|---|
| Backend (`bulk-edit-prod-api`) | LIVE, healthy |
| Frontend (`bulk-edit-prod-web`) | LIVE, healthy |
| PostgreSQL | Connected |
| Redis | Connected |
| Alembic revision | `0025` (single head) |
| Private Beta (`app.bulkeditapp.com`) | **Enabled** — new sign-ups paused, 307 → `/private-beta` on all app routes |
| Retention cleanup | **Option A live** — DO Scheduled Job `retention-cleanup`, `30 3 * * *` (03:30 UTC daily). First real execution succeeded 2026-07-15, 03:31:29–03:31:31 UTC, 0 rows deleted (all 4 tables), no errors. |
| Stripe | Live products/prices/env configured, validated end-to-end 2026-07-10 (controlled test account, zero real charges) |
| Etsy developer app | **Banned** (escalated 2026-07-13, no reason given by Etsy) |

## Environment Status

- Backend tests: **982 passed**, 0 failed (targeted retention: 7/7).
- Frontend: `tsc --noEmit` clean, `next lint` 0 errors, `next build` clean.
- Hosting: DigitalOcean App Platform + Cloudflare (see `docs/operations/DIGITALOCEAN_DEPLOY.md`, `CLOUDFLARE_DNS.md`). The original Vercel + Render plan was superseded before it was ever provisioned — see `DECISIONS.md`.
- AI: `ALLOW_ETSY_DATA_TO_AI` defaults `false` (not overridden in production); `AI_PROVIDER=mock` in production, so no live AI provider call is possible right now regardless of the flag.
- Pricing (live, confirmed correct): Free $0/mo · Basic $19/mo ($180/yr) · Pro $49/mo ($468/yr).

## Known Blockers

- **Etsy developer app "bulk-edit-app" is Banned**, no reason given. Blocks all live Etsy OAuth/API testing. Appeal fully drafted (`ETSY_FINAL_APPEAL_DRAFT.md`) but **not submitted** — requires owner review and explicit send.
- Email-delivery domain verification (Resend, `bulkeditapp.com`) status not re-checked this session — see `docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md` if this becomes relevant again.

## Manual Owner Actions Required

1. Review `ETSY_FINAL_APPEAL_DRAFT.md` in full, work through its §G pre-submission checklist (includes a manual in-browser re-check of Etsy's trademark-disclaimer wording — automated fetches of etsy.com legal pages are bot-blocked), fill in `[Owner name]`, and send it from the account/inbox that manages the Etsy developer app.
2. Nothing else is currently blocking — no other owner action is outstanding.

## Current Next Action

Owner reviews and (if approved) submits the Etsy appeal. No further engineering work is blocking that step. Once Etsy responds: re-test live OAuth, live Etsy writes, and the listing-video-upload endpoint (never exercised live — see `DECISIONS.md`).

## Last Updated

2026-07-15
