# Bulk-Edit — Canonical GitHub Task State

This root `TASKS.md` is the only authoritative current project-status tracker consumed by H!veAI. GitHub repository metadata and the latest commit are the remaining project-truth inputs. Historical control-plane files under `docs/migration/legacy-task-trackers/` are archival evidence only and must never override this file.

## Project Status

- Current Milestone: M13
- Current Sprint: M13.03
- Current Task: M13.03 — Etsy listing video upload workflow
- Current Task Status: BLOCKED
- Next Task/Action: M13.03 — Run the owner-approved single-listing live Etsy video upload acceptance; keep ETSY_VIDEO_UPLOAD_ENABLED disabled until the explicit test window and record the acceptance result here.
- Required Actor: OWNER
- Workflow State: BLOCKED_ON_OWNER_ACCEPTANCE
- Tracking Repository: Sekiph82/Bulk-Edit
- Tracking Branch: main

## Blockers/Waits

- M13.03 requires explicit owner approval and an owner-run live single-listing Etsy video upload acceptance before the upload gate can be treated as production-ready.
- M13.04 remains gated by `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED=false` until an owner-run live media restore/destructive-action acceptance is completed.
- M13.06 is blocked on Pinterest/Meta developer-app setup and required permissions/review.
- M08 owner/admin/private-beta management expansion is deferred by owner decision until customer-facing workflows are further completed.
- M20.03 registration re-enable remains blocked on an explicit owner decision.

## H!veAI Parser Contract

- Project Status metadata labels above are plain text. Do not wrap `Current Milestone:`, `Current Sprint:`, `Current Task:`, `Current Task Status:`, `Next Task/Action:`, `Required Actor:`, or `Workflow State:` in Markdown bold markers.
- Every canonical task row must use exactly one of these forms: `- [x] TASK-ID — Title`, `- [~] TASK-ID — Title`, `- [!] TASK-ID — Title`, or `- [ ] TASK-ID — Title`.
- Status semantics are: `[x]` validated complete, `[~]` implemented/active/partial, `[!]` blocked, `[ ]` planned/backlog.
- Only real task/package rows use checkbox markers. Evidence, acceptance notes, historical context, and limitations use ordinary indented bullets so H!veAI does not count them as separate tasks.
- Task IDs are stable. Do not reuse an ID for a different task after it has appeared in this file.
- Builder or agent self-reports are claims, not acceptance evidence. A task moves to `[x]` only with appropriate source/test/production/owner evidence for that task.
- Root `TASKS.md` is the only current-state ledger. `PROJECT_STATUS.md`, `HANDOFF.md`, historical `.hiveai` files, changelogs, audits, and execution logs are reference/history only and cannot override this file.

## Canonical Tracking Rules

- Keep Project Status synchronized with the task row that actually owns the current work.
- Update this file in the same branch/PR as the implementation or acceptance evidence it describes.
- `ROADMAP.md` is roadmap/reference material and does not override execution order here.
- `CHANGELOG_AI.md` and `DECISIONS.md` preserve engineering history and durable decisions; they are not competing live trackers.
- `docs/migration/legacy-task-trackers/` preserves retired H!veAI control-plane artifacts for provenance only.
- Etsy live tests and Etsy writes are owner-run unless the owner explicitly authorizes the exact action.
- Never print or commit Etsy secrets, OAuth credentials/tokens, DigitalOcean tokens, raw authorization headers, cookies, raw environment values, or database URLs.
- Production writes require preview, explicit confirmation, backup where supported, permission/plan checks, safe audit logging, item-level results, and the existing rate-limit/write-pacing protections.
- Merging to `main` deploys both production apps, including docs-only merges. Use PR review and do not merge tracker-only changes casually.
- Read-only/audit-only/subagent work cannot mutate repository or production state. Scope violations remain audit findings even when resulting code is technically correct.

## Current Truth Snapshot

