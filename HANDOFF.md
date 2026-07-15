# HANDOFF.md — Session Handoff

Purpose: only what the next session needs to resume safely. For full engineering history, see `CHANGELOG_AI.md`. For current production/environment state, see `PROJECT_STATUS.md`. For durable decisions, see `DECISIONS.md`.

## RESUME HERE — 2026-07-15

**Current state:** Production is LIVE and healthy (backend/frontend/DB/Redis all confirmed, migration `0025`, Private Beta enabled). Retention cleanup is Option A — DO Scheduled Job, first real execution succeeded 2026-07-15 (0 rows deleted, no errors). Etsy developer app remains **Banned**, no reason given. The final appeal package (`ETSY_FINAL_APPEAL_DRAFT.md`) is fully drafted and updated with the retention-run evidence, but **explicitly marked NOT SUBMITTED** — this requires the owner's own review and send, not something to do autonomously. PR #61 (retention-monitoring doc fix) and PR #62 (finalized appeal draft) are both merged. A documentation full-sync pass (this session) consolidated `PROJECT_STATUS.md`/`TASKS.md`/this file, synchronized the Etsy compliance docs, and fixed stale Vercel/Render-as-current-hosting claims in the operations docs.

**Critical environment facts:**
- Hosting: DigitalOcean App Platform (`bulk-edit-prod-api`, `bulk-edit-prod-web`) + Cloudflare. App IDs: prod-api `2f37fa86-a826-4dc2-b5d3-22f44d85cb1c`, prod-web `fb4415ca-cd2d-4929-a754-08f1893f4d25`.
- **Merging to `main` triggers an immediate production rebuild for BOTH apps** (`deploy_on_push: true`, no path filter) — even a docs-only merge redeploys both. Always confirm DB backup + any relevant preflight *before* merging, not after; the merge itself is the deploy trigger.
- Retention job monitoring: `doctl apps list-job-invocations <app-id> --job-name retention-cleanup --format ID,Jobname,Created,Started,Completed,Phase`, then `doctl apps logs <app-id> retention-cleanup --job-invocation <id> --type run`. (`--component` is not a real flag — component name is positional.)
- Backend tests: 982 passed (current authoritative count — anything citing 975/971/968/964 elsewhere is historical, already annotated as superseded where it appears).

**Current branch/PR state:** `docs/full-project-state-sync` (this session's documentation cleanup) — not yet opened as a PR as of this writing. `main` is otherwise clean; no other open feature branches in flight.

**Unresolved work:** none engineering-side. The only remaining step in the Etsy compliance effort is the owner's own appeal submission — see Pending Owner Action in `TASKS.md`.

**Exact next step:** if `docs/full-project-state-sync` hasn't been opened/merged yet, finish that (PR, CI, merge, post-merge prod health check). Otherwise: nothing is blocking engineering work. Whenever the owner is ready, they review and send `ETSY_FINAL_APPEAL_DRAFT.md`. After Etsy responds (either direction), re-test live OAuth, live Etsy writes, and the never-tested-live video-upload endpoint.

**Safety constraints still active:** never print secrets/tokens or DigitalOcean's `EV[...]` encrypted placeholders; no live Etsy write/OAuth test while banned; no real Stripe charge/subscription/refund without explicit instruction; do not disable Private Beta until Etsy responds; no DNS/Cloudflare/owner-domain changes without explicit instruction; do not deploy without explicit go-ahead beyond normal PR-merge flow; do not submit the Etsy appeal — that is the owner's action alone.

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
