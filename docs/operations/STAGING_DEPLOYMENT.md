# Staging Deployment Guide

> **Hosting: DigitalOcean App Platform + Cloudflare.** Concrete provisioning steps,
> app specs, and the staging→production gate are in `DIGITALOCEAN_DEPLOY.md`;
> DNS/Access/TLS/email in `CLOUDFLARE_DNS.md`. Specs: `.do/app.staging-*.yaml`.
> Staging protection = Cloudflare Access on the frontend + strict CORS on the API
> (`https://staging.bulkeditapp.com` only) + noindex + staging banner. This guide
> describes the general staging model; the DO docs are authoritative.

## Purpose

Staging mirrors production but uses test credentials and a separate database.
Every release must pass staging before promotion to production.

## Architecture

```
https://staging.bulkeditapp.com         → Frontend (Next.js)
https://api-staging.bulkeditapp.com     → Backend API (FastAPI)
Separate PostgreSQL DB                → Isolated from production
Separate Redis instance               → Isolated from production
```

## Staging Environment Variables

Start from `.env.example` and fill in staging-specific values:

| Variable | Staging Value | Notes |
|---|---|---|
| `DATABASE_URL` | Separate staging DB | **NEVER share with production** |
| `REDIS_URL` | Separate staging Redis | |
| `CELERY_BROKER_URL` | Same as REDIS_URL | |
| `CELERY_RESULT_BACKEND` | Same as REDIS_URL | |
| `JWT_SECRET` | Different from production | Generate a fresh one |
| `ENCRYPTION_KEY` | Different from production | Generate a fresh Fernet key |
| `BACKEND_CORS_ORIGINS` | `https://staging.bulkeditapp.com` | |
| `FRONTEND_URL` | `https://staging.bulkeditapp.com` | |
| `NEXT_PUBLIC_BACKEND_URL` | `https://api-staging.bulkeditapp.com` | |
| `NEXT_PUBLIC_APP_URL` | `https://staging.bulkeditapp.com` | |
| `STRIPE_SECRET_KEY` | `sk_test_...` | Stripe test mode |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` from Stripe test webhook | |
| `AI_PROVIDER` | `openai` or `mock` | Use mock to avoid AI costs |
| `RATE_LIMIT_ENABLED` | `true` | |
| `RATE_LIMIT_BACKEND` | `redis` | |
| `SENTRY_ENVIRONMENT` | `staging` | |
| `ENVIRONMENT` | `staging` | |
| `DEBUG` | `false` | |

## Etsy in Staging

Options (in order of preference):

1. **Mock the Etsy connection**: Set `ETSY_CLIENT_ID` to empty — the app handles this state gracefully (shows "Etsy not configured" in the shops page).
2. **Use a personal dev Etsy account**: Register a separate Etsy API app for staging with `ETSY_REDIRECT_URI=https://api-staging.bulkeditapp.com/api/v1/etsy/callback`.
3. **Etsy sandbox**: Etsy does not provide an official sandbox environment; personal dev accounts are the closest alternative.

## Deploying to Staging

### Step 1: Validate environment

```bash
cd apps/backend
ENVIRONMENT=staging python scripts/validate_env.py --env staging
```

Fix any errors before proceeding.

### Step 2: Apply database migrations

```bash
# Backup first
pg_dump $STAGING_DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Apply
alembic upgrade head

# Verify
alembic current
```

### Step 3: Deploy

```bash
# Using the production compose example
IMAGE_TAG=<commit-sha> docker compose -f docker-compose.prod.example.yml up -d
```

Or trigger your hosting platform's deploy command (Railway, Render, Fly.io).

### Step 4: Smoke test

```bash
./scripts/smoke_test_deployment.sh \
  https://staging.bulkeditapp.com \
  https://api-staging.bulkeditapp.com
```

All checks must pass.

### Step 5: Playwright E2E (optional but recommended)

```bash
cd apps/frontend
PLAYWRIGHT_BASE_URL=https://staging.bulkeditapp.com npm run e2e
```

## Seeded Test Accounts in Staging

Create via the register endpoint or by setting up `.local-superusers.env` with staging credentials. **Do NOT reuse local development passwords in staging.**

Minimum accounts needed:
- A regular user (free plan) — for testing customer flows
- A superuser — for testing admin panel

## Promotion Criteria (Staging → Production)

All items must be checked before promoting to production:

### Tests

- [ ] All backend tests pass in CI (`pytest` — 621+/621+)
- [ ] Frontend build clean (22+ routes, 0 errors)
- [ ] Playwright E2E passes on staging

### Manual QA

- [ ] Register a new user — completes without error
- [ ] Login / logout — works
- [ ] Dashboard loads with onboarding checklist for new user
- [ ] Billing page loads; plan shown correctly
- [ ] Stripe test payment completes (use card `4242 4242 4242 4242`)
- [ ] Etsy shop connection (if configured) — OAuth flow completes
- [ ] Admin nav hidden for regular user
- [ ] Admin dashboard accessible for superuser
- [ ] /admin 403 for regular user (shows "access denied" UI)

### Infrastructure

- [ ] `GET /api/v1/health` → `{"status":"ok"}`
- [ ] `GET /api/v1/health/ready` → `{"status":"ready"}`
- [ ] Rate limit test: 11+ login requests in 1 minute → 429 response
- [ ] Security headers present: `curl -I https://api-staging.bulkeditapp.com/api/v1/health`
- [ ] No secrets visible in any API response
- [ ] Alembic migration applied cleanly (`alembic current` shows latest revision)

### Observability

- [ ] Sentry receiving events (trigger an intentional 404, verify it appears)
- [ ] Rate limiting active (`RATE_LIMIT_ENABLED=true`, backend `redis`)

## Related Docs

- [DNS_SSL.md](DNS_SSL.md) — Domain and TLS setup
- [MIGRATIONS.md](MIGRATIONS.md) — Alembic migration commands
- [BACKUP_AND_ROLLBACK.md](BACKUP_AND_ROLLBACK.md) — Backup procedures
- [LAUNCH_READINESS_REPORT.md](LAUNCH_READINESS_REPORT.md) — Launch checklist template
