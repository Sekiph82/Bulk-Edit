# Production Deployment — Vercel (frontend) + Render (backend)

**SUPERSEDED (2026-07-15) — kept as historical reference only.** The project migrated to DigitalOcean App Platform + Cloudflare before this plan was ever provisioned in production (see `DECISIONS.md` "[DEPLOY] Migrating to DigitalOcean App Platform + Cloudflare"). Current live hosting is documented in `DIGITALOCEAN_DEPLOY.md` and `CLOUDFLARE_DNS.md` — use those, not this file, for anything touching the actual production environment.

Originally chosen hosting for **bulkeditapp.com** (never went live):

| Piece | Host |
|---|---|
| Frontend (`www.bulkeditapp.com`) | **Vercel** |
| Backend API (`api.bulkeditapp.com`) | **Render** (Docker web service) |
| PostgreSQL | Render managed Postgres (or any managed Postgres) |
| Redis | Render Key Value / Redis (or Upstash) |

Domain model: frontend on `www`, apex `bulkeditapp.com` → 301 to `www`, backend on `api`.
Local dev is unchanged (`localhost:3100` / `localhost:8100`).

Deploy model: **provider Git auto-deploy** (Vercel + Render both watch `main`). No custom
GitHub Actions deploy workflow — see "CI/CD" at the bottom for the rationale.

---

## 0. Claude Code guided deployment (no manual terminal work)

Prefer this if you want Claude Code to drive the deploy. You only fill one file and press
Continue/OK — no copying files, no PowerShell, no CLI by hand.

Flow:

1. Claude runs `scripts/prepare-deploy-secrets.ps1`, which creates `deploy-secrets.local.env` from
   the template and opens it in Notepad.
2. You fill the blanks, **save**, and press **Continue/OK** in Claude Code.
3. Claude runs `scripts/deploy-production.ps1`, which:
   - validates required keys (prints only present/MISSING — never values),
   - links + deploys the frontend to Vercel (needs `VERCEL_ORG_ID` + `VERCEL_PROJECT_ID`),
   - sets the two public Vercel env vars,
   - finds/uses the Render service, requests the `api` custom domain, triggers a Render deploy,
   - writes `scripts/output/render-env-to-set.local.txt` (local-only, gitignored) for the Render
     dashboard env vars (the API bulk-replace is avoided so it can't clobber the blueprint-wired
     `DATABASE_URL` / `REDIS_URL`).
4. If required keys are missing, the script lists the missing names, re-opens the file, and stops —
   fill them and press Continue/OK again.
5. After DNS is live, Claude runs `scripts/smoke-production.ps1`.

Secrets stay in `deploy-secrets.local.env`, which is gitignored and never committed or printed.

First-time dashboard clicks that still cannot be fully scripted:

- Creating the Vercel project once (to obtain `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID`).
- Creating the Render service once from the `render.yaml` blueprint (to obtain `RENDER_SERVICE_ID`).
- Adding domains + the apex→www redirect in Vercel; pasting env vars + adding the `api` custom domain
  in Render.
- DNS records at your registrar; registering provider callbacks (Etsy/Pinterest/Meta) + Stripe webhook.

---

## 1. Frontend — Vercel

### Project settings

| Setting | Value |
|---|---|
| Framework Preset | Next.js |
| Root Directory | `apps/frontend` |
| Build Command | `npm run build` |
| Install Command | `npm install` |
| Output Directory | `.next` (Next.js default — leave as auto) |
| Node.js Version | 20.x |
| Production Branch | `main` |

### Environment variables (Vercel → Project → Settings → Environment Variables, scope: Production)

```
NEXT_PUBLIC_BACKEND_URL=https://api.bulkeditapp.com
NEXT_PUBLIC_APP_URL=https://www.bulkeditapp.com
```

`NODE_ENV=production` is set by Vercel automatically — do not add it manually.

**Never put backend secrets in Vercel.** The frontend only needs the two `NEXT_PUBLIC_*` vars above.
`NEXT_PUBLIC_*` values are embedded in the browser bundle — only put public values there.

### Domains

1. Vercel → Project → Settings → Domains → add `www.bulkeditapp.com` (primary).
2. Add `bulkeditapp.com` (apex) and set it to **Redirect to `www.bulkeditapp.com`**.
3. Vercel shows the exact DNS target to set at your registrar (see DNS section below).

---

## 2. Backend — Render

Two ways to create the service:

- **Blueprint (recommended):** Render → New → Blueprint → point at this repo. It reads `render.yaml`
  at the repo root, which provisions the Postgres DB, Redis, and the Docker web service, and wires
  `DATABASE_URL` / `REDIS_URL` automatically. You then fill in the `sync: false` secrets.
- **Manual:** New → Web Service → Docker, with the settings below.

### Web service settings (manual)

| Setting | Value |
|---|---|
| Type | Web Service |
| Runtime | Docker |
| Dockerfile Path | `apps/backend/Dockerfile` |
| Docker Context | `apps/backend` |
| Health Check Path | `/api/v1/health` |
| Auto Deploy | On (branch `main`) |
| Region | closest to your users |

