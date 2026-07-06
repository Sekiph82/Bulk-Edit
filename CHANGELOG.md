# Changelog

All notable changes to Bulk Edit App are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project uses date-based release headings until versioned releases begin.

> AI-assisted session-by-session detail lives in `CHANGELOG_AI.md`. This file is
> the human-facing, product-level changelog.

## [Unreleased]

### Added
- Guardrails: `staging` branch, branch protection policy, CodeQL workflow, Dependabot.
- Production-domain configuration for `bulkeditapp.com` (frontend `www`/apex, `api` backend).
- Guided Vercel + Render deploy automation (retained as reference; DigitalOcean is the new target).
- DigitalOcean App Platform staging spec, Cloudflare DNS plan, staging protection scaffolding
  (host-based routing middleware, env-aware robots, staging banner).

### Changed
- Deployment target moving from Vercel + Render to **DigitalOcean App Platform + Cloudflare**.
  Vercel/Render files kept as fallback reference.

### Security
- Backend-enforced admin authorization, encrypted Etsy tokens, Stripe webhook verification +
  idempotency, Sentry PII scrubbing (pre-existing; catalogued during architecture audit).

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
