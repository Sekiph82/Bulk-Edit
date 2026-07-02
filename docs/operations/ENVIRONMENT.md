# Environment Variables Reference

All secrets are stored in environment variables. Never hardcode secrets in source code.

## Quick Start

```bash
cp .env.example .env
# Edit .env and fill in required values
```

For local Docker development, the `.env` file at the repo root is mounted into all containers via `docker-compose.yml`.

---

## Required Variables

### Database

| Variable | Example | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@db:5432/bulk_edit` | Async PostgreSQL connection string |

### Security

| Variable | Example | Description |
|---|---|---|
| `JWT_SECRET` | *(random 64-char hex)* | Signs JWT access + refresh tokens. Rotate if compromised. |
| `ENCRYPTION_KEY` | *(Fernet 32-byte base64)* | Encrypts Etsy OAuth tokens at rest. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

### Redis / Queue

| Variable | Example | Description |
|---|---|---|
| `REDIS_URL` | `redis://redis:6379/0` | Used by Celery broker and result backend |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Celery broker (same as REDIS_URL for local) |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Celery result backend |

---

## Optional Variables

### Stripe Billing

| Variable | Example | Description |
|---|---|---|
| `STRIPE_SECRET_KEY` | `sk_live_...` | Stripe secret key. Omit in local dev — billing endpoints return 503. |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Stripe webhook signing secret |
| `STRIPE_PRICE_ID_BASIC_MONTHLY` | `price_...` | Stripe price ID for basic monthly plan |
| `STRIPE_PRICE_ID_PRO_MONTHLY` | `price_...` | Stripe price ID for pro monthly plan |
| `STRIPE_PRICE_ID_BASIC_YEARLY` | `price_...` | Stripe price ID for basic yearly plan |
| `STRIPE_PRICE_ID_PRO_YEARLY` | `price_...` | Stripe price ID for pro yearly plan |

### Etsy OAuth

| Variable | Example | Description |
|---|---|---|
| `ETSY_CLIENT_ID` | `abc123...` | Etsy OAuth2 client ID. Omit in local dev — Etsy endpoints return 503. |
| `ETSY_CLIENT_SECRET` | `secret...` | Etsy OAuth2 client secret |
| `ETSY_REDIRECT_URI` | Local: `http://localhost:8100/api/v1/etsy/callback` · Prod: `https://api.bulkeditapp.com/api/v1/etsy/callback` | Backend callback route (verified in `app/api/v1/etsy.py`). Must match the Etsy app config exactly. |

### AI Providers

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `mock` | `mock` (no API calls), `openai`, or `anthropic` |
| `OPENAI_API_KEY` | — | Required if `AI_PROVIDER=openai` |
| `ANTHROPIC_API_KEY` | — | Required if `AI_PROVIDER=anthropic` |

### S3-Compatible Storage

| Variable | Example | Description |
|---|---|---|
| `S3_ENDPOINT` | `http://minio:9000` | MinIO local or AWS S3 endpoint |
| `S3_BUCKET` | `bulk-edit-media` | Bucket name for media uploads |
| `S3_ACCESS_KEY_ID` | `minioadmin` | S3 access key |
| `S3_SECRET_ACCESS_KEY` | `minioadmin` | S3 secret key |

### Email (SMTP)

| Variable | Example | Description |
|---|---|---|
| `SMTP_HOST` | `smtp.gmail.com` | SMTP host for transactional email |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | `noreply@bulkeditapp.com` | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |

### Application URLs

| Variable | Local | Production | Description |
|---|---|---|---|
| `FRONTEND_URL` | `http://localhost:3100` | `https://www.bulkeditapp.com` | Canonical frontend origin (used for Stripe success/cancel + portal return URLs) |
| `BACKEND_URL` | `http://localhost:8100` | `https://api.bulkeditapp.com` | Public backend base URL |
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8100` | `https://api.bulkeditapp.com` | Frontend → backend URL (exposed to browser) |
| `NEXT_PUBLIC_APP_URL` | `http://localhost:3100` | `https://www.bulkeditapp.com` | Canonical app URL (used in emails) |

The frontend reads `NEXT_PUBLIC_BACKEND_URL` at build/runtime (`apps/frontend/lib/api.ts`) and falls back to `http://localhost:8100` only when unset. Production URL is not hardcoded.

### Environment mode + subdomain model (DigitalOcean)

The production domain split (from the DigitalOcean migration — see `DIGITALOCEAN_DEPLOY.md`):

| Host | Serves | `NEXT_PUBLIC_BACKEND_URL` |
|---|---|---|
| `bulkeditapp.com` / `www` | Marketing (www 301→apex) | — |
| `app.bulkeditapp.com` | Private app | `https://api.bulkeditapp.com` |
| `api.bulkeditapp.com` | Backend API | — |
| `staging.bulkeditapp.com` | Staging app | `https://api-staging.bulkeditapp.com` |
| `api-staging.bulkeditapp.com` | Staging API | — |

| Variable | Values | Purpose |
|---|---|---|
| `NEXT_PUBLIC_APP_ENV` | `staging` \| `production` | Drives the staging banner + host-aware behavior. `staging` shows the "STAGING - NOT PRODUCTION" banner and forces noindex. |
| `ENVIRONMENT` (backend) | `local` \| `staging` \| `production` | Backend mode; staging must use test/dev credentials only. |

Host routing, `www`→apex redirect, and `X-Robots-Tag: noindex` for app/staging are handled by `apps/frontend/middleware.ts`; per-host `robots.txt` by `apps/frontend/app/robots.ts`.

