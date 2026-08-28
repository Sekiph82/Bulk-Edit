# TASKS.md — Bulk Edit Master Sprint Roadmap

Last updated: 2026-08-28

This file is the canonical task source for H!veAI and for all future Claude/Codex work on `Sekiph82/Bulk-Edit`.

It replaces the short, session-style active-work list with a stable product roadmap. The older `ROADMAP.md` remains useful as historical build context, especially the original v1.0-v1.3 platform sprints, but this file is the current operational task ledger.

---

## Authority rules

1. **This file is canonical.** If a task is not in `TASKS.md`, it is not current work unless the owner explicitly promotes it.
2. **Main sprint numbers must not be invented mid-session.** New work goes into Backlog / Intake first, then the owner decides whether to add it to an existing sprint or create a formally approved new sprint.
3. **Small fixes can be inserted into the relevant sprint.** Bug fixes, diagnostics, and production repairs should be placed under the sprint they belong to instead of spawning fake new sprints.
4. **Etsy live tests are owner-run only.** Claude/Codex must not call Etsy API directly from a different IP unless the owner explicitly approves it for that exact task. Owner runs live Etsy tests from the browser/app over owner VPN.
5. **No secrets in docs/logs.** Never print, commit, or log Etsy Shared Secret, Client Secret, OAuth code/state, access/refresh tokens, DigitalOcean token, raw Authorization, raw x-api-key, cookies, raw env values, or database URLs.
6. **Production writes require staged verification.** Single item first, then revert, then small batch, then larger batch. Every write needs item-level success/failed reporting and safe logs.
7. **Merging to `main` triggers production deploy.** Even docs-only merges can redeploy both production apps. Prefer PR review before merge.
8. **H!veAI reads this file as task authority.** `.hiveai/PROJECT_DASHBOARD.md` should point here and must not duplicate the task ledger.

---

## Status legend

- `[DONE]` shipped and manually verified
- `[PARTIAL]` shipped but needs more manual verification
- `[IN_PROGRESS]` active or next immediate work
- `[TODO]` planned, not started
- `[WATCH]` working but needs monitoring/hardening
- `[BLOCKED]` blocked by owner decision, external app review, credentials, policy, or live-test approval
- `[DEFERRED]` intentionally postponed

---

## Current production facts

- Product: Bulk Edit App, Etsy bulk editing SaaS.
- Repository: `Sekiph82/Bulk-Edit`.
- Local path: `C:\Users\sekip\Desktop\Bulk-Edit`.
- Production app: `https://app.bulkeditapp.com`.
- Production API: `https://api.bulkeditapp.com`.
- Public website: `https://bulkeditapp.com`.
- Production is under Private Beta. Registration remains paused; sign-in is allowed.
- Owner/test user: `sekiphayit1982@gmail.com`.
- Connected shop: `WearYourStoriesCom`.
- Active listings synced: 210 active listings.
- Comp/pro access: owner account has `pro_monthly` comp access.
- Confirmed live title write: working.
- Confirmed live price write: working at least once after PR #100.
- Latest new risk: Etsy per-second rate limit, HTTP 429, seen during follow-up price test.

---

## Research snapshot used for this update

This roadmap was refreshed from:

- Existing repo `TASKS.md`, which still had stale state claiming the readiness-state fix was pending.
- Existing repo `ROADMAP.md`, which describes the older completed platform build sprints.
- Existing repo `HANDOFF.md` and `PROJECT_STATUS.md`, which contain the latest production safety notes but were partially stale around PR #100/live retest.
- Recent merged PRs #78, #79, #81, #82, #83, #85, #86, #87, #89, #91, #93, #94, #96, #98, #100.
- Owner-provided live screenshots and session notes from 2026-08-28.
- Owner-provided H!veAI source example for `.hiveai/PROJECT_DASHBOARD.md`.

---

# Master sprint map

The current Bulk Edit roadmap is organized into 12 stable product sprints. These are the main sprint numbers going forward.

