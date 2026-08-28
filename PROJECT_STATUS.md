# PROJECT_STATUS.md

Single current-state source of truth. For history, see `CHANGELOG.md` (product/release) and `CHANGELOG_AI.md` (full engineering session log, Sprint 0 onward). For the next session's exact resume point, see `HANDOFF.md`. For durable architecture/product decisions, see `DECISIONS.md`.

## Current Phase

Post-launch production QA. Production is **LIVE** under Private Beta (new sign-ups paused) since 2026-07-06. **Etsy OAuth is fully live and confirmed working end-to-end**: `sekiphayit1982@gmail.com` (superuser, `pro_monthly` comp grant) has shop WearYourStoriesCom (44263504) connected with all 210 active listings synced. All planned sprints (0-27) are complete. Sprint 1 Follow-up QA (PR #91, merge `92d82c7`) deployed 2026-08-28; owner confirmed all 4 UI fixes (hover preview, decode, remove-change, footer), then ran controlled single-listing live writes: title change failed `HTTP 404` (new bug, never-before-exercised code path), price change failed `HTTP 400` (down from 404 — confirms PR #91's inventory-URL fix worked). Current work: **Bulk Edit write verification, 3rd round** (branch `fix/bulk-edit-write-verification-followup`, issue #92) — 3 fixes code-complete and test-verified as of 2026-08-28, pending PR/CI/merge/deploy — see `HANDOFF.md` for exact resume steps.

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
| Sprint 1 Follow-up QA | **Merged and deployed (2026-08-28)** — PR #91, merge `92d82c7`. Owner manually confirmed all 4 UI fixes (hover preview, listings table/detail decode, remove-change, footer). Owner's controlled live-write retest surfaced 2 new write bugs — see Bulk Edit write verification row below. |
| Bulk Edit write verification (3rd round) | **Code-complete, not yet merged (2026-08-28)** — branch `fix/bulk-edit-write-verification-followup`, issue #92. Bulk Edit preview Before/After decode fixed (`formatVal()`). Title PATCH 404 fixed — `patch_etsy_listing()` was missing `/shops/{shop_id}` (opposite direction from the prior round's inventory fix; Etsy's `updateListing` is shop-scoped). Inventory PUT 400 fixed — payload was missing Etsy-required top-level keys `price_on_property`/`quantity_on_property`/`sku_on_property`. Documented residual gap: payload still can't preserve `product_id`/`offering_id` (not stored locally) — a live retest that still 400s would mean the fetch-patch-put refactor `etsy_variation_write.py` already uses for variations is needed. No live Etsy write performed. |
| Public website | Aligned with the submitted appeal as of PR #64 (merge `6be4046`) — public AI/marketing wording neutralized, Privacy/Terms updated, feature/health public routes not exposed, sitemap clean. |

## Environment Status

- Backend tests: targeted files (`test_bulk_edit_inventory.py`, `test_bulk_edit_variation.py`) 75/75 passed on `fix/bulk-edit-write-verification-followup` (2026-08-28); `test_bulk_edit.py`/`test_bulk_edit_apply.py`/`test_bulk_edit_revert.py` 84 passed, 6 pre-existing 401-vs-403 baseline failures (no regressions). Full-repo count still 891+ as of PR #91; not re-run in full this round (targeted-only per scope).
- Frontend: `tsc --noEmit` clean, `next lint` 0 errors (pre-existing warnings only), `next build` clean (verified 2026-08-28 on `fix/bulk-edit-write-verification-followup`).
- Hosting: DigitalOcean App Platform + Cloudflare (see `docs/operations/DIGITALOCEAN_DEPLOY.md`, `CLOUDFLARE_DNS.md`).
- AI: `ALLOW_ETSY_DATA_TO_AI` defaults `false` (not overridden in production); `AI_PROVIDER=mock` in production, so no live AI provider call is possible right now regardless of the flag.
- Pricing (live, confirmed correct): Free $0/mo · Basic $19/mo ($180/yr) · Pro $49/mo ($468/yr).

## Known Blockers

- **Bulk Edit write verification (3rd round) not yet merged/deployed** — code-complete on `fix/bulk-edit-write-verification-followup`, needs PR open → CI green → merge → prod deploy → owner-approved controlled live retest. See `HANDOFF.md`.
- **Bulk Edit title/price write fixes not yet proven against a live Etsy write** — this is the *third* fix attempt on the write path (PR #89's `property_values` fix, PR #91's inventory-URL fix, and this round's title shop-scope + inventory schema-keys fixes). Each round diagnosed from code + this codebase's own already-correct sibling patterns, mocked-test coverage only, per the no-live-write constraint each round. A documented residual gap remains on the price fix (no `product_id`/`offering_id` preservation) — needs an owner-approved controlled single-listing live retest (both title and price) before assuming fully resolved. If price still 400s, the next step is the fetch-patch-put refactor (see `DECISIONS.md`).
- **HTML-entity DB backfill not run** — `apps/backend/scripts/backfill_html_entity_decode.py` written (dry-run by default) but not executed; the frontend decode fix already makes the visible symptom disappear, so this is a data-hygiene follow-up, not a blocker, pending owner approval to run `--apply`.
- Email-delivery domain verification (Resend, `bulkeditapp.com`) status not re-checked recently — see `docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md` if this becomes relevant again.

## Manual Owner Actions Required

Nothing currently blocking.

## Current Next Action

**Owner grants the internal test account a comp plan (Owner Console → Organizations), then approves a read-only re-sync validation** — expect ~210 listings to match Etsy Shop Manager. Do not create a new Etsy developer app, do not disable Private Beta, do not enable Etsy-derived external AI processing, do not perform any Etsy write, and do not submit another appeal.

## Last Updated

2026-07-31
