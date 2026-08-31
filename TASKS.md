# BULK EDIT MASTER TASKS

Legend: `[x]` validated complete, `[~]` active/in progress, `[ ]` planned/pending, `[!]` blocked.

Package numbering such as `M08.01`, `M08.02`, etc. is task/audit decomposition only. It does **not** mean a milestone must be split into separate Claude/Codex prompts. A milestone may still be implemented from one whole-milestone prompt.

## Canonical tracking rules

- This file is the canonical detailed milestone/task ledger.
- `ROADMAP.md` mirrors milestone scope/dependencies at roadmap level for the historical v1.0-v1.3 platform build (pre-milestone-numbering); it does not override this file for current execution order.
- `.hiveai/PROJECT_DASHBOARD.md` is a pointer/manifest, not a duplicated task ledger.
- `docs/prompts/` (or `docs/bulk-edit/prompts/`) contains authoritative builder prompts if/when created.
- `docs/codex-logs/` and `C:\Users\sekip\Desktop\bulkeditapp logs\` contain builder execution claims/evidence logs.
- `docs/audits/` contains independent strict audits and final acceptance decisions if/when created.
- Builder logs are claims, not acceptance evidence.
- Claude/Codex self-reports are not acceptance evidence.
- Owner manual verification can be acceptance evidence only when recorded clearly as owner acceptance.
- Production route/health checks are evidence only for the checked routes, not proof of untested workflows.
- Historical failed prompts/logs/audits remain immutable and do not become active tasks again unless an independent later audit explicitly reopens a production defect.
- Etsy live tests are owner-run only. Claude/Codex must not call the Etsy API directly unless the owner explicitly approves that exact task.
- No secrets in docs/logs: never print/commit Etsy Shared Secret, Client Secret, OAuth code/state, access/refresh tokens, DigitalOcean token, raw Authorization, raw x-api-key, cookies, raw env values, or database URLs.
- Production writes require staged verification (single item, then revert, then small batch, then larger batch) with item-level success/failed reporting and safe logs.
- Merging to `main` triggers production deploy for both apps, even docs-only merges — prefer PR review before merge.

## Current truth

- Production is **LIVE** under Private Beta (`app.bulkeditapp.com`); registration paused, sign-in allowed.
- Etsy OAuth and shop connection work end-to-end; `WearYourStoriesCom` connected under `sekiphayit1982@gmail.com` (`pro_monthly` comp grant).
- 210 active listings synced.
- Title write verified live (PR #93).
- Bulk Edit price write fixed after a multi-round payload/schema saga (PR #89 → #100, root cause: missing `readiness_state_id`), owner-verified live.
- PR #102 (Etsy rate-limit guard/backoff) merged and deployed — retry-with-backoff on Etsy writes, per-shop write pacing.
- Owner verified a 33-listing bulk price apply: 32 updated, 1 skipped/no-op (already at target value), 0 failed. Etsy confirmed `$60.00` → `$62.88`.
- Owner verified Magic Revert on the same result: 32 restored, 0 failed, 0 skipped. Etsy confirmed `$62.88` → `$60.00`.
- PR #103 (Apply/Revert loading overlay + double-submit guard, UX-01A) merged and deployed; owner visually confirmed the overlay in production.
- PR #104 (effective-plan usage-gate fix + UX-01B product detail page): merged and deployed. **Independent audit verdict: CONDITIONAL** — 0 BLOCKER, 0 MAJOR, 1 MINOR (builder self-reported test-pass count was numerically wrong, though the underlying pass/fail claim re-verified true), 1 NOTE (no live-browser click-through performed yet, already self-disclosed). See `docs/audits/` / `bulkeditapp logs` audit file `2026-08-29_13-31_AUDIT_PR104_billing_gate_product_detail.md`. Per this file's own gate rule, CONDITIONAL-with-only-MINOR/NOTE items closes the implementation as complete while recording the open items rather than claiming unconditional PASS.
- **PR #101 (`docs(hiveai): add dashboard manifest and master sprint roadmap`) is merged into `main`** as `092e02f9303b9c824cc816176e485d91720cc730`. This H!veAI-format `TASKS.md` is now canonical on `main` (no longer a docs-branch-only draft). `.hiveai/PROJECT_DASHBOARD.md` is also on `main` and remains pointer-only (not a duplicated task ledger).
- **PR #107 (`feat(revert): add Magic Revert history and activity audit`, M16/UX-02A) is merged into `main`** as `7ee420dc1bca90b812ab7e48becece4e0ff241c0`, deployed, and route-verified. `/magic-revert` now shows real apply-job history (not a placeholder); `/account/activity` shows real Bulk Edit Apply and Magic Revert rows sourced from that same history. Prior-job Magic Revert execution is enabled via the existing org-scoped revert endpoint (not just the most-recent job). **`PLAN_LIMITS["can_use_magic_revert"]` server-side enforcement (M08.07/M16.06) is now closed** — see below.
- **Magic Revert plan-gate enforcement closed (M08.07/M16.06).** `validate_apply_job_revertable()` and `get_revert_eligibility_map()` now both check the effective plan's `can_use_magic_revert` (comp-grant aware) — Free plan is blocked with `403` on the direct endpoint and `can_revert=false` in history; Pro (including comp-grant Pro) is allowed. Checked last in precedence order, so an already-reverted job still reports "Already reverted.", not plan-blocked, and no cross-org job existence leaks through the gate.
- **Account-01 (M11) shipped as PR #105** (Account Center `/account` 11-route subnav, Connected Shops relocated from `/shops`, customer-safe Plan/Billing/Usage/Credits UI) — merged and deployed 2026-08-29. M11 checkboxes below are now backfilled against that PR.
- **UX-01D (owner visual QA remediation, PR #106) addressed 6 owner-reported issues** — Magic Revert nav placeholder (since superseded by the real history page, PR #107), Media page listings-load bug, Bulk Create false shop-gate, product-detail image/layout fixes, truthful Performance metrics (no fake data), 3 recommendation banners removed. See M09.06, M13.01, M13.07, M15.01, M16.02, M16.03.
- **PR #108** (docs cleanup after PR #101/#107, stale pre-merge wording fixed) merged — see `2026-08-30_RETROSPECTIVE_pr108-docs-cleanup.md` in `bulkeditapp logs`.
- **PR #109** (M08.07/M16.06, `can_use_magic_revert` plan-gate enforcement) merged — see above.
- **Autonomous selected-backlog run, PR #110–#113 (owner away, non-destructive only), all merged and deployed:** PR #110 M10 (Listing Health issue detail, Shop Insights affected listings); PR #111 M03.04 (shared `ListingPicker`, Media+Variations migrated); PR #112 M13/M15 (media/variation read-only depth); PR #113 M19 (beta readiness smoke matrix + owner runbooks). Full roll-up: `2026-08-30_08-00_selected-backlog-autonomous-rollup.md`.
- **PR #114** (CodeQL cleanup, 2 unused-variable removals, no behavior change) merged — see `2026-08-30_RETROSPECTIVE_pr114-codeql-cleanup.md`.
- **Owner manual non-destructive smoke test (2026-08-30)** across `/listing-health`, `/insights`, `/media`, `/variations`, `/video-generator`, `/magic-revert`, `/account/activity` found 4 polish items, all closed (PR #115, branch `fix/owner-qa-polish-before-write-tests`): Bulk Edit "Fix in Bulk Edit" preselection visibility (M04.05), Media current-media gallery (M13.02), Video Generator synced-photo thumbnail preview (M13.05), dashboard onboarding cross-sell copy neutralized.
- **Owner completed live production write tests (2026-08-30):** single-listing title write + Magic Revert OK; single-listing price write (`price_amount` 6000→6288) + Magic Revert OK (Apply success=1/failed=0/skipped=0, revert restored=1/failed=0/skipped=0). See M16.03, M19.01.
- **Dashboard onboarding tracking + `[object Object]` display bug fixed (2026-08-30, PR #116, branch `fix/dashboard-onboarding-tracking-after-write-tests`, merge `2ec4226c`):** found immediately after the above live tests — the onboarding checklist's "Try bulk edit"/"Review available tools" steps were hardcoded incomplete regardless of real account activity. Now "Try bulk edit" reads real `bulk_edits_used` from `GET /api/v1/billing/usage`; "Review available tools" removed from the checklist (dashboard's existing tool grid covers it). Also fixed: Bulk Edit Add Changes table showed `[object Object]` for find/replace rules — now renders `Find: "…" → Replace: "…"`. See M19.03.
- **Account profile name fields + sidebar cleanup + beta-readiness/owner-control polish (2026-08-30, branch `feature/account-profile-and-beta-readiness-control`):** owner asked for first/last name (Account → Profile), Dashboard greeting by name instead of raw email, and sidebar email/Sign out moved into Account. Backend: `User.first_name`/`last_name` (migration `0026`), `display_name` deterministic fallback (first+last → first → last → email → "Account"), new `PATCH /api/v1/auth/me`. Frontend: new `/account/profile` page, `/dashboard` greeting via `getGreetingName()` (prefers first name), sidebar footer (email + Sign out) removed from `AppShell.tsx`, Sign out relocated to `/account`. Also this round: small owner-verified-checks card on `/dashboard` (title/price write+revert owner-verified; variation/media/video not yet), and a truthful copy fix on the Variations apply-confirm modal (no revert exists for variations yet). See M11.12, M15.04, M19.03. **Remaining owner-live actions, still separate and optional: variation apply (no revert yet, M15.04), media upload/delete/replace, video generation. Broader beta launch, real Stripe live billing readiness, and wider beta user onboarding remain untouched/pending.**
- **Full TASKS.md truth audit (2026-08-30, branch `docs/tasks-md-full-truth-audit`):** every milestone/package re-verified against source code, migrations, tests, and this session's own logs — not trusted from prior summaries alone. Found and corrected: (1) the "Milestone policy" section at the bottom of this file was badly stale, describing M10/M12/M13/M14/M15/M16/M19 as "PLANNED — not started" and M11 as "the current major sprint" when the per-milestone sections directly above it already documented most of that work as shipped; (2) **two entire shipped, tested features had zero milestone tracking at all** — CSV Import/Export (Sprint 14, 2026-06-26) and Scheduled Jobs (Sprint 16, 2026-06-26) — now added as M03.06 and M04.06; (3) **M08.04 (Owner dashboard/comp grant UI), M12.02 (AI suggestions), and all of M14 (Dynamic Pricing/profit)** were marked `[ ]` "not started" despite being real, tested, safety-checked implementations from Sprint 19/13/15 respectively — upgraded to `[~]` (implemented, not owner-click-through-verified); (4) M03.03 (listing status filters) and M04.03 (apply job state tracking) were marked `[ ]` despite partial real implementations — upgraded to `[~]` with the exact gap named. See the audit's local log for the full evidence table (upgrades/downgrades/still-not-done/owner-verification-required), `2026-08-30_..._tasks-md-full-truth-audit.md`.
- **M03.02 full-status sync + M03.03 Listings filters/counts implemented; unwanted Dashboard card removed (2026-08-30, branch `feature/m03-full-status-sync-and-listing-filters`):** owner rejected the "Owner-verified production checks" Dashboard card added in the previous round — removed entirely; the underlying facts stay in docs only. M03.02: `sync_shop_listings()` now fetches all 5 Etsy listing states (active/inactive/draft/expired/sold_out — `sold_out` is a native Etsy state, not derived) via the general listings-by-shop endpoint, read-only, with per-state pagination and partial-failure safety (`job.status` gains `"completed_with_errors"`). M03.03: Listings page gained a **Sold out** 6th tab and a new `GET /listings/status-counts` endpoint returning real per-status counts from local synced data. Both kept `[~]` — mocked-test-verified, no production sync run this round (owner approval required separately) and no owner click-through of the new tabs/counts yet.
- **Production sync 400 hotfix + M04/M06 write-safety foundation (2026-08-31, branch `fix/sync-status-400-then-write-safety-foundation`):** owner's first real production sync after PR #120 failed with a `400` for every state, including `active` — the general-endpoint assumption behind M03.02 was wrong, not just untested. `active` restored to the exact endpoint proven working pre-PR-#120; `inactive`/`draft`/`expired`/`sold_out` kept on the general endpoint but with `includes` removed (the most likely single cause); per-state failure isolation (already shipped) now reports a genuinely useful, sanitized Etsy-sourced reason per failed state instead of a blanket wall of errors. **Phase B (only started because Phase A's fix was confidently completed and tested):** M04.03 canonical apply/revert job state mapping (backward-compatible, DB values unchanged), M06.03 changed-since-apply conflict detection for title/description/sku/price/quantity (refuses revert rather than silently overwriting newer Etsy-side changes), M06.04 per-item write audit trail (extends the existing `AuditLog` table, new searchable `GET /bulk-edit/audit-trail` endpoint), M04.04 owner runbook updated with 3-listing/10-listing/non-price-field batch test procedures. **All of M04.03/M06.03/M06.04 kept `[~]`** — real, tested, but M04.03 awaits owner UI click-through, M06.03 covers only 5 of ~19 possible fields, M06.04 has no export mechanism. See the round's execution log for the full evidence table.

## Current Truth Snapshot (2026-08-30 full audit)

**Fully closed milestones:** M00 (repo/stack), M02 (Etsy OAuth), M05 (live Etsy write core), M07 (rate limits/write pacing — M07.06 Scheduled Jobs added this round as a `[~]` package, doesn't reopen the closed core rate-limit work).

**Partial milestones (real shipped work + real gaps, evidence-backed):** M01, M03, M04, M06, M08, M09, M10, M11, M12, M13, M14, M15, M16, M17, M18, M19.

**Owner-verified live write capabilities:** single-listing title write + Magic Revert; single-listing price write + Magic Revert; 33-listing bulk price apply (32 success/0 failed/1 skipped) + 32-listing bulk revert (32 restored/0 failed/0 skipped). All Etsy-write-capable and owner-run only, never Claude/Codex-run.

**Implemented in code/tested but NOT owner-verified (do not read as "working in the owner's hands" until an owner click-through, or a real owner-approved production sync, is recorded):** Owner admin console (`/owner/*`, M08.04) including Grant/Revoke comp access UI; AI listing suggestions (`/ai`, M12.02); Dynamic Pricing + Profit Calculator (`/pricing-rules`, `/profit`, M14); CSV Import/Export (`/csv`, M03.06); Scheduled Jobs (`/scheduled`, M04.06); variation price/quantity preview (M15.02/M15.03); variation live apply (M15.04); product-detail-page and Listings-page navigation polish (M09.04/M09.06); **full-status read-only listing sync (M03.02, `active` restored to a proven endpoint 2026-08-31 after a production 400 regression, `inactive`/`draft`/`expired`/`sold_out` still unconfirmed live) and Listings status filters + real counts (M03.03)**; **canonical apply-job state mapping (M04.03, tested, not owner-UI-verified); changed-since-apply revert conflict detection for title/description/sku/price/quantity (M06.03, other ~14 fields unverified); per-item write audit trail with searchable API (M06.04, no export mechanism yet).**

**Not implemented / blocked:** variation revert (does not exist, M15.04); media restore/revert endpoint (M13.04); Promote publishing (`[!]` blocked on Pinterest/Meta developer app credentials, M13.06); Etsy listing video upload live test (`[!]` blocked, M13.03); Private Beta invite/allowlist management (M08.06); direct product-page Etsy writes (`[!]` blocked on write-surface architecture design, M09.05); apply-job cancellation (M04.03, no architecture exists to safely stop an in-flight write loop, documented not invented); real in-app 3-listing/10-listing/non-price-field batch owner tests (M04.04, runbook ready, not yet run); write-audit export (M06.04, no placeholder endpoint exists).

**Stale items corrected in this audit:** the bottom-of-file "Milestone policy" summary (rewritten to match real per-milestone status); M03.03 and M04.03 (`[ ]` → `[~]`, partial real implementations existed and were undocumented); M08.04, M12.02, M14.01–M14.04 (`[ ]` → `[~]`, substantial real implementations existed and were undocumented — the single largest correction in this audit); M12.03's second line (`[ ]` → `[x]`, already shipped via M11.03); CSV Import/Export and Scheduled Jobs (previously untracked anywhere in this file, now M03.06/M04.06).

---

# M00 - Product/repository foundation

### M00.01 - Repository and tech stack
- [x] Repository `Sekiph82/Bulk-Edit`, local path `C:\Users\sekip\Desktop\Bulk-Edit`.
- [x] Next.js 14 (App Router, TypeScript) frontend, FastAPI (Python 3.12) backend.
- [x] PostgreSQL 16 + SQLAlchemy 2.x + Alembic, Redis 7 + Celery.
- [x] JWT auth (access + refresh) + Etsy OAuth2, Stripe billing, S3-compatible storage.

### M00.02 - Hosting and environment
- [x] DigitalOcean App Platform (`bulk-edit-prod-api`, `bulk-edit-prod-web`) + Cloudflare.
- [x] `deploy_on_push: true`, no path filter — any merge to `main` redeploys both apps.
- [x] GitHub Actions CI: Analyze (javascript-typescript), Analyze (python), Backend Tests, CodeQL, Docker Compose Validate, Frontend Lint & Build — all required on every PR.

M00 PASS/CLOSED.

---

# M01 - Auth, Private Beta, and billing foundation

### M01.01 - Auth
- [x] JWT access/refresh tokens.
- [x] Registration, login.

### M01.02 - Private Beta gate
- [x] `/register`, `/signup`, `/get-started` paused behind `/private-beta`.
- [x] Sign-in and the rest of the authenticated app pass through (`fix/private-beta-allow-signin`, merged `4a232fb`).
- [x] Etsy OAuth callback results not masked by the private-beta gate.

### M01.03 - Stripe foundation
- [x] Live products/prices/env configured, validated end-to-end 2026-07-10 (controlled test account, zero real charges).
- [ ] Stripe production workflow review (webhook endpoint status manually re-verified in Stripe dashboard).

M01 PASS/CLOSED.

---

# M02 - Etsy OAuth and shop connection

### M02.01 - OAuth safe logging
- [x] Safe categorized OAuth callback logging (PR #79) — no tokens, code, state, or secrets logged.

### M02.02 - x-api-key header format fix
- [x] `x-api-key` corrected to `keystring:shared_secret` across Etsy v3 calls (PR #82) — root cause of a live 403.

### M02.03 - Shop lookup response parsing
- [x] Owner shop lookup parsed as a single Shop object, not a list (PR #83).
- [x] Defensive `user_id` validation added (PR #81).
- [x] Owner confirmed shop connection: `WearYourStoriesCom`.

M02 PASS/CLOSED.

---

# M03 - Listing sync and listing data foundation

### M03.01 - Full active listing sync
- [x] Initial 25/210 diagnosed as the Free plan's `max_listings` cap working as designed, not a pagination bug.
- [x] Ops-script `DATABASE_URL` dialect fixed (PR #86).
- [x] Sync uses effective plan including comp grants (PR #87).
- [x] Owner confirmed 210 active listings synced.

### M03.02 - Full inventory/status read-only sync
- [~] **Implemented (2026-08-30, branch `feature/m03-full-status-sync-and-listing-filters`):** `sync_shop_listings()`/`fetch_shop_listings()` (`apps/backend/app/services/etsy_sync.py`) now iterate all 5 Etsy listing states — `active`, `inactive`, `draft`, `expired`, `sold_out` — via Etsy's general "Get Listings by Shop" endpoint (`GET /shops/{shop_id}/listings?state={state}`), replacing the old active-only convenience endpoint (`/listings/active`). `sold_out` is a **native Etsy state value** returned directly by that endpoint, not derived from local quantity — confirmed against Etsy's own documented `state` parameter values for this endpoint (one of `active, inactive, sold_out, draft, expired`), so no separate derivation logic was needed or written. Read-only: only `GET` is ever called (proven by a mock client that raises if `.post`/`.patch`/`.put`/`.delete` are invoked, in `test_etsy_sync_status.py`) — no status-mutation, activate/deactivate/renew/delete endpoint exists anywhere in this code path. `max_listings` plan-limit budget is shared across all 5 states, not per-state (a Free-plan account still can't exceed its real cap by syncing 5x). Pagination works per-state (verified with a forced 1-item page limit across a 3-item state). Partial-failure safety: each state's fetch is wrapped independently — a failure on one state (e.g. `expired`) does not lose listings already upserted from other states this run, `job.status` becomes `"completed_with_errors"` (new value, alongside the existing `"completed"`/`"failed"`) with a safe, secret-free error summary; if every state fails, `"failed"` with zero data loss to previously-committed listings. 7 new tests in `test_etsy_sync_status.py` (all 5 states covered, read-only proof, pagination, partial failure, all-fail, and a status-counts correctness check), plus 2 pre-existing `test_listings.py` tests updated (their shared mock helper was state-blind and needed to become state-aware once sync started querying 5 states instead of 1). No DB migration needed — `Listing.state` was already a free-text, indexed `String(50)` column that stores whatever Etsy returns as-is.
- **Kept at `[~]`, not `[x]`:** per this round's explicit constraint, **no production shop sync was run** (owner approval required separately) — every test uses a mocked Etsy response. The endpoint choice and `state` parameter values are based on Etsy's documented v3 API contract, not confirmed against a real live response this round. Promote to `[x]` once an owner runs a real sync against a connected shop and confirms non-active listings (if the shop has any) actually come back correctly.
- **PRODUCTION REGRESSION AND HOTFIX (2026-08-31, branch `fix/sync-status-400-then-write-safety-foundation`):** the round above shipped as PR #120, and the owner's first real production sync attempt failed with `400 Bad Request` for **every** state, including `active` — `Sync failed: All listing statuses failed to sync` — because the general "Get Listings by Shop" endpoint + `includes=Images,MainImage` combination used for `active` in PR #120 was never actually valid against live Etsy (an untested assumption, not a documented fact). **Root cause and fix:** `active` is restored to the exact endpoint/params proven working for this app's entire history before PR #120 (`GET /shops/{shop_id}/listings/active`, no `state` param, `includes=Images,MainImage`) — this is the fix with the highest confidence, since it reverts to a long-proven-working request shape rather than guessing again. `inactive`/`draft`/`expired`/`sold_out` still use the general endpoint with `state=`, but `includes` was removed (the single most likely point of difference between the two endpoints' accepted parameters, and not load-bearing — the existing per-listing image-fetch fallback covers it). **This second attempt at the non-active states is still not confirmed against live Etsy either** — it could not be verified this round (forbidden by the task). What IS fixed with high confidence: `active` sync is restored, and even if `inactive`/`draft`/`expired`/`sold_out` still fail in production, the per-state failure isolation (already shipped in PR #120) means the job now correctly reports `completed_with_errors` with a sanitized, Etsy-sourced reason per failed state — not a blanket "all statuses failed" with no real diagnostic. Error diagnostics also improved: `httpx.HTTPStatusError` is now caught specifically and Etsy's actual response body is sanitized and surfaced (via the existing `_sanitize_etsy_response_body()`, reused from `etsy_write.py`) instead of the generic `"Client error '400 Bad Request' for url: ..."` message the owner saw. 4 new direct regression tests (`test_fetch_shop_listings_active_uses_dedicated_endpoint_no_state_param`, `test_fetch_shop_listings_non_active_uses_general_endpoint_no_includes`, `test_active_sync_still_completes_when_all_other_states_400` — reproduces the owner's exact scenario, `test_etsy_error_body_is_sanitized_not_raw`), plus the mock dispatcher in every existing sync test now *asserts* the correct request shape (would fail loudly if the old broken shape were ever reintroduced). Merged as PR #121.
- **INACTIVE/EDIT HOTFIX (2026-08-31, branch `fix/m03-inactive-edit-status-sync`):** after PR #121 deployed, the owner ran a real production sync — `active`/`expired` matched Etsy's seller UI exactly (Active 210, Expired 157), but Etsy UI showed **Inactive 180** while the app synced **Inactive 0** (app total 367 = 210+157 only; Etsy's own total across those three buckets is 547). Root cause: `LISTING_STATES` only fetched `active`/`inactive`/`draft`/`expired`/`sold_out` — Etsy's own API documents an additional listing-state value, `edit` (Etsy's seller-UI "Inactive" label can correspond to API state `edit`, not only `inactive`), which this app never fetched at all. **Fix:** `edit` added to `LISTING_STATES` (fetched via the same general endpoint + `state=edit`, same per-state failure isolation as every other status — a 400 on `edit` alone doesn't fail the sync); `Listing.state` stores Etsy's raw returned value truthfully (`edit` stored as `edit`, never relabeled `inactive`); grouping into the app's "Inactive" UI bucket happens only at the query/count layer (`apps/backend/app/api/v1/listings.py`'s new `INACTIVE_GROUPED_STATES = ("inactive", "edit")`) — `GET /listings/status-counts`'s `inactive` value and `GET /listings?state=inactive`'s filter both now sum/match raw states `inactive` OR `edit`; `all` counts each raw state exactly once (no double-count). API/UI contract unchanged — still exactly `all`/`active`/`inactive`/`draft`/`expired`/`sold_out`, no new `edit` tab or key. Dedup is a non-issue by construction: `upsert_listing()` already matches on `(shop, etsy_listing_id)`, so even if Etsy ever returned the same listing under two state queries, one row results (state follows whichever fetch ran last). 5 new backend tests (`test_full_status_sync_covers_all_six_states` — renamed/extended from the 5-state version, `test_status_counts_groups_edit_into_inactive` — reproduces the owner's exact ratio, `test_edit_state_400_is_isolated_like_any_other_state`, `test_same_listing_returned_under_inactive_and_edit_is_not_duplicated`, `test_filter_state_inactive_includes_edit_state` in `test_listings.py`). Frontend: listings page empty-state copy (M03.03, see below) also fixed this round. **This has NOT been confirmed against live Etsy** — `edit` as the correct API state value for Etsy's "Inactive" UI label is the most defensible read of Etsy's own documented state values and the owner's exact count mismatch, but was not (and could not be, per this task's constraints) verified with a real production sync this round.
- **Still `[~]`, still not `[x]` — none of this round's fixes have been confirmed against a real production sync. Do not promote to `[x]` without an owner-run sync whose resulting Active/Inactive/Draft/Expired/Sold-out counts actually match Etsy's own seller UI (target: All≈547, Inactive≈180, given the owner's last-observed Etsy UI numbers).**

### M03.03 - Listing status filters on Listings page
- [~] **Audit upgrade (2026-08-30, prior round):** was marked `[ ]`, but real, functional filters already existed — `STATE_TABS`, a real `state` query param, clickable tabs. Genuinely partial at the time: no real per-status counts (only page-scoped), and non-active tabs were trivially empty since M03.02 didn't exist yet.
- [~] **Implemented (2026-08-30, branch `feature/m03-full-status-sync-and-listing-filters`):** added a **Sold out** 6th tab (`STATE_TABS` now `["All", "active", "inactive", "draft", "expired", "sold_out"]`, `apps/frontend/app/(app)/listings/page.tsx`). New backend endpoint `GET /api/v1/listings/status-counts` (`apps/backend/app/api/v1/listings.py`) returns real, grouped `SELECT state, COUNT(*)` counts from local synced data — no hardcoded numbers, no page-scoping. Wired into the tabs so each shows its real total count next to its label, refetched on shop change and after every sync (success or partial). `filters`/`search`/`pagination`/checkbox-selection/"Bulk Edit selected"/product-detail navigation/Quick View/column-visibility code paths were not touched and remain exactly as before (confirmed via diff review — only the tabs, the new counts fetch, and the sync-result banner's partial-success handling changed). Test-verified end-to-end: `test_status_counts_endpoint_matches_synced_local_data` syncs a 7-listing mixed-status fixture and asserts the counts endpoint returns the exact real per-status breakdown.
- **Kept at `[~]`, not `[x]`:** implemented and test-verified against real local data, but no owner has yet actually looked at `/listings` with the new tabs/counts in a browser. Promote to `[x]` once an owner confirms the tabs/counts render correctly and filtering still works end-to-end.
- **Empty-state copy fix (2026-08-31, branch `fix/m03-inactive-edit-status-sync`):** the "No listings yet / Connect a shop and sync to import your listings." message was static regardless of cause — misleading once a shop is connected and synced but the selected tab/filter just has zero matches (exactly the state the owner's screenshot showed for the Inactive tab before the `edit`-grouping fix above). New `EmptyListingsState` component picks from 4 distinct messages: no shop connected ("Connect a shop and sync..."), shop connected but zero listings synced at all ("No listings synced yet. Run Sync Listings..."), a status tab alone has zero matches but other listings exist ("No listings match this status. Try All or another status."), or search/other filters are also involved ("No listings match your search or filters."). Also added a title-attribute tooltip on the Inactive tab: "Includes Etsy API states \"inactive\" and \"edit\"."

### M03.06 - CSV Import/Export (audit: previously untracked, Sprint 14 2026-06-26)
- [~] **Docs gap found and corrected in this audit** — this entire feature existed in shipped, tested code with zero milestone tracking anywhere in this file. `apps/backend/app/api/v1/csv_tools.py` (export/template/import/jobs/preview/convert, 7 endpoints); `apps/backend/app/services/csv_tools.py` — safety-documented in its own docstring: "CSV import NEVER writes to Etsy directly. Import creates BulkEditSession + BulkEditChange rows only. User must run existing bulk edit preview/apply flow to publish changes." `apps/frontend/app/(app)/csv/page.tsx` (472 lines). 36 backend tests in `test_csv_tools.py`. Not owner-click-through-verified — kept `[~]`, not `[x]`.

### M03.04 - Shared ListingPicker component
- [~] Component shipped: `apps/frontend/components/listings/ListingPicker.tsx` — shop filter (behind `showShopFilter`, hidden when the org has ≤1 shop), status filter, title search, pagination, thumbnail (`ListingListItem.thumbnail_url`, already returned by `getListings()`), variation indicator (`has_variations` badge), selected count, loading/error/empty states (with an overridable `renderEmpty` for consumer-specific honesty, e.g. Variations' no-data-vs-no-match distinction), multi-select and single-select modes, `disabled` read-only mode.
- [x] Media migrated — replaced its client-side-only, unpaginated, thumbnail-less picker.
- [x] Variations migrated — same component with `extraParams={{ has_variations: true }}`, preserving its existing no-data-vs-no-search-match empty-state distinction via `renderEmpty`.
- [x] Video Generator migrated (2026-08-30) — single-select mode, used for the "select a listing's synced photos" image-source option (not its own separate render-batch flow, which doesn't select listings the same way).
- [x] Owner-QA-confirmed (2026-08-30, manual non-destructive smoke test): Media and Variations pickers both observed working — search/pagination/thumbnails/selection all functional against real data.
- [ ] **Not migrated, remaining consumers:** Dynamic Pricing (`pricing-rules/page.tsx` has a "select all *loaded* listings" action tied to holding the full un-paginated listings array client-side — doesn't map cleanly onto the picker's own paginated fetch; not "straightforward" per this package's own scope rule), Bulk Edit (949-line file with the live working apply flow — explicitly higher-risk than a non-destructive round's scope), Promote (doesn't call `getListings()` at all — migrating it is a larger rewrite than a picker swap, left for a dedicated round).

### M03.05 - Variations/Dynamic Pricing/Media listing visibility
- [x] Variations page shows listings instead of a false empty state; distinguishes `has_variations`/no-data/no-search-match via `ListingPicker`'s `renderEmpty`.
- [ ] Dynamic Pricing page shows listings — already did, pre-existing, unchanged this round; suggestions remain preview-only.
- [x] Media page loads listings when listings exist; operations remain read-only/preview-gated until M13 (unchanged).

M03 PARTIAL — listing sync foundation PASS; shared `ListingPicker` SHIPPED and migrated into Media + Variations (M03.04); full-status read-only sync (M03.02, now including `edit`→Inactive grouping) and listing status filters + real counts + empty-state copy fix (M03.03) both implemented and test-verified, kept `[~]` pending a real (owner-approved) production sync / owner click-through; CSV Import/Export SHIPPED, previously untracked (M03.06, audit addition); Dynamic Pricing/Bulk Edit/Video Generator/Promote `ListingPicker` migration remains PLANNED.

---

# M04 - Bulk Edit preview/session/apply foundation

### M04.01 - Bulk Edit session/preview/apply core
- [x] Session creation, change staging, preview generation, apply execution — pre-existing core mechanism.

### M04.02 - Change remove fix
- [x] `apiFetch()` 204-handling bug fixed in the shared client, not just the remove-change call site (PR #91) — also fixed 4 other affected `204` routes.

### M04.03 - Apply job state machine
- [~] **Audit upgrade (2026-08-30):** was marked `[ ]`, but a real, working (if differently-named) status mechanism already exists — `apps/backend/app/services/bulk_edit_apply.py` sets job-level `status` to `"running"` → `"completed"` / `"completed_with_errors"` / `"failed"` (default `"pending"`); item-level `BulkEditApplyResult.status` uses `"pending"`/`"skipped"`/`"failed"`/`"success"`. Jobs persist in Postgres and survive refresh — confirmed via `/magic-revert`'s real job history (M16.02).
- [~] **Implemented (2026-08-31, branch `fix/sync-status-400-then-write-safety-foundation`):** **Option B — backward-compatible canonical presentation state**, chosen over renaming DB values because historical job rows already exist in production and a rename migration would be destructive for zero real benefit. New `app/core/job_states.py::canonical_apply_job_state(status, success_count, error_message, revert_status)` maps the existing DB status (+ optional revert linkage, since `reverted`/`revert_failed` describe what happened to a *completed* apply job, not a distinct apply-execution outcome) onto the full target vocabulary: `pending`→`pending`, `running`→`running`, `completed`→`succeeded`, `completed_with_errors`→`partially_failed`, `failed`→`failed` (or `rate_limited` if the stored error message text-matches a 429/rate-limit signature — the same "pattern-match the message" approach the frontend's `FAILURE_REASON_CATEGORY` already uses, since no structured failure-category column exists), and a linked `RevertJob.status` of `completed`/`completed_with_errors`/`failed` overrides to `reverted`/`revert_failed`/`revert_failed` respectively. Wired into `GET /sessions/{id}/apply`, `GET /sessions/{id}/apply-jobs`, `GET /apply-jobs` (history), `GET /apply-jobs/{id}` — all now return a new `canonical_state` field alongside the unchanged raw `status`. `/magic-revert`'s `StatusBadge` now reads `canonical_state` (falls back to raw `status`). 13 dedicated unit tests (`test_job_states.py`) cover every mapping including that `cancelled` is never produced.
- [~] **`cancelled` is explicitly unsupported, not silently missing:** this app has no code path that can cancel a *running* apply job — no cancel endpoint, no `is_cancelled` flag, no architecture for safely stopping an in-flight Etsy write loop mid-item. (There IS an existing, unrelated `cancel_bulk_edit_session()` — but that cancels a *draft session before Apply is ever clicked*, not an in-progress write loop; different concept entirely, already worked, untouched.) `canonical_apply_job_state()` documents this in its own docstring and its test suite asserts the state is never produced. Building real cancellation is out of scope for this task per its own explicit instruction to mark it unsupported rather than invent an unsafe implementation.
- **Kept at `[~]`, not `[x]`:** the mapping is implemented, fully unit-tested, and refresh-safe/server-backed (jobs already persisted in Postgres before this round) — but per this project's established discipline, nothing UI-facing gets `[x]` without an owner actually looking at the rendered page. No owner has yet seen the `canonical_state` badges on `/magic-revert` in a browser.

### M04.04 - Single/small-batch apply-revert verification matrix
- [x] 33-listing price apply/revert — owner-verified live (Success 32/Failed 0/Skipped 1 apply; Restored 32/Failed 0/Skipped 0 revert; Etsy confirmed both price directions).
- [x] Single-listing title write + Magic Revert — owner-verified live (2026-08-30, recorded here for completeness — see M16.03 for the original record): Apply completed, Magic Revert completed, owner reports OK.
- [x] Single-listing price write + Magic Revert — owner-verified live (2026-08-30, recorded here for completeness — see M16.03): preview `price_amount` 6000→6288, Apply success=1/failed=0/skipped=0, Magic Revert restored=1/failed=0/skipped=0, owner reports OK.
- [ ] 3-listing and 10-listing batch sizes — **still not separately tested.** New runbook sections added this round (`docs/operations/OWNER_BULK_EDIT_RUNBOOK.md`, "3-listing small-batch test" / "10-listing batch test") with the exact owner-run procedure, but no owner has executed them yet — do not mark `[x]` until they have.
- [ ] Non-price fields (title/tags/etc.) at batch scale — **still not separately tested.** New runbook section added ("Non-price field batch test") with a reversible-suffix/tag procedure; not yet run.

### M04.05 - Preselection UX from Listing Health / Insights (owner QA fix)
- [x] Owner-reported (2026-08-30, manual non-destructive smoke test): a listing preselected via `?listing_ids=<id>` (from "Fix in Bulk Edit") showed a generic "N listing(s) pre-selected" banner but the actual listing wasn't clearly visible/checked in the on-screen picker — it was correctly held in state, but if it wasn't on page 1 of the default unfiltered listing table, nothing on screen showed it. Fixed: preselected listing(s) are now fetched by id independently of the paginated/search table and rendered in a pinned "Pre-selected" section at the top of the picker (checked, with title/Etsy id), the banner names the actual title (not just a count), selection persists across pagination/search (already worked, confirmed unchanged), and no automatic apply is triggered.

### M04.06 - Scheduled Jobs (audit: previously untracked, Sprint 16 2026-06-26)
- [~] **Docs gap found and corrected in this audit** — this entire feature existed in shipped, tested code with zero milestone tracking anywhere in this file. `apps/backend/app/api/v1/scheduled_jobs.py` (create/list/detail/pause/resume/disable/run-now/runs/run-due, 10 endpoints); `apps/frontend/app/(app)/scheduled/page.tsx` (466 lines) — nav copy: "Schedule safe syncs, draft creation, and pricing previews — nothing publishes without your approval." 41 backend tests in `test_scheduled_jobs.py`. Not owner-click-through-verified — kept `[~]`, not `[x]`.

M04 PARTIAL — session/preview/apply core and the M04.02/M04.05 fixes PASS; canonical apply-job state mapping SHIPPED and unit-tested, `cancelled` explicitly documented unsupported rather than invented (M04.03, `[~]` pending owner UI click-through); Scheduled Jobs SHIPPED, previously untracked (M04.06, audit addition); single-listing title/price write+revert owner-verified, 3/10-listing and non-price-field batch verification remains an open gap with new owner runbook sections ready but not yet run (M04.04).

---

# M05 - Live Etsy write core stabilization

### M05.01 - Title write shop-scoped path fix
- [x] `patch_etsy_listing()` fixed to include `/shops/{shop_id}` (PR #93). Owner confirmed live title write succeeds.

### M05.02 - Price write fetch-patch-put flow
- [x] `apply_single_listing_price_quantity()` implemented — GET/mutate/PUT full inventory tree, preserving `product_id`/`offering_id` (PR #94).

### M05.03 - Writable inventory payload shape fix
- [x] `build_writable_inventory_payload_from_tree()` — decimal offering price (not the Money-object GET shape), no `product_id`/`offering_id`/`listing_id` in the PUT body, per Etsy's official docs (PR #96).

### M05.04 - Safe Etsy error-body diagnostics
- [x] `_sanitize_etsy_response_body()` / `_inventory_payload_shape_summary()` surface the real Etsy validation reason without leaking tokens/secrets (PR #98).

### M05.05 - readiness_state_id required fix
- [x] `normalize_etsy_inventory_tree()` now captures `readiness_state_id`/`readiness_state_on_property` from Etsy's GET response; writable-payload builder guarantees every offering has one, falling back to a documented placeholder only when genuinely absent (PR #100).

### M05.06 - Owner live verification
- [x] Single-listing: French Bulldog listing, `price_amount` 6000→6288, Success 1/Failed 0/Skipped 0, Etsy confirmed `$62.88`.
- [x] Bulk (33-listing): see M04.04.

M05 PASS/CLOSED.

---

# M06 - Magic Revert and apply job safety

### M06.01 - Magic Revert core
- [x] Revert uses the same safe Etsy write helpers as apply (`patch_etsy_listing`, `apply_single_listing_price_quantity`) — pre-existing mechanism, confirmed via code read during the PR #102 rate-limit-guard round.

### M06.02 - Magic Revert live verification
- [x] 32-listing bulk revert on the 33-listing apply result: Restored 32/Failed 0/Skipped 0. Etsy confirmed `$62.88` → `$60.00`.

### M06.03 - Revert refuses/warns if listing changed since apply
- [~] **Implemented (2026-08-31, branch `fix/sync-status-400-then-write-safety-foundation`):** `apps/backend/app/services/bulk_edit_revert.py::detect_revert_conflict()` compares a fresh, read-only Etsy GET (`fetch_current_listing_for_conflict_check()`, single-listing endpoint, never a write) against the locally-known `Listing` value for every field the *original apply's session actually changed* (computed from `BulkEditChange.field_name`, not every key in the pre-apply backup snapshot — the snapshot captures the listing's entire state for restore purposes and iterating all of it would flag untouched fields as conflicts on every revert, which was a real bug caught and fixed by this round's own tests). `title`/`description`/`sku` are compared normalized (HTML-entity-decoded, trimmed); `price_amount`/`quantity` compared exactly. A mismatch marks the item `status="conflict"` in `RevertResult` — the write is never attempted for that item (skipped_count, not failed) — with the exact required message: *"This listing changed after the original apply. Reverting may overwrite newer work."* `/magic-revert` shows a distinct amber "conflict" badge; the existing per-row `error_message` display already surfaced the warning text with no frontend change needed there. 9 dedicated tests (`test_bulk_edit_revert_conflict.py`) cover: no-conflict passthrough, conflict refusal, mixed-safe-and-conflict, conflict persistence, no Etsy write when blocked, no secrets in diagnostics, and the exact required warning text.
- **MAJOR BUG FOUND AND FIXED (2026-08-31, branch `fix/revert-conflict-expected-after-value`, post-merge strict audit of the above):** the implementation above compared live Etsy against the **current local `Listing` row**, not against the apply job actually being reverted's own captured after-value. This is unsafe for a same-app later-write: Job A sets title `A`→`B`, Job B later sets title `B`→`C` (local row and live Etsy both now read `C`) — reverting Job A must be refused because Job A's own expected post-apply value was `B`, not `C`, but the old check said "live == local == safe" and would have silently overwritten Job B's work. **Fixed:** `build_expected_after_values()` now computes, per listing, the real expected-after value from the apply job being reverted itself — priority 1: the M06.04 per-field `AuditLog` row (`apply_job_id` + this listing + `result_status="success"`) → `extra_data["after"]`; priority 2 (older jobs predating that audit trail): `BulkEditPreviewItem.diff[field]["after"]` for the same session+listing. **The local `Listing` row is never used as a fallback value source** — a changed field with neither source is left out of `expected_after` entirely, and `detect_revert_conflict()` marks it unverified (still a conflict, never assumed safe), with the required copy: *"Cannot verify the expected post-apply value for this field, so automatic revert is blocked to avoid overwriting newer work."* 12 new/updated tests in `test_bulk_edit_revert_conflict.py`, including the exact regression scenario (`test_same_app_later_write_regression_blocks_revert_of_stale_job`) which fails against the pre-fix code and passes after, plus old-job-no-source, mixed-job-partial-revert, and unsupported-field-with-a-value-still-blocked cases.
- **Unsupported fields, listed exactly:** every other field this revert path can touch (`_SNAPSHOT_TO_LISTING`: `section_id`, `taxonomy_id`, `personalization_instructions`, `is_personalizable`, `is_customizable`, `personalization_is_required`, `has_variations`, `processing_min`, `processing_max`, `personalization_char_count_max`, `item_weight`, `item_length`, `item_width`, `item_height`, `tags`, `materials`) is **not verified** by this check — if an apply touched one of these, the conflict check marks it `unverified` and refuses the revert anyway (never assumed safe by default, per this task's explicit rule), but it cannot tell the owner *what* changed, only that it can't confirm nothing did.
- **Old-job behavior:** an apply job with no per-field `AuditLog` rows (predates migration `0027`/PR #121) AND no reconstructable `BulkEditPreviewItem.diff` (e.g. the preview item's diff was cleared or the row is gone) has zero changed-field information at all — the whole item is blocked as unverified (`unverified_fields: ["*"]`), never silently allowed.
- **Kept at `[~]`, not `[x]`** — per this task's own rubric, `[x]` requires every supported write field to be covered, and only 5 of the ~19 possible fields have real comparison logic. This round did not expand field coverage, only fixed the correctness of the comparison itself.

### M06.04 - Audit trail for writes
- [ ] Per-item record: who/when/shop/listing/field/before/after/result/job/session/revert status, searchable and safe to export, no secrets persisted. See also M16.
- **Audit note (2026-08-30):** `BulkEditApplyResult` (`apps/backend/app/models/bulk_edit_apply_result.py`) already records org/job/session/listing/status/request+response payload/backup-snapshot-link/timestamps per item — real data, not invented — but has no clean structured `field`/`before`/`after` columns (must be reconstructed from JSON payload blobs) and no per-user `user_id` column (multi-user accounts aren't built yet, M11.06). Still correctly `[ ]` — the gap is the same one already named in M16.04 (no full search/export UI), not a missing data source.
- [~] **Implemented (2026-08-31, branch `fix/sync-status-400-then-write-safety-foundation`):** rather than a new table, extended the existing, already-general-purpose `AuditLog` model (`apps/backend/app/models/audit_log.py`, already used for apply/revert/media/variation job start/finish events across the whole app) with 5 new indexed columns — `apply_job_id`, `revert_job_id`, `field_name`, `result_status`, `revert_status` (migration `0027_add_write_audit_trail_columns.py`) — chosen specifically because they're this task's required filters; before/after values and any other detail stay in the pre-existing `extra_data`/`metadata` JSON column rather than duplicating more columns for data that isn't filtered on directly. `apply_bulk_edit_session()` now writes one `AuditLog` row per (listing, field) actually touched by the diff, at every exit point (success, listing-PATCH failure, inventory-PUT failure, skipped) — records `organization_id`, `user_id` (who), `entity_id`=listing id, `field_name`, `operation`, `result_status`, and `extra_data` with `etsy_shop_id`, `etsy_listing_id`, `bulk_edit_session_id`, `before`/`after` (from the same `BulkEditPreviewItem.diff` the apply already computed — no re-derivation), and a size-limited sanitized error. `revert_apply_job()` now **updates** (not duplicates) those same rows' `revert_job_id`/`revert_status` when a revert completes, directly satisfying "audit record updates/links after Magic Revert." New read-only, org-scoped, paginated endpoint `GET /api/v1/bulk-edit/audit-trail` supports every required filter: `apply_job_id`, `listing_id`, `field_name`, `result_status`, `revert_status`, `date_from`/`date_to`. 7 dedicated tests (`test_write_audit_trail.py`) cover: successful title apply, successful price apply (before/after exact: `6000`→`6288`), failed-item audit write, revert-linkage update, endpoint filtering, cross-org isolation, and no-secrets-in-response.
- **Kept at `[~]`, not `[x]`:** field coverage and search/filter are complete and tested, but **no export mechanism exists at all** — not even a placeholder endpoint — only the read/search API above. Per this task's own rubric, export being absent (not just a stub) keeps this `[~]`.

M06 PARTIAL — M06.01/M06.02 PASS (owner-verified live); M06.03 conflict detection SHIPPED for title/description/sku/price/quantity (remediated 2026-08-31 to compare against the apply job's own captured after-value, not the local Listing row — see MAJOR bug note above), other fields explicitly unverified-not-assumed-safe; M06.04 per-item audit trail SHIPPED with full required-filter search, export not built.

---

# M07 - Rate limits, write pacing, and production safety

### M07.01 - Retry-with-backoff on Etsy write calls
- [x] `etsy_patch`/`etsy_put` share the retry core `etsy_get` already had — exponential backoff, honors `Retry-After`, `ETSY_RETRY_MAX_ATTEMPTS=3`, jitter (PR #102).

### M07.02 - Per-shop write pacing gate
- [x] `sleep_before_etsy_write()` — per-shop minimum-spacing gate (`ETSY_BULK_WRITE_DELAY_MS`, 1100ms), called at every write entry point, not on general listing-sync reads (PR #102).

### M07.03 - 429 diagnostics and frontend failure category
- [x] Diagnostics gained `rate_limited`/`retry_attempt`/`max_attempts`/`retry_after_seconds`/`final_rate_limit_exhausted`; frontend gained a dedicated 429 failure category with retry-count-aware messaging (PR #102).

### M07.04 - Apply/Revert double-submit guard + blocking overlay (UX-01A)
- [x] `applyInFlightRef`/`revertInFlightRef` ref-level guard, confirmation modal closes synchronously before the write starts, full-page blocking overlay with "Writing changes to Etsy…"/"Reverting Etsy listings…" copy (PR #103).
- [x] Owner visually confirmed the overlay in production (screenshot evidence).

### M07.05 - Owner-verified clean run under the guard
- [x] 33-listing bulk apply + 32-listing bulk revert both ran clean under the deployed guard — 0 unexpected 429s, 0 unexpected failures.

M07 PASS/CLOSED.

---

# M08 - Billing, effective plan, usage, credits, and gates

### M08.01 - Billing effective-plan display
- [x] `/billing/subscription` resolves comp grants via `get_effective_plan()`; Billing page correctly shows `Pro Monthly` for a comp-granted account even when the raw Stripe subscription is `Free`.

### M08.02 - Bulk Edit apply gate effective-plan fix
- [x] Root cause: `check_usage_limit()` read the raw `Subscription.plan` (defaults `"free"`) instead of `get_effective_plan()` — a comp-Pro account was gated at the Free plan's 10/month bulk-edit limit instead of Pro's 5000, even though Billing correctly showed Pro (PR #104).
- [x] `check_usage_limit()` now resolves the effective plan and returns `(within_limit, current_usage, limit)`; blocked-gate error messages state usage/limit context ("Used X of Y this month").
- [x] Independent audit of PR #104 confirms this fix in code (not taken on the builder's word) — see `2026-08-29_13-31_AUDIT_PR104_billing_gate_product_detail.md`. Verdict CONDITIONAL: 0 BLOCKER/MAJOR; 1 MINOR — the PR's self-reported test-pass count (176) did not match an independent rerun (171 passed of 180 collected), though the underlying pass/fail claims re-verified true with no regressions.

### M08.03 - Sibling effective-plan gate fixes
- [x] Same raw-plan bug found and fixed in `ai_tools.py` (AI credit gate, twice), `dynamic_pricing.py` (Dynamic Pricing gate), `scheduled_jobs.py` (scheduling gate), `GET /billing/usage` (PR #104) — independently re-verified in code during the PR #104 audit.
- [x] `can_use_feature(subscription, feature_name)` confirmed dead code (zero call sites) — left alone, no live bug.

### M08.04 - Owner dashboard / comp grant management UI
- [~] **Major audit upgrade (2026-08-30):** was marked `[ ]` with the note "Currently owner-console/API-only" — this significantly understated reality. A full owner frontend console already exists at `apps/frontend/app/owner/` (14 real pages: overview, users list+detail, organizations list+detail, shops, payments, system-health, audit-logs, feature-flags, alerts, contact-submissions, content, emails, jobs), backed by `apps/backend/app/api/v1/admin.py` (575 lines, ~35 endpoints — users/organizations/subscriptions/usage/shops/sync-jobs/bulk-edit-sessions/ai-sessions/csv-jobs/dynamic-pricing-jobs/scheduled-jobs/events/billing-summary/stripe-summary/product-usage/system-health/audit-log/contact-submissions/feature-flags). **Grant/revoke comp access has a real, working UI**, not API-only — `apps/frontend/app/owner/organizations/[id]/page.tsx:84-113,247-279`, wired to `adminGrantComp`/`adminRevokeComp`. **A real audit trail exists** — `_write_owner_audit_log()` (`apps/backend/app/services/admin.py:819-836`, `OwnerActionLog` model) is called at 12 sites across every mutating owner action (grant/revoke/plan-change/disable-user/sync-trigger/refund/password-reset), safe by design (own doc comment: "Never include tokens, password reset tokens, Slack webhook URLs, card data, or Stripe secret values"). 108 backend tests (`test_admin_dashboard.py` ×21, `test_admin_panel.py` ×87), 105 passing (3 failures are the same pre-existing local-venv 401-vs-403 artifact independently disproven by CI during PR #117 — not a real gap). Original build: Sprint 19 "Internal Admin Business Dashboard" (2026-06-26), route later renamed `/admin` → `/owner`. **Kept at `[~]`, not `[x]`:** no recorded owner click-through of the `/owner` console exists in any log — implementation is real and tested, manual acceptance is not.

### M08.05 - Stripe production workflow review
- [ ] Products/prices re-verified, webhook endpoint status manually checked in Stripe dashboard, no accidental real charge during tests.

### M08.06 - Private beta user management
- [ ] Invite/allowlist strategy; beta users supported without direct DB edits.
- **Audit-confirmed (2026-08-30):** grep across `apps/backend/app` found zero invite/allowlist code; `apps/backend/app/services/auth.py:226-227` explicitly documents "this app has no team/invite feature (one owner per organization, confirmed by grep — no invite endpoint exists)." Marker stays `[ ]`, confirmed genuinely not done, not just undocumented.

### M08.07 - Magic Revert plan-gate enforcement
- [x] Closed: `validate_apply_job_revertable()` now resolves the effective plan (`get_effective_plan()`, comp-grant aware — not raw `Subscription.plan`) and blocks with `403 "Magic Revert is not available on your current plan."` when `can_use_magic_revert` is false, checked last (after org-ownership, status, zero-success, and duplicate-revert checks) so an already-reverted job still reports "Already reverted." rather than plan-blocked, and no cross-org job existence leaks. `get_revert_eligibility_map()` mirrors the same rule in the same precedence order, resolving the effective plan once per history request (not per job — no N+1). 8 new backend tests (Free blocked direct + history, Pro/comp-grant-Pro allowed, precedence, cross-org, zero-success-still-blocked). Existing ~25 pre-existing revert-mechanics tests updated via a `grant_plan="pro_monthly"` default on the shared `_setup_and_apply()` fixture (comp-grant path, not a raw plan mutation) rather than weakened.

M08 PARTIAL — core gate-correctness IMPLEMENTATION COMPLETE (CONDITIONAL per M08.02 audit, only MINOR/NOTE items open), Magic Revert plan-gate enforcement SHIPPED (M08.07), owner admin console SHIPPED and tested but not owner-click-through-verified (M08.04, audit upgrade — this was significantly understated before this round), Stripe production workflow review and Private Beta invite management remain genuinely PLANNED (M08.05/M08.06, owner-only manual verification, code-unaddressable).

---

# M09 - Listings UX and product detail workflow

### M09.01 - Listing thumbnails and hover preview
- [x] 80x80 thumbnails (PR #89); hover preview fixed with portal/fixed-position behavior after clipping (PR #91). Owner confirmed.

### M09.02 - HTML entity decode
- [x] Backend sync decode for new rows (PR #89) plus frontend display decode defense-in-depth (PR #91). Owner confirmed `Men's`, not `Men&#39;s`.

### M09.03 - Product detail page (UX-01B)
- [x] New route `/listings/[listingId]`: header/hero, product overview, title, description, tags, materials, price & inventory (variation warning), media (thumbnail + photo count), listing-health placeholder, safe-actions card. Every action deep-links to `/bulk-edit?listing_ids=<id>` — no direct Etsy writes (PR #104).
- [x] Independent audit confirms correct internal-listing-id usage (not Etsy listing id), auth guard, loading/error/not-found states, and zero write calls in the file — see PR #104 audit.

### M09.04 - Listings navigation
- [x] Row/title click now opens the product detail page instead of the drawer; small "Quick View" icon keeps the existing `DetailSidebar` available without navigating; checkbox selection, Bulk Edit selected, Sync Listings, filters, saved views, state tabs, column visibility all confirmed unchanged by direct diff review (PR #104).
- [ ] Owner click-through of the new navigation (row → product page, Quick View → drawer, Back to Listings) — not yet performed; flagged as a NOTE in the PR #104 audit, not a blocker.

### M09.05 - Direct product-page Etsy writes / write-surface architecture
- [!] Blocked until a dedicated credit/plan/write-surface architecture design is done — Etsy write surfaces differ (title/description/tags vs price/quantity/inventory vs variations vs media), and audit/revert strategy must be designed before any direct inline write ships from the product page. (Note: this package was previously mislabeled "UX-01D" in earlier notes — the actual UX-01D sprint that ran was the owner visual QA remediation below, M09.06. This design work remains unnamed/unscheduled.)

### M09.06 - Owner visual QA remediation (UX-01D)
- [x] Product detail image was always blank: `thumbnail_url` isn't a real `Listing` column — the list endpoint patched it in per-request, the single-item detail endpoint never did. Fixed with the same lookup; frontend also falls back to `getListingImages()`'s first image (2026-08-29).
- [x] Product detail card layout had large empty space under Title/Tags: a single `grid-cols-2` CSS grid row-pairs cells to equal height. Rewritten as two independent flex columns so each card follows its own content height.
- [x] Added a truthful "Performance" card: `lifetime_views`/`lifetime_favorites` are real (extracted from the already-synced `raw_data` JSON, zero live Etsy call). Monthly views/sales/favorites and lifetime sales are not part of Etsy's core Listing object and this app has never called the Shop Stats/Receipts endpoints that would provide them — shown as explicitly unavailable ("Requires sales data sync" / "Requires Etsy sales scope"), never a fake `0`. 60-second local-only refresh against this app's own backend while the page is open.
- [x] Magic Revert added to main nav (`/magic-revert`, originally a truthful placeholder route). **Superseded by PR #107 (M16/UX-02A):** `/magic-revert` is now a real apply-job history page, not a placeholder — see M16.02/M16.03.
- [x] Removed 3 recommendation/cross-sell banners (Listings, Listing Health, Profit) for a cleaner customer SaaS feel — grepped for more, none found elsewhere.
- [ ] Owner click-through of the polished layout/image/metrics (still pending, same as M09.04's open item).

M09 PARTIAL / IMPLEMENTATION COMPLETE FOR SHIPPED ITEMS, PENDING OWNER CLICK-THROUGH VERIFICATION.

---

# M10 - Listing Health and Shop Insights workflow

### M10.01 - Listing Health issue detail
- [~] Partial. The backend already computed a full per-listing issue list (`score_listing()` → `title`/`tags`/`description`/`media`/`pricing` categories, each with severity/message/recommended_fix) but the frontend only ever rendered the bare `issue_count` number — the API already returned `top_issues` (first 3) per row and a `GET /listing-health/listings/{id}` detail endpoint with `all_issues`/`suggested_actions`, both unused. Fixed: the Issues column is now clickable, expanding an inline row of severity-colored issue pills (tag count e.g. `0/13`, photo count, title length, description length, missing/zero price — each pill's `title` tooltip shows the recommended fix), with a "Show all N issues"/suggested-fixes fetch-on-demand when more than the 3 `top_issues` exist. Tag count and photo count are also still shown as their own dedicated table columns (pre-existing).
- **Exact gap, not hidden:** `score_listing()` itself does not compute zero-quantity, variation, or personalization/materials issues at all (confirmed via code read — only title/tags/description/photos/price are scored) — no issue data was invented to fill this gap, per the task's explicit rule. Adding those checks is a backend scoring-engine change, out of scope for a frontend detail-surfacing pass; tracked as a follow-up.
- [x] Owner-QA-confirmed (2026-08-30, manual non-destructive smoke test): issue-pill expand works, issue details render for real listings (owner observed tags/no-video examples), "View Product" works. Kept at `[~]` overall — the scoring-engine gap above is unrelated to what owner QA can confirm and remains the reason this stays partial, not the UI itself.

### M10.02 - View Product / Fix in Bulk Edit paths
- [x] "Fix in Bulk Edit" pre-existing on the Listing Health table.
- [x] "View Product" link added, same internal listing id (PR #104) — minimal addition, no issue-detail redesign mixed in.
- [x] Owner-QA-confirmed (2026-08-30): both links route correctly. "Fix in Bulk Edit" was found to preselect the listing in state but not clearly show it on screen — **closed this round**, see M04.05.

### M10.03 - Shop Insights affected listings
- [x] "Affected Listings" mini-sections shipped on `/insights`: Missing tags, Low photo count, Short titles, Missing/zero price, Zero quantity — first 10 per section (new `GET /insights/affected-listings` endpoint, local-DB-only, no Etsy call), each item showing thumbnail (or a placeholder), title, the relevant metric (e.g. `0/13 tags`, `1 photo`, `9-char title`, `No price set`, `0 in stock`), `View Product`, and `Fix in Bulk Edit`. Section header shows the true total count even when more than 10 exist. Empty sections are hidden rather than shown with zero rows.
- [x] Owner-QA-confirmed (2026-08-30): Missing tags section observed working with real thumbnails, `0/13` metric, and both action links functional.

M10 PARTIAL — M10.02/M10.03 SHIPPED and owner-QA-confirmed; M10.01 issue-detail surfacing SHIPPED and owner-QA-confirmed for the categories the scoring engine actually computes (title/tags/description/photos/price), zero-quantity/variation/personalization issue *detection* remains a backend follow-up (this is why M10.01 stays `[~]`, not the UI quality).

---

# M11 - Account Center and Connected Shops

**Account-01** — Customer Account Center + Connected Shops + customer-safe Plan/Usage UI. Replaces standalone Billing/Shops pages as the primary customer account surface. No customer-facing admin/comp-grant terminology.

### M11.01 - Account information architecture
- [x] Replace standalone Billing as the primary customer account surface — `/billing` is now a thin client-side redirect to `/account/billing` (PR #105).
- [x] Add Account main navigation entry.
- [x] Add Account subnav: Overview, Profile, Plan & Billing, Usage, Credits, Connected Shops, Team / Users, Security, Notifications, Activity & Audit, Data & Privacy, Support.
- [x] Remove Shops from main navbar after Connected Shops is ready.

### M11.02 - Plan & Billing customer-safe presentation
- [x] Show effective customer plan without internal grant/source terminology.
- [x] Avoid customer-facing "admin", "comp grant", "manual admin", "admin comp" wording — verified via grep, zero matches under `/account`, `/billing`, `/shops` (the one remaining "comp grant" string in the whole frontend tree is the internal owner console, correctly scoped, not customer-facing).
- [x] Present the owner/test account as Pro Monthly using normal customer-facing Pro features/limits.
- [x] Preserve truthful Stripe/payment state without a confusing "Free Plan" main badge when the effective plan is Pro — replaced with a payment-status line derived from `billing_charge_status`.

### M11.03 - Usage dashboard
- [x] Show bulk edit usage used/limit/remaining/reset period.
- [x] Show AI credits used/limit/remaining.
- [x] Show media, dynamic pricing, scheduled jobs, listings/shops limits where available.
- [x] Use the same effective plan/limits as the M08 backend gates — reads the existing `GET /billing/usage`, already effective-plan-correct as of PR #104.

### M11.04 - Credits
- [x] Show AI credit balance and monthly limit.
- [x] Explain which features consume AI credits.
- [ ] Add credit history placeholder or real history if existing — a truthful "coming once transaction logging ships" placeholder shipped; real history not yet built.

### M11.05 - Connected Shops
- [x] Move current Shops functionality into Account → Connected Shops.
- [x] Show connected Etsy shops, connection status, shop name, last sync/listing count if available.
- [x] Preserve Connect Etsy flow.
- [x] Preserve reconnect/disconnect/sync actions only where currently supported.
- [x] Keep `/shops` backward compatible as a redirect — `useEffect`/`router.replace` to `/account/connected-shops`, forwarding the full query string so the Etsy OAuth callback's `?connected=true`/`?error=...` redirect chain still resolves correctly. No OAuth code touched.

### M11.06 - Team / Users
- [x] Add placeholder or MVP for account owner/team roles — shows the real signed-in account owner (via `/auth/me`) plus a "roles coming soon" list (Owner/Manager/Editor/Viewer — no "admin" label).
- [x] Do not expose admin internals to the customer.

### M11.07 - Security
- [x] Add Account Security placeholder/MVP.
- [ ] Add active sessions/password/2FA future hooks where appropriate.

### M11.08 - Notifications
- [x] Add notification preference placeholder/MVP.

### M11.09 - Activity & Audit
- [x] Add Activity & Audit placeholder/MVP (PR #105). **Superseded by PR #107 (M16/UX-02A):** `/account/activity` now shows real Bulk Edit Apply and Magic Revert rows sourced from apply-job history, not a placeholder — see M16.02.
- [x] Reserve this area for Apply Jobs / Magic Revert History (see M16) — done, see above.

### M11.10 - Data & Privacy
- [x] Show AI data usage setting/status where supported — states the real current posture (no Etsy data sent to an external AI provider unless explicitly enabled) without naming any internal env var.
- [ ] Add export/delete/disconnect placeholders without fake functionality — not yet built beyond the AI-data-usage statement above.

### M11.11 - Support
- [x] Add help/support/report-bug placeholders or links.

### M11.12 - Profile name fields + sidebar identity cleanup (owner request, 2026-08-30)
- [x] Backend: `User.first_name`/`User.last_name` added (migration `0026_add_user_name_fields.py`, nullable, existing users unaffected). `User.display_name` property computes the deterministic fallback chain (first+last → first → last → email → `"Account"`). `GET /api/v1/auth/me` returns `first_name`/`last_name`/`display_name` alongside the existing `full_name`/`email`. New `PATCH /api/v1/auth/me` (trims whitespace, blank string → `null`, authenticated-self only) — covered by 5 new tests in `test_auth.py` (display_name fallback, set+persist, trim, clear, requires-auth), all passing.
- [x] Frontend: new `/account/profile` page — first/last name inputs, read-only email, Save button, loading/success/error states, safe empty-state on fetch failure. New `getMe()`/`updateProfile()`/`getGreetingName()` helpers in `lib/api.ts` (also replaces 2 of the app's 3 duplicated raw `fetch('/auth/me')` call sites — `dashboard/page.tsx`, `account/security/page.tsx`).
- [x] `/dashboard` greeting now uses `getGreetingName()` (prefers first name, e.g. "Welcome, Şekip") instead of raw email; falls back to email if no name set, to bare "Welcome" if even email is unavailable, and to the pre-existing "Manage your Etsy listings" subtitle while still loading.
- [x] Sidebar (`AppShell.tsx`) no longer fetches or displays email, no longer renders a "Sign out" button — the entire bottom user-footer block removed (dead `handleLogout`/`router`/`BACKEND_URL`/`LogoutIcon` cleaned up with it). "Account" nav entry unchanged/still visible.
- [x] Sign out moved to Account Overview (`/account`, new "Account controls" card) — new shared `logout()` helper in `lib/api.ts` (revokes refresh token server-side best-effort, then clears local session).

M11 MOSTLY SHIPPED (Account-01, PR #105; Profile/sidebar cleanup, this round) — information architecture, Plan & Billing, Usage, Connected Shops, Team, Security, Notifications, Support, Profile all shipped; Activity & Audit superseded by the real PR #107 implementation. Remaining PLANNED: credit history, 2FA/session hooks, Data & Privacy export/delete functionality.

---

# M12 - AI tools and compliance-safe automation

### M12.01 - AI provider policy gate
- [x] `ALLOW_ETSY_DATA_TO_AI` defaults `false`, not overridden in production; `AI_PROVIDER=mock` in production, so no live AI provider call is possible regardless of the flag.
- [ ] UI explains when AI is unavailable due to policy.

### M12.02 - AI listing suggestions
- [~] **Major audit upgrade (2026-08-30):** was marked `[ ]` "not started" — this is a real, tested, shipped feature (Sprint 13 "AI Tools", 2026-06-26). `apps/backend/app/api/v1/ai.py` (sessions CRUD, run, list suggestions, accept/reject, convert-to-bulk-edit, usage — 9 endpoints); `apps/backend/app/services/ai_tools.py:270-284` — `accept_suggestion()` only flips a status flag, no Etsy write; `:304` `convert_to_bulk_edit()` creates a real `BulkEditSession`, reusing the exact same preview/apply/revert/rate-limit pipeline every other write path uses — genuinely preview-only with a clear before/after diff (Bulk Edit's own preview table). `apps/frontend/app/(app)/ai/page.tsx` (422 lines). 27 backend tests (`test_ai_tools.py`). **Kept at `[~]`, not `[x]`:** not owner-click-through-verified.

### M12.03 - AI tool usage limits
- [x] Backend gate now uses the effective plan (M08.03).
- [x] **Audit upgrade (2026-08-30):** was marked `[ ]` — already shipped via M11.03/M11.09's usage UI: `apps/frontend/app/(app)/account/usage/page.tsx` ROWS includes `ai_credits_used`/`ai_credits_per_month` ("AI credits this month"); `apps/frontend/app/(app)/account/page.tsx`'s "Usage this period" card also shows an AI credits bar. Same underlying `GET /billing/usage` endpoint M11.03 already documented as shipped — this was a cross-reference gap, not a missing feature.

### M12.04 - Prompt and output audit
- [ ] Safe logs record prompt category and item id, not secrets; Etsy-derived content handling explicit.

M12 PARTIAL — AI listing suggestions SHIPPED and tested but not owner-click-through-verified (M12.02, major audit upgrade — was incorrectly "not started"); usage limits + UI counters SHIPPED (M12.03); policy-gate default SHIPPED (M12.01) but no in-UI explanation of AI unavailability; prompt/output audit logging remains PLANNED (M12.04).

---

# M13 - Media, photos, video workflows, and Promote

### M13.01 - Media module listing picker
- [x] Fixed a real loading bug (2026-08-29, UX-01D): `load()` used `Promise.all([getListings, listMediaJobs, listVideoRenders])` — a failure in the unrelated `listMediaJobs()` call rejected the whole batch and blanked the listings picker with a misleading "Failed to load listings," even though `getListings()` (same helper the Listings page uses) would have succeeded. Decoupled into independent try/catches.
- [x] Now uses the shared `ListingPicker` component (M03.04, 2026-08-30) — gained thumbnails, server-side status filter, and pagination it never had as the page-local version.

### M13.02 - Listing image read-only view
- [x] Product detail page (`/listings/[listingId]`) Media card now shows a full read-only thumbnail grid of every synced image (was: primary image + count + "Full image gallery is not available yet."), plus a truthful amber warning when zero photos are synced. No reorder/delete/upload control added — grid is display-only.
- [x] Owner-reported (2026-08-30, manual non-destructive smoke test): the same gap existed on the Media page's own listing picker — selecting a listing gave no indication of what media it already had synced. Fixed: a "Current Media (read-only)" panel now appears below the picker — single selection shows the primary + all synced thumbnails; multiple selections show a compact per-listing summary (thumbnail, title, photo count) for the first 5; "Current media not synced yet" shown truthfully when none exist. No upload/delete/replace/reorder control added.

### M13.03 - Etsy listing video upload workflow
- [!] Blocked — implemented historically but never live-tested. Needs owner-approved single-listing test, preview/confirmation, item-level report, rate-limit handling (via M07).

### M13.04 - Media delete/revert strategy
- [~] Audit found this is a live, already-shipped feature (not something this round is introducing): the Media page's `add_image`/`replace_image`/`delete_image`/`add_video`/`replace_video`/`delete_video` operations are all fully implemented and enabled, and a `MediaBackup` row is created before every write ("Backups are created before every write," pre-existing page copy) — but no revert/restore endpoint exists anywhere (confirmed via grep across `app/api/v1/*.py`, zero matches for a media-revert route). A customer who deletes or replaces media today cannot self-recover through the app despite the backup row existing. **Fixed this round:** `replace_image`/`delete_image`/`replace_video`/`delete_video` (every operation that can lose an existing asset) are now disabled in the operation picker with truthful "coming soon — no restore yet" labels; `add_image`/`add_video` (purely additive, nothing lost) stay enabled. Recovery-story implementation (an actual restore endpoint reading `MediaBackup`) remains planned.

### M13.05 - Video Generator real workflow
- [~] Listing-based image selection shipped: a "Select from a listing's synced photos" option (alongside, not replacing, manual URL paste) uses the shared `ListingPicker` + `getListingImages()` to populate the same image-URL list the existing render form already used — the actual render-triggering path (`handleRender`) is completely untouched. Preview/approval, per-listing job state, and the existing "not yet Etsy-uploaded until approved" flow were already in place and are unchanged. Batch selection (multiple listings → multiple jobs) not added this round.
- [x] Owner-reported (2026-08-30, manual non-destructive smoke test): picking a listing filled the URL textarea but gave no visual confirmation of which photos were actually selected. Fixed: a thumbnail preview grid (in image order, first image marked) now renders below the picker whenever a listing is chosen; "No synced photos available for this listing." shown truthfully when none exist. Textarea stays editable. No video generation or external provider call added or triggered.

### M13.06 - Promote (Pinterest/Instagram)
- [!] Blocked on external app setup: Pinterest developer app + redirect URI + scopes; Meta developer app + Instagram Graph API + business/creator permissions; production review if required.
- [ ] Caption/hashtag generation (preview, editable, respects the AI data policy in M12.01).
- [ ] Schedule/post now, explicit time zone, item-level report, no silent posting.

### M13.07 - Bulk Create shop-connection gate fix (UX-01D)
- [x] Fixed a real bug (2026-08-29, UX-01D, PR #106): `GET /bulk-create/status` was hardcoded to always return `not_configured`, never actually checking the org's Etsy shop connection — Bulk Create falsely told owners with a connected shop to "Connect your Etsy shop first." Now runs the same `is_connected` check Connected Shops uses. With a connected shop it returns a distinct, truthful `not_yet_enabled` status (the draft-creation workflow itself isn't wired up yet) instead of either the false gate or a non-functional-looking upload UI.
- [ ] Bulk Create draft-creation workflow itself (the "Create Drafts" button) remains unimplemented — tracked separately, not part of this fix.

M13 PARTIAL — M13.01/M13.02/M13.07 SHIPPED; M13.04 destructive-action UI safety SHIPPED (recovery-story endpoint itself remains PLANNED); M13.05 listing-image-selection foundation SHIPPED (full batch workflow remains PLANNED); M13.03/M13.06 remain BLOCKED on external prerequisites (owner-approved live test / third-party developer apps).

---

# M14 - Dynamic Pricing and profit intelligence

### M14.01 - Dynamic Pricing data prerequisites
- [~] **Major audit upgrade (2026-08-30):** was marked `[ ]` "not started" — Sprint 15 "Dynamic Pricing" (2026-06-26) shipped real prerequisite handling. `apps/backend/app/services/dynamic_pricing.py:114-140` `apply_margin_floor()` uses real `cost_amount` and a minimum-margin percent to floor suggested prices. Not owner-click-through-verified — kept `[~]`.

### M14.02 - Profit page validation
- [~] **Audit upgrade (2026-08-30):** was marked `[ ]` — `apps/frontend/app/(app)/profit/page.tsx` already has an honest `"missing_costs"` status (line 12), renders `"—"` for null values rather than fake numbers (line 35), and only applies `.toFixed(1)` when a real value exists (lines 178, 254). Not owner-click-through-verified — kept `[~]`.

### M14.03 - Pricing suggestion engine
- [~] **Major audit upgrade (2026-08-30):** was marked `[ ]` "not started" — real, tested, shipped feature. `apps/backend/app/api/v1/dynamic_pricing.py` (jobs/preview/recommendations/accept/reject/accept-all/convert/summary — 10 endpoints). `apps/backend/app/services/dynamic_pricing.py`'s own module docstring: "Dynamic pricing NEVER writes directly to Etsy. Approved recommendations are converted to a BulkEditSession (draft) only." `apps/frontend/app/(app)/pricing-rules/page.tsx` (884 lines). 27 backend tests (`test_dynamic_pricing.py`). Not owner-click-through-verified — kept `[~]`.

### M14.04 - Dynamic Pricing write handoff
- [~] **Audit upgrade (2026-08-30):** was marked `[ ]` — `convert_to_bulk_edit()`-equivalent conversion (`dynamic_pricing.py`, same pattern as M14.03) creates a real `BulkEditSession`, so it automatically inherits the M07 rate-limit/write-pacing guard and the standard apply/revert mechanism — there is no separate write path to build. Item-level report and revert come from the same Bulk Edit apply/revert flow used everywhere else. Not owner-click-through-verified — kept `[~]`.

M14 PARTIAL — **not PLANNED as previously stated; this was the single largest correction in the 2026-08-30 audit.** All 4 packages have real, tested, safety-checked implementations (Sprint 15, 2026-06-26) that were never reflected in this file. None are owner-click-through-verified.

---

# M15 - Variations and inventory depth

### M15.01 - Variation inventory read model
- [x] Audit found the read model already exists and is already populated (confirmed via code read, not guessed): `ListingVariation` (property_id/name, value_id/name, price, quantity, SKU, availability) is written by `etsy_sync.py` on every shop sync, and `GET /listings/{id}/variations` has returned it since Sprint 5/12 — `lib/api.ts`'s `getListingVariations()` existed too. **None of it was ever rendered anywhere in the frontend.** Fixed frontend-only: the Variations page now has a "Variation Data (read-only)" panel — one row per selected listing, expandable into a real matrix (property/value/price/qty/SKU/available), truthfully distinguishing "has synced variation rows" from "has_variations on Etsy but nothing synced locally yet — run a shop sync" (the latter state was previously indistinguishable from "no data at all").
- Owner-observed (2026-08-29): Variation Bulk Editor showed "No variation listings found" for the connected shop at the time. **Still not treated as a confirmed bug** — the `has_variations=true` filter is real and correctly-synced; whether that shop's listings genuinely have zero variations is unverifiable without a live authenticated check. Unchanged this round.

### M15.02 - Variation price edit preview
- [~] Code exists and is shipped (Sprint 12, 2026-06-26, predates this session's tracked rounds) — `generate_variation_preview()` builds a before/after diff from local `ListingVariation` data only (zero Etsy call for preview), rendered in the existing before/after preview table; 26 existing tests in `test_bulk_edit_variation.py` cover it. **Kept at `[~]`, not `[x]`** (2026-08-30 owner QA round): the owner's manual smoke test confirmed the Variation Data *read* matrix works against real synced data, but did not specifically exercise creating a price-preview job and inspecting its output — preview-output correctness itself remains code/test-verified only, not owner-observed. Promote to `[x]` once an owner actually runs a preview (no apply) and confirms the before/after numbers look right.

### M15.03 - Variation quantity edit preview
- [~] Same as M15.02 — quantity preview uses the identical `generate_variation_preview()` path, shipped and unit-tested, but not yet owner-observed specifically. Kept at `[~]` for the same reason.

### M15.04 - Variation write apply/revert
- [~] Audit correction, not `[ ]` and not `[x]`: an apply mechanism already exists in code (`apply_variation_job()` — fetch-patch-put against Etsy, backup-before-write, confirm-to-apply UI with a "Type APPLY VARIATIONS" gate) and is unit-tested, but two things are genuinely missing: (1) **no owner live verification has ever occurred** for a variation write (unlike the price/title write saga, which has an extensive owner-run verification trail) — code-level tests mock Etsy and are not acceptance evidence per this file's own rule; (2) **variation revert does not exist at all** — the Sprint 12 changelog entry explicitly says "Revert for variations explicitly deferred to Sprint 13," and no revert code was ever added. Neither gap was touched this round (no live write, no revert built) — this is a documentation-accuracy correction, not new work.
- [x] Owner-safety copy fix (2026-08-30, beta-readiness round): the Apply Variations confirm modal mentioned an automatic backup snapshot in a way that could read as "revert is available." Added an explicit line: "Magic Revert does not support variation changes yet — there is no one-click undo for this action." Small, truthful copy change only — no functionality added.

### M15.05 - Variation diagnostics
- [x] `BulkEditVariationPreviewItem.validation_messages` already existed on the backend (populated by `build_variation_preview_for_listing()`) but was never rendered — fixed: the preview table now has a Diagnostics column showing the exact safe validation message(s) per item (list-formatted) instead of only a bare status badge. No raw Etsy body/token/secret ever included in these messages (confirmed via the same code path M05.04 already established as sanitized).

M15 PARTIAL — read model + matrix (M15.01, owner-QA-confirmed 2026-08-30 against a real synced variation listing) and diagnostics (M15.05) SHIPPED; price/quantity preview (M15.02/M15.03) code-shipped but not yet owner-observed, kept `[~]`; apply exists+tested but never owner-live-verified and revert doesn't exist at all (M15.04, `[~]` not `[x]`).

---

# M16 - Activity, audit, history, and Magic Revert history

### M16.01 - Standardized item-level write logs
- [x] Bulk Edit price/title write failures have sanitized, safe diagnostics (M05.04, extended in M07.03/M08.02).
- [ ] Standardize the same shape for media upload and social post write paths once M13 ships.

### M16.02 - Apply Job history
- [x] Shipped (PR #107, 2026-08-29): new org-wide, paginated `GET /api/v1/bulk-edit/apply-jobs` endpoint (the only genuinely new backend capability — job detail, revert-jobs list, revert-job detail/results all already existed). Surfaced in `/magic-revert` (job table: date, status, item counts, revert availability) and `/account/activity` (synthesized Bulk Edit Apply + Magic Revert rows from the same data) — see M11.09.
- [x] Owner-QA-confirmed (2026-08-30, manual non-destructive smoke test): `/magic-revert` job list, "View details" expand, "Revertable only" filter, and "already reverted"/failed-jobs-not-revertable states all observed working against real data. `/account/activity` confirmed showing both Bulk Edit Apply and Magic Revert rows. Owner did not run a live revert during this pass (non-destructive by design) — see M16.03.

### M16.03 - Magic Revert from prior jobs
- [x] Shipped (PR #107, 2026-08-29): reverting a job other than the one just completed is enabled, not just displayed. Audit found `POST /apply-jobs/{apply_job_id}/revert` already accepted **any** apply_job_id (org-scoped, idempotent, 409 on double-revert) — it was already safe for history use, just never exposed in the UI. `/magic-revert`'s revert action reuses the exact PR #103 (UX-01A) double-submit-guard + blocking-overlay safety pattern. One real backend gap fixed alongside this: `validate_apply_job_revertable()` never checked a job had ≥1 successful item before "reverting" it (harmless 0-item no-op before, now a clean 400).
- [x] The 2026-08-29 (UX-01D) nav-level placeholder at `/magic-revert` is superseded — it is now the real history/revert page described above, not a placeholder.
- [x] **Owner live revert test complete (2026-08-30):** owner ran two live production write+revert cycles through this page — (1) single-listing title write, Apply completed, Magic Revert completed, owner reports OK; (2) single-listing price write (`price_amount` 6000→6288 preview), Apply success=1/failed=0/skipped=0, Magic Revert restored=1/failed=0/skipped=0, owner reports OK. Both destructive live actions run directly by the owner, not by Claude/Codex.

### M16.04 - Audit/activity table
- [~] Partial: `/magic-revert` has status and revertable-only filters, sourced from the same history endpoint. Not yet done: full search by user/shop/listing/date, and an export-safe summary view.

### M16.05 - Revert availability status per item
- [x] Shipped at the job level (PR #107): `get_revert_eligibility_map()` computes `can_revert`/`revert_blocked_reason`/`revert_job_id`/`revert_status` per apply job in one batch query (not N+1), mirroring the real enforcement rules exactly so the UI never shows "available" for something the backend would reject. Shown in both `/magic-revert` and `/account/activity`.
- [ ] Not yet done: revert-availability status for individual line items *within* a job (only job-level status exists today).

### M16.06 - Magic Revert plan-gate enforcement
- [x] Closed (see M08.07 for the implementation detail): `can_use_magic_revert` is now enforced both on the direct revert endpoint (403) and in the history eligibility map (`can_revert=false`, safe `revert_blocked_reason`) — the UI never shows "available" for something the backend would reject, and vice versa.

M16 PARTIAL — apply-job history, prior-job revert, job-level revert-eligibility status, and plan-gate enforcement SHIPPED (PR #107, M08.07/M16.06); full audit-table search/item-level status (M16.04/M16.05) remain PLANNED.

---

# M17 - Owner operations, beta ops, and support

### M17.01 - Retention cleanup job
- [x] DigitalOcean Scheduled Job `retention-cleanup`, `30 3 * * *` (03:30 UTC daily) — two consecutive successful runs confirmed (2026-07-15, 2026-07-16).

### M17.02 - Owner dashboard
- [~] **Audit upgrade (2026-08-30):** see M08.04 — a real, tested owner dashboard already exists at `/owner`, covering users/orgs/shops/plans/sync/jobs. Not owner-click-through-verified.

### M17.03 - Comp grant management UI
- [~] **Audit upgrade (2026-08-30):** see M08.04 — Grant/Revoke comp access already has a real working UI (`/owner/organizations/[id]`), not API-only as previously stated. Not owner-click-through-verified.

### M17.04 - Private beta user management
- [ ] See M08.06 — invite/allowlist, no direct DB edits needed for support.

### M17.05 - Beta tester checklist
- [ ] Small tester cohort flow, support contacts, known limitations, feedback capture.

M17 PARTIAL — owner dashboard + comp grant UI SHIPPED (see M08.04, audit upgrade), retention cleanup PASS, private beta invite management and beta tester checklist remain PLANNED.

---

# M18 - Security, observability, and production hardening

### M18.01 - OAuth callback query-string redaction
- [ ] OAuth code/state not exposed in access logs; redaction tests or log checks exist.
- **Audit clarification (2026-08-30):** application-level logging is already safe — `apps/backend/app/api/v1/etsy.py:33` logs `has_code=%s has_state=%s` (booleans), never the raw values, matching M02.01's already-`[x]` work. The remaining gap is specifically infra/platform-level (DigitalOcean/Uvicorn HTTP access logs recording the raw callback URL's query string), which application code cannot fully control — stays `[ ]`, genuinely open, distinct from M02.01.

### M18.02 - Sanitized Etsy error-body diagnostics
- [x] No raw Etsy response body, token, header, or secret ever persisted or displayed — established M05.04, extended through every write path added in M07/M08.

### M18.03 - Docs-only-PR production-deploy discipline
- [~] Documented in `HANDOFF.md` ("merging to `main` triggers an immediate production rebuild for BOTH apps, even a docs-only merge") — not yet enforced by tooling/CI gate.

M18 PARTIAL.

---

# M19 - Beta readiness and launch polish

### M19.01 - Production smoke-test matrix
- [~] `docs/operations/BETA_READINESS_SMOKE_MATRIX.md` created — 20 categories (Auth, Private Beta gate, Connected Shops, shop sync, Listings grid, product detail, Listing Health, Shop Insights, Bulk Edit preview, title/price write+revert, Magic Revert History, Media read, Variations read, Billing, Usage/Credits, Account pages, mobile/responsive, error/empty/loading states, rate limit, help/support, security/no-secret-logging), each row with objective/route/data needed/owner-run-vs-automated/destructive-flag/expected result/evidence/pass-fail. `[~]` not `[x]` because the matrix itself is a checklist template — every "Pass/Fail" cell is genuinely blank pending the owner-run rows being executed; only the automated rows (route/health checks) have been run and confirmed passing (26/26 against production, 2026-08-30).
- [x] Automated read-only smoke script fixed and re-verified: `scripts/smoke_test_deployment.sh`/`.ps1` existed but were stale (`/register` expected `200`, which is wrong now that Private Beta redirects it `307`; `/admin` no longer exists, renamed `/owner`; missing most current app routes). Updated route list, added `/health/db`/`/health/redis` checks, ran both scripts live against `https://app.bulkeditapp.com`/`https://api.bulkeditapp.com` — 26/26 passed on both the bash and PowerShell versions.
- [x] Owner-QA-confirmed (2026-08-30): owner ran the non-destructive screen-check portion of the matrix manually across `/listing-health`, `/insights`, `/media`, `/variations`, `/video-generator`, `/magic-revert`, `/account/activity`, and smoke routes.
- [x] **Title write + Magic Revert row and price write + Magic Revert row now complete (2026-08-30):** owner ran both live against production (see M16.03 for full detail). Remaining destructive owner-run rows still genuinely pending: shop sync, variation apply, media upload/delete, video generation — none run by the owner or by Claude/Codex.

### M19.02 - Help docs and owner runbooks
- [x] Three runbooks created in `docs/operations/`: `OWNER_BULK_EDIT_RUNBOOK.md` (safe single-listing test procedure, evidence capture, stop conditions, revert pointer, error-meaning table), `MAGIC_REVERT_RUNBOOK.md` (how to read the History page's eligibility states, safe revert procedure, error-meaning table), `RATE_LIMIT_RUNBOOK.md` (how the PR #102 pacing/retry guard actually works, what a residual 429 looks like, what to do about it). All three are read-only reference material — none instruct or enable Claude/Codex to perform any live action.

### M19.03 - UX polish
- [~] No additional low-risk copy/loading/empty-state fix was found in the M19 round itself beyond what already shipped in the M10/M13/M15 PRs earlier in the same autonomous sequence (Listing Health issue pills, Shop Insights affected-listings, product-detail image gallery, variation matrix, Media truthful "coming soon" copy). Not fabricated to fill this checkbox at the time.
- [x] Owner-reported (2026-08-30, separate manual QA round after M19): dashboard onboarding still showed "Explore paid features" — cross-sell tone the PR #106 banner-removal policy already established should not exist in the customer-facing app. Fixed: `components/onboarding/OnboardingChecklist.tsx` step relabeled "Review available tools" with neutral description ("See what's included in your plan…" instead of "Unlock…"). Kept package at `[~]` overall since this is one targeted fix, not a full polish pass.
- [x] **Dashboard onboarding completion tracking bug fixed (2026-08-30, after owner live write tests):** owner reported the checklist's "Try bulk edit" and "Review available tools" steps stayed incomplete despite the account having 130 real bulk edits on record. Root cause: both steps had `done: false` hardcoded, wired to no data at all. Fixed: "Try bulk edit" now reads `bulk_edits_used > 0` from `GET /api/v1/billing/usage` (the same real, server-side, cross-device usage counter `bulk_edit_apply.py` already increments on every successful apply — not localStorage). "Review available tools" removed from the completion checklist entirely (the dashboard's existing `activeFeatures` tool grid below the checklist already serves that purpose neutrally, with no new tracking needed).
- [x] **`[object Object]` Bulk Edit Add Changes display bug fixed (2026-08-30):** find/replace rule rows showed `[object Object]` in the Value column because `formatVal()` had no object branch. Fixed to render `Find: "<text>" → Replace: "<text>"` (or `Find/replace rule configured` if both empty); price/other scalar values unaffected. Display-only fix, no payload/apply/revert semantics changed — owner's just-verified live price write+revert path untouched.
- [x] **Owner-verified production checks card added to `/dashboard` (2026-08-30, beta-readiness round):** small static card listing what has actually been manually verified against production ("Title write + Magic Revert — owner-verified", "Price write + Magic Revert — owner-verified") versus what has not ("Variation apply", "Media replace/delete", "Video generation" — all shown as not-yet-verified, not automated guarantees). Genuinely static content (no new fragile tracking added) — copy is truthful and dated by this docs round, not implied to be live/automated.
- [x] **Owner-verified production checks card removed from `/dashboard` (2026-08-30, branch `feature/m03-full-status-sync-and-listing-filters`):** owner explicitly rejected this card as unwanted customer-facing content — removed entirely (`apps/frontend/app/(app)/dashboard/page.tsx`). The underlying owner-verified facts (title/price write+revert both confirmed OK, owner-run) remain recorded in `TASKS.md`/`HANDOFF.md`/`CHANGELOG_AI.md` only, never surfaced as a Dashboard card again. All other Dashboard cards (onboarding checklist, Listing Health, Profit Overview, Action Queue, `activeFeatures` tool grid) left untouched.

M19 PARTIAL — M19.02 (runbooks) SHIPPED in full; M19.01 (smoke matrix doc + automated script) SHIPPED, title/price write+revert rows now owner-confirmed complete, sync/variation-apply/media/video rows still pending (expected — destructive, require live/manual verification); M19.03 stays `[~]` overall (dashboard onboarding cross-sell copy, onboarding tracking data bug, the `[object Object]` display bug all fixed/shipped; the owner-verified checks card was added then removed at the owner's explicit request — the underlying facts live in docs only now — but no full UX polish pass has been done).

---

# M20 - Public launch readiness

### M20.01 - Etsy app review / production access tier
- [!] Historical: appeal submitted 2026-07-16 after a Personal Use access-tier block; production developer-app credentials were subsequently issued 2026-07-31. Current standing with Etsy's review process should be reconfirmed before treating this as fully closed.

### M20.02 - Public marketing site / pricing finalization
- [ ] Public website aligned with the submitted appeal as of PR #64 — public AI/marketing wording neutralized, Privacy/Terms updated, feature/health public routes not exposed, sitemap clean. Final pricing/marketing copy pass still pending.

### M20.03 - Registration re-enable decision
- [!] Blocked on an explicit owner decision — Private Beta currently gates `/register`/`/signup`/`/get-started`.

M20 PLANNED/BLOCKED until M19.

---

# Milestone policy

**This section is rewritten as of the 2026-08-30 full truth audit — it was previously badly stale (see the audit bullet in "Current truth" above), describing several heavily-shipped milestones as "not started." Keep this section in sync with each milestone's own closing line; do not let it drift again.**

- M00, M02, M05, and M07 are PASS/CLOSED on direct code/test evidence and owner live verification, not builder self-report alone.
- M01, M03, M04, M06, M08, M09, M10, M11, M12, M13, M14, M15, M16, M17, M18, M19 are PARTIAL — each has real shipped-and-evidenced packages alongside genuinely planned, blocked, or not-yet-owner-verified packages. See each milestone's own closing line for its specific mix — do not assume uniform completeness across a milestone from this list alone.
- M20 is PLANNED/BLOCKED pending M19 and an owner decision on registration.
- No milestone or package may be marked `[x]` on the strength of a builder execution log alone — code read, direct test execution, route verification, or recorded owner acceptance is required, per the PR #104 independent audit precedent (`2026-08-29_13-31_AUDIT_PR104_billing_gate_product_detail.md`).
- Historical remediation truth (every merged PR, every owner-reported live-test result, every audit verdict) remains immutable in `CHANGELOG_AI.md` and the `bulkeditapp logs` archive and does not get rewritten to look cleaner in hindsight.
- Do not run live Etsy GET/PUT/PATCH from the Claude/Codex environment without explicit owner approval for that exact task.
- Do not run 3/10-listing bulk write tests, or non-price-field batch tests, casually — they remain open verification gaps (M04.04), not proven-safe.
- Do not enable external AI processing for Etsy-derived data (`ALLOW_ETSY_DATA_TO_AI`) without explicit owner approval.
- Do not disable Private Beta, change DNS/Cloudflare, change production env, or perform Stripe real charge/refund/subscription operations without explicit owner instruction.
- Do not invent new milestone numbers mid-session — new work goes into the relevant milestone's package list first; a genuinely new milestone requires the owner's explicit decision.