| Sprint | Name | Current state | Purpose |
|---|---|---|---|
| 1 | Production QA and write-core stabilization | `[PARTIAL]` | Close core live Etsy write, UI trust, and immediate QA gaps. |
| 2 | Bulk Edit write hardening and rate limits | `[IN_PROGRESS]` | Revert, rate limiting, batch apply/revert, partial success. |
| 3 | Data coverage and shared listing source | `[TODO]` | Full inventory/status sync and shared picker foundation. |
| 4 | Variations and inventory depth | `[TODO]` | Variation visibility and safe variation write foundations. |
| 5 | Dynamic Pricing and profit intelligence | `[TODO]` | Listing visibility, profit inputs, pricing suggestions, preview-first writes. |
| 6 | Media module and listing media workflows | `[TODO]` | Media visibility, image/video management, safe upload/delete. |
| 7 | Video Generator real workflow | `[TODO]` | Listing-based video generation and confirmed Etsy listing video upload. |
| 8 | Promote production setup | `[TODO]` | Pinterest/Instagram OAuth, content generation, post/schedule. |
| 9 | AI tools and compliance-safe automation | `[TODO]` | AI feature governance, safe prompts, external-AI policy controls. |
| 10 | Billing, plans, owner admin, beta operations | `[TODO]` | Owner/admin console, comp grants, Stripe, beta user ops. |
| 11 | Security, ops, audit, observability | `[TODO]` | Redaction, write logs, audit trail, alerts, deployment discipline. |
| 12 | Beta readiness and launch polish | `[TODO]` | UX polish, docs, smoke matrix, beta tester readiness. |

---

# Sprint 1 — Production QA and write-core stabilization

Goal: make the already-live Private Beta trustworthy for the owner’s real Etsy shop before expanding features.

## Completed

### 1.1 Private Beta sign-in gate
Status: `[DONE]`

Evidence:
- PR #78 allowed sign-in and authenticated app routes while keeping registration paused.
- `/register`, `/signup`, `/get-started` remain paused behind Private Beta.

Acceptance:
- Owner can sign in.
- Registration remains paused.
- Etsy OAuth callback results are not masked by the private-beta gate.

### 1.2 Etsy OAuth safe logging and connection chain
Status: `[DONE]`

Evidence:
- PR #79 added safe categorized OAuth callback logging.
- PR #81 added defensive user_id validation.
- PR #82 fixed x-api-key header format to `keystring:shared_secret` across Etsy v3 calls.
- PR #83 fixed owner shop lookup parsing as single Shop object.
- Owner confirmed shop connection: WearYourStoriesCom.

Acceptance:
- Shop connection works.
- No tokens, code, state, or secrets are logged.

### 1.3 Full active listing sync for owner shop
Status: `[DONE]`

Evidence:
- Initial 25/210 was diagnosed as Free plan cap, not pagination.
- PR #86 fixed admin scripts using rewritten async DB URL.
- PR #87 made sync use effective plan including comp grants.
- Owner later confirmed 210 active listings synced.

Acceptance:
- Owner shop active listings sync beyond Free cap.
- Comp grant affects effective plan gates.

### 1.4 Billing effective plan / comp plan display
Status: `[DONE]`

Evidence:
- Sprint 1 QA PR #89 corrected billing effective plan behavior.

Acceptance:
- Billing and gates use effective access, not misleading raw Free display.

### 1.5 Listing thumbnails and hover preview
Status: `[DONE]`

Evidence:
- PR #89 added 80x80 thumbnails.
- PR #91 fixed clipped hover preview with portal/fixed-position behavior.
- Owner manually confirmed hover preview works.

Acceptance:
- Thumbnails are usable.
- Hover preview is visible and not clipped.

### 1.6 HTML entity decode
Status: `[DONE]`

Evidence:
- PR #89 added backend sync decode for new rows.
- PR #91 added frontend display decode defense-in-depth.
- Owner confirmed normal listing UI and detail drawer display `Men's`, not `Men&#39;s`.

Acceptance:
- User-facing listing text displays decoded entities.
- No raw HTML rendering.

### 1.7 Footer Akilta link
Status: `[DONE]`

Acceptance:
- Footer credits Akilta and links to `https://www.akilta.com`.

### 1.8 Bulk Edit change remove
Status: `[DONE]`

