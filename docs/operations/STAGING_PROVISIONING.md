# Staging Provisioning — DigitalOcean + Cloudflare

Step-by-step to stand up STAGING only. Production stays design-only.
Companion files: `.do/app.staging-frontend.yaml`, `.do/app.staging-backend.yaml`,
`DIGITALOCEAN_DEPLOY.md`, `CLOUDFLARE_DNS.md`, `ENVIRONMENT.md`.

Hard rules: separate staging DB + Redis, Stripe TEST mode, no production secrets,
never point at prod resources.

---

## 1. DigitalOcean prerequisites

- DO account + a Project (e.g. "bulk-edit-staging") to group resources.
- `doctl` authenticated (`doctl auth init`) OR use the dashboard.
- Region: **NYC** (matches specs; pick one region and keep DB/Redis/apps together
  for low latency + private networking).
- GitHub connected to DO App Platform, authorized for `Sekiph82/Bulk-Edit`.

**App creation order** (backend first — frontend depends on the API URL):
1. Backend app (`bulk-edit-staging-api`) + managed PG + managed Redis + migrate job.
2. Frontend app (`bulk-edit-staging-web`).

Two apps (DO ingress routes by path, not host, so subdomains = separate apps).

### Values: dummy/test vs real secret

| Kind | Keys | Value |
|---|---|---|
| Safe/non-secret (in spec) | ENVIRONMENT, DEBUG, LOG_LEVEL, FRONTEND_URL, BACKEND_URL, BACKEND_CORS_ORIGINS, RATE_LIMIT_*, AI_PROVIDER=mock, VIDEO_RENDERER_ENABLED=false, *_REDIRECT_URI | committed in `.do/*.yaml` |
| Auto-wired | DATABASE_URL, REDIS_URL | `${staging-db.DATABASE_URL}`, `${staging-redis.DATABASE_URL}` |
| Real staging secret (DO dashboard) | JWT_SECRET, ENCRYPTION_KEY | generate staging-only values |
| Test-mode secret (optional) | STRIPE_SECRET_KEY (`sk_test_`), STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_* | Stripe test dashboard |
| Optional (blank = feature off) | ETSY_*, PINTEREST_*, META_*, OPENAI/ANTHROPIC key, SMTP_*, SENTRY_DSN | dev/low-limit or leave unset |

**Critical:** `ENCRYPTION_KEY` for staging MUST be a **freshly generated, private**
Fernet key — do NOT reuse the CI test key (`uOv7…`), which is public in the repo.
Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
`JWT_SECRET`: `python -c "import secrets; print(secrets.token_urlsafe(64))"`.

---

## 2. Cloudflare prerequisites

Enter DNS values only AFTER DO shows the real ingress hostnames.

| Record | Name | Type | Value | Proxy |
|---|---|---|---|---|
| Frontend | `staging` | CNAME | `<DO staging-web ingress>` | **Proxied** (Access needs it) |
| Backend | `api-staging` | CNAME | `<DO staging-api ingress>` | **Proxied** (WAF option) |
| DO domain-verify TXT (if DO asks) | as DO specifies | TXT | `<from DO>` | **DNS-only** |

- **SSL/TLS mode: Full (strict).** DO serves a valid cert; never "Flexible".
- **Cloudflare Access** on `staging.bulkeditapp.com` only (Zero Trust → Access →
  self-hosted app → policy = team emails / one-time PIN).
- **`api-staging.bulkeditapp.com` stays public** (decision: option 2) but restricted by:
  strict CORS (`https://staging.bulkeditapp.com` only), JWT auth, noindex, optional
  Cloudflare WAF/rate-limit rules, staging-only DB/Redis, Stripe test only.
  Do NOT put Access in front of api-staging (would block frontend XHR).

---

## 3. Staging env matrix

### Frontend (`bulk-edit-staging-web`)
```
NEXT_PUBLIC_APP_ENV=staging
NEXT_PUBLIC_BACKEND_URL=https://api-staging.bulkeditapp.com
NEXT_PUBLIC_APP_URL=https://staging.bulkeditapp.com
NODE_ENV=production
```

### Backend (`bulk-edit-staging-api`) — non-secret (spec)
```
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
FRONTEND_URL=https://staging.bulkeditapp.com
BACKEND_URL=https://api-staging.bulkeditapp.com
BACKEND_CORS_ORIGINS=https://staging.bulkeditapp.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_BACKEND=redis
AI_PROVIDER=mock
VIDEO_RENDERER_ENABLED=false
ETSY_REDIRECT_URI=https://api-staging.bulkeditapp.com/api/v1/etsy/callback
PINTEREST_REDIRECT_URI=https://api-staging.bulkeditapp.com/api/v1/promote/pinterest/callback
INSTAGRAM_REDIRECT_URI=https://api-staging.bulkeditapp.com/api/v1/promote/instagram/callback
```

