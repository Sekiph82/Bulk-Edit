# PROJECT_STATUS.md

Single current-state source of truth. For history, see `CHANGELOG.md` (product/release) and `CHANGELOG_AI.md` (full engineering session log, Sprint 0 onward). For the next session's exact resume point, see `HANDOFF.md`. For durable architecture/product decisions, see `DECISIONS.md`.

## Current Phase

Post-launch production QA. Production is **LIVE** under Private Beta (new sign-ups paused) since 2026-07-06. **Etsy OAuth is fully live and confirmed working end-to-end**: `sekiphayit1982@gmail.com` (superuser, `pro_monthly` comp grant) has shop WearYourStoriesCom (44263504) connected with all 210 active listings synced. All planned sprints (0-27) are complete. PR #100 (readiness_state_id fix), PR #102 (Etsy rate-limit guard/backoff), and PR #103 (Apply/Revert loading overlay + double-submit guard, UX-01A) are all merged and deployed (2026-08-28/29) — the multi-round Bulk Edit price-write bug is resolved, Etsy write calls retry-with-backoff and pace per shop, and the owner visually confirmed the Apply/Revert overlay working in production. Owner then ran a 33-listing bulk price apply and a 32-listing bulk Magic Revert live, both clean — documented on `docs/hiveai-dashboard-and-tasks` (PR #101, not merged). **New critical bug found and fixed this round:** the Bulk Edit apply gate used the raw (Free-defaulting) subscription plan instead of the comp-grant-aware effective plan, so a Pro comp-grant account was blocked at the Free plan's 10/month ceiling instead of Pro's 5000 — same bug independently duplicated in 4 other feature gates (AI tools, Dynamic Pricing, scheduled jobs, `/billing/usage`), all fixed together. **Also this round: UX-01B**, a product detail page (`/listings/[listingId]`) with safe launch-only actions (no direct Etsy writes). PR #104 has since been independently audited (verdict CONDITIONAL, 0 BLOCKER/MAJOR, 1 MINOR + 1 NOTE, both recorded, neither blocking) and `TASKS.md` converted to the H!veAI-style milestone ledger (`docs/hiveai-dashboard-and-tasks`, PR #101, still not merged). Account-01 (PR #105) has since merged and deployed — Account Center (`/account`, 11-route subnav), Connected Shops (relocated from `/shops`), customer-safe Plan/Billing/Usage/Credits UI. **Current work: UX-01D**, owner visual QA remediation — real bugs fixed: Media page's "Failed to load listings" (a `Promise.all` all-or-nothing failure masking a working listings fetch), Bulk Create's false "Connect your Etsy shop first" (the status endpoint was hardcoded, never checked real connection state), and product-detail images always blank (`thumbnail_url` was never patched onto the single-item endpoint the way the list endpoint does it). Plus: Magic Revert added to nav (new placeholder route), product-detail card layout fixed (two independent columns instead of a row-pairing CSS grid), a truthful Performance metrics card (`lifetime_views`/`lifetime_favorites` real, monthly/sales metrics explicitly unavailable, never faked), and 3 cross-sell recommendation banners removed. Branch `fix/ux01d-owner-visual-remediation`, based on `origin/main` past PR #105's `1bc563e` — see `HANDOFF.md` for exact resume steps and PR/deploy status.

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
| Etsy rate-limit guard/backoff | **Merged and deployed (2026-08-28)** — PR #102, merge `c68b4649`. Retry-with-backoff (honors `Retry-After`, max 3 attempts) on Etsy write calls plus a per-shop 1100ms write-spacing gate. Owner's 33-listing bulk apply + 32-listing bulk revert both ran clean under it. |
| Apply/Revert loading overlay + double-submit guard (UX-01A) | **Merged and deployed, owner-verified in production (2026-08-29)** — PR #103, merge `5b195ea8`. Owner screenshot confirms the blocking overlay and copy appear correctly during Apply. |
| Pro comp-grant bulk edit gate fix | **This round (2026-08-29)** — `check_usage_limit()` and 4 sibling feature gates (AI tools, Dynamic Pricing, scheduled jobs, `/billing/usage`) were reading the raw Free-defaulting `Subscription.plan` instead of the comp-grant-aware effective plan. A Pro comp-grant account was blocked at Free's 10/month bulk-edit ceiling instead of Pro's 5000. Fixed at the root (`get_effective_plan()`), error messages now state usage/limit context. See `DECISIONS.md`/`CHANGELOG_AI.md` for full root-cause writeup. |
| Product detail page (UX-01B) | **This round (2026-08-29)** — new route `/listings/[listingId]`, safe launch-only actions (all deep-link to Bulk Edit, no direct Etsy writes). Listings page row/title click now opens it; a small Quick View icon keeps the existing drawer available. |
| Public website | Aligned with the submitted appeal as of PR #64 (merge `6be4046`) — public AI/marketing wording neutralized, Privacy/Terms updated, feature/health public routes not exposed, sitemap clean. |

## Environment Status

- Backend tests: `test_billing.py`+`test_bulk_edit_apply.py`+`test_ai_tools.py`+`test_dynamic_pricing.py`+`test_scheduled_jobs.py`: **171 passed of 180 collected** on `main@60f9734` (independently re-verified 2026-08-29 during the PR #104 audit — corrects an earlier self-reported "176 passed" that didn't match either the pass count or the collected total), 9 pre-existing `*_requires_auth`/`*_blocked_when_etsy_not_configured` baseline failures confirmed present on `origin/main` before the PR #104 branch too (no regressions). Frontend Account-01 round: no backend files changed, no backend re-run needed.
- Frontend: `tsc --noEmit` clean, `next lint` 0 errors, `next build` clean — new route `/listings/[listingId]` plus `listings/page.tsx` and `listing-health/page.tsx` changed this round.
- Hosting: DigitalOcean App Platform + Cloudflare (see `docs/operations/DIGITALOCEAN_DEPLOY.md`, `CLOUDFLARE_DNS.md`).
- AI: `ALLOW_ETSY_DATA_TO_AI` defaults `false` (not overridden in production); `AI_PROVIDER=mock` in production, so no live AI provider call is possible right now regardless of the flag.
- Pricing (live, confirmed correct): Free $0/mo · Basic $19/mo ($180/yr) · Pro $49/mo ($468/yr).

## Known Blockers

- **Pro comp-grant bulk edit gate fix not yet merged/deployed** — code-complete on `fix/billing-gate-and-product-detail-page`, needs PR open → CI green → merge → prod deploy. See `HANDOFF.md`.
- **HTML-entity DB backfill not run** — `apps/backend/scripts/backfill_html_entity_decode.py` written (dry-run by default) but not executed; the frontend decode fix already makes the visible symptom disappear, so this is a data-hygiene follow-up, not a blocker, pending owner approval to run `--apply`.
- Email-delivery domain verification (Resend, `bulkeditapp.com`) status not re-checked recently — see `docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md` if this becomes relevant again.

## Manual Owner Actions Required

Nothing currently blocking.

## Current Next Action

**Merge and deploy `fix/billing-gate-and-product-detail-page`, verify health/route status, then owner retries the single-listing price apply that was previously blocked** — it should now succeed against the correct Pro comp-grant limit. Do not create a new Etsy developer app, do not disable Private Beta, do not enable Etsy-derived external AI processing, do not perform any Etsy write from this session, and do not submit another appeal.

## Last Updated

2026-08-29
