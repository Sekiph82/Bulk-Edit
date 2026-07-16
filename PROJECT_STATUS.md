# PROJECT_STATUS.md

Single current-state source of truth. For history, see `CHANGELOG.md` (product/release) and `CHANGELOG_AI.md` (full engineering session log, Sprint 0 onward). For the next session's exact resume point, see `HANDOFF.md`. For durable architecture/product decisions, see `DECISIONS.md`.

## Current Phase

Post-appeal waiting period / Private Beta operations. Production is **LIVE** under Private Beta (new sign-ups paused) since 2026-07-06. The Etsy appeal has been **submitted by the owner**; the project is now waiting on Etsy's response. All planned sprints (0-27) are complete — see `CHANGELOG_AI.md` for the full build history. PR #64 (2026-07-16) aligned the public website with the submitted appeal (neutralized remaining public AI wording, updated Privacy/Terms) — no authenticated in-app functionality was changed. Current work is monitoring/documentation only, not feature development.

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
| Etsy developer app | **Banned**, no reason given. **Appeal submitted by owner** — awaiting Etsy's response. |
| Public website | Aligned with the submitted appeal as of PR #64 (merge `6be4046`) — public AI/marketing wording neutralized, Privacy/Terms updated, feature/health public routes not exposed, sitemap clean. |

## Environment Status

- Backend tests: **982 passed**, 0 failed (unchanged by PR #64 — no backend files touched).
- Frontend: `tsc --noEmit` clean, `next lint` 0 errors, `next build` clean (verified again on PR #64).
- Hosting: DigitalOcean App Platform + Cloudflare (see `docs/operations/DIGITALOCEAN_DEPLOY.md`, `CLOUDFLARE_DNS.md`).
- AI: `ALLOW_ETSY_DATA_TO_AI` defaults `false` (not overridden in production); `AI_PROVIDER=mock` in production, so no live AI provider call is possible right now regardless of the flag.
- Pricing (live, confirmed correct): Free $0/mo · Basic $19/mo ($180/yr) · Pro $49/mo ($468/yr).

## Known Blockers

- **Etsy developer app "bulk-edit-app" is Banned**, no reason given. Appeal has been submitted; **awaiting Etsy's response** — this is the only blocker on live Etsy OAuth/API/write/video-upload verification. Do not submit a duplicate appeal; do not contact Etsy again unless the owner explicitly decides to.
- Email-delivery domain verification (Resend, `bulkeditapp.com`) status not re-checked this session — see `docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md` if this becomes relevant again.

## Manual Owner Actions Required

1. **Record the Etsy appeal's exact submission timestamp and any case/ticket number**, if not already captured — see `ETSY_FINAL_APPEAL_DRAFT.md` submission-status header.
2. **When Etsy responds**, forward the response for next-step planning (do not act on it unilaterally, and do not re-test live Etsy OAuth/writes until the ban is confirmed lifted).
3. Nothing else is currently blocking.

## Current Next Action

**Wait for Etsy's response.** Do not create a new Etsy developer app, do not disable Private Beta, do not enable Etsy-derived external AI processing, and do not attempt live Etsy OAuth/write until Etsy access is restored. When Etsy responds, record their answer exactly before deciding next steps.

## Last Updated

2026-07-16