The container runs `apps/backend/start.sh`: it applies Alembic migrations (with a short retry for a
cold DB), then starts uvicorn on Render's `$PORT`. No manual migration step needed for normal deploys.

### DATABASE_URL scheme note

Render's Postgres connection string is `postgresql://…`. The app rewrites it to
`postgresql+asyncpg://…` at load time (`app/core/config.py::_force_asyncpg_driver`), so you can paste
the raw Internal Database URL (or let the blueprint auto-wire it) without editing the scheme.

### Environment variables (Render → service → Environment)

Non-secret (already in `render.yaml` if you used the blueprint):

```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
FRONTEND_URL=https://www.bulkeditapp.com
BACKEND_URL=https://api.bulkeditapp.com
BACKEND_CORS_ORIGINS=https://www.bulkeditapp.com,https://bulkeditapp.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_BACKEND=redis
ETSY_REDIRECT_URI=https://api.bulkeditapp.com/api/v1/etsy/callback
PINTEREST_REDIRECT_URI=https://api.bulkeditapp.com/api/v1/promote/pinterest/callback
INSTAGRAM_REDIRECT_URI=https://api.bulkeditapp.com/api/v1/promote/instagram/callback
CONTACT_FROM_EMAIL=noreply@bulkeditapp.com
CONTACT_TO_EMAIL=support@bulkeditapp.com
VIDEO_RENDERER_ENABLED=false
AI_PROVIDER=mock
DATABASE_URL=<Render Postgres Internal URL — auto-wired by blueprint>
REDIS_URL=<Render Redis Internal URL — auto-wired by blueprint>
```

Secrets — set as `sync: false` / dashboard-only, never in git:

```
JWT_SECRET=<64-char random>
ENCRYPTION_KEY=<Fernet key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
STRIPE_SECRET_KEY=<sk_live_…>
STRIPE_WEBHOOK_SECRET=<whsec_…>
STRIPE_PRICE_BASIC_MONTHLY / _PRO_MONTHLY / _BASIC_YEARLY / _PRO_YEARLY=<price ids>
ETSY_CLIENT_ID / ETSY_CLIENT_SECRET=<from Etsy>
PINTEREST_CLIENT_ID / PINTEREST_CLIENT_SECRET=<from Pinterest, if used>
META_APP_ID / META_APP_SECRET=<from Meta, if used>
OPENAI_API_KEY / ANTHROPIC_API_KEY=<if AI_PROVIDER != mock>
SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD=<if email used>
SENTRY_DSN=<if error monitoring used>
```

> Note: there is no `SECRET_KEY` in this app — token signing uses `JWT_SECRET`.

### Video renderer on Render

ffmpeg is installed in the image. Render's disk is ephemeral — `/tmp/video_renders` is fine only
because generated videos are downloaded immediately. Keep `VIDEO_RENDERER_ENABLED=false` until the
temp-file download flow is validated on Render. Persistent media requires S3/R2 (future work).

### Backend custom domain

Render → service → Settings → Custom Domains → add `api.bulkeditapp.com`. Render shows the DNS target
and issues a TLS cert once DNS resolves.

---

## 3. DNS (at your registrar)

Do **not** hardcode targets from this doc — copy the exact values Vercel and Render show.

| Record | Name | Target | Source |
|---|---|---|---|
| CNAME | `www` | *(Vercel target, e.g. `cname.vercel-dns.com`)* | Vercel Domains tab |
| ALIAS/A | `bulkeditapp.com` (apex) | *(Vercel apex target)* | Vercel Domains tab |
| CNAME | `api` | *(Render target)* | Render Custom Domains |

Apex → www redirect is handled by **Vercel** (add apex, set "Redirect to www"). If instead you front
DNS with Cloudflare, do the redirect there with a redirect rule and set records to "DNS only" for the
API host so Render's cert can issue.

After DNS resolves, confirm TLS is active for `www.bulkeditapp.com` and `api.bulkeditapp.com`.

---

## 4. Provider callbacks (register after domains are live)

Verified backend routes (do not change):

```
Etsy      : https://api.bulkeditapp.com/api/v1/etsy/callback
Pinterest : https://api.bulkeditapp.com/api/v1/promote/pinterest/callback
Instagram : https://api.bulkeditapp.com/api/v1/promote/instagram/callback
Stripe    : https://api.bulkeditapp.com/api/v1/billing/webhook
```

Register each in its provider dashboard. See `PROVIDER_SETUP.md` for per-provider steps.

---

## 5. CI/CD — why no deploy workflow (yet)

`.github/workflows/ci.yml` still runs tests, lint, and build on every push/PR — keep it.

For deployment we rely on **Vercel + Render native Git integration** (both auto-deploy on push to
`main`). This is the recommended path for the first production launch: fewer moving parts, no tokens
in CI, and each provider handles its own build/rollback.

A custom `deploy.yml` using `VERCEL_TOKEN` / `RENDER_API_KEY` (+ `RENDER_SERVICE_ID`,
`VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` as GitHub Secrets) can be added later if you need deploys gated
on CI success or coordinated multi-service releases. Deferred until the first deploy is stable.