- Production is live in Private Beta at `app.bulkeditapp.com`; registration remains paused while sign-in is allowed.
- Etsy OAuth/shop connection, listing sync, Bulk Edit title/price writes, Magic Revert, rate-limit guards, and apply/revert audit history have real production evidence.
- Listing status counts were owner-verified against Etsy as `All 547 / Active 210 / Inactive 180 / Draft 0 / Expired 157 / Sold out 0` after the `edit`-state grouping correction.
- M13.05 local video generation/download/in-app preview/text branding was owner-verified with newly generated production MP4s. Video generation never auto-uploads to Etsy.
- M13.03 has a dedicated `ETSY_VIDEO_UPLOAD_ENABLED` gate, a read-only upload-intent flow, and upload primitives, but the real live upload acceptance remains blocked on the owner. The gate stays off outside an explicitly approved test.
- M13.04 image restore/destructive-media infrastructure exists and is tested, but production destructive/restore operations remain disabled pending owner live acceptance; video restore remains incomplete.
- Historical implementation/audit detail remains in Git history, `CHANGELOG_AI.md`, `DECISIONS.md`, `docs/audits/`, `docs/operations/`, and `docs/migration/legacy-task-trackers/`. This ledger intentionally keeps only parser-safe task truth plus concise evidence notes.

## Tasks

Legend: `[x]` validated complete, `[~]` active/implemented-but-partial, `[ ]` planned/backlog, `[!]` blocked.

### M00 — Product and repository foundation

- [x] M00.01 — Repository and tech stack
  - Evidence: `Sekiph82/Bulk-Edit`; Next.js 14/TypeScript frontend, FastAPI/Python backend, PostgreSQL/SQLAlchemy/Alembic, Redis/Celery, JWT/Etsy OAuth, Stripe, S3-compatible storage.
- [x] M00.02 — Hosting, environment, and CI foundation
  - Evidence: DigitalOcean App Platform + Cloudflare; `main` deploys production; GitHub Actions covers backend/frontend/CodeQL/compose checks.

### M01 — Auth, Private Beta, and billing foundation

- [x] M01.01 — JWT authentication foundation
  - Evidence: registration/login plus access/refresh-token flow shipped.
- [x] M01.02 — Private Beta registration gate
  - Evidence: registration routes are gated while authenticated sign-in and Etsy OAuth callback flow remain usable.
- [~] M01.03 — Stripe foundation and production workflow review
  - Evidence: products/prices/environment were validated without a real charge; manual production webhook/workflow re-review remains open.

### M02 — Etsy OAuth and shop connection

- [x] M02.01 — OAuth safe logging
  - Evidence: callback logging records categories/booleans without code, state, token, or secret values.
- [x] M02.02 — Etsy `x-api-key` header format
  - Evidence: live 403 root cause fixed to the required key/shared-secret shape.
- [x] M02.03 — Owner shop lookup and connection parsing
  - Evidence: defensive user-id validation and single-Shop parsing shipped; owner confirmed `WearYourStoriesCom` connection.

### M03 — Listing sync and listing-data foundation

- [x] M03.01 — Full active-listing sync
  - Evidence: effective-plan cap handling and pagination fixes shipped; owner confirmed 210 active listings.
- [x] M03.02 — Full inventory/status read-only sync
  - Evidence: active plus non-active states, `edit`→Inactive grouping, isolation/error handling, and production data were owner-verified.
- [x] M03.03 — Listing status filters and real counts
  - Evidence: All/Active/Inactive/Draft/Expired/Sold out tabs/counts are backed by local synced data and owner-verified in production.
- [~] M03.04 — Shared `ListingPicker` adoption
  - Evidence: Media, Variations, and Video Generator migrated and owner-observed; Dynamic Pricing, Bulk Edit, and Promote remain unmigrated where a simple swap is unsafe or non-trivial.
- [~] M03.05 — Cross-module listing visibility consistency
  - Evidence: Variations and Media visibility are fixed; Dynamic Pricing already displays listings but the package has not received a dedicated closure pass.