Evidence:
- PR #91 fixed 204 response handling in shared API client.
- Owner confirmed added Bulk Edit changes can be removed.

Acceptance:
- Remove change works without false failure.

### 1.9 Bulk Edit title write
Status: `[DONE]`

Evidence:
- PR #93 fixed title PATCH shop-scoped path.
- Owner confirmed live title write succeeds.

Acceptance:
- Single title update succeeds on live Etsy listing.
- No regression after price fixes.

### 1.10 Bulk Edit price write, single listing
Status: `[DONE]`

Evidence chain:
- PR #91 fixed inventory URL from wrong shop-scoped path.
- PR #93 fixed title path and top-level inventory keys.
- PR #94 introduced fetch-patch-put inventory flow.
- PR #96 changed writable inventory payload shape: decimal offering price, no response-only IDs.
- PR #98 surfaced safe Etsy error body.
- PR #100 fixed readiness_state_id capture and per-offering presence.
- Owner live-tested French Bulldog `price_amount` 6000 → 6288.
- Bulk Edit showed Success 1 / Failed 0 / Skipped 0.
- Etsy Shop Manager showed `$62.88`.
- Bulk Edit Listings showed `USD 62.88`.

Acceptance:
- One non-variation listing price write succeeded live.

## Remaining in Sprint 1

### 1.11 Magic Revert for the successful price write
Status: `[IN_PROGRESS]`

Required manual test:
1. Use the successful French Bulldog apply job.
2. Click `Magic Revert`.
3. Confirm app result Success 1 / Failed 0 / Skipped 0.
4. Confirm Etsy Shop Manager returns `$62.88` → `$60.00`.
5. Sync Listings.
6. Confirm Bulk Edit Listings shows `USD 60.00`.

Exit criteria:
- Single-listing price revert proven live.

### 1.12 Stop rapid manual price retests until rate-limit handling exists
Status: `[WATCH]`

Observed:
- Miniature Schnauzer price test after success failed with HTTP 429.
- Etsy message: `Exceeded per second rate limit`.

Interpretation:
- This is not a payload/schema failure.
- Write engine has crossed the main schema hurdle, but repeated writes can hit Etsy’s rate limits.

Exit criteria:
- Sprint 2 rate-limit guard added or owner explicitly accepts risk for manual slow tests.

---

# Sprint 2 — Bulk Edit write hardening and rate limits

Goal: turn the single-item write success into a reliable, owner-safe bulk write system.

## Tasks

### 2.1 Rate-limit-aware Etsy write queue
Status: `[TODO]`

Requirements:
- Per-shop write throttle.
- Per-second request limiter.
- Configurable delay between item writes.
- Honor `Retry-After` when present.
- Exponential backoff for HTTP 429.
- Max retry count per item.
- Stop rapid-fire writes.
- UI reason must say rate-limited, not generic payload failure.

Acceptance:
- Repeated price writes do not immediately trigger 429 under normal use.
- If 429 occurs, it is retried safely or marked retryable.

### 2.2 Apply job state machine
Status: `[TODO]`

States:
- pending
- running
- succeeded
- partially_failed
- failed
- rate_limited
- cancelled
- reverted
- revert_failed

Acceptance:
- UI can clearly show batch progress and final state.
- Jobs survive refresh.

### 2.3 Single-listing apply/revert matrix
Status: `[TODO]`

Test fields:
- title
- price_amount
- quantity, if supported

Acceptance:
- Apply succeeds.
- Revert succeeds.
- Etsy side is verified by owner.
- Bulk Edit sync reads the reverted value.

### 2.4 Small-batch apply/revert matrix
Status: `[TODO]`

Batch sizes:
- 3 listings
- 10 listings
- 33 listings only after 3 and 10 pass

Acceptance:
- Success/failed/skipped counts are accurate.
- Partial success is handled without hiding failed items.
- Revert can target only succeeded items.
- Rate limits are handled.

### 2.5 Item-level retry / resume failed items
Status: `[TODO]`

Acceptance:
- Failed 429 items can be retried later.
- Failed schema/policy items are not blindly retried.
- Owner can export or copy a failed-item report.

