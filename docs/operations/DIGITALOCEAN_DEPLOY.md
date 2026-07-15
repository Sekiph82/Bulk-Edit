# DigitalOcean Deployment (App Platform + Cloudflare)

**Current status (2026-07-15): this is the live hosting.** Production (`bulk-edit-prod-api`, `bulk-edit-prod-web`) has been provisioned and live since 2026-07-06 (Private Beta gate), running the Etsy-compliance deployment since 2026-07-14. The staging→production gate below is kept as the process record for how production was first provisioned, not a currently-pending step.

Specs live in `.do/` (see `.do/README.md`). DNS/TLS/Access in `CLOUDFLARE_DNS.md`.

## Topology

Two DO apps per environment (DO ingress routes by path, not host):

```
STAGING
  bulk-edit-staging-web   -> staging.bulkeditapp.com        (Next.js Node, branch: staging)
  bulk-edit-staging-api   -> api-staging.bulkeditapp.com    (FastAPI + migrate job + PG + Redis)

PRODUCTION (design only for now)
  bulk-edit-prod-web      -> bulkeditapp.com / www / app     (one Next.js app, host-routed)
  bulk-edit-prod-api      -> api.bulkeditapp.com             (FastAPI + migrate job + PG + Redis)
```

Frontend must be a **Next.js Node service** (not static export) — host-based
routing (`middleware.ts`), redirects, `X-Robots-Tag`, and the staging banner need
a running server.

## Migrations (pre-deploy job)

Each backend app has a `PRE_DEPLOY` job running `alembic upgrade head`. The web
service `run_command` is uvicorn only. Benefits:
- failed migration aborts the deploy (web stays on the previous release),
- migrations run once per deploy, not once per web instance.

Alembic is idempotent, so the Dockerfile default `start.sh` (migrate+serve) staying
in place for Render/local is harmless — DO overrides `run_command`.

## Database / Redis

- **Postgres**: DO managed PG 16. `DATABASE_URL` injected as `${*-db.DATABASE_URL}`
  (`postgresql://…`); the backend normalizes to `postgresql+asyncpg://` at load
  (`app/core/config.py`).
- **Redis/Valkey**: DO managed Redis via `${*-redis.DATABASE_URL}`.
  - Compatibility: the app uses `redis==5.1.1` (rate limiting) and Redis for
    Celery. DO managed Redis/Valkey speaks the Redis protocol — expected to work.
  - **Fallback (Upstash):** if the DO instance is incompatible (TLS/auth/eviction
    quirks), remove the `staging-redis` database block and instead set `REDIS_URL`
    as a SECRET pointing at an Upstash `rediss://` URL. Nothing else changes.

## Backups / rollback

- Enable **automated backups + PITR** on the production managed PG.
- **App rollback != DB rollback.** Reverting a deploy does not undo a migration.
  Forward-fix with a new migration, or restore a PG snapshot/PITR. See
  `BACKUP_AND_ROLLBACK.md`.
- Before any production migration: verify it ran clean on staging first.

## Secrets

Never in `.do/*.yaml`. Set as encrypted `SECRET` env vars in the DO dashboard.
Staging = TEST/DEV credentials only (Stripe `sk_test_`, dev Etsy, low-limit AI).
Required keys listed at the bottom of each backend spec.

## Provisioning order (staging)

1. `doctl auth init` (or use the dashboard).
2. Create the managed PG + Redis (via the specs' `databases` blocks or standalone).
3. `doctl apps create --spec .do/app.staging-backend.yaml`.
4. `doctl apps create --spec .do/app.staging-frontend.yaml`.
5. Set all SECRET env vars in the dashboard (staging/test values).
6. Add custom domains in each app; copy the DO ingress targets.
7. Cloudflare: add DNS records to those targets + Access on staging (`CLOUDFLARE_DNS.md`).
8. Trigger a deploy; confirm the pre-deploy migrate job succeeds.
9. Run `scripts/smoke-production.ps1` adapted to staging hosts (or curl the health paths).

## Staging -> production gate (historical — production already passed this)

Provision production only after ALL are true:
- [ ] staging frontend + backend deploy successfully
- [ ] pre-deploy migration job runs clean on staging
- [ ] staging DB + Redis are separate from any prod resource (verified)
- [ ] Cloudflare Access + noindex + banner confirmed on staging
- [ ] `/api/v1/health` and `/api/v1/health/ready` return 200 on api-staging
- [ ] no production/live secrets used anywhere in staging

## Health checks

- Backend: `GET /api/v1/health` (liveness). `/api/v1/health/ready` checks DB+Redis.
- Frontend: `GET /` returns 200.

## Manual steps summary

DO: create 2 staging apps + managed PG + managed Redis; set SECRET env vars;
attach domains; enable PG backups.
Cloudflare: DNS records (real DO targets), `www`→apex redirect, Access on
`staging`, SSL Full (strict). See `CLOUDFLARE_DNS.md`.
