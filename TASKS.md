# TASKS.md — Active Work

Legend: `[ ]` todo · `[~]` in progress · `[x]` done

Full sprint-by-sprint build history (Sprint 0 through Sprint 27, all DevOps fixes, the Vercel/Render → DigitalOcean hosting migration) lives in `CHANGELOG_AI.md` — not repeated here. This file tracks only what's currently active, blocked, or pending.

---

## Current Phase

Post-appeal waiting period / Private Beta operations. All planned feature sprints are complete. The Etsy appeal has been submitted by the owner. Current focus: none active — waiting on Etsy's response.

## In Progress

None.

## Blocked Externally

- **Etsy OAuth / live API verification** — Etsy developer app "bulk-edit-app" is Banned (escalated 2026-07-13, no reason given). Appeal submitted by owner; cannot be resolved from this side — waiting on Etsy's response.
- **Live Etsy write verification** (bulk-edit apply, revert, media, variations) — code-verified only, never re-exercised against a live shop since the ban.
- **Etsy listing-video-upload endpoint** — implemented per documented endpoint shape, never tested against a live shop (see `DECISIONS.md`, "[MEDIA] Etsy listing video upload/delete implemented for real").
- **Etsy-derived external AI processing guidance** — `ALLOW_ETSY_DATA_TO_AI` stays off by default until Etsy responds (see `ETSY_FINAL_APPEAL_DRAFT.md` §F, question 1).
- **Social republishing guidance** (Pinterest/Instagram auto-post) — deliberately stubbed pending Etsy's confirmation (§F, question 4).
- Any other action requiring Etsy developer access to be restored.

## Owner Action

- **Wait for Etsy's response** — nothing to do until then.
- **Record the Etsy appeal's case/ticket number**, if one becomes available (not yet captured in the repo — see `ETSY_FINAL_APPEAL_DRAFT.md` submission-status header).
- **When Etsy replies, send the response to the project/Claude** for next-step planning before acting on it.

## Deferred

- **Enabling external AI processing for Etsy-derived data** (`ALLOW_ETSY_DATA_TO_AI=true`) — deferred pending Etsy's written confirmation that sending Etsy-derived listing content to a third-party AI provider is permitted (`ETSY_FINAL_APPEAL_DRAFT.md` §F, question 1).
- **Disabling Private Beta** — deferred until Etsy responds and live OAuth is re-verified; not an engineering decision (see `DECISIONS.md`, "[LAUNCH] Private Beta gate stays enabled until Etsy's ban is resolved").
- **Pinterest/Instagram cross-posting** (live `POST` calls) — deliberately stubbed pending Etsy's confirmation that republishing synced listing content to a third-party marketing platform is permitted (§F, question 4).
- **Stripe webhook endpoint existence/events verification** — the Stripe MCP connector has no webhook-endpoint API access; unverifiable from this tooling. Needs a manual Stripe Dashboard check.
- **Real Celery worker** — not needed at current volume; retention cleanup runs as a DO Scheduled Job instead (see `DECISIONS.md`, "[OPS] Retention scheduling uses a DO App Platform `SCHEDULED` job, not Celery"). Revisit if background-task volume grows.
- **Migration 0023 backfill precision** — pre-existing snapshot rows got a retention window measured from migration-deploy-time rather than true `created_at`; documented, not fixed (makes retention more conservative, never less) — see `ETSY_DATA_RETENTION.md` §2.
- **Old Dependabot PRs / dependency bumps** — not merged unless separately requested by the owner.

## Recently Completed

- **Post-appeal public copy alignment (2026-07-16):** PR #64 (`fix/current-public-copy-appeal-alignment`, merge `6be4046`) neutralized remaining public AI wording (homepage hero/pricing preview, `/pricing`, `/features` metadata + safety line, FAQ, feature registry) and updated Privacy/Terms for current AI-safeguard and retention/account-deletion behavior. CI green (6/6), merged, both prod apps redeployed to `ACTIVE`, live site verified. No authenticated in-app functionality removed.
- **Post-PR-#64 production health re-verification (2026-07-16):** API health, DB connectivity, Redis connectivity, retention scheduler config/cron/command, and latest retention invocation (`ad207ee4-f05c-4038-b244-6e54bf9fd13a`, SUCCEEDED — second consecutive successful daily run) all confirmed read-only, no production changes made.
- **Documentation full-sync (2026-07-15):** consolidated `PROJECT_STATUS.md`/`TASKS.md`/`HANDOFF.md` to current-state-only; synchronized all Etsy compliance docs and the appeal draft to the confirmed-live retention scheduler and 982-test count; fixed stale Vercel/Render-as-current-hosting claims in `docs/operations/DEPLOYMENT.md`/`DNS_SSL.md`/`PRODUCTION_SMOKE_TEST.md` (now correctly point to DigitalOcean + Cloudflare, with the old plan marked superseded); merged PR #61 (retention-monitoring command fix) and PR #62 (finalized appeal draft).
- **Retention cleanup Option A (2026-07-14/15):** DO Scheduled Job live, first real execution succeeded 2026-07-15 (0 rows deleted, no errors) — see `ETSY_DATA_RETENTION.md` §2, `docs/operations/WORKERS.md`.
- **Etsy compliance + production-readiness pass (2026-07-13/14):** full audit, OAuth scope-storage bug fix, AI-data gate (`ALLOW_ETSY_DATA_TO_AI`), 30-day configurable retention, terms/privacy acceptance, self-service account deletion with a Stripe billing-safety gate (block, don't auto-cancel), 9 missing FK constraints fixed (migration `0025`), public-site marketing corrections. Merged to `main` (`435a1aa`) and deployed directly to production. Full detail: `ETSY_COMPLIANCE_AUDIT.md`, `ETSY_FEATURE_MATRIX.md`, `ETSY_PRODUCTION_READINESS.md`, `ETSY_DATA_RETENTION.md`.
- **Production Activation (2026-07-06/10):** Private Beta gate live; Stripe Live checkout validated end-to-end (zero real charges); all four price mappings confirmed. Etsy OAuth validation was blocked by app review status at the time (later escalated to Banned — see above).
- All 27 feature sprints (monorepo skeleton through Promote/Media/Video polish) — see `CHANGELOG_AI.md` for full detail per sprint.

## Backlog / Future

- Shopify integration
- Multi-language support
- Mobile app
- Affiliate program
- Public API for integrations
