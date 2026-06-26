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
| `ETSY_REDIRECT_URI` | `http://localhost:3100/etsy/callback` | Must match Etsy app configuration exactly |

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
| `SMTP_USER` | `noreply@bulk-edit.com` | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |

### Application URLs

| Variable | Example | Description |
|---|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8100` | Frontend → backend URL (exposed to browser) |
| `NEXT_PUBLIC_APP_URL` | `http://localhost:3100` | Canonical app URL (used in emails) |

### CORS

| Variable | Example | Description |
|---|---|---|
| `BACKEND_CORS_ORIGINS` | `http://localhost:3100` | Comma-separated or JSON list of allowed origins |

### Observability

| Variable | Example | Description |
|---|---|---|
| `SENTRY_DSN` | `https://...@sentry.io/...` | Sentry error tracking DSN. Omit to disable. |
| `DEBUG` | `false` | Enables `/docs` and `/redoc` on backend. Never enable in production. |

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
