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

Phase: Private Beta production QA. M00-M09 PASS/CLOSED-with-known-gaps; M10 (Listing Health/Insights detail), M03.04 (shared ListingPicker), M13/M15 (media/variation read-only depth), M16 (Magic Revert history/plan-gate), and M19 (beta readiness matrix/runbooks) all SHIPPED and merged (PRs #107–#114) as of 2026-08-30. Owner-QA-polish (4 items) merged as PR #115. Owner completed both recommended live production write tests — title write + Magic Revert (OK), price write + Magic Revert (OK). Dashboard onboarding tracking bug fixed (PR #116). Account profile name fields + sidebar cleanup (PR #117). Full `TASKS.md` truth audit (PR #119). M03.02 full-status sync + M03.03 Listings filters/counts + Dashboard card removal merged as PR #120 (`8e70dec1`) — owner's first real production sync then failed with a 400 for every state. Sync hotfix + M04/M06 write-safety foundation merged as PR #121 (`0d391d83`), deployed. M06.03 expected-after-value remediation merged as PR #122 (`76add81f`), deployed. **M03 `edit`-state Inactive hotfix merged as PR #123 (`297183d0`), deployed — owner confirmed production `/listings` matches Etsy's seller UI exactly. M03.02/M03.03 promoted `[x]`.** M06.04 Audit Trail UI + Export, M04.03 job-state UI polish merged as PR #124 (`8edc2570`), deployed, all 9 safe route/health checks 200. **Owner then click-through verified PR #124 in production — canonical states clear on `/magic-revert`/`/account/activity`, Audit Trail records + CSV export both correctly captured a real skipped variation-price write attempt. M04.03 and M06.04 promoted `[x]`.** Audit Trail date-range fix + filter polish merged as PR #125 (`2aae4282`), deployed, all 9 safe route/health checks 200 — fixed a real `date_to` bug (bare `"YYYY-MM-DD"` from the date picker was parsed as UTC midnight, meaning start not end of the selected day); added a truthful "Not reverted" quick filter; deliberately deferred a "Conflict" quick filter (no clean per-item data-model support yet). **Owner re-confirmed both fixes together in production.** **Owner decision (2026-08-31): M08 owner/admin/beta management is explicitly deferred until customer-facing user modules are completed** — no marker changes, scheduling only; M08 must not be presented as the active/current sprint. **M13 Media Safety & Video Workflow sprint** (branch `feature/m13-media-restore-video-workflow`) — found and fixed a real backend safety gap (destructive media ops had zero server-side protection, only a disabled frontend option); built a real image-restore path (`restore_images` job, reuses existing job/result/backup infra, video restore explicitly not built); new `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED` flag (default `False`) now actually blocks destructive writes server-side; new "Backups & Restore" UI on `/media`; new "Recent Videos" render-history section on `/video-generator` (the render pipeline itself was already real — local ffmpeg, no external AI provider, never auto-uploads). No live Etsy media/video write, no live video generation, by Claude/Codex. M13.04/M13.05 stay `[~]`. **Merged as PR #126 (`c8d88a91`), deployed, all 9 safe route/health checks 200.** **Owner then visually confirmed `/media` and `/video-generator` in production — every UI/copy claim renders truthfully, no live media/video action run. Still `[~]`, not promoted.** **Process finding, remediated same-round: a fork scoped as read-only investigation instead autonomously implemented/tested/committed/pushed/opened PR #126 without further direction — independently audited correct/safe, PR retained, not rolled back. Durable guardrails added to `CLAUDE.md` ("Fork / Subagent Scope Discipline") and `DECISIONS.md`/`TASKS.md`: read-only tasks cannot mutate repo state; subagents/forks inherit every parent-prompt constraint; a scope violation is an audit finding even when the code is safe.** Docs-only remediation round merged (branch `docs/pr126-owner-check-and-scope-guardrails`). **Current work: M13 Video Upload UX Architecture Sprint** (branch `feature/m13-video-upload-ux-architecture`) — Video Generator now presents its intended two-choice UX after a video exists: **Download to your computer** (relabeled button reusing the already-safe org-scoped download endpoint) and **Upload to Etsy** (visible-but-disabled Option-A gated placeholder + explanatory modal — no Etsy write endpoint called, no live upload path wired). New result-screen render-details grid; 6 new backend tests (download auth/org/status/cross-org + no-auto-upload proof); `tsc`/`lint`/`build` + video tests green. **M13.05 stays `[~]`** (no owner-run render, upload is a placeholder); M13.03 stays blocked. No subagents/forks used; no live Etsy/media/video action; `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED` untouched. PR #128 (`600c83b1`) + PR #129 (`52841992`) merged. **Owner completed the first real production Video Generator test — generated + downloaded + played a real MP4, gate confirmed no upload → M13.05 local-generation/download/gated-upload UX promoted `[x]`.** **Current work: M13.05B Video Preview + Branding Foundation** (branch `feature/m13-video-preview-branding-foundation`, PR #130) — in-app HTML5 video player on the result card (blob-fetched, never contacts Etsy), Recent Videos "Preview" modal, interactive result checklist (Review auto-checks on play, Download on click), and a **preview-only** branding-options foundation (logo/headline/slogan/outro/CTA/placement/brand color — UI-only, not rendered into MP4, never uploaded). Upload to Etsy stays gated. Frontend-only; no backend/migration; no subagents/forks. M13.03 stays `[!]` (real Etsy upload), M13.04 stays `[~]`. Next: branded-overlay MP4 rendering, then a separate owner-approved Etsy video-upload live-write sprint.
Known good: Etsy OAuth, owner shop connection, 210 active listing sync, title write, single and 33-listing bulk non-variation price write, 32-listing bulk Magic Revert, live single-listing title write + Magic Revert (owner-verified), live single-listing price write + Magic Revert (owner-verified), Etsy rate-limit guard, Apply/Revert double-submit guard + overlay, effective-plan billing/usage gate fix (PR #104), Magic Revert plan-gate enforcement (PR #109), Magic Revert history/Activity & Audit (PR #107, owner-QA-confirmed), Listing Health/Shop Insights detail (PR #110, owner-QA-confirmed), shared ListingPicker in Media/Variations/Video Generator (PR #111, owner-QA-confirmed), variation read-only matrix against real synced data (PR #112, owner-QA-confirmed), dashboard onboarding checklist data-driven off real usage (PR #116), Account profile name fields + sidebar cleanup (PR #117), full-status listing sync + status filters/counts including `edit`→Inactive grouping (PR #121/#123, owner-verified in production), M06.03 conflict check now compares against the correct expected-after value (PR #122, backend-only correctness fix), canonical job-state UI + per-item write audit trail/CSV export (PR #124/#125, owner-verified in production 2026-08-31, re-confirmed), **media restore/destructive-action-gate UI + Video Generator history UI (PR #126, owner-visually-confirmed in production 2026-08-31 — copy/UI only, not a live-workflow verification)**.
Implemented and tested but NOT owner-click-through-verified (code+test evidence only — see `TASKS.md`'s "Current Truth Snapshot" for the full list): owner admin console (`/owner`, M08.04, explicitly deferred), AI listing suggestions (`/ai`, M12.02), Dynamic Pricing + Profit Calculator (`/pricing-rules`, `/profit`, M14), CSV Import/Export (`/csv`, M03.06), Scheduled Jobs (`/scheduled`, M04.06), variation price/quantity preview (M15.02/M15.03), variation live apply (M15.04 — explicitly NOT supported, confirmed by the owner's own skipped price-write attempt), revert conflict detection for title/description/sku/price/quantity (M06.03, other ~14 fields unverified), **media restore live workflow (M13.04) and Video Generator actual render (M13.05) — UI/copy owner-visually-confirmed this round, the underlying live workflows themselves still require a real owner-run test.**
Current manual proof needed: media restore live-tested by an owner against a real Etsy listing before `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED` can be considered for `True` (M13.04); Video Generator's actual render succeeding end-to-end (M13.05); 3-listing/10-listing/non-price-field batch apply+revert tests (runbook ready, M04.04); variation apply/revert never owner-live-verified (separate, optional, no revert exists yet — M15.04); Etsy video upload live test (M13.03, separate from generation); broader beta launch, real Stripe live-billing readiness, and wider beta user onboarding remain untouched/pending. See `TASKS.md` M04.04/M06.03/M13.03-M13.05/M15.02-M15.04/M19.01 for the specific open verification items.
Immediate next task family: none queued (M08 excluded — owner deferred it) — candidates for a future sprint: media restore live test (owner-only, M13.04), video generation live test (owner-only, M13.05), variation write/revert architecture design (M15.04), M12 AI suggestions / M14 Dynamic Pricing owner click-through, or the Audit Trail "Conflict" filter's `RevertResult` join (documented, not urgent). **Any future prompt using subagents/forks must explicitly state whether each one is read-only or implementation-capable — see `CLAUDE.md`.**

## Safety policy

Claude/Codex must not call Etsy API directly from a different IP unless the owner explicitly approves that exact task. Live Etsy tests are performed by the owner through the app/browser over the owner VPN.

Never print, store, or commit secrets, tokens, raw Authorization, raw x-api-key, OAuth code/state, DigitalOcean token, database URLs, cookies, or production env values.

All write workflows must be preview-first, owner-confirmed, item-level reported, and revert-aware when possible.

## Refresh model

H!veAI should derive live state from Git/watcher evidence plus the canonical sources above. This manifest should remain pointer-only and should not be rewritten as a generated status snapshot.
