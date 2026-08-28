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

Phase: Private Beta production QA moving into write hardening.
Known good: Etsy OAuth, owner shop connection, 210 active listing sync, title write, single non-variation price write.
Current manual proof needed: Magic Revert for the successful single-listing price change.
Current risk: Etsy HTTP 429 per-second rate limit during repeated write tests.
Immediate next task family: Sprint 2 rate-limit guard and write hardening after Magic Revert proof.

## Safety policy

Claude/Codex must not call Etsy API directly from a different IP unless the owner explicitly approves that exact task. Live Etsy tests are performed by the owner through the app/browser over the owner VPN.

Never print, store, or commit secrets, tokens, raw Authorization, raw x-api-key, OAuth code/state, DigitalOcean token, database URLs, cookies, or production env values.

All write workflows must be preview-first, owner-confirmed, item-level reported, and revert-aware when possible.

## Refresh model

H!veAI should derive live state from Git/watcher evidence plus the canonical sources above. This manifest should remain pointer-only and should not be rewritten as a generated status snapshot.
