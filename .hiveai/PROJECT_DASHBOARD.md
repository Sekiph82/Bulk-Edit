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

Phase: Private Beta production QA. M00-M09 PASS/CLOSED-with-known-gaps; M10 (Listing Health/Insights detail), M03.04 (shared ListingPicker), M13/M15 (media/variation read-only depth), M16 (Magic Revert history/plan-gate), and M19 (beta readiness matrix/runbooks) all SHIPPED and merged (PRs #107–#114) as of 2026-08-30. Owner then ran a manual non-destructive smoke test across 7 screens and found 4 polish items, all closed in the current in-flight PR (branch `fix/owner-qa-polish-before-write-tests`).
Known good: Etsy OAuth, owner shop connection, 210 active listing sync, title write, single and 33-listing bulk non-variation price write, 32-listing bulk Magic Revert, Etsy rate-limit guard, Apply/Revert double-submit guard + overlay, effective-plan billing/usage gate fix (PR #104), Magic Revert plan-gate enforcement (PR #109), Magic Revert history/Activity & Audit (PR #107, owner-QA-confirmed 2026-08-30), Listing Health/Shop Insights detail (PR #110, owner-QA-confirmed), shared ListingPicker in Media/Variations/Video Generator (PR #111, owner-QA-confirmed), variation read-only matrix against real synced data (PR #112, owner-QA-confirmed).
Current manual proof needed: **owner has not yet run a live title write + Magic Revert, or a live price write + Magic Revert, through the app** — this is the next recommended owner action, see `HANDOFF.md` and `docs/operations/OWNER_BULK_EDIT_RUNBOOK.md`/`MAGIC_REVERT_RUNBOOK.md`. Variation apply/revert also never owner-live-verified (separate, optional). See `TASKS.md` M04.04/M15.02-M15.04/M19.01 for the specific open verification items.
Immediate next task family: owner-run live write verification (title, then price, then optionally variation) — no further autonomous engineering work is queued pending that owner action.

## Safety policy

Claude/Codex must not call Etsy API directly from a different IP unless the owner explicitly approves that exact task. Live Etsy tests are performed by the owner through the app/browser over the owner VPN.

Never print, store, or commit secrets, tokens, raw Authorization, raw x-api-key, OAuth code/state, DigitalOcean token, database URLs, cookies, or production env values.

All write workflows must be preview-first, owner-confirmed, item-level reported, and revert-aware when possible.

## Refresh model

H!veAI should derive live state from Git/watcher evidence plus the canonical sources above. This manifest should remain pointer-only and should not be rewritten as a generated status snapshot.
