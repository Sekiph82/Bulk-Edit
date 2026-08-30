---
hiveaiDashboardSchema: hiveai-project-dashboard/v1
projectKey: bulk-edit
repository: Sekiph82/Bulk-Edit
branchPolicy: main branch is the active production branch; merging main triggers production deploy for API and web apps
dashboardMode: source-map
refreshPolicy: watcher-driven source invalidation; no generated status commits
---

# H!veAI Project Dashboard Manifest

This file is a pointer map for H!veAI. It is not a task ledger and must not duplicate task checkboxes.

## Project identity

Project: Bulk Edit App
Repository: `Sekiph82/Bulk-Edit`
Active branch: `main`
Local path: `C:\Users\sekip\Desktop\Bulk-Edit`
Product: Etsy bulk editing SaaS for safe preview, apply, revert, sync, media, promotion, and automation workflows.

## Production identity

Public website: `https://bulkeditapp.com`
App: `https://app.bulkeditapp.com`
API: `https://api.bulkeditapp.com`
Private Beta: enabled; registration paused; sign-in allowed.
Connected owner test shop: WearYourStoriesCom.

## Source authorities

Canonical task source: `TASKS.md`
Roadmap source: `TASKS.md` for current work; `ROADMAP.md` for historical platform build plan.
Handoff source: `HANDOFF.md`
Current status source: `PROJECT_STATUS.md`
Progress/history sources: `CHANGELOG_AI.md`, `CHANGELOG.md`, merged PR history.
Local execution log index: `C:\Users\sekip\Desktop\bulkeditapp logs\LOG_INDEX.md`
Decision/governance source: `DECISIONS.md`
Agent instruction source: `CLAUDE.md`
Operations sources: `docs/operations/`, deployment logs, DigitalOcean deployment status.
Security/compliance sources: `ETSY_COMPLIANCE_AUDIT.md`, `ETSY_PRODUCTION_READINESS.md`, `ETSY_DATA_RETENTION.md`, `ETSY_FINAL_APPEAL_DRAFT.md`.
Build/test metadata: `apps/backend/requirements*.txt`, `apps/frontend/package.json`, GitHub Actions workflows.

## Authority notes

`TASKS.md` is the current canonical task ledger and sprint plan. It overrides old short active-work snapshots when they disagree.

`ROADMAP.md` is a historical/product-planning source for the older platform build sprints. It must not override `TASKS.md` for current execution order.

`CHANGELOG_AI.md`, execution logs, previous prompts, screenshots, and merged PR bodies are evidence/history. They are not current task authority unless `TASKS.md` explicitly reopens or promotes a finding.

`HANDOFF.md` is the next-session resume file. If it is stale relative to `TASKS.md`, update it rather than letting it override the canonical task ledger.

## Current operating state

`TASKS.md` was converted to the H!veAI-style milestone ledger (M00-M20) on 2026-08-29, merged to `main` as PR #101 (`092e02f`) on 2026-08-30. This section is a snapshot pointer only — `TASKS.md`'s own "Current truth" section is authoritative if the two ever disagree.

Phase: Private Beta production QA. M00-M09 PASS/CLOSED-with-known-gaps; M10 (Listing Health/Insights detail), M03.04 (shared ListingPicker), M13/M15 (media/variation read-only depth), M16 (Magic Revert history/plan-gate), and M19 (beta readiness matrix/runbooks) all SHIPPED and merged (PRs #107–#114) as of 2026-08-30. Owner-QA-polish (4 items) merged as PR #115 (`e2bfe46`). Owner completed both recommended live production write tests — title write + Magic Revert (OK), price write + Magic Revert (OK). Dashboard onboarding tracking bug + `[object Object]` display bug fixed and merged as PR #116 (`2ec4226c`). Account profile name fields + sidebar identity cleanup + small beta-readiness polish merged as PR #117 (`96b9f027`). **Current work: full `TASKS.md` truth audit** (docs-only, branch `docs/tasks-md-full-truth-audit`) — every milestone re-verified against source code/tests/migrations rather than trusted from prior summaries; corrected a badly stale bottom-of-file "Milestone policy" summary, added two entirely untracked shipped features (CSV Import/Export M03.06, Scheduled Jobs M04.06), and upgraded M08.04 (owner admin console)/M12.02 (AI suggestions)/M14 (Dynamic Pricing) from `[ ]` "not started" to `[~]` (real, tested, not owner-click-through-verified).
Known good: Etsy OAuth, owner shop connection, 210 active listing sync, title write, single and 33-listing bulk non-variation price write, 32-listing bulk Magic Revert, live single-listing title write + Magic Revert (owner-verified), live single-listing price write + Magic Revert (owner-verified), Etsy rate-limit guard, Apply/Revert double-submit guard + overlay, effective-plan billing/usage gate fix (PR #104), Magic Revert plan-gate enforcement (PR #109), Magic Revert history/Activity & Audit (PR #107, owner-QA-confirmed), Listing Health/Shop Insights detail (PR #110, owner-QA-confirmed), shared ListingPicker in Media/Variations/Video Generator (PR #111, owner-QA-confirmed), variation read-only matrix against real synced data (PR #112, owner-QA-confirmed), dashboard onboarding checklist data-driven off real usage (PR #116), Account profile name fields + sidebar cleanup (PR #117).
Implemented and tested but NOT owner-click-through-verified (code+test evidence only — see `TASKS.md`'s "Current Truth Snapshot" for the full list): owner admin console (`/owner`, M08.04), AI listing suggestions (`/ai`, M12.02), Dynamic Pricing + Profit Calculator (`/pricing-rules`, `/profit`, M14), CSV Import/Export (`/csv`, M03.06), Scheduled Jobs (`/scheduled`, M04.06), variation price/quantity preview (M15.02/M15.03), variation live apply (M15.04).
Current manual proof needed: variation apply/revert never owner-live-verified (separate, optional, no revert exists yet — M15.04); media upload/delete/replace remains disabled pending a restore endpoint (M13.04); video generation never run; broader beta launch, real Stripe live-billing readiness, and wider beta user onboarding remain untouched/pending. See `TASKS.md` M15.02-M15.04/M19.01 for the specific open verification items.
Immediate next task family: none queued — this audit surfaced several real, tested-but-unverified capabilities as candidates for a future owner click-through pass; variation apply/media/video remain separate, optional, owner-approval-only actions.

## Safety policy

Claude/Codex must not call Etsy API directly from a different IP unless the owner explicitly approves that exact task. Live Etsy tests are performed by the owner through the app/browser over the owner VPN.

Never print, store, or commit secrets, tokens, raw Authorization, raw x-api-key, OAuth code/state, DigitalOcean token, database URLs, cookies, or production env values.

All write workflows must be preview-first, owner-confirmed, item-level reported, and revert-aware when possible.

## Refresh model

H!veAI should derive live state from Git/watcher evidence plus the canonical sources above. This manifest should remain pointer-only and should not be rewritten as a generated status snapshot.