### CORS

| Variable | Local | Production | Description |
|---|---|---|---|
| `BACKEND_CORS_ORIGINS` | `http://localhost:3100` | `https://www.bulkeditapp.com,https://bulkeditapp.com` | Comma-separated or JSON list of allowed origins. Parsed by `Settings.get_cors_origins()`. Wildcard `*` is forbidden in production (`validate_env.py`). |

### Observability

| Variable | Example | Description |
|---|---|---|
| `SENTRY_DSN` | `https://...@sentry.io/...` | Sentry error tracking DSN. Leave empty to disable Sentry entirely. Never expose real value in logs. |
| `SENTRY_ENVIRONMENT` | `production` | Sentry environment tag. Default: `development`. |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Fraction of transactions to trace (0.0–1.0). Default: `0.0` (disabled). |
| `DEBUG` | `false` | Enables `/docs` and `/redoc` on backend. Never enable in production. |

### Rate Limiting

| Variable | Example | Default | Description |
|---|---|---|---|
| `RATE_LIMIT_ENABLED` | `true` | `false` | Master toggle. Set `false` in tests and local dev. |
| `RATE_LIMIT_REDIS_URL` | `redis://redis:6379/1` | *(empty — uses `REDIS_URL`)* | Redis URL for rate limit counters. Falls back to `REDIS_URL` if empty; falls back to in-memory if Redis unavailable. |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | `10` | `10` | Max login attempts per IP per minute. |
| `RATE_LIMIT_REGISTER_PER_MINUTE` | `5` | `5` | Max register attempts per IP per minute. |
| `RATE_LIMIT_CONTACT_PER_HOUR` | `5` | `5` | Max contact-form submissions per IP per hour. |

### Video Generator

| Variable | Default | Description |
|---|---|---|
| `VIDEO_RENDERER_ENABLED` | `false` | Set `true` to enable the Video Generator. ffmpeg must be available. |
| `FFMPEG_PATH` | `ffmpeg` | Override ffmpeg binary path. Leave empty to use system default. |
| `VIDEO_OUTPUT_DIR` | `/tmp/video_renders` | Directory where rendered MP4 files are stored inside the container. |

When `VIDEO_RENDERER_ENABLED=false`, the Video Generator page shows all controls normally. Customers see a friendly modal when they click Generate Video. No env var names or developer instructions are shown.

### Pinterest Integration

| Variable | Description |
|---|---|
| `PINTEREST_CLIENT_ID` | Pinterest app ID from developers.pinterest.com |
| `PINTEREST_CLIENT_SECRET` | Pinterest app secret. Never expose in logs or API responses. |
| `PINTEREST_REDIRECT_URI` | OAuth callback URL. Must match what is registered in your Pinterest app. Local: `http://localhost:8100/api/v1/promote/pinterest/callback` · Prod: `https://api.bulkeditapp.com/api/v1/promote/pinterest/callback` |

All three must be set for Pinterest Connect to work. If any are missing, `config-status` returns `pinterest_configured: false` and the Connect button opens a friendly unavailable modal.

### Instagram / Meta Integration

| Variable | Description |
|---|---|
| `META_APP_ID` | Meta app ID from developers.facebook.com |
| `META_APP_SECRET` | Meta app secret. Never expose in logs or API responses. |
| `INSTAGRAM_REDIRECT_URI` | OAuth callback URL. Must match what is registered in your Meta app. Local: `http://localhost:8100/api/v1/promote/instagram/callback` · Prod: `https://api.bulkeditapp.com/api/v1/promote/instagram/callback` |

All three must be set for Instagram Connect to work. Instagram publishing requires a Business or Creator account connected to a Facebook Page.

### Project Isolation

| Variable | Value | Description |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | `bulk-edit` | Docker Compose project name. Set by startup scripts automatically. |

---

## Local Superuser Seed (Development Only)

File: `apps/backend/.local-superusers.env`

**NEVER commit this file.** It is gitignored. It is only read on backend startup for local development.

```env
FREE_EMAIL=test@example.com
FREE_PASSWORD=YourPassword1!
FREE_FULL_NAME=Test User
FREE_ORG_NAME=Test Org

PAID_EMAIL=test-su@example.com
PAID_PASSWORD=YourPassword1!
PAID_FULL_NAME=Admin User
PAID_ORG_NAME=Admin Org
PAID_PLAN=pro_monthly
PAID_IS_SUPERUSER=true
```

See `.local-superusers.env.example` for the template.

---

## Environment Hierarchy

| Environment | `.env` source | AI_PROVIDER | Stripe | Etsy |
|---|---|---|---|---|
| Local (Docker) | `.env` (from `.env.example`) | `mock` | Not configured | Not configured |
| CI/CD | GitHub Actions secrets | `mock` | Not configured | Not configured |
| Staging | Deployment platform secrets | `openai` | Stripe test keys | Etsy sandbox |
| Production | Deployment platform secrets | `openai` | Stripe live keys | Etsy production |

---

## Secrets Rotation

If any secret is compromised:

1. **JWT_SECRET** — Rotate immediately. All existing sessions will be invalidated (users must log in again).
2. **ENCRYPTION_KEY** — Rotating requires re-encrypting all stored Etsy tokens. Contact the engineering team.
3. **STRIPE_WEBHOOK_SECRET** — Regenerate in Stripe Dashboard and update in environment.
4. **ETSY_CLIENT_ID** — Regenerate in Etsy Developer Portal and re-authorize all shops.
