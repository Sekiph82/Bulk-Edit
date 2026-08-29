# HANDOFF.md — Session Handoff

Purpose: only what the next session needs to resume safely. For full engineering history, see `CHANGELOG_AI.md`. For current production/environment state, see `PROJECT_STATUS.md`. For durable decisions, see `DECISIONS.md`.

## RESUME HERE — 2026-08-29 (docs cleanup after PR #101 + PR #107; next: close the Magic Revert plan-gate gap)

**Both PR #107 and PR #101 are merged into `main` and deployed:**
- PR #107 (`feat(revert): add Magic Revert history and activity audit`, M16/UX-02A) — merge commit `7ee420dc1bca90b812ab7e48becece4e0ff241c0`. `/magic-revert` and `/account/activity` are real apply-job-history pages (not placeholders); prior-job Magic Revert execution is enabled via the existing org-scoped revert endpoint. Deployed and route-verified (both prod apps `ACTIVE`, 9 read-only health/route checks 200).
- PR #101 (`docs(hiveai): add dashboard manifest and master sprint roadmap`) — merge commit `092e02f9303b9c824cc816176e485d91720cc730`. `TASKS.md` (H!veAI format, `M00`-`M20`) and `.hiveai/PROJECT_DASHBOARD.md` (pointer-only) are now canonical on `main`. Deployed and route-verified (both prod apps `ACTIVE`, 8 read-only health/route checks including confirmation Private Beta is unchanged).
- This round (`docs/update-current-truth-after-pr101-pr107`): fixed stale pre-merge PR #101 wording left over in `TASKS.md`/`HANDOFF.md`/`PROJECT_STATUS.md` from before those two merges landed, backfilled M11 checkboxes against PR #105, recorded PR #106/#107 shipped-state in M09/M13/M16, and recorded the `can_use_magic_revert` plan-gate known gap as a tracked package (M08.07/M16.06) instead of only prose.

**Recommended next work, in order (see `TASKS.md` M08.07/M16.06 for the gap detail):**
1. **Close the `can_use_magic_revert` server-side plan-gate gap** — `PLAN_LIMITS["can_use_magic_revert"]` is defined but never checked in `validate_apply_job_revertable()`/`get_revert_eligibility_map()`. Fixing it now requires touching ~20 pre-existing tests in `test_bulk_edit_revert.py`/`test_bulk_edit.py` that assume revert just works (grant them a paid plan or adjust assertions) — do this as its own focused round, not bundled with UI work.
2. **Then, owner live QA of the Magic Revert History UI** (`/magic-revert`, `/account/activity`) — click-through only; do not actually run a Magic Revert against a real Etsy listing unless the owner explicitly approves that exact action in-session.
3. **Then, UX-01C** — Listing Health issue detail (tag count, photo count, missing/zero price, variation warnings) + Shop Insights affected-listings navigation (see `TASKS.md` M10.01/M10.03).

---

## Previously — 2026-08-29 (UX-01D: owner visual QA remediation)

**Owner tested production after PR #105 and reported 6 issues, all addressed this round — branch `fix/ux01d-owner-visual-remediation`, based on `origin/main` past PR #105's `1bc563e`.**

