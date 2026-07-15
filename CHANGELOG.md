# Changelog

All notable changes to Bulk Edit App are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project uses date-based release headings until versioned releases begin.

> AI-assisted session-by-session detail lives in `CHANGELOG_AI.md`. This file is
> the human-facing, product-level changelog.

## [2026-07-14] Etsy compliance, production deployment, retention automation

### Added
- Full Etsy compliance + production-readiness audit and remediation: `ALLOW_ETSY_DATA_TO_AI` gate
  (default off), configurable 30-day retention on backup snapshots/CSV jobs, terms/privacy acceptance
  enforcement, self-service account deletion (blocked while a Stripe subscription is active/billable,
  never auto-cancels).
- Automated daily retention cleanup in production — DigitalOcean App Platform Scheduled Job
  (`retention-cleanup`, 03:30 UTC), first real execution succeeded 2026-07-15 (0 rows deleted, no errors).
- Final Etsy appeal package drafted (`ETSY_FINAL_APPEAL_DRAFT.md`) — **not yet submitted**, pending
  owner review.

### Fixed
- OAuth granted-scope storage bug (was recording token type, not the granted scope string).
- Shop disconnect now deletes stored tokens immediately instead of only marking them inactive.
- 9 tables were missing an `organization_id` foreign key, so account deletion could leave Etsy
  shop/token/listing data orphaned — fixed via migration `0025`.

### Changed
- Public site copy corrected: removed pre-launch/"founding access" framing on an already-live product;
  removed public marketing for AI Listing Optimization and Listing Health Score (both remain live
  in-app) pending Etsy's guidance on Etsy-derived-data AI use.

### Security
- Backend-enforced admin authorization, encrypted Etsy tokens, Stripe webhook verification +
  idempotency, Sentry PII scrubbing (pre-existing; catalogued during architecture audit).

## [2026-07-06] Production launch (Private Beta)

### Added
- Production live on **DigitalOcean App Platform + Cloudflare** (`bulk-edit-prod-api`,
  `bulk-edit-prod-web`) — the original Vercel + Render plan was superseded before it was ever
  provisioned in production; kept only as historical reference (`docs/operations/VERCEL_RENDER_DEPLOY.md`).
- Private Beta gate: new sign-ups paused pending Etsy/Stripe production validation.
- Guardrails: `staging` branch, branch protection policy, CodeQL workflow, Dependabot.
- Production-domain configuration for `bulkeditapp.com` (marketing `www`/apex, `app`, `api`).

### Changed
- Deployment target: DigitalOcean App Platform + Cloudflare (not Vercel + Render).

<!--
Release template:

## [YYYY-MM-DD]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security
-->