### Database + Redis (auto-wired)
```
DATABASE_URL=${staging-db.DATABASE_URL}     # postgresql:// -> app normalizes to +asyncpg
REDIS_URL=${staging-redis.DATABASE_URL}
```

### Secrets (DO dashboard, encrypted) — staging/test values only
```
JWT_SECRET=<staging random 64+>
ENCRYPTION_KEY=<fresh staging Fernet, NOT the public CI key>
# Stripe TEST mode (only if testing billing on staging):
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...            # from a staging webhook endpoint
STRIPE_PRICE_BASIC_MONTHLY=price_...       # test-mode ids
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_BASIC_YEARLY=price_...
STRIPE_PRICE_PRO_YEARLY=price_...
# Optional (blank => feature unavailable):
ETSY_CLIENT_ID= / ETSY_CLIENT_SECRET=      # dev app if available
OPENAI_API_KEY= / ANTHROPIC_API_KEY=       # only if AI_PROVIDER != mock (low-limit)
SENTRY_DSN=                                # optional staging Sentry project
SMTP_*=                                    # optional (email is Phase 3)
```

---

## 4. Deployment sequence

1. Create backend app from `.do/app.staging-backend.yaml`
   (`doctl apps create --spec .do/app.staging-backend.yaml`).
2. DO provisions `staging-db` (PG16) + `staging-redis` from the spec's `databases`.
3. Set backend SECRET env vars in the dashboard (section 3).
4. Deploy. Confirm the **PRE_DEPLOY `migrate` job** runs `alembic upgrade head` clean.
5. Verify backend health: `/api/v1/health`, `/api/v1/health/ready`, `/db`, `/redis`.
6. Add custom domain `api-staging.bulkeditapp.com`; copy the DO ingress target.
7. Create frontend app from `.do/app.staging-frontend.yaml`; set the 4 frontend envs.
8. Add custom domain `staging.bulkeditapp.com`; copy its DO ingress target.
9. Cloudflare DNS: add both CNAMEs (proxied) to the DO targets; SSL Full (strict).
10. Cloudflare Access: protect `staging.bulkeditapp.com`.
11. Verify frontend loads (through Access), API calls succeed (CORS), robots/noindex,
    staging banner, and that no production credential is present.

---

## 5. Validation checklist

```bash
# Backend health + readiness
curl -sI https://api-staging.bulkeditapp.com/api/v1/health       # 200
curl -s  https://api-staging.bulkeditapp.com/api/v1/health/ready  # ready ok
curl -s  https://api-staging.bulkeditapp.com/api/v1/health/db     # db ok
curl -s  https://api-staging.bulkeditapp.com/api/v1/health/redis  # redis ok

# CORS: allowed origin passes, other origin rejected
curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: https://staging.bulkeditapp.com" \
  -H "Access-Control-Request-Method: GET" \
  https://api-staging.bulkeditapp.com/api/v1/health

# robots + noindex (through Access session)
curl -s https://staging.bulkeditapp.com/robots.txt                # Disallow: /
curl -sI https://staging.bulkeditapp.com/ | grep -i x-robots-tag  # noindex, nofollow
```

- [ ] Frontend build/deploy succeeded on DO.
- [ ] Staging banner "STAGING ENVIRONMENT - NOT PRODUCTION" visible.
- [ ] Migration job succeeded (DO deploy logs show `alembic upgrade head`).
- [ ] **DB isolation**: `staging-db` host != any prod DB host; DB is empty/staging data only.
- [ ] **Redis isolation**: `staging-redis` != prod; separate instance.
- [ ] Stripe key starts with `sk_test_` (never `sk_live_`).
- [ ] No production DATABASE_URL / REDIS_URL / live keys anywhere in staging env.

---

## 6. STOP conditions (halt, do not continue)

- Pre-deploy **migration fails** (do not force it; fix migration, retry on staging).
- Backend **cannot connect to staging DB** (wrong URL / not provisioned / network).
- Frontend **points to production API** (any prod URL in NEXT_PUBLIC_BACKEND_URL).
- Staging uses **production Stripe live keys** (`sk_live_`).
- Staging uses **production DB or Redis** (host matches prod).
- **Cloudflare Access blocks required frontend usage** (misconfigured policy).
- **DNS/SSL error** (526/525/redirect loop → likely not Full-strict or cert not issued).
- Any secret is about to be **committed** or printed.
- `ENCRYPTION_KEY` is the **public CI key** or missing/invalid Fernet.

On any STOP: do not proceed to production, do not merge, report the exact failure.

---

## Production gate (reminder)

Provision production ONLY after: staging deploys, migrate job runs clean, DB/Redis
isolation verified, Access + noindex + banner confirmed, health/ready 200, no prod
secrets used. Production specs stay design-only until then.