- [~] M03.06 — CSV Import/Export
  - Evidence: real preview-safe import/export implementation and tests exist; owner click-through acceptance is still missing.

### M04 — Bulk Edit preview/session/apply foundation

- [x] M04.01 — Bulk Edit session, preview, and apply core
  - Evidence: session creation, staged changes, before/after preview, and apply execution are production-established.
- [x] M04.02 — Shared 204-response handling and change removal
  - Evidence: common API client fix covers remove-change and other 204 routes.
- [x] M04.03 — Canonical apply-job state presentation
  - Evidence: persisted raw states map to canonical UI states; owner verified job states/counts in `/magic-revert` and `/account/activity`; running-job cancellation remains explicitly unsupported rather than faked.
- [~] M04.04 — Apply/revert verification matrix
  - Evidence: owner-verified 33-listing price apply/revert and single-listing title/price apply/revert exist; dedicated 3-listing, 10-listing, and non-price batch acceptance rows remain open.
- [x] M04.05 — Listing Health/Insights preselection UX
  - Evidence: preselected listings are pinned and visibly checked without auto-applying.
- [~] M04.06 — Scheduled Jobs
  - Evidence: real create/list/pause/resume/run workflow and tests exist; owner click-through acceptance remains open.

### M05 — Live Etsy write core stabilization

- [x] M05.01 — Shop-scoped title-write path
- [x] M05.02 — Price/quantity fetch-mutate-put inventory flow
- [x] M05.03 — Writable Etsy inventory payload normalization
- [x] M05.04 — Sanitized Etsy error diagnostics
- [x] M05.05 — `readiness_state_id` inventory requirement
- [x] M05.06 — Owner live title/price write verification
  - Evidence: live title and price writes succeeded; price flow was verified at single-item and bulk scale with successful reverts.

### M06 — Magic Revert and apply-job safety

- [x] M06.01 — Magic Revert core
- [x] M06.02 — Magic Revert live verification
- [~] M06.03 — Changed-since-apply revert conflict protection
  - Evidence: title/description/sku/price/quantity expected-after comparison is implemented and tested; unsupported write fields are fail-safe blocked but not semantically compared, so coverage is intentionally partial.
- [x] M06.04 — Per-field write audit trail and CSV export
  - Evidence: org-scoped audit records, filters, UI, export, before/after data, revert linkage, and owner production verification are complete.

### M07 — Rate limits, pacing, and write safety

- [x] M07.01 — Retry-with-backoff for Etsy writes
- [x] M07.02 — Per-shop write pacing gate
- [x] M07.03 — 429 diagnostics and frontend categorization
- [x] M07.04 — Apply/Revert double-submit guard and blocking overlay
- [x] M07.05 — Owner-verified clean guarded bulk apply/revert

### M08 — Billing, effective plan, usage, credits, and gates

- [x] M08.01 — Effective-plan billing display
- [x] M08.02 — Bulk Edit effective-plan usage gate
- [x] M08.03 — Sibling effective-plan feature gates
- [~] M08.04 — Owner dashboard and comp-grant management UI
  - Evidence: substantial `/owner` UI/API/audit support exists and is tested; recorded owner click-through acceptance remains missing.
- [ ] M08.05 — Stripe production workflow review
- [ ] M08.06 — Private Beta invite/allowlist user management
- [x] M08.07 — Magic Revert plan-gate enforcement
  - Evidence: effective-plan enforcement is mirrored in direct revert and history eligibility without cross-org leakage.

### M09 — Listings UX and product-detail workflow

- [x] M09.01 — Listing thumbnails and hover preview
- [x] M09.02 — HTML entity decoding
- [x] M09.03 — Product detail page and safe Bulk Edit deep links
- [~] M09.04 — Listings navigation acceptance
  - Evidence: row/title navigation and Quick View are implemented; explicit owner click-through of the final navigation pattern remains open.
