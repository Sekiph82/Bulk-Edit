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
- PR #101 (`docs/hiveai-dashboard-and-tasks`) remains open and is **not merged**.
- **Account-01 (M11) shipped as PR #105** (Account Center `/account` 11-route subnav, Connected Shops relocated from `/shops`, customer-safe Plan/Billing/Usage/Credits UI) — merged and deployed 2026-08-29. This docs branch has not yet done a full M11 checkbox backfill against that PR; see `CHANGELOG_AI.md`/main-branch `HANDOFF.md` for the shipped detail in the meantime.
- **UX-01D (owner visual QA remediation, PR #106) addressed 6 owner-reported issues** — Magic Revert nav placeholder, Media page listings-load bug, Bulk Create false shop-gate, product-detail image/layout fixes, truthful Performance metrics (no fake data), 3 recommendation banners removed. See M09.06, M13.01, M15.01, M16.03.

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
- [ ] Shop filter, status filter, title search, pagination, thumbnail, variation indicator, selected count, empty/error/loading states.
- [ ] Consumers: Bulk Edit, Variations, Dynamic Pricing, Media, Video Generator, Promote.

### M03.05 - Variations/Dynamic Pricing/Media listing visibility
- [ ] Variations page shows listings instead of a false empty state; distinguishes `has_variations`/`no_variations`/unknown.
- [ ] Dynamic Pricing page shows listings; suggestions remain preview-only.
- [ ] Media page loads listings when listings exist; operations remain read-only until M13.

M03 PARTIAL — listing sync foundation PASS, shared-picker/status-filter work PLANNED.

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

M08 PARTIAL — core gate-correctness IMPLEMENTATION COMPLETE (CONDITIONAL per M08.02 audit, only MINOR/NOTE items open), owner/admin-facing billing tooling PLANNED.

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
- [x] Magic Revert added to main nav (`/magic-revert`, new truthful placeholder route — explains today's in-flight-only behavior, links to Bulk Edit and `/account/activity`).
- [x] Removed 3 recommendation/cross-sell banners (Listings, Listing Health, Profit) for a cleaner customer SaaS feel — grepped for more, none found elsewhere.
- [ ] Owner click-through of the polished layout/image/metrics (still pending, same as M09.04's open item).

M09 PARTIAL / IMPLEMENTATION COMPLETE FOR SHIPPED ITEMS, PENDING OWNER CLICK-THROUGH VERIFICATION.

---

# M10 - Listing Health and Shop Insights workflow

### M10.01 - Listing Health issue detail
- [ ] Show issue detail, not just a count: tag count (e.g. `0/13`), photo count, title length, description length, missing/zero price, zero quantity, variation warnings, personalization/materials warnings where data supports them.

### M10.02 - View Product / Fix in Bulk Edit paths
- [x] "Fix in Bulk Edit" pre-existing on the Listing Health table.
- [x] "View Product" link added, same internal listing id (PR #104) — minimal addition, no issue-detail redesign mixed in.

### M10.03 - Shop Insights affected listings
- [ ] "Affected Listings" mini-sections (missing tags, low photo count — first 10 each), each with `View Product` and `Fix in Bulk Edit`. Metric cards clickable where useful.

M10 PLANNED / PARTIAL (View Product link only).

---

# M11 - Account Center and Connected Shops

**Account-01** — Customer Account Center + Connected Shops + customer-safe Plan/Usage UI. Replaces standalone Billing/Shops pages as the primary customer account surface. No customer-facing admin/comp-grant terminology.

### M11.01 - Account information architecture
- [ ] Replace standalone Billing as the primary customer account surface.
- [ ] Add Account main navigation entry.
- [ ] Add Account subnav: Overview, Plan & Billing, Usage, Credits, Connected Shops, Team / Users, Security, Notifications, Activity & Audit, Data & Privacy, Support.
- [ ] Remove Shops from main navbar after Connected Shops is ready.

### M11.02 - Plan & Billing customer-safe presentation
- [ ] Show effective customer plan without internal grant/source terminology.
- [ ] Avoid customer-facing "admin", "comp grant", "manual admin", "admin comp" wording.
- [ ] Present the owner/test account as Pro Monthly using normal customer-facing Pro features/limits.
- [ ] Preserve truthful Stripe/payment state without a confusing "Free Plan" main badge when the effective plan is Pro.

### M11.03 - Usage dashboard
- [ ] Show bulk edit usage used/limit/remaining/reset period.
- [ ] Show AI credits used/limit/remaining.
- [ ] Show media, dynamic pricing, scheduled jobs, listings/shops limits where available.
- [ ] Use the same effective plan/limits as the M08 backend gates.

### M11.04 - Credits
- [ ] Show AI credit balance and monthly limit.
- [ ] Explain which features consume AI credits.
- [ ] Add credit history placeholder or real history if existing.

### M11.05 - Connected Shops
- [ ] Move current Shops functionality into Account → Connected Shops.
- [ ] Show connected Etsy shops, connection status, shop name, last sync/listing count if available.
- [ ] Preserve Connect Etsy flow.
- [ ] Preserve reconnect/disconnect/sync actions only where currently supported.
- [ ] Keep `/shops` backward compatible as a redirect or hidden functional route.

### M11.06 - Team / Users
- [ ] Add placeholder or MVP for account owner/team roles.
- [ ] Do not expose admin internals to the customer.

### M11.07 - Security
- [ ] Add Account Security placeholder/MVP.
- [ ] Add active sessions/password/2FA future hooks where appropriate.

### M11.08 - Notifications
- [ ] Add notification preference placeholder/MVP.

### M11.09 - Activity & Audit
- [ ] Add Activity & Audit placeholder/MVP.
- [ ] Reserve this area for Apply Jobs / Magic Revert History (see M16).

### M11.10 - Data & Privacy
- [ ] Show AI data usage setting/status where supported.
- [ ] Add export/delete/disconnect placeholders without fake functionality.

### M11.11 - Support
- [ ] Add help/support/report-bug placeholders or links.

M11 ACTIVE / IN PROGRESS.

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
- [ ] Still loads via a page-local `getListings()` call, not yet the shared `ListingPicker` component (M03.04).

### M13.02 - Listing image read-only view
- [ ] Image count, primary image, missing-media warnings; no reorder/delete/upload until enabled.

### M13.03 - Etsy listing video upload workflow
- [!] Blocked — implemented historically but never live-tested. Needs owner-approved single-listing test, preview/confirmation, item-level report, rate-limit handling (via M07).

### M13.04 - Media delete/revert strategy
- [ ] No destructive media operation without a recovery story; delete requires explicit confirmation.

### M13.05 - Video Generator real workflow
- [ ] Listing-based image auto-fetch (replace manual URL paste), batch selection, one video job per listing, item-level states, preview/approval before any Etsy upload, upload to existing listing only after approval.

### M13.06 - Promote (Pinterest/Instagram)
- [!] Blocked on external app setup: Pinterest developer app + redirect URI + scopes; Meta developer app + Instagram Graph API + business/creator permissions; production review if required.
- [ ] Caption/hashtag generation (preview, editable, respects the AI data policy in M12.01).
- [ ] Schedule/post now, explicit time zone, item-level report, no silent posting.

M13 PLANNED / BLOCKED on several external integrations.

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
- [ ] Fetch and store/read variation products/offerings/property_values in a safe local representation; read-only matrix view first.
- Owner-observed (2026-08-29): Variation Bulk Editor shows "No variation listings found" for the connected shop. **Audited, not treated as a confirmed bug** — the `has_variations=true` filter uses the same shared `getListings()` helper as the Listings page and a real, correctly-synced Etsy field, so this may be a truthful zero-result for this shop rather than a broken filter; no live/authenticated way exists in this session to check the real count. Empty state improved (distinguishes no-data from no-search-match) without loosening the filter. Revisit if the owner confirms variation listings do exist in the connected shop.

### M15.02 - Variation price edit preview
- [ ] Owner can preview variation-specific price changes; no write until explicit approval.

### M15.03 - Variation quantity edit preview
- [ ] Per-offering quantity preview; invalid combinations blocked before write.

### M15.04 - Variation write apply/revert
- [ ] Single variation listing tested first; preserve SKU, property_values, readiness_state_id, price_on_property, quantity_on_property, sku_on_property; revert works for succeeded variation writes.

### M15.05 - Variation diagnostics
- [ ] Item-level failure shows exact safe reason; no raw Etsy body, token, secret, or header leak.

M15 PLANNED.

---

# M16 - Activity, audit, history, and Magic Revert history

### M16.01 - Standardized item-level write logs
- [x] Bulk Edit price/title write failures have sanitized, safe diagnostics (M05.04, extended in M07.03/M08.02).
- [ ] Standardize the same shape for media upload and social post write paths once M13 ships.

### M16.02 - Apply Job history
- [ ] Surface existing apply-job records (already persisted) in a dedicated Activity view — see M11.09 for the Account-side placeholder this feeds.

### M16.03 - Magic Revert from prior jobs
- [ ] Allow reverting a job other than the one just completed, not only the most recent apply result.
- [x] A truthful nav-level placeholder for this now exists (2026-08-29, UX-01D): `/magic-revert`, linked from the main nav, explicitly states this isn't built yet and links to `/account/activity` (where it will eventually live) and `/bulk-edit` (today's actual Magic Revert entry point). Not a functional implementation of this package — just makes the gap discoverable and honest instead of the feature being invisible.

### M16.04 - Audit/activity table
- [ ] Searchable by user/shop/listing/job/date; export-safe summary; no secrets.

### M16.05 - Revert availability status per item
- [ ] Show whether each historical item is still revertible (backup snapshot present, listing unchanged since apply — depends on M06.03).

M16 PLANNED.

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