### 2.6 Magic Revert hardening
Status: `[TODO]`

Acceptance:
- Revert uses the same safe Etsy write helpers as apply.
- Revert has item-level diagnostics.
- Revert refuses or warns if listing changed since original apply.
- Revert respects rate limits.

### 2.7 Audit trail for writes
Status: `[TODO]`

Acceptance:
- For every item write, record who/when/shop/listing/field/before/after/result/job/session/revert status.
- Logs are searchable and safe to export.
- No secrets are persisted.

---

# Sprint 3 — Data coverage and shared listing source

Goal: every feature page should see the same reliable listing universe.

## Tasks

### 3.1 Full inventory/status read-only sync
Status: `[TODO]`

Statuses:
- active
- draft
- inactive
- expired
- sold_out if returned/supported

Acceptance:
- Status counts visible.
- No write during sync.
- Draft/inactive/expired are read-only initially.
- No accidental activation/deactivation.

### 3.2 Listing status filters on Listings page
Status: `[TODO]`

Acceptance:
- All / Active / Inactive / Draft / Expired filters work.
- Counts match synced data.
- Search and filters combine correctly.

### 3.3 Shared ListingPicker component
Status: `[TODO]`

Consumers:
- Bulk Edit
- Variations
- Dynamic Pricing
- Media
- Video Generator
- Promote

Capabilities:
- shop filter
- status filter
- title search
- pagination
- thumbnail
- variation indicator
- selected count
- empty/error/loading states

### 3.4 Variations page listing visibility
Status: `[TODO]`

Acceptance:
- Variations page shows listings instead of false empty state.
- Distinguishes has_variations / no_variations / unknown inventory state.

### 3.5 Dynamic Pricing listing visibility
Status: `[TODO]`

Acceptance:
- Dynamic Pricing page shows listings.
- Suggestions remain preview-only until write workflow is approved.

### 3.6 Media module listing visibility
Status: `[TODO]`

Acceptance:
- Media page no longer fails to load listings when listings exist.
- Media operations remain read-only until later sprint.

---

# Sprint 4 — Variations and inventory depth

Goal: support variation listings safely without breaking the now-working non-variation write path.

## Tasks

### 4.1 Variation inventory read model
Status: `[TODO]`

Acceptance:
- Fetch and store/read variation products/offers/property_values in a safe local representation.
- Show variation matrix read-only first.

### 4.2 Variation price edit preview
Status: `[TODO]`

Acceptance:
- Owner can preview variation-specific price changes.
- No write until explicit approval.

### 4.3 Variation quantity edit preview
Status: `[TODO]`

Acceptance:
- Quantity changes preview per offering.
- Invalid combinations blocked before write.

### 4.4 Variation write apply/revert
Status: `[TODO]`

Acceptance:
- Single variation listing test first.
- Preserve SKU, property_values, readiness_state_id, price_on_property, quantity_on_property, sku_on_property.
- Revert works for succeeded variation writes.

### 4.5 Variation diagnostics
Status: `[TODO]`

Acceptance:
- Item-level failure shows exact safe reason.
- No raw Etsy body, token, secret, or header leak.

---

# Sprint 5 — Dynamic Pricing and profit intelligence

Goal: make pricing suggestions useful and safe before allowing broader price automation.

## Tasks

### 5.1 Dynamic Pricing data prerequisites
Status: `[TODO]`

Inputs:
- current price
- quantity
- listing status
- product cost, if available
- shipping profile or shipping cost, if available
- Etsy fees model, if implemented
- manual margin target

### 5.2 Profit page validation
Status: `[TODO]`

Acceptance:
- Profit page numbers are explainable.
- Missing cost data is clearly marked.
- No fake precision.

### 5.3 Pricing suggestion engine
Status: `[TODO]`

Acceptance:
- Suggests price changes with reason.
- Preview-only by default.
- User can choose exact listings.

### 5.4 Dynamic Pricing write handoff
Status: `[TODO]`

Acceptance:
- Uses Sprint 2 write queue and rate-limit guard.
- Item-level report and revert available.

---

# Sprint 6 — Media module and listing media workflows

Goal: make listing media visible and safely manageable.