- [!] M09.05 — Direct product-page Etsy write architecture
  - Blocker: dedicated credit/plan/write/revert architecture is required before direct inline Etsy writes may ship.
- [~] M09.06 — Owner visual QA remediation
  - Evidence: product image/layout/performance-card/nav/banner fixes shipped; final product-detail owner click-through remains open.

### M10 — Listing Health and Shop Insights

- [~] M10.01 — Listing Health issue detail and scoring depth
  - Evidence: issue detail UI is owner-observed; scoring still lacks zero-quantity, variation, and personalization/materials issue detection.
- [x] M10.02 — View Product and Fix in Bulk Edit paths
- [x] M10.03 — Shop Insights affected-listings drill-down

### M11 — Account Center and Connected Shops

- [x] M11.01 — Account information architecture
- [x] M11.02 — Customer-safe Plan & Billing presentation
- [x] M11.03 — Usage dashboard
- [~] M11.04 — Credits UI and credit history
  - Evidence: balance/limits/explanation shipped; real credit transaction history remains unbuilt.
- [x] M11.05 — Connected Shops inside Account
- [x] M11.06 — Team/Users MVP without admin leakage
- [~] M11.07 — Security surface and future session/2FA hooks
  - Evidence: Security MVP exists; active sessions/password/2FA depth remains planned.
- [x] M11.08 — Notification preferences MVP
- [x] M11.09 — Activity & Audit backed by real apply/revert history
- [~] M11.10 — Data & Privacy controls
  - Evidence: AI-data-use posture is shown; export/delete/disconnect controls remain incomplete.
- [x] M11.11 — Support/help surface
- [x] M11.12 — Profile names, greeting, and sidebar identity cleanup

### M12 — AI tools and compliance-safe automation

- [~] M12.01 — AI provider policy gate and customer explanation
  - Evidence: external Etsy-data-to-AI policy gate defaults safe; customer-facing explanation of policy-disabled state remains incomplete.
- [~] M12.02 — AI listing suggestions
  - Evidence: suggestion/session/accept/reject/convert-to-Bulk-Edit flow is implemented and tested; owner click-through remains open.
- [x] M12.03 — AI usage limits and usage UI
- [ ] M12.04 — Safe prompt/output audit logging

### M13 — Media, photos, video workflows, and Promote

- [x] M13.01 — Media module listing picker
- [x] M13.02 — Listing image read-only views
- [!] M13.03 — Etsy listing video upload workflow
  - Evidence: upload primitives, dedicated disabled-by-default gate, dry-run upload intent, current-slot/add-vs-replace planning, and gated frontend architecture exist.
  - Blocker: real single-listing upload acceptance is owner-only and has not been completed; `ETSY_VIDEO_UPLOAD_ENABLED` must remain false outside an explicit approved test.
  - Follow-up: refresh current Etsy video-slot metadata immediately before any future live upload so add-vs-replace decisions are not based on stale sync data.
- [~] M13.04 — Media backup/restore and destructive-action safety
  - Evidence: image restore infrastructure, backup history, and backend destructive-operation gate are implemented/tested; owner live restore acceptance is missing and video restore remains unbuilt.
- [x] M13.05 — Local Video Generator workflow
  - Evidence: owner generated real MP4s, verified in-app playback for new renders, Recent Videos preview, download, checklist, text branding, and no-auto-upload behavior.
  - Remaining enhancement: server-side logo overlay is deferred pending an SSRF-safe asset-fetch design and does not reopen the validated core video workflow.
- [!] M13.06 — Promote to Pinterest/Instagram
  - Blocker: external Pinterest/Meta developer apps, redirect/scopes, permissions, and possible production review are not configured.
- [~] M13.07 — Bulk Create shop-gate and draft workflow
  - Evidence: false connection gate fixed; actual Create Drafts workflow remains unimplemented.

### M14 — Dynamic Pricing and profit intelligence

