# PROJECT_STATUS.md

Single current-state source of truth. For history, see `CHANGELOG.md` (product/release) and `CHANGELOG_AI.md` (full engineering session log, Sprint 0 onward). For the next session's exact resume point, see `HANDOFF.md`. For durable architecture/product decisions, see `DECISIONS.md`.

## Current Phase

Post-launch production QA. Production is **LIVE** under Private Beta (new sign-ups paused) since 2026-07-06. **Etsy OAuth is fully live and confirmed working end-to-end**: `sekiphayit1982@gmail.com` (superuser, `pro_monthly` comp grant) has shop WearYourStoriesCom (44263504) connected with all 210 active listings synced. All planned sprints (0-27) are complete. **PR #100 (merge `c880c91`) deployed 2026-08-28 and the owner's live retest succeeded** — French Bulldog listing, `price_amount` 6000→6288, confirmed on both Etsy Shop Manager (`$62.88`) and Bulk Edit Listings (`USD 62.88`) after sync. The multi-round Bulk Edit price-write payload/schema problem (PR #89 through #100) is resolved and owner-verified. A follow-up test hit Etsy's `HTTP 429` per-second rate limit on a different listing, and **PR #102 (merge `c68b4649`) shipped a rate-limit guard/backoff (2026-08-28)** — retry-with-backoff on Etsy writes plus per-shop write pacing. **Owner then ran a 33-listing bulk price apply and a 32-listing bulk Magic Revert live (2026-08-29), both clean under the new guard**: apply `completed_with_errors` (Success 32/Failed 0/Skipped 1, the 1 skip being a correct no-op — already at target value), revert `completed` (Restored 32/Failed 0/Skipped 0), Etsy Shop Manager confirmed both price directions. This is documentation only — no frontend/backend status wording or `completed_with_errors`/skipped semantics changed. **Current work: UX-01A**, a runtime fix for a newly observed issue — the Apply/Revert confirmation modal stays interactable during an in-flight write, risking duplicate submits. **Task tracking is in `TASKS.md`** (canonical sprint roadmap on branch `docs/hiveai-dashboard-and-tasks`, PR #101, not yet merged) — see it for current sprint detail; `HANDOFF.md` carries the short resume note.

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
| Bulk Edit price write — readiness_state_id required | **Merged and deployed (2026-08-28)** — PR #100, merge `c880c91`. **Owner's live retest succeeded** — French Bulldog listing, Success 1/Failed 0/Skipped 0, confirmed on Etsy (`$62.88`) and in-app (`USD 62.88`). The price-write payload/schema problem is resolved. |
| Etsy rate-limit guard/backoff | **Merged and deployed (2026-08-28)** — PR #102, merge `c68b4649`. Retry-with-backoff on Etsy writes (honors `Retry-After`, max 3 attempts), per-shop 1100ms write-spacing gate, dedicated 429 UI failure category. |
| Bulk apply/revert owner verification (33/32 listings) | **Owner-verified live (2026-08-29), documentation only.** 33-listing price apply: `completed_with_errors`, Success 32/Failed 0/Skipped 1 (correct no-op). 32-listing Magic Revert: `completed`, Restored 32/Failed 0/Skipped 0. Etsy Shop Manager confirmed both directions (`$60.00`↔`$62.88`). No frontend/backend semantics changed as part of this — see `TASKS.md` 1.11/1.12/2.1/2.4/2.6. |
| Apply/Revert loading overlay + double-submit guard (UX-01A) | **In progress (2026-08-29)** — branch `fix/bulk-edit-apply-revert-loading-guard`. Fixes a newly observed issue: the confirmation modal stayed interactable during an in-flight write. |
| Public website | Aligned with the submitted appeal as of PR #64 (merge `6be4046`) — public AI/marketing wording neutralized, Privacy/Terms updated, feature/health public routes not exposed, sitemap clean. |

## Environment Status

- Backend tests: `test_bulk_edit_inventory.py` 67/67 passed on `fix/inventory-readiness-state-required` (2026-08-28). `test_bulk_edit_variation.py`/`test_bulk_edit_apply.py`/`test_bulk_edit_revert.py`/`test_bulk_edit.py`: 133 passed, 6 pre-existing 401-vs-403 baseline failures (no regressions).
- Frontend: `tsc --noEmit` clean, `next lint` 0 errors (pre-existing warnings only), `next build` clean — no frontend files changed this round (last verified on PR #98).
- Hosting: DigitalOcean App Platform + Cloudflare (see `docs/operations/DIGITALOCEAN_DEPLOY.md`, `CLOUDFLARE_DNS.md`).
- AI: `ALLOW_ETSY_DATA_TO_AI` defaults `false` (not overridden in production); `AI_PROVIDER=mock` in production, so no live AI provider call is possible right now regardless of the flag.
- Pricing (live, confirmed correct): Free $0/mo · Basic $19/mo ($180/yr) · Pro $49/mo ($468/yr).

## Known Blockers

- **Apply/Revert double-submit risk (UX-01A, in progress)** — the confirmation modal stays interactable during an in-flight write; owner clicked confirm 4-5 times mid-operation on the live 2026-08-29 test. Fix in progress on `fix/bulk-edit-apply-revert-loading-guard`.
- **3-listing and 10-listing batch sizes, and non-price bulk fields, remain unverified** — the 33-listing case (largest) is proven for price; smaller sizes and other fields are not blockers but are still open Sprint 2 test gaps.
- PR #101 (`docs/hiveai-dashboard-and-tasks`) restructures `TASKS.md` into the canonical sprint roadmap — open, not yet merged, intentionally.
- **HTML-entity DB backfill not run** — `apps/backend/scripts/backfill_html_entity_decode.py` written (dry-run by default) but not executed; the frontend decode fix already makes the visible symptom disappear, so this is a data-hygiene follow-up, not a blocker, pending owner approval to run `--apply`.
- Email-delivery domain verification (Resend, `bulkeditapp.com`) status not re-checked recently — see `docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md` if this becomes relevant again.

## Manual Owner Actions Required

Nothing currently blocking.

## Current Next Action

**UX-01A (Apply/Revert loading overlay + double-submit guard)** is in progress on `fix/bulk-edit-apply-revert-loading-guard`. After it ships: owner may run 3-listing and 10-listing batch tests at lower risk; UX-01B (product detail page) is next in the roadmap. Do not create a new Etsy developer app, do not disable Private Beta, do not enable Etsy-derived external AI processing, do not perform any Etsy write from this session, and do not submit another appeal.

## Last Updated

2026-08-29