1. **Magic Revert missing from nav** — added `/magic-revert` (new truthful placeholder route: explains today's Magic Revert lives on the Bulk Edit page right after Apply, links to Bulk Edit and `/account/activity` for the planned job-history revert) plus a nav entry under Workspace next to Bulk Edit.
2. **Variation Bulk Editor "no listings"** — audited, not blindly fixed: the `has_variations=true` filter is real (Etsy's own field, correctly synced and queried), so this may be a truthful zero-result for this shop, not a bug. Improved the empty state instead (distinguishes no-data from no-search-match, links to Listings) rather than guessing the filter is wrong.
3. **Media page "Failed to load listings"** — real bug, fixed: a `Promise.all([getListings, listMediaJobs, listVideoRenders])` meant a failure in the unrelated `listMediaJobs()` call blanked the whole listings picker. Decoupled into independent try/catches.
4. **Bulk Create false "Connect your Etsy shop first"** — real bug, fixed: `GET /bulk-create/status` was hardcoded to always return `not_configured`, never actually checking `org_id`'s shop connection. Now runs the same `is_connected` check Connected Shops uses.
5. **Product detail images blank** — real bug, fixed: `thumbnail_url` isn't a real column; the list endpoint patches it in per-request, the single-item detail endpoint never did. Added the same lookup, plus a frontend fallback to `getListingImages()`'s first image.
6. **Product detail layout gaps** — real bug, fixed: a single `grid-cols-2` CSS grid row-pairs cells to equal height, which is why Title/Tags (short) sat next to Overview/Description (tall) with huge empty space. Rewritten as two independent flex columns.
7. **Product Overview metrics** — added a truthful "Performance" card: `lifetime_views`/`lifetime_favorites` are real (extracted from the already-synced `raw_data` JSON blob, Etsy's core Listing object carries these as lifetime counters), the 4 requested-but-unavailable metrics (monthly views/sales/favorites, lifetime sales) show "—" + "Requires sales data sync"/"Requires Etsy sales scope" — never a fake `0`, since Etsy's Listing object has no monthly breakdown and this app has never called the Shop Stats/Receipts endpoints sales data would need. 60-second local-only refresh (`GET /listings/{id}` on this app's own backend, never Etsy) while the page stays open, cleared on unmount.
8. **Recommendation banners** — removed exactly 3 ("Not sure what to fix first? Review Listing Health", "Combine margin data... View Profit", "Optimize high-margin listings first... Review Listing Health") from Listings/Listing Health/Profit. Grepped for more elsewhere — none found; all other colored banners tie to real state (errors, warnings) and were left alone.

**4 new backend tests** (2 for the thumbnail fix, 2 for the Bulk Create gate fix). Targeted suite: 41 passed, 1 pre-existing baseline failure (confirmed via `git stash` A/B, not a regression). Frontend `tsc`/`lint`/`build` all clean.

**No Etsy API call, no Bulk Edit apply/Magic Revert/shop sync, no OAuth completed, no Connect Etsy clicked, no Stripe/DNS/Cloudflare/env change by Claude/Codex.** PR #101 untouched this round (merged later — see current HANDOFF top for status).

**Not yet done as of this write-up:** commit, push, PR open, CI watch, merge, deploy, post-deploy route verification (the full route list from the task, including `/magic-revert` and a safe listing-id product-detail load if one is available without live data access).

---

## Previously — 2026-08-29 (Account Center + Connected Shops + customer-safe Plan/Usage UI — Account-01)

**Preceded by an independent strict audit of PR #104** (billing effective-plan gate fix + UX-01B product detail page): code read directly, fresh test/build execution, not the builder log taken on faith. Verdict CONDITIONAL — 0 BLOCKER, 0 MAJOR, 1 MINOR (self-reported test-pass count was numerically wrong, underlying claim re-verified true), 1 NOTE (no live-browser click-through yet, already self-disclosed). Full audit: `2026-08-29_13-31_AUDIT_PR104_billing_gate_product_detail.md`. `TASKS.md` was then converted to the H!veAI-style milestone ledger (`M00`-`M20`) on `docs/hiveai-dashboard-and-tasks` (PR #101 — merged into `main` later, see current HANDOFF top for status) — see that branch's `TASKS.md` for the full milestone map at the time.

**This round — branch `feature/account-center-connected-shops`, based on `origin/main` past PR #104's `60f9734`.** Built the first Account Center: new `/account` section with an 11-route subnav (Overview, Plan & Billing, Usage, Credits, Connected Shops, Team/Users, Security, Notifications, Activity & Audit, Data & Privacy, Support). "Shops" removed from the main sidebar nav; "Account" added in its place. `/shops` and `/billing` are now thin client-side redirects (`router.replace`) to `/account/connected-shops` and `/account/billing`, both preserving the full query string — the Etsy OAuth callback still targets `{FRONTEND_URL}/shops?connected=true`/`?error=...` on the backend (confirmed via grep, unchanged), so the redirect chain keeps that working without touching OAuth code at all.

**Customer-facing wording cleanup, frontend-only, zero backend files changed:** the old `/billing` page showed "Access source: Comp grant" and the literal sentence "This access was granted by an admin comp — no Stripe charge is associated with it" directly to the customer, plus a prominent "Billing subscription: Free" row even when the effective plan was Pro. `/account/billing` drops the `access_source` display entirely, replaces the raw subscription-plan row with a single truthful payment-status line ("Billed through Stripe." / "Not billed through Stripe." / "No Stripe subscription is associated with this plan."), and removes the "admin comp" sentence — no new backend fields were needed since `effective_plan`/`billing_charge_status` already existed on `/billing/subscription` and already carry everything required; only the frontend stopped surfacing the internal-only fields. Verified via grep: zero matches for `comp grant`/`manual admin`/`admin comp`/`access source` anywhere under the customer-facing `/account`, `/billing`, `/shops` routes (the one remaining "comp grant" match in the codebase is in `/owner/organizations/[id]` — the internal owner console, correctly scoped, not customer-facing).

**Connected Shops** (`/account/connected-shops`) is the old `/shops` page content relocated verbatim (connect/reconnect via Etsy OAuth redirect, disconnect, shop list with connection status and last-synced) — no OAuth rewrite. **Usage/Credits** pages read the existing `/billing/usage` endpoint (already effective-plan-correct after PR #104) — no new backend endpoint needed. **Team/Security/Notifications/Activity/Data & Privacy/Support** are truthful MVP placeholders (no fake data, no fake controls) per the task's explicit spec.

**No Etsy API call, no OAuth completed, no Bulk Edit apply, no Magic Revert, no shop sync, no Stripe mutation performed by Claude/Codex this round.** PR #101 untouched this round (merged later — see current HANDOFF top for status).

**Not yet done as of this write-up:** commit, push, PR open, CI watch, merge, deploy, post-deploy route verification (11 `/account/*` routes + `/billing` + `/shops` + the usual health endpoints — no Etsy write as part of that verification either).

---

## Previously — 2026-08-29 (Pro comp-grant bulk edit gate fix + UX-01B product detail page)

**Owner observed a critical mismatch:** Billing page correctly shows Pro Monthly (5000 bulk edits/month) via comp grant, but Bulk Edit apply blocked a single-listing price change with "Monthly bulk edit limit reached." **Root cause found and fixed (branch `fix/billing-gate-and-product-detail-page`, based on `origin/main` past PR #103's `5b195ea`):** `billing.py::check_usage_limit()` (backing the apply gate) read the raw `Subscription.plan` (defaults `"free"` for a comp-only account) instead of `get_effective_plan()` (comp-grant aware, already used correctly by `/billing/subscription` since PR #87). Free plan's `bulk_edits_per_month` is 10 — the owner's own 33-listing/32-success live test alone exceeds that, which is why it blocked; nowhere close to the real 5000 ceiling. **Not a usage overage — a wrong-plan-resolved bug**, proven from code + the org's own visible apply history, no production DB write or credential use needed.

Audited every caller of the same raw-plan pattern and found the identical bug independently duplicated in `ai_tools.py` (AI credit gate ×2), `dynamic_pricing.py` (Dynamic Pricing gate), `scheduled_jobs.py` (scheduling gate), and `GET /billing/usage` — fixed all five in this same PR (same one-line root cause, see `DECISIONS.md`). `check_usage_limit()` now returns `(within_limit, current_usage, limit)` instead of a bare bool, and every blocked-gate error message now states usage/limit context ("Used X of Y this month") instead of a bare "limit reached." 5 new tests in `test_billing.py` cover: free-over-limit blocks, comp-Pro-under-5000-not-blocked (the exact reported bug, regression-proof), comp-Pro-blocks-at-5000, gate/Billing-endpoint agreement, and the error-message content with a no-secret-leak assertion.

**Same PR, Part B — UX-01B product detail page** (owner's design, listed in full in `TASKS.md` Sprint 12.3 on the docs branch): new route `apps/frontend/app/(app)/listings/[listingId]/page.tsx` — full MVP page (header/hero, overview, title, description, tags, materials, price & inventory, media, health placeholder, safe-actions card), all action buttons deep-link to `/bulk-edit?listing_ids=<id>` (preselect only — no direct Etsy writes). Listings page: clicking a row/title now navigates to the product page instead of opening the drawer; added a small 👁 "Quick View" icon per row that still opens the existing `DetailSidebar` without navigating; selection checkboxes, sync, filters, saved views, column visibility, thumbnail hover all untouched. Listing Health page gained a "View Product" link next to its existing "Bulk Edit" action, same internal listing id.

**No Etsy API call, no Bulk Edit apply, no Magic Revert, no shop sync performed by Claude/Codex.** No production DB read or write — the 5000-vs-actual-usage question was answered from code + this session's own visible apply history, not a live query. PR #101 untouched this round (merged later — see current HANDOFF top for status).

---

## Previously — 2026-08-29 (UX-01A: Apply/Revert loading overlay + double-submit guard)

**Owner ran a 33-listing bulk price apply and a 32-listing bulk Magic Revert live (2026-08-29), both clean under PR #102's rate-limit guard** — apply `completed_with_errors` (Success 32/Failed 0/Skipped 1, the skip a correct no-op already at target value), revert `completed` (Restored 32/Failed 0/Skipped 0), Etsy Shop Manager confirmed `$60.00`↔`$62.88` both directions. Recorded on `docs/hiveai-dashboard-and-tasks` (PR #101 — merged into `main` later) — documentation/tracking only, no frontend/backend status wording or semantics changed.

**Same test surfaced a UX bug:** the Apply/Revert confirmation modal stayed interactable while the write was in flight — owner clicked confirm 4-5 times mid-operation. This round (branch `fix/bulk-edit-apply-revert-loading-guard`, based on `origin/main` past PR #102, frontend-only) fixes it in `apps/frontend/app/(app)/bulk-edit/page.tsx`: added `applyInFlightRef`/`revertInFlightRef` (synchronous guard, closes the race window `useState` can't — a fast double click could fire the handler twice before React re-renders with the new state), moved the confirmation-modal close to the top of each handler (synchronous, before the `await`, instead of after it resolved), and added a full-page blocking overlay (`fixed inset-0`, `z-[70]`, spinner + "Writing changes to Etsy…" / "Reverting Etsy listings…" + "Please keep this page open…") shown whenever `applying || reverting` is true — it sits above the (now-already-closed) modal and blocks every click on the page until the API call resolves.

**Explicitly not touched:** `completed_with_errors`/skipped/no-op wording, backend job status semantics, result card colors — confirmed via `git diff` grep, zero matches for any of those strings in the frontend diff. No backend files changed this round.

**No Etsy API call, no Bulk Edit apply, no Magic Revert performed by Claude/Codex** — this is a UI-only race-condition fix, verified via `tsc --noEmit`/`next lint`/`next build` (all clean) and manual code trace (no existing frontend test framework in this repo — established prior-session decision, not repeated here).

**Not yet done as of this write-up:** commit, push, PR open, CI watch, merge, deploy. Do that next: commit `fix(bulk-edit): guard apply revert submits`, push `fix/bulk-edit-apply-revert-loading-guard`, open PR, wait for CI, merge if green, verify prod health + route policy only (add `/bulk-edit` to the usual health/route checklist). **Do not perform any live Etsy write as part of this deploy's verification.**

**Safety constraints still active (unchanged):** never print secrets/tokens; no live Etsy write; no real Stripe action; do not disable Private Beta; no DNS/Cloudflare changes; no staging action; do not merge PR #101; do not push directly to main.

---

## Previously — 2026-08-28 (Etsy rate-limit guard/backoff for Bulk Edit writes)

**Owner confirmed the price-write fix from PR #100 works live**: French Bulldog listing, `price_amount` 6000→6288, Bulk Edit showed Success 1/Failed 0/Skipped 0, Etsy Shop Manager and Bulk Edit Listings both reflected `$62.88`/`USD 62.88` after sync. The multi-round payload/schema saga (readiness_state_id, Money-object vs decimal price, endpoint scoping) is resolved. A later manual apply on a different listing (Miniature Schnauzer Makeup Bag) hit a live `HTTP 429 "Exceeded per second rate limit"` — expected, since no Etsy WRITE call had retry/backoff or inter-item pacing before this round (reads via `etsy_get` did; writes didn't).

**This round — branch `fix/etsy-rate-limit-guard`, based on `origin/main` (not the docs branch behind PR #101, which was merged into `main` later — untouched this round).** Added a rate-limit guard/backoff layer in `app.services.etsy_http`: `etsy_patch`/`etsy_put` now share the same retry-with-backoff core `etsy_get` already had (`_request_with_retry`: exponential backoff honoring `Retry-After`, `ETSY_RETRY_MAX_ATTEMPTS=3`, jitter), plus a new `sleep_before_etsy_write()` — a per-shop minimum-spacing gate (`ETSY_BULK_WRITE_DELAY_MS`, bumped from the unused 200ms default to 1100ms) called at every write entry point (`patch_etsy_listing`, `patch_etsy_listing_inventory`, `fetch_etsy_listing_inventory`, `put_etsy_listing_inventory`) so a multi-item apply/revert loop can't rapid-fire past Etsy's limit — deliberately NOT applied to general listing-sync reads. `EtsyWriteError`/`EtsyVariationWriteError` now carry `retry_after_seconds`; the shared write-diagnostics dict (already sanitized, no secrets) gained `rate_limited`/`retry_attempt`/`max_attempts`/`final_rate_limit_exhausted` fields — 429 is the only status retried/flagged rate-limited, 400/401/403/404 stay distinct and non-retryable. Frontend (`apps/frontend/app/(app)/bulk-edit/page.tsx`) gained a dedicated 429 failure category and a retry-count-aware detail message ("Etsy returned HTTP 429: ... Retried N/3 times; try again later.").

**No Etsy API call was made by Claude/Codex this round** — everything above is code-only, verified via existing production log/DB reads and the owner's own report, per this task's hard safety rules. 33 new backend tests added (`test_etsy_rate_limit_guard.py` — retry/backoff/pacing primitives; additions to `test_bulk_edit_inventory.py` — write-path wiring, retry_after threading, no-token-leak; addition to `test_bulk_edit_revert.py` — Magic Revert 429 handling). Full targeted suite (`test_bulk_edit_inventory.py`+`test_bulk_edit_apply.py`+`test_bulk_edit_revert.py`+`test_bulk_edit.py`+new file): 182 passed, 8 pre-existing failures confirmed present on `origin/main` before this branch too (all `*_requires_auth`/`*_blocked_when_etsy_not_configured` — unrelated, not a regression). `git diff --check` clean, secret scan clean.

**Not yet done as of this write-up:** commit, push, PR open, CI watch, merge, deploy. Do that next: commit `fix(bulk-edit): add Etsy rate limit guard`, push `fix/etsy-rate-limit-guard`, open PR, wait for all 6 required checks, merge if green, verify prod health endpoints only. **Do not perform any live Etsy write after this deploys.** Owner's next action, in order: (1) Magic Revert on the French Bulldog listing, (2) if that succeeds, one more single-listing price apply after a pause, (3) only then consider a 3-listing bulk test — all owner-run, not Claude/Codex-run.

**Safety constraints still active (unchanged):** never print secrets/tokens; no live Etsy write; no real Stripe action; do not disable Private Beta; no DNS/Cloudflare changes; no staging action; do not merge PR #101; do not touch `docs/hiveai-dashboard-and-tasks`.

---

## Previously — 2026-08-29 (TASKS.md converted to H!veAI milestone format; independent PR #104 audit CONDITIONAL)

**`TASKS.md` was fully rewritten into the H!veAI-style milestone ledger** (`# BULK EDIT MASTER TASKS`, `M00`-`M20`, `### Mxx.yy` packages, `[x]`/`[~]`/`[ ]`/`[!]` checkboxes, per-milestone status lines) — same structure as `AI-Commerce-HQ`'s `H!veAI/TASKS.md` (fetched directly from GitHub as the format authority, not guessed). Old ad hoc "Sprint 1/2/3..." numbering is retired; every prior sprint item was mapped into the new milestone map (see `TASKS.md`'s own "Milestone policy" section for the mapping rationale). Structure validated: 21 milestone headers, 21 status lines, 95 packages, no malformed checkboxes. `.hiveai/PROJECT_DASHBOARD.md` "Current operating state" refreshed to match, still pointer-only.

**Before converting, an independent strict audit of PR #104** (`fix(billing): align bulk edit limits with effective plan and add listing detail page`) was run — code read directly (not the builder log taken on faith), fresh test execution, fresh `tsc`/`lint`/`build`, fresh `git diff --check`/secret scan. **Verdict: CONDITIONAL** — 0 BLOCKER, 0 MAJOR. 1 MINOR: the PR's self-reported test-pass count ("176 passed") did not match an independent rerun (171 passed of 180 collected on the same command) — the underlying claim re-verified true (same 9 named pre-existing failures, all new tests pass, no regression), only the headline number was wrong. 1 NOTE: no live-browser click-through of the new Listings navigation was performed (already self-disclosed in the original execution log, not a hidden gap). Full audit file: `2026-08-29_13-31_AUDIT_PR104_billing_gate_product_detail.md`. Per the gate rule (CONDITIONAL-with-only-MINOR/NOTE → continue), Phase 2 (this conversion) and Phase 3 (Account-01) proceeded.

**Both phases happened on `docs/hiveai-dashboard-and-tasks` (PR #101 — merged into `main` later) for docs, and a separate fresh runtime branch for Account-01 — see the next section below once that phase completes.**

---

## Previously — 2026-08-29 (Bulk apply/revert owner-verified; UX-01A in progress)

**Owner ran a 33-listing bulk price apply and a 32-listing bulk Magic Revert live (2026-08-29), both under the PR #102 rate-limit guard.** Apply: `price_amount=6288` on 33 listings, UI status `completed_with_errors`, Success 32 / Failed 0 / Skipped 1 (1 listing was already at 6288 — correct no-op). Owner's tracking interpretation: 100% successful business outcome. Etsy Shop Manager confirmed `$60.00`→`$62.88`. Revert: `completed`, Restored 32 / Failed 0 / Skipped 0, Etsy confirmed `$62.88`→`$60.00`. **This is documentation/tracking only — no frontend/backend status wording, `completed_with_errors` semantics, or skipped/no-op labeling was changed.** See `TASKS.md` 1.11, 1.12, 2.1, 2.4, 2.6 for full detail.

**New issue found during the same live test:** the Apply/Revert confirmation modal stays interactable while the write is in flight — owner clicked confirm 4-5 times mid-operation. Tracked as **UX-01A**, this session's runtime task: ref-level double-submit guard + full-page blocking loading overlay ("Writing changes to Etsy…" / "Reverting Etsy listings…"). Branch `fix/bulk-edit-apply-revert-loading-guard`, frontend-only, based on latest `origin/main` (past PR #102's `c68b464`). Explicitly not touching job status semantics, skipped/no-op wording, or result card colors.

**Also recorded this session (documentation only, not implemented):** UX-01B (product detail page `/listings/[listingId]`), UX-01C (Listing Health issue detail + Shop Insights affected-listings navigation), UX-01D (product-page action/credit/write-surface architecture) — see `TASKS.md` Sprint 12.3 for full acceptance criteria. None of these are implemented in this session.

**Branch discipline this session:** docs work stays on `docs/hiveai-dashboard-and-tasks` (PR #101 — merged into `main` later). Runtime UX-01A work is on a fresh branch from `origin/main`, never on the docs branch. No cherry-picking either direction.

---

## Previously — 2026-08-28 (Price write solved live — task authority moved to TASKS.md)

**PR #100 (merge `c880c91`) deployed, and the owner's live retest succeeded.** The `readiness_state_id` fix worked: French Bulldog listing, `price_amount` 6000→6288, Bulk Edit reported Success 1/Failed 0/Skipped 0, Etsy Shop Manager showed `$62.88`, Bulk Edit Listings showed `USD 62.88` after sync. **The Bulk Edit price-write payload/schema problem that spanned PR #89 through #100 is now resolved and owner-verified.**

A follow-up manual price test on a different listing hit `HTTP 429` ("Exceeded per second rate limit") — a genuinely different, expected class of problem (Etsy rate limiting under repeated manual writes), not a recurrence of the payload bug. This is now tracked as the next engineering risk.

**`TASKS.md` was restructured this session (PR #101, branch `docs/hiveai-dashboard-and-tasks` at the time — merged into `main` later) into the canonical sprint roadmap and task ledger — it is now the authoritative source for current work, superseding this file's prior blow-by-blow round tracking.** `.hiveai/PROJECT_DASHBOARD.md` is a pointer manifest for H!veAI, not a task ledger — see it for source-of-truth pointers. This `HANDOFF.md` stays as the short next-session resume note; see `TASKS.md` for the full sprint detail and acceptance criteria.

**Immediate next actions (see `TASKS.md` for full detail):**
1. Owner manual test: Magic Revert on the successful French Bulldog price change (confirm Etsy returns to `$60.00`, Bulk Edit Listings shows `USD 60.00` after sync).
2. Engineering: Etsy rate-limit guard/backoff (Sprint 2) before any 3/10/33-listing batch price tests are attempted.
3. Then continue the roadmap: Sprint 3, data coverage and shared listing source work.

**Do not run larger batch live-write tests until Magic Revert is proven and a rate-limit guard exists, or the owner explicitly accepts the risk.**

**Safety constraints still active (unchanged):** never print secrets/tokens; no live Etsy write; no real Stripe action; do not disable Private Beta; no DNS/Cloudflare changes; no staging action; do not create a new Etsy developer app; do not submit another Etsy appeal; do not perform live OAuth completion without explicit per-session owner approval.

**Earlier today (2026-08-27), for context, in order:** (1) Private Beta was blocking sign-in entirely, including masking the OAuth callback's `/shops?...` redirect behind `/private-beta?...` — fixed, `fix/private-beta-allow-signin`, merged `4a232fb`. (2) `/etsy/callback` had zero logging anywhere in its failure path — added 11 safe categories, `fix/etsy-oauth-safe-callback-logging`, merged `34b53c9`. (3) `doctl` auth had expired (`401`) — restored via a local-only script reading the token from `deploy-production.local.env` directly into doctl's config file (never printed, never a CLI arg). (4) Owner retried OAuth; diagnosed as `etsy_oauth_shop_lookup_failed` / 403, provisionally attributed to Personal Use access tier. (5) Shipped defensive `user_id` validation (`fix/etsy-oauth-user-id-validation`, merged `48f5a02`) — didn't fix the 403, closed an unrelated real gap. (6) x-api-key format fix (`fix/etsy-oauth-shop-lookup-x-api-key`, merged `9336c53`) — this was the actual 403 root cause, confirmed by the next retry no longer 403ing. (7) Owner retried again post-deploy: new failure, `etsy_oauth_shop_not_found`; owner confirmed active shop exists; response-shape parsing bug found and fixed above.

**Previously (2026-07-31), for context:** Etsy issued new developer-app credentials for `bulk-edit-app` (owner received Keystring + Shared Secret directly from Etsy, rate limit 5 QPS / 5000 QPD — matching this project's existing `ETSY_API_REQUESTS_PER_SECOND`/`ETSY_API_DAILY_LIMIT` defaults exactly, no code change needed). Credentials were configured as encrypted `SECRET` env vars on `bulk-edit-prod-api` via `doctl apps update --spec`, and production OAuth URL generation was verified end-to-end against the live API (masked keystring `qvmj...fh33`, callback `https://api.bulkeditapp.com/api/v1/etsy/callback`, scopes `listings_r listings_w shops_r profile_r`, PKCE `S256` present). Live OAuth completion was deliberately NOT performed that session — that still needed explicit owner go-ahead (see `TASKS.md` Owner Action). Full detail: `CHANGELOG_AI.md` entry `2026-07-31`.

**Mid-task bug caught and fixed in the 2026-07-31 session (documented for anyone touching `.ops-local` deploy scripts later):** an initial PowerShell env-patch script used `[regex]::Replace($text, $pattern, $replacement, 1)` intending "replace first match only" — the 4th positional arg to the *static* `Regex.Replace` overload is actually `RegexOptions`, not a match-count limiter, so `1` was silently interpreted as `IgnoreCase` and the patch applied to every `envs:` block in the spec (api service + both jobs), triple-duplicating the new Etsy env entries and leaving the old encrypted values still present too. Caught by re-fetching and grep-counting keys (values redacted) before trusting the deploy; fixed with a YAML-aware Python pass (`.ops-local/fix-etsy-env-duplicates.py`, PyYAML) that deduped to exactly one entry per key in the `api` service and stripped the 6 stray entries each from `migrate`/`retention-cleanup` jobs, then redeployed and re-verified counts. Net effect on production: two consecutive `bulk-edit-prod-api` deploys this session, both `ACTIVE`, final state clean and confirmed. `.ops-local/deploy-etsy-env-to-digitalocean.ps1` still contains the original buggy regex path — **do not trust its "patch existing" branch as-is**; it needs the same fix (or should be replaced by the Python approach) before reuse.

**Previously (2026-07-16), for context:** the Etsy appeal had been **submitted by the owner** and production was LIVE and fully healthy (backend/frontend/DB/Redis confirmed, migration `0025`, Private Beta enabled). Retention cleanup Option A (DO Scheduled Job) had two consecutive successful runs. PR #64 aligned the public website with the submitted appeal. That waiting period is now resolved by the credential issuance above.

**Critical environment facts:**
- Hosting: DigitalOcean App Platform (`bulk-edit-prod-api`, `bulk-edit-prod-web`) + Cloudflare. App IDs: prod-api `2f37fa86-a826-4dc2-b5d3-22f44d85cb1c`, prod-web `fb4415ca-cd2d-4929-a754-08f1893f4d25`.
- **Merging to `main` triggers an immediate production rebuild for BOTH apps** (`deploy_on_push: true`, no path filter) — even a docs-only merge redeploys both. Always confirm DB backup + any relevant preflight *before* merging, not after; the merge itself is the deploy trigger.
- Retention job monitoring: `doctl apps list-job-invocations <app-id> --job-name retention-cleanup --format ID,Jobname,Created,Started,Completed,Phase`, then `doctl apps logs <app-id> retention-cleanup --job-invocation <id> --type run`. (`--component` is not a real flag — component name is positional.)
- Checking Alembic revision live without a direct DB connection: the `migrate` PRE_DEPLOY job (`alembic upgrade head`) runs on every deploy — `doctl apps logs <api-app-id> migrate --deployment <deployment-id> --type run` shows "Running upgrade" lines only if something was actually applied. No lines + a repo migration chain topping out at the expected revision = confirmation, without ever opening a credentialed DB connection. (A prior session attempt to install a DB driver for a direct query was correctly blocked by the permission system — don't repeat that; this log-based method is the safer existing path.)
- Backend tests: 982 passed (current authoritative count).

**Current branch/PR state:** `main` is clean and matches `origin/main`. No open feature branches from this session (no code change was needed — env/config only).

**Unresolved work:** engineering side is done for this credential-configuration pass. The only remaining step is an **owner decision**: explicitly approve a live OAuth test (connect one real test Etsy shop, no writes) before anything Etsy-live is exercised further.

**Exact next step:** get owner approval for a live OAuth test per `TASKS.md` → Owner Action, then connect one test shop, confirm token exchange, and re-verify live Etsy reads (writes stay preview-gated as always — see `CLAUDE.md` rule 2). Do not create a new Etsy developer app, do not disable Private Beta, do not enable Etsy-derived external AI processing (`ALLOW_ETSY_DATA_TO_AI`), do not perform any Etsy write, and do not submit another appeal.

**Safety constraints still active:** never print secrets/tokens or DigitalOcean's `EV[...]` encrypted placeholders; no live Etsy write; no real Stripe charge/subscription/refund without explicit instruction; do not disable Private Beta without explicit instruction; no DNS/Cloudflare/owner-domain changes without explicit instruction; do not deploy without explicit go-ahead beyond normal PR-merge flow; do not submit another Etsy appeal or contact Etsy again unless the owner explicitly decides to; do not perform live OAuth completion without explicit per-session owner approval even though credentials are now configured.

---

## Known Issues (carried forward, still accurate)

- Etsy access-token auto-refresh: implemented and wired into the sync path (fixed during the 2026-07-13 compliance pass — earlier notes calling this "not implemented" are stale).
- `fetch_listing_videos` is best-effort — returns empty list on 404/405.
- Image reorder has no live Etsy endpoint — delete-then-reupload is the only workaround and was deliberately not implemented (real risk window on a live listing) — see `DECISIONS.md`.
- `AuditLog` model uses `extra_data` in Python, stored as `metadata` column in DB (SQLAlchemy reserves `metadata`).
- `anyio==4.6.2` in `requirements-dev.txt` is yanked upstream but works fine — upgrade when 4.7.0 is stable.
- Frontend `node_modules` may be absent on a fresh checkout — run `npm install` inside `apps/frontend` or `docker compose up`.

## Local Development

- `start-dev.bat` / `start-dev-clean.bat` — Windows one-click dev startup (see `README.md` for full instructions).
- Ports: frontend 3100, backend 8100, Postgres 55432, Redis 56379.
- Windows note: host-port binding to 55432 can hit a Hyper-V/WSL2 dynamic-port reservation conflict — see `docker-compose.dev-ports.yml` and `DECISIONS.md` for the workaround (already applied in `docker-compose.yml` via `expose:` instead of `ports:` for postgres/redis).