- [~] M14.01 — Dynamic Pricing data prerequisites
- [~] M14.02 — Profit page validation
- [~] M14.03 — Pricing suggestion engine
- [~] M14.04 — Dynamic Pricing handoff into Bulk Edit
  - Evidence: these are real, tested, preview-safe implementations; the milestone remains partial because owner click-through acceptance is not recorded.

### M15 — Variations and inventory depth

- [x] M15.01 — Variation inventory read model and matrix
- [~] M15.02 — Variation price edit preview
- [~] M15.03 — Variation quantity edit preview
- [~] M15.04 — Variation write apply and revert
  - Evidence: apply mechanism is implemented/tested but not owner-live-verified; one-click variation revert is not implemented.
- [x] M15.05 — Variation diagnostics

### M16 — Activity, audit, history, and Magic Revert history

- [~] M16.01 — Standardized item-level write logs across all write surfaces
  - Evidence: Bulk Edit is standardized; media/social paths need the same final shape as those workflows mature.
- [x] M16.02 — Apply-job history
- [x] M16.03 — Magic Revert from prior jobs
- [~] M16.04 — Full audit/activity search and summary surface
  - Evidence: real history/audit UI exists; broader user/shop/listing/date search coverage remains incomplete.
- [~] M16.05 — Revert availability status depth
  - Evidence: job-level eligibility is complete; individual line-item availability remains unbuilt.
- [x] M16.06 — Magic Revert plan-gate enforcement

### M17 — Owner operations, beta ops, and support

- [x] M17.01 — Retention cleanup scheduled job
- [~] M17.02 — Owner dashboard acceptance
  - Evidence: real owner dashboard exists; owner click-through acceptance remains open.
- [~] M17.03 — Comp-grant management UI acceptance
  - Evidence: real Grant/Revoke UI exists; owner click-through acceptance remains open.
- [ ] M17.04 — Private Beta user invite/allowlist management
- [ ] M17.05 — Beta tester checklist and feedback flow

### M18 — Security, observability, and production hardening

- [ ] M18.01 — OAuth callback query-string redaction at infrastructure/access-log layer
  - Evidence: application logs are already safe; remaining gap is platform/access-log redaction verification.
- [x] M18.02 — Sanitized Etsy error-body diagnostics across write paths
- [~] M18.03 — Docs-only production-deploy discipline
  - Evidence: policy is documented; no tooling/CI enforcement exists yet.

### M19 — Beta readiness and launch polish

- [~] M19.01 — Production smoke-test matrix
  - Evidence: automated production smoke routes and substantial owner QA are complete; remaining destructive/manual rows are not all closed.
- [x] M19.02 — Help docs and owner runbooks
- [~] M19.03 — UX polish
  - Evidence: multiple owner-reported issues and onboarding regressions were fixed; no single comprehensive final polish/acceptance pass has closed the package.

### M20 — Public launch readiness

- [!] M20.01 — Etsy app review / production-access standing reconfirmation
  - Blocker: historical production credentials exist, but current review/access standing must be explicitly reconfirmed before closure.
- [ ] M20.02 — Public marketing site and pricing finalization
- [!] M20.03 — Registration re-enable decision
  - Blocker: Private Beta remains intentional until the owner explicitly authorizes public registration.

## Milestone Summary

- M00, M02, M05, and M07 are fully validated/closed at the package level represented here.
- M01, M03, M04, M06, M08-M19 contain a mix of validated, partial, planned, or blocked packages and therefore remain open as milestones even where substantial production functionality exists.
- M13.03 is the current blocking task because the implementation architecture exists but the required owner live acceptance has not occurred.
- M20 remains launch-readiness work and is not the current execution milestone while M13 owner acceptance and other customer-facing gaps remain open.
- Historical task/evidence prose removed from this canonical ledger remains recoverable in Git history and the archived engineering/audit documents; it was intentionally de-duplicated so H!veAI counts actual tasks rather than evidence bullets.
