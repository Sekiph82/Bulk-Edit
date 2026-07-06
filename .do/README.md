# DigitalOcean App Platform specs

Four app specs. Each `.yaml` = one DO app. Two apps per environment (frontend +
backend) because DO ingress routes by path, not by hostname — so different
subdomains need separate apps.

| File | App | Domain(s) | Branch | Status |
|---|---|---|---|---|
| `app.staging-frontend.yaml` | Next.js web | `staging.bulkeditapp.com` | `staging` | Provision in Phase 1 |
| `app.staging-backend.yaml` | FastAPI + migrate job + PG + Redis | `api-staging.bulkeditapp.com` | `staging` | Provision in Phase 1 |
| `app.production-frontend.yaml` | Next.js web (apex + www + app) | `bulkeditapp.com`, `www`, `app` | `main` | **Design only** |
| `app.production-backend.yaml` | FastAPI + migrate job + PG + Redis | `api.bulkeditapp.com` | `main` | **Design only** |

- Migrations run in a **PRE_DEPLOY job** (`alembic upgrade head`), never in the web
  container start — a failed migration aborts the deploy instead of crash-looping.
- **No secrets in these files.** Secret env vars are set in the DO dashboard as
  encrypted `SECRET` vars (each backend spec lists the required keys at the bottom).
- Redis uses DO managed Redis/Valkey; if incompatible, swap for an Upstash
  `REDIS_URL` SECRET (see `docs/operations/DIGITALOCEAN_DEPLOY.md`).

Full walkthrough: `docs/operations/DIGITALOCEAN_DEPLOY.md`.
DNS/TLS/Access: `docs/operations/CLOUDFLARE_DNS.md`.
