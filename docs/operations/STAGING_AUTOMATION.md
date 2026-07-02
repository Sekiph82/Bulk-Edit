# Staging Provisioning Automation

Token-driven automation for the DigitalOcean + Cloudflare **staging** environment.
You fill one gitignored env file; the scripts do the rest. Production is never touched.

Companion: `STAGING_PROVISIONING.md` (manual walkthrough), `.do/app.staging-*.yaml`,
`CLOUDFLARE_DNS.md`, `DIGITALOCEAN_DEPLOY.md`.

## Files

| File | Purpose |
|---|---|
| `deploy-staging.local.env.example` | committed template (placeholders only) |
| `deploy-staging.local.env` | your filled copy — **gitignored, never committed** |
| `scripts/prepare-staging-secrets.ps1` | create the local env file + open it |
| `scripts/provision-staging.ps1` | validate + generate secrets + create DO/CF staging resources |
| `scripts/smoke-staging.ps1` | post-deploy health/CORS/robots/noindex checks |

## 1. Fill `deploy-staging.local.env`

Run:
```
powershell -ExecutionPolicy Bypass -File scripts/prepare-staging-secrets.ps1
```
It copies the template and opens it in Notepad. Fill:

**Required**
- `DIGITALOCEAN_ACCESS_TOKEN` — DO → API → Tokens → Generate. Scopes: **read + write**
  (App Platform + Databases). Staging only.
- `CLOUDFLARE_API_TOKEN` — CF → My Profile → API Tokens → Create Token. Permissions:
  **Zone:DNS:Edit** + **Zone:Read** for `bulkeditapp.com`. For Access also:
  **Account: Access: Apps and Policies: Edit** (+ read).
- `CLOUDFLARE_ZONE_ID` — CF → `bulkeditapp.com` → Overview (right sidebar).
- `CLOUDFLARE_ACCOUNT_ID` — CF → Overview / Zero Trust.

**Auto-generated if blank** (never printed, written into the local file):
- `JWT_SECRET`, `ENCRYPTION_KEY` (fresh private Fernet — never the public CI key).

**Optional (staging/test only)**
- `STRIPE_SECRET_KEY` (**must** be `sk_test_`; `sk_live_` is refused), `STRIPE_WEBHOOK_SECRET`
- `ETSY_CLIENT_ID` / `ETSY_CLIENT_SECRET` (dev app or blank)
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` (low-limit; blank ⇒ `AI_PROVIDER=mock`)
- `SENTRY_DSN`

Do **not** paste any token into chat. Never commit this file.

## 2. Provision

Install `doctl` first (not in winget):
```
scoop install doctl        # or: choco install doctl
# or download: https://github.com/digitalocean/doctl/releases  (add to PATH)
```
Then:
```
powershell -ExecutionPolicy Bypass -File scripts/provision-staging.ps1
```

What it does (staging only, in order):
1. Validate required values; **refuse** `sk_live_`, the public CI Fernet key, any
   production host, or hand-set `DATABASE_URL`/`REDIS_URL`.
2. Generate `JWT_SECRET` + `ENCRYPTION_KEY` if missing (stored locally, never printed).
3. Verify `doctl` + authenticate via `DIGITALOCEAN_ACCESS_TOKEN` (token never printed).
4. Create the staging **backend** + **frontend** apps from the committed specs
   (idempotent — skips if they already exist). This creates **paid** apps + the
   spec's dev DB + Redis. Confirm the price DO shows.
5. Print the backend secret env vars to set (encrypted, in the DO dashboard) — the
   generated values live in the gitignored local file; copy them in, never to chat.
6. Read the DO ingress hostnames.
7. Create/update **Cloudflare** `api-staging` + `staging` CNAMEs (proxied). Non-staging
   record names are refused (prod DNS protection).
8. Print the DO custom-domain + Cloudflare Access + SSL steps that remain manual.

Secrets: never printed, never committed. Logs show resource names/status only.

## 3. Smoke test (after deploys are live)

```
powershell -ExecutionPolicy Bypass -File scripts/smoke-staging.ps1
```
Checks: `/api/v1/health` + `/ready` + `/db` + `/redis`, CORS allow(staging)/reject(random),
`robots.txt` `Disallow: /`, `X-Robots-Tag: noindex`, frontend not referencing prod API,
no `sk_live_` locally.

## Stop conditions (script refuses / you must halt)

- `sk_live_` Stripe key, or `STRIPE_SECRET_KEY` not `sk_test_`.
- `ENCRYPTION_KEY` == public CI dummy (`uOv7…Tio=`).
- Any production host / DB / Redis in the env.
- `DATABASE_URL` / `REDIS_URL` hand-set (must auto-wire).
- `doctl` missing or auth failed.
- Pre-deploy migration fails (check DO deploy logs).
- Cloudflare Access would block the frontend, or DNS/SSL 525/526/redirect loop.
- Any production resource about to be created/modified → STOP.

## Expected resources & cost (staging, approx/mo)

| Resource | ~Cost |
|---|---|
| `bulk-edit-staging-api` (App Platform basic-xxs) | ~$5 |
| `bulk-edit-staging-web` (basic-xxs) | ~$5 |
| `staging-db` (spec dev DB) | $0–15 (verify tier) |
| `staging-redis` (spec dev) | $0–15 (verify tier) |
| Cloudflare Access | $0 (Zero Trust free ≤50 users) |

Confirm exact figures in the DO dashboard before creating.

## Rollback / cleanup

- Remove staging apps: DO dashboard → app → Destroy, or `doctl apps delete <id>`.
- Remove DB/Redis with the app (or separately if standalone).
- Remove Cloudflare records: CF dashboard → DNS, delete `staging` / `api-staging` CNAMEs.
- Local secrets: delete `deploy-staging.local.env` (gitignored).
- Cleanup affects **staging only** — never production.

## Never production

These scripts operate on `*-staging` names/hosts only, refuse production hosts, and
never read/write production DNS, DB, Redis, or live keys. Production stays design-only
(`.do/app.production-*.yaml`).
