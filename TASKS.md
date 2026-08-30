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
- [ ] Sync `active`/`draft`/`inactive`/`expired`/`sold_out` statuses, read-only, no accidental activation/deactivation.

### M03.03 - Listing status filters on Listings page
- [ ] All/Active/Inactive/Draft/Expired filters with counts matching synced data.

### M03.04 - Shared ListingPicker component
- [~] Component shipped: `apps/frontend/components/listings/ListingPicker.tsx` — shop filter (behind `showShopFilter`, hidden when the org has ≤1 shop), status filter, title search, pagination, thumbnail (`ListingListItem.thumbnail_url`, already returned by `getListings()`), variation indicator (`has_variations` badge), selected count, loading/error/empty states (with an overridable `renderEmpty` for consumer-specific honesty, e.g. Variations' no-data-vs-no-match distinction), multi-select and single-select modes, `disabled` read-only mode.
- [x] Media migrated — replaced its client-side-only, unpaginated, thumbnail-less picker.
- [x] Variations migrated — same component with `extraParams={{ has_variations: true }}`, preserving its existing no-data-vs-no-search-match empty-state distinction via `renderEmpty`.
- [ ] **Not migrated this round, remaining consumers:** Dynamic Pricing (`pricing-rules/page.tsx` has a "select all *loaded* listings" action tied to holding the full un-paginated listings array client-side — doesn't map cleanly onto the picker's own paginated fetch; not "straightforward" per this package's own scope rule), Bulk Edit (949-line file with the live working apply flow — explicitly higher-risk than this round's non-destructive scope), Video Generator and Promote (neither currently calls `getListings()` at all — manual-URL/other selection flows — migrating them is a larger rewrite than a picker swap, left for a dedicated round).

### M03.05 - Variations/Dynamic Pricing/Media listing visibility
- [x] Variations page shows listings instead of a false empty state; distinguishes `has_variations`/no-data/no-search-match via `ListingPicker`'s `renderEmpty`.
- [ ] Dynamic Pricing page shows listings — already did, pre-existing, unchanged this round; suggestions remain preview-only.
- [x] Media page loads listings when listings exist; operations remain read-only/preview-gated until M13 (unchanged).

M03 PARTIAL — listing sync foundation PASS; shared `ListingPicker` SHIPPED and migrated into Media + Variations (M03.04); Dynamic Pricing/Bulk Edit/Video Generator/Promote consumer migration remains PLANNED.

---

# M04 - Bulk Edit preview/session/apply foundation

### M04.01 - Bulk Edit session/preview/apply core
- [x] Session creation, change staging, preview generation, apply execution — pre-existing core mechanism.

### M04.02 - Change remove fix
- [x] `apiFetch()` 204-handling bug fixed in the shared client, not just the remove-change call site (PR #91) — also fixed 4 other affected `204` routes.

### M04.03 - Apply job state machine
- [ ] States: `pending`, `running`, `succeeded`, `partially_failed`, `failed`, `rate_limited`, `cancelled`, `reverted`, `revert_failed`.
- [ ] UI shows clear batch progress and final state; jobs survive refresh.

### M04.04 - Single/small-batch apply-revert verification matrix
- [x] 33-listing price apply/revert — owner-verified live (Success 32/Failed 0/Skipped 1 apply; Restored 32/Failed 0/Skipped 0 revert; Etsy confirmed both price directions).
- [ ] 3-listing and 10-listing batch sizes — not separately tested.
- [ ] Non-price fields (title/tags/etc.) at batch scale — not separately tested.

M04 PARTIAL.

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
- [ ] Not implemented.

### M06.04 - Audit trail for writes
- [ ] Per-item record: who/when/shop/listing/field/before/after/result/job/session/revert status, searchable and safe to export, no secrets persisted. See also M16.

M06 PARTIAL.

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
- [ ] Owner can view users, orgs, shops, plans, sync status, recent write jobs; grant/revoke comp access safely with an audit trail. Currently owner-console/API-only (`POST /admin/organizations/{org_id}/comp`).

### M08.05 - Stripe production workflow review
- [ ] Products/prices re-verified, webhook endpoint status manually checked in Stripe dashboard, no accidental real charge during tests.

### M08.06 - Private beta user management
- [ ] Invite/allowlist strategy; beta users supported without direct DB edits.

### M08.07 - Magic Revert plan-gate enforcement
- [x] Closed: `validate_apply_job_revertable()` now resolves the effective plan (`get_effective_plan()`, comp-grant aware — not raw `Subscription.plan`) and blocks with `403 "Magic Revert is not available on your current plan."` when `can_use_magic_revert` is false, checked last (after org-ownership, status, zero-success, and duplicate-revert checks) so an already-reverted job still reports "Already reverted." rather than plan-blocked, and no cross-org job existence leaks. `get_revert_eligibility_map()` mirrors the same rule in the same precedence order, resolving the effective plan once per history request (not per job — no N+1). 8 new backend tests (Free blocked direct + history, Pro/comp-grant-Pro allowed, precedence, cross-org, zero-success-still-blocked). Existing ~25 pre-existing revert-mechanics tests updated via a `grant_plan="pro_monthly"` default on the shared `_setup_and_apply()` fixture (comp-grant path, not a raw plan mutation) rather than weakened.

M08 PARTIAL — core gate-correctness IMPLEMENTATION COMPLETE (CONDITIONAL per M08.02 audit, only MINOR/NOTE items open), owner/admin-facing billing tooling PLANNED, Magic Revert plan-gate enforcement SHIPPED (M08.07).

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

### M10.02 - View Product / Fix in Bulk Edit paths
- [x] "Fix in Bulk Edit" pre-existing on the Listing Health table.
- [x] "View Product" link added, same internal listing id (PR #104) — minimal addition, no issue-detail redesign mixed in.

### M10.03 - Shop Insights affected listings
- [x] "Affected Listings" mini-sections shipped on `/insights`: Missing tags, Low photo count, Short titles, Missing/zero price, Zero quantity — first 10 per section (new `GET /insights/affected-listings` endpoint, local-DB-only, no Etsy call), each item showing thumbnail (or a placeholder), title, the relevant metric (e.g. `0/13 tags`, `1 photo`, `9-char title`, `No price set`, `0 in stock`), `View Product`, and `Fix in Bulk Edit`. Section header shows the true total count even when more than 10 exist. Empty sections are hidden rather than shown with zero rows.

M10 PARTIAL — M10.02/M10.03 SHIPPED; M10.01 issue-detail surfacing SHIPPED for the categories the scoring engine actually computes (title/tags/description/photos/price), zero-quantity/variation/personalization issue *detection* remains a backend follow-up.

---

# M11 - Account Center and Connected Shops

**Account-01** — Customer Account Center + Connected Shops + customer-safe Plan/Usage UI. Replaces standalone Billing/Shops pages as the primary customer account surface. No customer-facing admin/comp-grant terminology.

### M11.01 - Account information architecture
- [x] Replace standalone Billing as the primary customer account surface — `/billing` is now a thin client-side redirect to `/account/billing` (PR #105).
- [x] Add Account main navigation entry.
- [x] Add Account subnav: Overview, Plan & Billing, Usage, Credits, Connected Shops, Team / Users, Security, Notifications, Activity & Audit, Data & Privacy, Support.
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

M11 MOSTLY SHIPPED (Account-01, PR #105) — information architecture, Plan & Billing, Usage, Connected Shops, Team, Security, Notifications, Support all shipped; Activity & Audit superseded by the real PR #107 implementation. Remaining PLANNED: credit history, 2FA/session hooks, Data & Privacy export/delete functionality.

---

# M12 - AI tools and compliance-safe automation

### M12.01 - AI provider policy gate
- [x] `ALLOW_ETSY_DATA_TO_AI` defaults `false`, not overridden in production; `AI_PROVIDER=mock` in production, so no live AI provider call is possible regardless of the flag.
- [ ] UI explains when AI is unavailable due to policy.

### M12.02 - AI listing suggestions
- [ ] Preview-only suggestions; user must approve before any write; clear before/after diff.

### M12.03 - AI tool usage limits
- [x] Backend gate now uses the effective plan (M08.03).
- [ ] Clear monthly usage counters in the UI (see M11.04).

### M12.04 - Prompt and output audit
- [ ] Safe logs record prompt category and item id, not secrets; Etsy-derived content handling explicit.

M12 PLANNED / PARTIAL (policy default only).

---

# M13 - Media, photos, video workflows, and Promote

### M13.01 - Media module listing picker
- [x] Fixed a real loading bug (2026-08-29, UX-01D): `load()` used `Promise.all([getListings, listMediaJobs, listVideoRenders])` — a failure in the unrelated `listMediaJobs()` call rejected the whole batch and blanked the listings picker with a misleading "Failed to load listings," even though `getListings()` (same helper the Listings page uses) would have succeeded. Decoupled into independent try/catches.
- [x] Now uses the shared `ListingPicker` component (M03.04, 2026-08-30) — gained thumbnails, server-side status filter, and pagination it never had as the page-local version.

### M13.02 - Listing image read-only view
- [x] Product detail page (`/listings/[listingId]`) Media card now shows a full read-only thumbnail grid of every synced image (was: primary image + count + "Full image gallery is not available yet."), plus a truthful amber warning when zero photos are synced. No reorder/delete/upload control added — grid is display-only.

### M13.03 - Etsy listing video upload workflow
- [!] Blocked — implemented historically but never live-tested. Needs owner-approved single-listing test, preview/confirmation, item-level report, rate-limit handling (via M07).

### M13.04 - Media delete/revert strategy
- [~] Audit found this is a live, already-shipped feature (not something this round is introducing): the Media page's `add_image`/`replace_image`/`delete_image`/`add_video`/`replace_video`/`delete_video` operations are all fully implemented and enabled, and a `MediaBackup` row is created before every write ("Backups are created before every write," pre-existing page copy) — but no revert/restore endpoint exists anywhere (confirmed via grep across `app/api/v1/*.py`, zero matches for a media-revert route). A customer who deletes or replaces media today cannot self-recover through the app despite the backup row existing. **Fixed this round:** `replace_image`/`delete_image`/`replace_video`/`delete_video` (every operation that can lose an existing asset) are now disabled in the operation picker with truthful "coming soon — no restore yet" labels; `add_image`/`add_video` (purely additive, nothing lost) stay enabled. Recovery-story implementation (an actual restore endpoint reading `MediaBackup`) remains planned.

### M13.05 - Video Generator real workflow
- [~] Listing-based image selection shipped: a "Select from a listing's synced photos" option (alongside, not replacing, manual URL paste) uses the shared `ListingPicker` + `getListingImages()` to populate the same image-URL list the existing render form already used — the actual render-triggering path (`handleRender`) is completely untouched. Preview/approval, per-listing job state, and the existing "not yet Etsy-uploaded until approved" flow were already in place and are unchanged. Batch selection (multiple listings → multiple jobs) not added this round.

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
- [ ] Current price, quantity, listing status, product cost (if available), shipping cost/profile (if available), Etsy fees model (if implemented), manual margin target.

### M14.02 - Profit page validation
- [ ] Numbers explainable, missing cost data clearly marked, no fake precision.

### M14.03 - Pricing suggestion engine
- [ ] Suggests price changes with a stated reason, preview-only by default, user chooses exact listings.

### M14.04 - Dynamic Pricing write handoff
- [ ] Uses the M07 write queue/rate-limit guard; item-level report and revert available. Backend gate already effective-plan-correct (M08.03).

M14 PLANNED.

---

# M15 - Variations and inventory depth

### M15.01 - Variation inventory read model
- [x] Audit found the read model already exists and is already populated (confirmed via code read, not guessed): `ListingVariation` (property_id/name, value_id/name, price, quantity, SKU, availability) is written by `etsy_sync.py` on every shop sync, and `GET /listings/{id}/variations` has returned it since Sprint 5/12 — `lib/api.ts`'s `getListingVariations()` existed too. **None of it was ever rendered anywhere in the frontend.** Fixed frontend-only: the Variations page now has a "Variation Data (read-only)" panel — one row per selected listing, expandable into a real matrix (property/value/price/qty/SKU/available), truthfully distinguishing "has synced variation rows" from "has_variations on Etsy but nothing synced locally yet — run a shop sync" (the latter state was previously indistinguishable from "no data at all").
- Owner-observed (2026-08-29): Variation Bulk Editor showed "No variation listings found" for the connected shop at the time. **Still not treated as a confirmed bug** — the `has_variations=true` filter is real and correctly-synced; whether that shop's listings genuinely have zero variations is unverifiable without a live authenticated check. Unchanged this round.

### M15.02 - Variation price edit preview
- [x] Audit correction: this was already fully shipped (Sprint 12, 2026-06-26, predates this session's tracked rounds) — `generate_variation_preview()` builds a before/after diff from local `ListingVariation` data only (zero Etsy call for preview), rendered in the existing before/after preview table. Was incorrectly still marked `[ ]`; corrected based on code + the 26 existing tests in `test_bulk_edit_variation.py`, not newly built this round.

### M15.03 - Variation quantity edit preview
- [x] Same correction as M15.02 — quantity preview uses the identical `generate_variation_preview()` path; already shipped, already tested, was mismarked `[ ]`.

### M15.04 - Variation write apply/revert
- [~] Audit correction, not `[ ]` and not `[x]`: an apply mechanism already exists in code (`apply_variation_job()` — fetch-patch-put against Etsy, backup-before-write, confirm-to-apply UI with a "Type APPLY VARIATIONS" gate) and is unit-tested, but two things are genuinely missing: (1) **no owner live verification has ever occurred** for a variation write (unlike the price/title write saga, which has an extensive owner-run verification trail) — code-level tests mock Etsy and are not acceptance evidence per this file's own rule; (2) **variation revert does not exist at all** — the Sprint 12 changelog entry explicitly says "Revert for variations explicitly deferred to Sprint 13," and no revert code was ever added. Neither gap was touched this round (no live write, no revert built) — this is a documentation-accuracy correction, not new work.

### M15.05 - Variation diagnostics
- [x] `BulkEditVariationPreviewItem.validation_messages` already existed on the backend (populated by `build_variation_preview_for_listing()`) but was never rendered — fixed: the preview table now has a Diagnostics column showing the exact safe validation message(s) per item (list-formatted) instead of only a bare status badge. No raw Etsy body/token/secret ever included in these messages (confirmed via the same code path M05.04 already established as sanitized).

M15 PARTIAL — read model + matrix (M15.01), price/quantity preview (M15.02/M15.03, corrected from a stale `[ ]`), and diagnostics (M15.05) SHIPPED; apply exists+tested but never owner-live-verified and revert doesn't exist at all (M15.04, `[~]` not `[x]`).

---

# M16 - Activity, audit, history, and Magic Revert history

### M16.01 - Standardized item-level write logs
- [x] Bulk Edit price/title write failures have sanitized, safe diagnostics (M05.04, extended in M07.03/M08.02).
- [ ] Standardize the same shape for media upload and social post write paths once M13 ships.

### M16.02 - Apply Job history
- [x] Shipped (PR #107, 2026-08-29): new org-wide, paginated `GET /api/v1/bulk-edit/apply-jobs` endpoint (the only genuinely new backend capability — job detail, revert-jobs list, revert-job detail/results all already existed). Surfaced in `/magic-revert` (job table: date, status, item counts, revert availability) and `/account/activity` (synthesized Bulk Edit Apply + Magic Revert rows from the same data) — see M11.09.

### M16.03 - Magic Revert from prior jobs
- [x] Shipped (PR #107, 2026-08-29): reverting a job other than the one just completed is enabled, not just displayed. Audit found `POST /apply-jobs/{apply_job_id}/revert` already accepted **any** apply_job_id (org-scoped, idempotent, 409 on double-revert) — it was already safe for history use, just never exposed in the UI. `/magic-revert`'s revert action reuses the exact PR #103 (UX-01A) double-submit-guard + blocking-overlay safety pattern. One real backend gap fixed alongside this: `validate_apply_job_revertable()` never checked a job had ≥1 successful item before "reverting" it (harmless 0-item no-op before, now a clean 400).
- [x] The 2026-08-29 (UX-01D) nav-level placeholder at `/magic-revert` is superseded — it is now the real history/revert page described above, not a placeholder.

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
- [ ] See M08.04 — owner views users/orgs/shops/plans/sync/jobs.

### M17.03 - Comp grant management UI
- [ ] See M08.04 — owner-console UI for grant/revoke, currently API-only.

### M17.04 - Private beta user management
- [ ] See M08.06 — invite/allowlist, no direct DB edits needed for support.

### M17.05 - Beta tester checklist
- [ ] Small tester cohort flow, support contacts, known limitations, feedback capture.

M17 PARTIAL.

---

# M18 - Security, observability, and production hardening

### M18.01 - OAuth callback query-string redaction
- [ ] OAuth code/state not exposed in access logs; redaction tests or log checks exist.

### M18.02 - Sanitized Etsy error-body diagnostics
- [x] No raw Etsy response body, token, header, or secret ever persisted or displayed — established M05.04, extended through every write path added in M07/M08.

### M18.03 - Docs-only-PR production-deploy discipline
- [~] Documented in `HANDOFF.md` ("merging to `main` triggers an immediate production rebuild for BOTH apps, even a docs-only merge") — not yet enforced by tooling/CI gate.

M18 PARTIAL.

---

# M19 - Beta readiness and launch polish

### M19.01 - Production smoke-test matrix
- [ ] Auth, shop connect, sync, listings grid, bulk edit preview, title write/revert, price write/revert, media read, billing plan display, private beta routes.

### M19.02 - Help docs and owner runbooks
- [ ] How to sync, how to run a safe bulk edit, what to do on failed items, what to do on rate limit, how to revert.

### M19.03 - UX polish
- [ ] Loading states, empty states, error copy, mobile/responsive review (beyond the M07/M09 items already shipped).

M19 PLANNED.

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

- M00, M02, M05, and M07 are PASS/CLOSED on direct code/test evidence and owner live verification, not builder self-report alone.
- M01, M03, M04, M06, M08, M09, M17, M18 are PARTIAL — real shipped evidence exists for some packages, other packages remain planned or blocked.
- M10, M12, M13, M14, M15, M16, M19 are PLANNED — not started, or only a minimal linking change has shipped.
- M11 (Account-01) is ACTIVE / IN PROGRESS — the current major sprint.
- M20 is PLANNED/BLOCKED pending M19 and an owner decision on registration.
- No milestone or package may be marked `[x]` on the strength of a builder execution log alone — code read, direct test execution, route verification, or recorded owner acceptance is required, per the PR #104 independent audit precedent (`2026-08-29_13-31_AUDIT_PR104_billing_gate_product_detail.md`).
- Historical remediation truth (every merged PR, every owner-reported live-test result, every audit verdict) remains immutable in `CHANGELOG_AI.md` and the `bulkeditapp logs` archive and does not get rewritten to look cleaner in hindsight.
- Do not run live Etsy GET/PUT/PATCH from the Claude/Codex environment without explicit owner approval for that exact task.
- Do not run 3/10-listing bulk write tests, or non-price-field batch tests, casually — they remain open verification gaps (M04.04), not proven-safe.
- Do not enable external AI processing for Etsy-derived data (`ALLOW_ETSY_DATA_TO_AI`) without explicit owner approval.
- Do not disable Private Beta, change DNS/Cloudflare, change production env, or perform Stripe real charge/refund/subscription operations without explicit owner instruction.
- Do not invent new milestone numbers mid-session — new work goes into the relevant milestone's package list first; a genuinely new milestone requires the owner's explicit decision.
