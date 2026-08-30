# HANDOFF.md — Session Handoff

Purpose: only what the next session needs to resume safely. For full engineering history, see `CHANGELOG_AI.md`. For current production/environment state, see `PROJECT_STATUS.md`. For durable decisions, see `DECISIONS.md`.

## RESUME HERE — 2026-08-30 (M03.02 full-status sync + M03.03 Listings filters/counts + Dashboard card removal — branch `feature/m03-full-status-sync-and-listing-filters`)

**Owner review of `/dashboard` after the account-profile round: mostly good (greeting uses saved name, sidebar clean), but explicitly rejected the "Owner-verified production checks" card as unwanted customer-facing content.** Removed entirely from `apps/frontend/app/(app)/dashboard/page.tsx` — the underlying facts (title/price write+revert both owner-verified OK) stay in `TASKS.md`/`HANDOFF.md`/`CHANGELOG_AI.md` only, never a Dashboard card again. All other Dashboard cards (onboarding checklist, Listing Health, Profit Overview, Action Queue, tool grid) untouched.

**M03.02 — Full inventory/status read-only sync, implemented:**
- `sync_shop_listings()`/`fetch_shop_listings()` (`apps/backend/app/services/etsy_sync.py`) now iterate all 5 Etsy listing states — `active`, `inactive`, `draft`, `expired`, `sold_out` — via Etsy's general "Get Listings by Shop" endpoint (`GET /shops/{shop_id}/listings?state={state}`), replacing the old active-only convenience endpoint.
- `sold_out` is a **native Etsy state value**, not derived from local quantity — confirmed against Etsy's documented `state` parameter values for this endpoint.
- Read-only, proven by a mock client that raises if `.post`/`.patch`/`.put`/`.delete` are ever called on it.
- `max_listings` plan-limit budget shared across all 5 states (not per-state — a Free plan still can't exceed its real cap 5x over).
- Per-state pagination; partial-failure safety (one state's failure doesn't lose other states' listings this run; `job.status` gains `"completed_with_errors"`).
- 7 new tests in `test_etsy_sync_status.py`; 2 pre-existing `test_listings.py` tests updated (their mock helper was state-blind, needed to become state-aware).
- **Kept `[~]`, not `[x]`:** no production shop sync was run this round (owner approval required separately, per explicit task constraint) — only mocked Etsy responses were tested.

**M03.03 — Listings status filters + counts, implemented:**
- New **Sold out** 6th tab on `/listings` (`STATE_TABS` now includes it).
- New `GET /api/v1/listings/status-counts` endpoint — real, grouped `SELECT state, COUNT(*)` from local data, not hardcoded, not page-scoped. Every tab shows its real count.
- Search/pagination/checkbox-selection/"Bulk Edit selected"/product-detail navigation/Quick View/column-visibility untouched (confirmed via diff review).
- **Kept `[~]`, not `[x]`:** test-verified against real local data, but no owner click-through yet.

**Files changed:** backend — `app/services/etsy_sync.py`, `app/api/v1/listings.py`, `app/schemas/listings.py`, `tests/test_etsy_sync_status.py` (new), `tests/test_listings.py`. Frontend — `app/(app)/dashboard/page.tsx`, `app/(app)/listings/page.tsx`, `lib/api.ts`.

**Checks:** `npx tsc --noEmit` clean, `npx next lint` no new warnings, `npx next build` clean. Backend: local run (SQLite) — 1006 passed, 32 failed, all matching the confirmed local-venv-only 401-vs-403 artifact (30 pre-existing + 1 new, same pattern) plus 2 unrelated pre-existing `test_video_generator.py` failures. `git diff --check` clean, manual secret scan clean.

**Safety, explicit:** no Etsy write/status-mutation endpoint ever called (GET only, proven in tests); no listing activation/deactivation/renewal/deletion; no production shop sync run; no Bulk Edit Apply/Magic Revert/media/video action by Claude/Codex.

**Recommended next owner action:** refresh `/dashboard` and confirm the owner-verified card is gone; open `/listings` and confirm the status tabs/counts render and filtering still works. **Do not run a production sync unless you explicitly choose to** — M03.02 has only been verified against mocked Etsy responses.

---

## Previously — 2026-08-30 (TASKS.md full truth audit — PR #119, branch `docs/tasks-md-full-truth-audit`, merge `77e1b250c29f13f077a5b489be3aeb4adbf2726d`)

**Owner instruction: strict, docs-only truth audit of every line in `TASKS.md`. No feature work, no implementation of M03.02/M03.03/M04.03/M06.03/M08.04 or any other product feature — verification and correction only.**

**What this audit found and corrected** (full evidence table in the execution log):
1. The bottom-of-file "Milestone policy" summary was badly stale — it described M10/M12/M13/M14/M15/M16/M19 as "PLANNED — not started" and M11 as "the current major sprint," directly contradicting the detailed per-milestone sections just above it (most of which say SHIPPED/PARTIAL with real evidence). Rewritten to defer to each milestone's own closing line.
2. **Two entire shipped, tested features had zero milestone tracking anywhere in `TASKS.md`:** CSV Import/Export (Sprint 14, 2026-06-26 — `apps/backend/app/api/v1/csv_tools.py`, 36 backend tests, safe "converts to a BulkEditSession draft, never writes Etsy directly" design) and Scheduled Jobs (Sprint 16, 2026-06-26 — `apps/backend/app/api/v1/scheduled_jobs.py`, 41 backend tests). Added as new packages M03.06 and M04.06.
3. **M08.04 (Owner dashboard / comp grant management UI) was marked `[ ]`** with the note "currently owner-console/API-only" — false. A full owner frontend console already exists (`apps/frontend/app/owner/`, 14 real pages), backed by a 575-line, ~35-endpoint admin API, with a real working Grant/Revoke comp access UI and a comprehensive audit-log helper (`_write_owner_audit_log()`, called at 12 sites, safe by design) — 108 backend tests, 105 passing (3 failures are the same known local-venv 401-vs-403 artifact, not real). Original build: Sprint 19 "Internal Admin Business Dashboard." Upgraded to `[~]` — real and tested, but no owner click-through is recorded anywhere.
4. **M12.02 (AI listing suggestions) and all of M14 (Dynamic Pricing/profit)** were marked `[ ]` "not started" — false. Both are real, tested, safety-checked features (Sprint 13 and Sprint 15, 2026-06-26 respectively) that convert approved suggestions into a draft `BulkEditSession` and never write to Etsy directly. Upgraded to `[~]`.
5. M03.03 (listing status filters) and M04.03 (apply job state tracking) had real partial implementations that were marked `[ ]` — upgraded to `[~]` with the exact remaining gap named in each case.
6. M12.03's second line, M08.06, and M18.01 got clarifying evidence notes; no marker changes (already accurate or already correctly `[ ]`).

**What did NOT change:** M03.02 (full-status sync — only Etsy's `/listings/active` endpoint is ever called, confirmed via `etsy_sync.py:98`), M06.03 (no listing-staleness check in revert code, confirmed via grep), M08.05/M08.06 (Stripe review / beta invite management — genuinely not built, confirmed via grep), M09.04/M09.06 owner click-through (not in the scope of any recorded smoke test), M15.04 variation revert (does not exist), M13.04 media restore (does not exist). No item was ever marked owner-verified without a specific recorded owner action.

**Files changed:** `TASKS.md` (new "Current Truth Snapshot" section, M03.03/M03.06/M04.03/M04.06/M06.04/M08.04/M08.06/M12.02/M12.03/M14.01-04/M17.02/M17.03/M18.01 edits, rewritten "Milestone policy"), `PROJECT_STATUS.md`, `HANDOFF.md`, `CHANGELOG_AI.md`, `DECISIONS.md`, `.hiveai/PROJECT_DASHBOARD.md`. Zero code files touched.

**Checks:** `git diff --check` clean on `TASKS.md`; checkbox-marker sanity grep clean (no malformed `[?]` markers); each milestone's closing-line summary confirmed to appear exactly once (no duplicated/conflicting closing lines). No backend/frontend build checks needed — docs-only change, confirmed via `git status` before commit.

**Safety, explicit:** read-only research only — no Etsy API call, no Apply/Revert/Sync, no media/video action, no Stripe/env/DNS change, no destructive DB action, no secrets read or printed. All evidence gathered via source-code grep/read, local test runs of already-existing test files, and reading this session's own prior logs — nothing new was built or deployed.

**Recommended next owner action:** none required immediately — this is a documentation-truth correction, not a feature change. When convenient, an owner click-through of `/owner` (admin console), `/ai` (AI suggestions), `/pricing-rules` + `/profit` (Dynamic Pricing), `/csv`, and `/scheduled` would let those `[~]` items graduate to `[x]` in a future round.

---

## Previously — 2026-08-30 (Account profile name + sidebar cleanup + beta-readiness/owner-control polish — PR #117, branch `feature/account-profile-and-beta-readiness-control`, merge `96b9f02742af5ade337240eb6608170455517c4e`)

**Owner request, after both live write tests passed (see previous round):** add first/last name to Account, use it for greetings instead of raw email, and clean up the sidebar footer (remove email + Sign out, move Sign out into Account).

**Part 1 — Account profile:**
1. Backend: `User.first_name`/`User.last_name` added (migration `0026_add_user_name_fields.py`, nullable, no forced backfill). `User.display_name` property: deterministic fallback `first+last → first → last → email → "Account"`. `GET /api/v1/auth/me` now returns `first_name`/`last_name`/`display_name`. New `PATCH /api/v1/auth/me` — authenticated-self only, trims whitespace, blank string → `null` (clears the name). 5 new tests in `test_auth.py`, all passing.
2. Frontend: new `/account/profile` page (first/last name inputs, read-only email, Save, loading/success/error states). New `lib/api.ts` helpers: `getMe()`, `updateProfile()`, `getGreetingName()` (greeting variant prefers first name alone, e.g. "Welcome, Şekip" not "Welcome, Şekip Hayıt").
3. `/dashboard` greeting now uses `getGreetingName()` — falls back to email if no name set, to bare "Welcome" if even email unavailable, to the existing "Manage your Etsy listings" subtitle while loading.
4. Sidebar (`AppShell.tsx`): removed the entire bottom user-footer block (email display + "Sign out" button + their fetch/handler code). Sign out moved to `/account` (new "Account controls" card, new `logout()` helper in `lib/api.ts`). Account nav entry unchanged.

**Part 2 — Beta readiness / owner control polish (small, product-state-clarity only):**
1. New static "Owner-verified production checks" card on `/dashboard` — truthfully lists what's actually been manually verified (title write+revert, price write+revert) vs. not yet (variation apply, media destructive actions, video generation). Explicitly not framed as automated.
2. Variations page's Apply confirm modal: added one line — "Magic Revert does not support variation changes yet" — the existing copy mentioned an automatic backup snapshot in a way that could read as "revert available." No functionality changed.
3. Account structure reviewed — already coherent (Profile/Plan & Billing/Usage/Credits/Connected Shops/Activity & Audit/Data & Privacy/Support/Sign out all present); no new large features added.
4. Media/Magic Revert/Video Generator copy already honest from prior rounds (checked, no change needed) — coming-soon/no-restore-yet, cannot-be-undone, never-auto-uploaded language all already present.

**Files changed:** backend — `app/models/user.py`, `app/schemas/auth.py`, `app/services/auth.py`, `app/api/v1/auth.py`, `alembic/versions/0026_add_user_name_fields.py`, `tests/test_auth.py`. Frontend — `lib/api.ts`, `app/(app)/dashboard/page.tsx`, `app/(app)/account/layout.tsx`, `app/(app)/account/page.tsx`, `app/(app)/account/profile/page.tsx` (new), `app/(app)/account/security/page.tsx`, `app/(app)/variations/page.tsx`, `components/ui/AppShell.tsx`.

**Checks:** `npx tsc --noEmit` clean, `npx next lint` no new warnings, `npx next build` clean (`/account/profile` route confirmed in output). Backend: CI (Postgres) — **1136 passed, 0 failed** on PR #117, after fixing one wrong assertion in a new test (see note below). `git diff --check` clean, manual secret scan clean.

**Correction to a stale local-testing claim:** a local `pytest` run (SQLite) showed 30 failures matching what looked like a pre-existing `*_requires_auth` 401-vs-403 baseline (and `PROJECT_STATUS.md` had an old note claiming the same, from a past session). CI's actual run proved this was a **local-venv-only artifact** — a stale dependency locally returns 401 for a missing token where FastAPI's real default (and CI's clean-install behavior) is 403. CI was fully green except for one of this round's own new tests, which had wrongly asserted 401 to match the misleading local result — fixed to assert 403. `PROJECT_STATUS.md`'s old "9 pre-existing baseline failures" note has been corrected. Trust CI, not a local run, for backend test baselines going forward.

**Safety, explicit:** no Claude/Codex live Etsy action — the title/price write+revert tests referenced above were owner-run in production in the previous round, not by Claude/Codex. This round only adds a profile field, a greeting, a sidebar cleanup, and two copy changes — no new write/apply/revert/sync/media/video code path.

**Recommended next owner action:** open `/account/profile`, enter first and last name, save, refresh `/dashboard` and confirm the greeting uses the saved name, confirm the sidebar no longer shows email/Sign out, confirm `/account` has a visible Sign out control, and confirm the onboarding checklist still shows the completed live-bulk-edit state.

---

## Previously — 2026-08-30 (Dashboard onboarding tracking fix after owner live write tests — PR #116, branch `fix/dashboard-onboarding-tracking-after-write-tests`, merge `2ec4226c8067ab59dde6fd203b77239c53ff13d9`)

**Owner completed the two live production write tests recommended by the previous round:**
1. Single-listing title write + Magic Revert — Apply completed, Magic Revert completed, owner reports OK.
2. Single-listing price write + Magic Revert — field-level preview `price_amount` 6000→6288; Apply success=1/failed=0/skipped=0; Magic Revert restored=1/failed=0/skipped=0; owner reports OK.

**Bug found immediately after:** Dashboard `/dashboard` onboarding checklist still showed "Try bulk edit" and "Review available tools" as NOT complete, despite Account Usage showing 130/5,000 bulk edits used this month. Root cause: both steps had `done: false` hardcoded in `OnboardingChecklist.tsx` — wired to no data source at all (not a stale-cache/localStorage problem).

**Fixed this round (PR #115's follow-up, branch above):**
1. "Try bulk edit" now reads real server-side evidence: `bulk_edits_used > 0` from `GET /api/v1/billing/usage` (the same counter `bulk_edit_apply.py` increments on every successful apply — durable across refresh/logout/device).
2. "Review available tools" removed from the completion checklist entirely — the dashboard's pre-existing `activeFeatures` tool grid (rendered unconditionally below the checklist) already serves that purpose neutrally; adding a 4th completion gate would have needed new, riskier tracking for no real benefit.
3. Also fixed, same round: Bulk Edit Add Changes table showed `[object Object]` for find/replace rules (`formatVal()` had no object branch). Now renders `Find: "<text>" → Replace: "<text>"`. Display-only — no payload/apply/revert semantics touched.

**Files changed:** `apps/frontend/components/onboarding/OnboardingChecklist.tsx`, `apps/frontend/app/(app)/dashboard/page.tsx`, `apps/frontend/app/(app)/bulk-edit/page.tsx`.

**Checks:** `npx tsc --noEmit` clean, `npx next lint` no new warnings, `npx next build` clean, `git diff --check` clean, manual secret scan clean. No backend files changed.

**Safety, explicit:** no Claude/Codex live Etsy action — both write+revert tests above were owner-run in production, not run by Claude/Codex. This round's fixes only read an existing usage endpoint and fixed a display bug; no new write paths added.

**Remaining owner-live actions, still separate and optional, not marked complete anywhere in `TASKS.md`:**
- Variation apply — no revert exists yet (M15.04).
- Media upload/delete/replace — no restore endpoint yet (M13.04).
- Video generation — never run.

**Recommended next owner action:** refresh `/dashboard` and confirm the onboarding checklist now correctly shows "Try bulk edit" complete (3/3, checklist auto-hides once all steps done). No further live write test is required unless the owner wants an additional confirmation.

---

## Previously — 2026-08-30 (Owner QA polish before write tests — PR #115, merge `e2bfe46fb99674f92ccddab092cf7a97dd2eaa10`)

**Owner ran a manual, non-destructive smoke test across 7 screens** (`/listing-health`, `/insights`, `/media`, `/variations`, `/video-generator`, `/magic-revert`, `/account/activity` + smoke routes) after the autonomous M10→M03.04→M13/M15→M19 sequence (PRs #110–#113) and the PR #114 CodeQL cleanup. **Most flows pass.** Four polish items fixed this round, frontend-only, no behavior change to any write/apply/revert/sync/media/video code path:

1. **Bulk Edit preselection visibility** — a listing preselected via `?listing_ids=<id>` (from "Fix in Bulk Edit") was correctly held in state but not visibly checked if it wasn't on page 1 of the default table. Fixed: preselected listing(s) now fetched independently and pinned in their own "Pre-selected" section at the top of the picker, banner names the actual title, selection still survives pagination/search, no auto-apply.
2. **Media current-media gallery** — selecting a listing on `/media` gave no indication of what was already synced. Fixed: a read-only "Current Media" panel now shows the primary + synced thumbnails (single selection) or a compact per-listing summary (multi-selection, first 5), with a truthful "not synced yet" state. Replace/delete stay disabled (M13.04, unchanged).
3. **Video Generator thumbnail preview** — picking a listing filled the URL textarea with no visual confirmation. Fixed: a thumbnail grid (in image order) now renders below the picker; "No synced photos available for this listing." shown truthfully when empty. No video generation, no external provider call.
4. **Dashboard onboarding copy** — "Explore paid features" was inconsistent with the PR #106 banner-removal policy. Relabeled "Review available tools", description softened from "Unlock…" to "See what's included in your plan…".

**Last known merged PRs, in order:** #101 (H!veAI `TASKS.md` format, `092e02f`) → #107 (Magic Revert history/activity, `7ee420d`) → #108 (current-truth docs cleanup, retrospective log backfilled this round) → #109 (M08.07/M16.06 plan-gate, `fd7269e`) → #110 (M10 Listing Health/Insights, `f7d79e7`) → #111 (M03.04 shared `ListingPicker`, `9a220b0`) → #112 (M13/M15 media/variation depth, `10c7d54`) → #113 (M19 smoke matrix/runbooks, `e400272`) → #114 (CodeQL cleanup, `cbcbbc9`) → #115 (owner-QA-polish, `e2bfe46`).

**Owner manual QA results this round:**
1. Listing Health — **conditional pass** (issue pills/View Product work; scoring-engine gap for zero-qty/variation/personalization issues is a known, separate, pre-existing limitation, not a bug).
2. Insights — **pass**.
3. Media — **conditional pass** (picker worked; current-media gallery was the gap, closed this round).
4. Variations — **pass** (read-only matrix confirmed against real synced data; preview-output and apply/revert remain not owner-verified, see M15.02–M15.04).
5. Video Generator — **conditional pass** (listing selection worked; thumbnail preview was the gap, closed this round).
6. Magic Revert + Activity — **pass** (history, filters, already-reverted state, Activity rows all confirmed; no live revert run).
7. Smoke matrix non-destructive rows — **pass** (26/26 automated + owner screen checks).

**Remaining blockers before broader beta, unchanged by this round:**
- Owner live title write + Magic Revert (never run).
- Owner live price write + Magic Revert (never run).
- Variation apply live test — optional, separate owner approval required; no revert exists for it yet (M15.04).
- Media restore/revert endpoint — doesn't exist (M13.04); the disabled replace/delete buttons are the mitigation, not the fix.
- Remaining `ListingPicker` consumers (Dynamic Pricing, Bulk Edit, Promote) — M03.04.

**Safety, explicit:** no Claude/Codex live Etsy action of any kind this round or any prior round in this sequence — every fix was a frontend rendering/wording change reusing already-existing, already-tested read endpoints. All live verification is owner-run only, per the runbooks in `docs/operations/`.

**Checks:** `npx tsc --noEmit` clean, `npx next lint` no new warnings, `npx next build` clean, `git diff --check` clean, manual secret scan clean.

**Local log discipline, effective this round (see `DECISIONS.md`):** every future Claude/Codex task creates a local execution log before PR merge and updates `C:\Users\sekip\Desktop\bulkeditapp logs\LOG_INDEX.md` after merge. PR #108 had no dedicated log — retrospectively backfilled this round and marked `RETROSPECTIVE BACKFILL LOG`.

**Recommended next owner action, in order:**
1. Single-listing title write + Magic Revert (see `OWNER_BULK_EDIT_RUNBOOK.md`, `MAGIC_REVERT_RUNBOOK.md`).
2. Single-listing price write + Magic Revert.
3. Variation apply — separate, optional, requires explicit owner approval (no revert exists yet).

---

## Previously — 2026-08-30 (M19: beta readiness smoke matrix + owner runbooks — PR 4 of 4, final PR in the autonomous backlog run)

Branch `feature/m19-beta-readiness-smoke-matrix`, based on `origin/main` past PR #112's `10c7d54b3a1cbdf8577ce00c0524b76cce74d6de`. Merged as PR #113 (`e40027269c327964cf03c67e56a3ea5548c27621`), deployed, route-verified (26/26 smoke script pass). New `docs/operations/BETA_READINESS_SMOKE_MATRIX.md` (20 categories) plus a real fix to the stale pre-existing `scripts/smoke_test_deployment.sh`/`.ps1`, and three owner runbooks. This was PR 4 of 4 in the autonomous selected-backlog sequence (M10 → M03.04 → M13/M15 → M19), all four now merged/deployed/verified. See `CHANGELOG_AI.md` for full detail.

---

## Previously — 2026-08-30 (M13/M15: read-only media + variation depth — PR 3 of an autonomous 4-PR backlog run)

Branch `feature/media-variations-read-depth`, based on `origin/main` past PR #111's `9a220b08a902ff521c19c5365946c7964048f696`. Merged as PR #112 (`10c7d54b3a1cbdf8577ce00c0524b76cce74d6de`), deployed, route-verified. Zero backend files changed. Product detail page's Media card now shows a full read-only image gallery; Variations page shows a real read-only variation-data matrix (backend data existed and synced since Sprint 5/12, never rendered) plus a Diagnostics column; Media's replace/delete operations disabled pending a real restore endpoint (decision in `DECISIONS.md`); Video Generator gained listing-image selection; M15.02/M15.03/M15.04 statuses corrected to reflect pre-existing Sprint 12 code. See `CHANGELOG_AI.md` for full detail.

---

## Previously — 2026-08-30 (M03.04: shared ListingPicker — PR 2 of an autonomous 4-PR backlog run)

Branch `feature/m03-shared-listing-picker`, based on `origin/main` past PR #110's `f7d79e795be68026333908cca6a9b3303e6649e2`. Merged as PR #111 (`9a220b08a902ff521c19c5365946c7964048f696`), deployed, route-verified. New `apps/frontend/components/listings/ListingPicker.tsx` (shop/status filter, search, pagination, thumbnails, variation badge, empty/error/loading states), migrated into Media and Variations; Dynamic Pricing/Bulk Edit/Video Generator/Promote intentionally left for a later round (documented reasons per consumer, M03.04 stays `[~]`). See `CHANGELOG_AI.md` for full detail.

---

## Previously — 2026-08-30 (M10: Listing Health issue detail + Shop Insights affected listings — PR 1 of an autonomous 4-PR backlog run)

Branch `feature/m10-listing-health-insights-details`, based on `origin/main` past PR #109's `fd7269e0a469d40ecbad9b7386bdca639980f3a5`. Merged as PR #110 (`f7d79e795be68026333908cca6a9b3303e6649e2`), deployed, route-verified. Audit found the backend already computed everything for M10.01 (full per-listing issue list via `score_listing()`) — fixed frontend-only, `[~]` marked for the honest zero-quantity/variation/personalization scoring-engine gap. M10.03 shipped a new `GET /insights/affected-listings` endpoint in full, `[x]`. See `CHANGELOG_AI.md` for full detail.

---

## Previously — 2026-08-30 (M08.07/M16.06: Magic Revert plan-gate enforcement)

**Branch `fix/magic-revert-plan-gate`, based on `origin/main` past PR #108's `1f984baa248d041f0f630535815b7b368dbbd34f`.** Closes the known gap PR #107/#108 tracked but deliberately didn't fix: `PLAN_LIMITS["can_use_magic_revert"]` (Free: `False`) is now actually enforced server-side.

**Audit first, code-read not guessed:** `get_effective_plan()` (`app/core/plans.py`, comp-grant aware) is the established helper — same one PR #104 used to fix the analogous bulk-edit-usage-gate bug. `validate_apply_job_revertable()` (`app/services/bulk_edit_revert.py`) is the single call site both the direct revert endpoint (`POST /apply-jobs/{id}/revert`) and, indirectly via `get_revert_eligibility_map()`, the history endpoint (`GET /apply-jobs`) both route through.

**Enforcement:** the plan gate is checked **last** in `validate_apply_job_revertable()` — after the org-scoped lookup (404, so a cross-org job id never leaks existence), status check (400), zero-success check (400), and duplicate-revert check (409) — so an already-reverted job still reports "Already reverted.", not "plan blocked", and no RevertJob row is created and no Etsy call is made before every check passes. `get_revert_eligibility_map()` mirrors the identical rule in the identical order, resolving the effective plan **once per history request** (not per job — no N+1). Blocked response: `403 "Magic Revert is not available on your current plan."` — no "admin"/"comp grant"/internal wording.

**Tests:** 8 new (`test_bulk_edit_revert.py`) — Free blocked direct-call + history, Pro allowed, comp-grant-Pro allowed (same bug class as PR #104, raw `Subscription.plan` stays `free` while effective plan gates correctly), already-reverted-takes-precedence, cross-org-still-404-not-leaked, zero-success-still-blocked-on-Pro. All ~25 pre-existing revert-mechanics tests updated via a `grant_plan="pro_monthly"` default added to the shared `_setup_and_apply()` fixture (comp-grant path, not a raw plan mutation) — none skipped or weakened. Targeted suite (`test_bulk_edit_revert.py`+`test_bulk_edit.py`+`test_bulk_edit_apply.py`+`test_billing.py`): 129 passed, 13 pre-existing baseline failures (same local-only `*_requires_auth` 401-vs-403 quirk documented in every prior round, confirmed via `git stash` A/B against `origin/main` before this branch) — no regressions.

**Frontend: no change needed.** `/magic-revert` (PR #107) already renders `revert_blocked_reason` as the disabled-button tooltip/label, and `lib/api.ts`'s `ApiError.message` already surfaces the backend's exact `detail` string on a direct 403 — both were built generically enough in PR #107 to need no update for this new reason string.

**No Etsy API call, no Bulk Edit apply/Magic Revert/shop sync/OAuth by Claude/Codex.**

**Recommended next work, in order:**
1. **Owner live QA of the Magic Revert History UI** (`/magic-revert`, `/account/activity`) — click-through only; do not actually run a Magic Revert against a real Etsy listing unless the owner explicitly approves that exact action in-session.
2. **UX-01C** — Listing Health issue detail (tag count, photo count, missing/zero price, variation warnings) + Shop Insights affected-listings navigation (see `TASKS.md` M10.01/M10.03).

---

## Previously — 2026-08-29 (docs cleanup after PR #101 + PR #107)

Both PR #107 (`7ee420dc1bca90b812ab7e48becece4e0ff241c0`) and PR #101 (`092e02f9303b9c824cc816176e485d91720cc730`) merged into `main` and deployed; branch `docs/update-current-truth-after-pr101-pr107` (PR #108) fixed stale pre-merge PR #101 wording left in `TASKS.md`/`HANDOFF.md`/`PROJECT_STATUS.md`, backfilled M11 checkboxes against PR #105, recorded PR #106/#107 shipped-state in M09/M13/M16, and recorded the `can_use_magic_revert` plan-gate known gap as a tracked package (M08.07/M16.06) instead of only prose. See `CHANGELOG_AI.md` for full detail.

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