## Tasks

### 6.1 Media module listing picker
Status: `[TODO]`

Acceptance:
- Loads listings via shared picker.
- Shows existing images/videos when available.

### 6.2 Listing image management read-only view
Status: `[TODO]`

Acceptance:
- Show image count, primary image, missing media warnings.
- No reorder/delete/upload until enabled.

### 6.3 Etsy listing video upload workflow
Status: `[BLOCKED]`

Blocker:
- Live video upload endpoint was implemented historically but not live-tested.

Acceptance:
- Owner-approved single listing video upload test.
- Preview and confirmation before upload.
- Item-level success/failed report.
- Rate-limit handling.

### 6.4 Media delete/revert strategy
Status: `[TODO]`

Acceptance:
- No destructive media operation without a recovery story.
- Delete operations require explicit confirmation.

---

# Sprint 7 — Video Generator real workflow

Goal: turn video generation into a listing-based production workflow.

## Tasks

### 7.1 Replace manual image URL workflow
Status: `[TODO]`

Acceptance:
- User selects listings.
- App auto-fetches listing images.
- User does not paste image URLs manually as the main path.

### 7.2 Batch listing selection
Status: `[TODO]`

Acceptance:
- Select 1 listing.
- Select 20-25 listings.
- Show image availability and selected count.

### 7.3 Generate separate video per listing
Status: `[TODO]`

Acceptance:
- One selected listing produces one video job.
- Batch produces separate jobs.
- Item-level states: queued, generating, preview_ready, failed, approved, uploaded.

### 7.4 Preview and approval
Status: `[TODO]`

Acceptance:
- No silent Etsy upload.
- User can approve/reject per video.

### 7.5 Upload approved video to existing Etsy listing
Status: `[TODO]`

Acceptance:
- Upload only after user approval.
- Existing listing updated, not draft listing.
- Item-level report.
- Rate-limit aware.

---

# Sprint 8 — Promote production setup

Goal: make Promote usable with real integrations instead of placeholder modals.

## Tasks

### 8.1 Promote page search/filter
Status: `[TODO]`

Acceptance:
- Search by title.
- Filter by shop/status.
- Uses shared ListingPicker/listing source.
- No endless scroll hunting.

### 8.2 Pinterest OAuth and board selection
Status: `[BLOCKED]`

External setup:
- Pinterest developer app.
- Redirect URI.
- Required scopes.
- Production review if required.

Acceptance:
- OAuth flow.
- Board selection.
- Token storage safe.
- No posting until user confirms.

### 8.3 Instagram/Meta OAuth and account/page selection
Status: `[BLOCKED]`

External setup:
- Meta developer app.
- Instagram Graph API requirements.
- Business/creator account/page permissions.
- Production review if required.

Acceptance:
- OAuth flow.
- Page/account selection.
- Token storage safe.

### 8.4 Caption/hashtag generation
Status: `[TODO]`

Acceptance:
- Caption preview.
- Hashtag preview.
- Editable before post/schedule.
- Respects Etsy-derived-data AI policy.

### 8.5 Schedule/post now
Status: `[TODO]`

Acceptance:
- User chooses post now or scheduled time.
- Time zone is clear.
- Item-level report.
- No silent posting.

---

# Sprint 9 — AI tools and compliance-safe automation

Goal: keep AI features useful without violating Etsy-derived data constraints.

## Tasks

### 9.1 AI provider policy gate
Status: `[TODO]`

Acceptance:
- `ALLOW_ETSY_DATA_TO_AI=false` remains default.
- Any feature that sends Etsy-derived content externally is blocked unless explicitly allowed.
- UI explains when AI is unavailable due to policy.

### 9.2 AI listing suggestions
Status: `[TODO]`

Acceptance:
- Suggestions are preview-only.
- User must approve before any write.
- Clear before/after diff.

### 9.3 AI tool usage limits
Status: `[TODO]`

Acceptance:
- Uses effective plan/comp grants.
- Clear monthly usage counters.

### 9.4 Prompt and output audit
Status: `[TODO]`

Acceptance:
- Safe logs record prompt category and item id, not secrets.
- Etsy-derived content handling is explicit.

