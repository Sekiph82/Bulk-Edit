# PROJECT_STATUS.md

Single current-state source of truth. For history, see `CHANGELOG.md` (product/release) and `CHANGELOG_AI.md` (full engineering session log, Sprint 0 onward). For the next session's exact resume point, see `HANDOFF.md`. For durable architecture/product decisions, see `DECISIONS.md`.

## Current Phase

Post-launch production QA. Production is **LIVE** under Private Beta (new sign-ups paused) since 2026-07-06. **Etsy OAuth is fully live and confirmed working end-to-end**: `sekiphayit1982@gmail.com` (superuser, `pro_monthly` comp grant) has shop WearYourStoriesCom (44263504) connected with all 210 active listings synced. All planned sprints (0-27) are complete. **PR #100 (readiness_state_id fix) and PR #102 (Etsy rate-limit guard/backoff) both merged and deployed (2026-08-28)** — the multi-round Bulk Edit price-write bug is resolved, and Etsy write calls now retry-with-backoff plus pace per shop. **Owner then ran a 33-listing bulk price apply and a 32-listing bulk Magic Revert live (2026-08-29), both clean under the guard** — documented on `docs/hiveai-dashboard-and-tasks` (PR #101, not merged), no runtime semantics changed. Current work: **UX-01A**, an Apply/Revert loading-overlay + double-submit guard (branch `fix/bulk-edit-apply-revert-loading-guard`, frontend-only, based on `origin/main`) — code-complete and verified as of 2026-08-29, pending PR/CI/merge/deploy — see `HANDOFF.md` for exact resume steps.

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
| Etsy developer app | **Credentials received from Etsy 2026-07-31**, configured on `bulk-edit-prod-api` as encrypted `SECRET` env vars. **OAuth shop connection confirmed working end-to-end (2026-08-27)** — WearYourStoriesCom, shop ID `44263504`, connected. Issue #80 closed. **All 210 active listings now synced** (2026-08-28) under `sekiphayit1982@gmail.com` — the initial 25-listing cap was the Free plan's `max_listings` gate working as designed; fixed by granting a `pro_monthly` comp plan, which required two further bug fixes (PR #86: ops-script `DATABASE_URL` dialect; PR #87: comp grants weren't checked by the sync's plan-limit gate). |
| Sprint 1 Core QA | **Merged and deployed (2026-08-28)** — PR #89, merge `309cff0`. Owner manually verified: footer + thumbnail size OK; hover preview, HTML decode, remove-change, and the Bulk Edit price-apply write itself all still broken on manual check. |
| Sprint 1 Follow-up QA | **Merged and deployed (2026-08-28)** — PR #91, merge `92d82c7`. Owner manually confirmed all 4 UI fixes (hover preview, listings table/detail decode, remove-change, footer). Owner's controlled live-write retest surfaced 2 new write bugs. |
| Bulk Edit write verification (3rd round) | **Merged and deployed (2026-08-28)** — PR #93, merge `1c27337`. Bulk Edit preview Before/After decode fixed. Title PATCH 404 fixed (`patch_etsy_listing()` was missing `/shops/{shop_id}`) — **owner confirmed title write now succeeds live.** Inventory PUT 400 fixed with top-level schema keys — owner's live retest still got `HTTP 400` (down from 404), leading to the next row. |
| Bulk Edit price write — fetch-patch-put refactor | **Merged and deployed (2026-08-28)** — PR #94, merge `b0bc144`. Implemented `apply_single_listing_price_quantity()` (GET/mutate/PUT full inventory tree). Owner's live retest still got `HTTP 400` on a different listing — payload shape itself was still wrong, see next row. |
| Bulk Edit price write — writable payload shape fix | **Merged and deployed (2026-08-28)** — PR #96, merge `fde35aa`. New `build_writable_inventory_payload_from_tree()` (decimal price, no product_id/offering_id/listing_id, per Etsy's official docs). Owner's live retest on a third listing still got `HTTP 400` — log audit confirmed this fix's code did execute, so the payload-shape theory alone wasn't the whole story; see next row. |
| Bulk Edit price write — safe error-body diagnostics | **Merged and deployed (2026-08-28)** — PR #98, merge `b12ca31`. Diagnostics-only — surfaced the real Etsy error in the UI for the first time. Owner's live retest showed exactly why: "All offerings need readiness state." See next row for the fix. |
| Bulk Edit price write — readiness_state_id required | **Merged and deployed, owner-confirmed live success (2026-08-28)** — PR #100. `normalize_etsy_inventory_tree()` now captures `readiness_state_id` from Etsy's GET response; the writable-payload builder guarantees every offering has one, falling back to a documented placeholder only when Etsy's own response genuinely lacks one. Owner's live retest: French Bulldog listing price write succeeded end-to-end. |
| Etsy rate-limit guard/backoff | **Code-complete, not yet merged (2026-08-28)** — branch `fix/etsy-rate-limit-guard`, engineering-only. Owner's next live apply (different listing) hit `HTTP 429`. Added retry-with-backoff (honors `Retry-After`, max 3 attempts) to the write calls that previously had none (`etsy_patch`/`etsy_put`, matching `etsy_get`'s existing behavior), plus a per-shop minimum-spacing gate (`sleep_before_etsy_write`, 1100ms) at every write entry point so a multi-item apply/revert loop can't rapid-fire past Etsy's limit. Diagnostics gained `rate_limited`/`retry_after_seconds`/`final_rate_limit_exhausted`; frontend gained a distinct 429 failure category. No Etsy API call performed by Claude/Codex. Magic Revert still owner-pending (not yet run since PR #100); larger 3/10/33-listing tests remain paused until this deploys and the owner approves. |
| Public website | Aligned with the submitted appeal as of PR #64 (merge `6be4046`) — public AI/marketing wording neutralized, Privacy/Terms updated, feature/health public routes not exposed, sitemap clean. |

## Environment Status

- Backend tests: `test_bulk_edit_inventory.py`+`test_bulk_edit_apply.py`+`test_bulk_edit_revert.py`+`test_bulk_edit.py`+`test_etsy_rate_limit_guard.py` (new): 182 passed on `fix/etsy-rate-limit-guard` (2026-08-28), 8 pre-existing `*_requires_auth`/`*_blocked_when_etsy_not_configured` baseline failures confirmed present on `origin/main` before this branch too (no regressions).
- Frontend: `apps/frontend/app/(app)/bulk-edit/page.tsx` changed this round (429 failure category + retry-count messaging) — see `HANDOFF.md` for typecheck/lint/build results.
- Hosting: DigitalOcean App Platform + Cloudflare (see `docs/operations/DIGITALOCEAN_DEPLOY.md`, `CLOUDFLARE_DNS.md`).
- AI: `ALLOW_ETSY_DATA_TO_AI` defaults `false` (not overridden in production); `AI_PROVIDER=mock` in production, so no live AI provider call is possible right now regardless of the flag.
- Pricing (live, confirmed correct): Free $0/mo · Basic $19/mo ($180/yr) · Pro $49/mo ($468/yr).

## Known Blockers

- **Etsy rate-limit guard not yet merged/deployed** — code-complete on `fix/etsy-rate-limit-guard`, needs PR open → CI green → merge → prod deploy. See `HANDOFF.md`.
- **Larger bulk tests (3/10/33 listings) remain paused** until the rate-limit guard deploys and the owner explicitly approves — the owner already hit a live 429 on an unthrottled single follow-up write, so any multi-item test before this deploys risks the same failure repeatedly.
- **Magic Revert not yet run live** since the price-write fix (PR #100) — owner's planned next action, in order: Magic Revert on the French Bulldog listing, then one more single-listing price apply, then (only after the guard is deployed) a small bulk test.
- **HTML-entity DB backfill not run** — `apps/backend/scripts/backfill_html_entity_decode.py` written (dry-run by default) but not executed; the frontend decode fix already makes the visible symptom disappear, so this is a data-hygiene follow-up, not a blocker, pending owner approval to run `--apply`.
- Email-delivery domain verification (Resend, `bulkeditapp.com`) status not re-checked recently — see `docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md` if this becomes relevant again.

## Manual Owner Actions Required

Nothing currently blocking.

## Current Next Action

**Owner grants the internal test account a comp plan (Owner Console → Organizations), then approves a read-only re-sync validation** — expect ~210 listings to match Etsy Shop Manager. Do not create a new Etsy developer app, do not disable Private Beta, do not enable Etsy-derived external AI processing, do not perform any Etsy write, and do not submit another appeal.

## Last Updated

2026-07-31
