---
hiveaiDashboardSchema: hiveai-project-dashboard/v1
projectKey: bulk-edit
repository: Sekiph82/Bulk-Edit
branchPolicy: main
dashboardMode: source-map
refreshPolicy: watcher-driven source invalidation; no generated status commits
---

# H!veAI Project Dashboard Manifest

This file is a pointer map for H!veAI. It is not a task ledger and must not duplicate task checkboxes.

## Project identity

Project: Bulk Edit
Repository: `Sekiph82/Bulk-Edit`
Default branch: `main`

## Source authorities

Canonical task source: `TASKS.md`
Handoff source: `HANDOFF.md`
Roadmap source: `ROADMAP.md`
Progress/history source: `CHANGELOG_AI.md`
Status snapshot source: `PROJECT_STATUS.md` as secondary context only
Architecture source: `ARCHITECTURE.md`
Decision source: `DECISIONS.md`
Product source: `PRODUCT.md`
Agent instruction source: `CLAUDE.md`
Security source: `SECURITY.md`
Build/test metadata: repository `Makefile`, application package manifests, and CI configuration

## Authority notes

`TASKS.md` is the task authority. `HANDOFF.md` may describe current/next/blocker/waiting state, but must not silently override task truth.

`PROJECT_STATUS.md` is a snapshot and `CHANGELOG_AI.md` is execution history. They are secondary evidence, not competing task ledgers.

Etsy compliance/readiness documents are domain evidence and policy context, not the canonical project backlog unless a task is explicitly mirrored into `TASKS.md`.

## Refresh model

H!veAI should derive live state from Registry/Git/watcher evidence plus the canonical sources above. This manifest should remain pointer-only and should not be rewritten as a generated status snapshot.