---

# Sprint 10 — Billing, plans, owner admin, beta operations

Goal: make private beta and monetization manageable by owner.

## Tasks

### 10.1 Owner dashboard
Status: `[TODO]`

Acceptance:
- Owner can view users, orgs, shops, plans, sync status, recent write jobs.

### 10.2 Comp grant management UI
Status: `[TODO]`

Acceptance:
- Owner can grant/revoke comp access safely.
- Effective plan updates correctly.
- Audit trail exists.

### 10.3 Stripe production workflow review
Status: `[TODO]`

Acceptance:
- Products/prices verified.
- Webhook endpoint status manually verified in Stripe dashboard.
- No accidental real charge during tests.

### 10.4 Private beta user management
Status: `[TODO]`

Acceptance:
- Invite/allowlist strategy.
- Registration gate behavior remains explicit.
- Beta users can be supported without direct DB edits.

---

# Sprint 11 — Security, ops, audit, observability

Goal: make production operations boring, safe, and traceable.

## Tasks

### 11.1 Uvicorn/OAuth callback query-string redaction
Status: `[TODO]`

Acceptance:
- OAuth code/state not exposed in access logs.
- Redaction tests or log checks exist.

### 11.2 Standardized item-level write logs
Status: `[PARTIAL]`

Already improved:
- Bulk Edit failed items have safer details.
- Sanitized Etsy error body can surface validation messages.

Remaining:
- Standardize for title, price, quantity, revert, media upload, social post.

### 11.3 Audit log polish
Status: `[TODO]`

Acceptance:
- Searchable by user/shop/listing/job/date.
- Export safe summary.
- No secrets.

### 11.4 Deployment and docs-only PR discipline
Status: `[TODO]`

Acceptance:
- Docs-only PRs acknowledge that merge triggers production deploy.
- Production health check run after merge.

### 11.5 Retention/job monitoring review
Status: `[TODO]`

Acceptance:
- Retention job status is easy to inspect.
- Failure path documented.

---

# Sprint 12 — Beta readiness and launch polish

Goal: prepare the app for carefully expanded beta usage.

## Tasks

### 12.1 Production smoke-test matrix
Status: `[TODO]`

Areas:
- auth
- shop connect
- sync
- listings grid
- bulk edit preview
- title write/revert
- price write/revert
- media read
- billing plan display
- private beta routes

### 12.2 Help docs and owner runbooks
Status: `[TODO]`

Acceptance:
- How to sync.
- How to run a safe bulk edit.
- What to do on failed items.
- What to do on rate limit.
- How to revert.

### 12.3 UX polish
Status: `[TODO]`

Acceptance:
- Loading states.
- Empty states.
- Error copy.
- Mobile/responsive review.

### 12.4 Beta tester checklist
Status: `[TODO]`

Acceptance:
- Small tester cohort flow.
- Support contacts.
- Known limitations.
- Feedback capture.

---

# Immediate next actions

1. `[IN_PROGRESS]` Run single-listing Magic Revert on the successful French Bulldog price change.
2. `[TODO]` Verify Etsy `$60.00` and Bulk Edit `USD 60.00` after sync.
3. `[TODO]` Add Sprint 2 rate-limit guard before any 3/10/33 listing batch writes.
4. `[TODO]` Make H!veAI project dashboard valid via `.hiveai/PROJECT_DASHBOARD.md` pointing to this file.

---

# Do not do without explicit owner approval

- Do not run live Etsy GET/PUT/PATCH from Claude/Codex environment.
- Do not run 3/10/33 listing bulk write tests before Magic Revert and rate-limit guard decisions.
- Do not enable external AI processing for Etsy-derived data.
- Do not disable Private Beta.
- Do not change DNS/Cloudflare.
- Do not change production env.
- Do not perform Stripe real charge/refund/subscription operations.
- Do not invent new sprint numbers mid-session.

---

# Backlog / intake

Use this section for new ideas that are not yet assigned to a sprint.

## Intake rules

- Add the idea here first.
- State why it matters.
- State likely sprint destination.
- Owner approves promotion into a sprint.

## Current intake items

- None.
