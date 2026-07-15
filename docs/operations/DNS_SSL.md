# DNS and SSL Guide

Production domain: **bulkeditapp.com** (purchased). This guide configures DNS, SSL, CORS, and
OAuth/webhook callbacks for the production domain model.

> **Current hosting: DigitalOcean App Platform (frontend + backend) + Cloudflare (DNS/TLS).** For the
> step-by-step provider setup (app specs, env vars, custom domains), see
> [`DIGITALOCEAN_DEPLOY.md`](DIGITALOCEAN_DEPLOY.md) and [`CLOUDFLARE_DNS.md`](CLOUDFLARE_DNS.md) — the
> latter is authoritative for actual DNS records. This file covers the DNS/SSL/CORS layer conceptually;
> the older Vercel + Render specifics below (`VERCEL_RENDER_DEPLOY.md`) were superseded before production
> ever used them and are kept only as historical reference.

## Domain Model

| Host | Purpose | Behavior |
|---|---|---|
| `www.bulkeditapp.com` | Frontend (marketing + authenticated app) | Canonical frontend origin |
| `bulkeditapp.com` (apex/root) | Root domain | **Redirect** to `https://www.bulkeditapp.com` |
| `api.bulkeditapp.com` | Backend API | FastAPI backend |
| `staging.bulkeditapp.com` | Staging frontend (optional) | — |
| `api-staging.bulkeditapp.com` | Staging backend (optional) | — |

The Next.js App Router serves both marketing and the authenticated app from the same codebase on
`www.bulkeditapp.com`. The apex `bulkeditapp.com` should 301-redirect to `www` at the hosting
provider level.

## DNS Records

Exact target values depend on the hosting provider (Vercel / Netlify / Render / Fly / Railway /
DigitalOcean / AWS). Do not copy literal IPs from this doc — read them from your provider's
custom-domain settings.

### Frontend — www + apex

```
Type    Name                    Value
CNAME   www                     <frontend hosting target>   # e.g. cname.vercel-dns.com
ALIAS   bulkeditapp.com (apex)  <frontend hosting target>   # ALIAS/ANAME if provider supports it
# or, if apex only supports A records:
A       bulkeditapp.com         <frontend hosting IP>
```

Configure the **apex → www redirect** in the hosting provider dashboard (Vercel: add both domains,
set `bulkeditapp.com` to "Redirect to www.bulkeditapp.com"; Netlify/Cloudflare: a redirect rule).

### Backend — api

```
Type    Name                    Value
CNAME   api.bulkeditapp.com     <backend hosting target>
# or, if the backend host gives an IP:
A       api.bulkeditapp.com     <backend hosting IP>
```

### Staging (optional)

```
CNAME   staging.bulkeditapp.com      <staging frontend target>
CNAME   api-staging.bulkeditapp.com  <staging backend target>
```

## SSL / TLS

Use the hosting platform's automatic TLS — no manual certificate management required. HTTPS only.

| Platform | TLS |
|---|---|
| Vercel | Automatic Let's Encrypt, wildcard certs |
| Netlify | Automatic Let's Encrypt |
| Railway | Automatic TLS on custom domains |
| Render | Automatic Let's Encrypt |
| Fly.io | Automatic Let's Encrypt |
| Self-hosted | Caddy (automatic) or certbot + nginx |

Certificates must be active for **both** `www.bulkeditapp.com` and `api.bulkeditapp.com` (and the
apex `bulkeditapp.com` so the redirect itself is served over HTTPS).

### HSTS

HSTS is enabled in `apps/frontend/next.config.mjs` for `NODE_ENV=production`:

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

**Do not enable HSTS on staging** unless you fully control that domain long-term — HSTS preloading
is difficult to undo and can lock browsers into HTTPS for years.

## CORS Configuration

The backend parses `BACKEND_CORS_ORIGINS` via `Settings.get_cors_origins()` — a comma-separated
list (or JSON array) of exact origins. Include both the `www` host and the apex (the apex is served
before the redirect resolves).

### Production

```
BACKEND_CORS_ORIGINS=https://www.bulkeditapp.com,https://bulkeditapp.com
```

### Staging

```
BACKEND_CORS_ORIGINS=https://staging.bulkeditapp.com
```

**Never use `*` (wildcard) CORS in production or staging.** `validate_env.py` fails on wildcard.

## OAuth and Webhook Callback URLs

All callback routes below are the **backend** routes (verified in code) and resolve on
`api.bulkeditapp.com`, not the `www` frontend.

### Etsy OAuth Redirect URI

Route: `app/api/v1/etsy.py` → `/api/v1/etsy/callback`. Register in the
[Etsy Developer Portal](https://www.etsy.com/developers) under your app settings.

```
Production: https://api.bulkeditapp.com/api/v1/etsy/callback
Staging:    https://api-staging.bulkeditapp.com/api/v1/etsy/callback
```

The URL must match **exactly** — no trailing slash, correct scheme (https).

```
ETSY_REDIRECT_URI=https://api.bulkeditapp.com/api/v1/etsy/callback
```

### Pinterest OAuth Redirect URI

Route: `/api/v1/promote/pinterest/callback`.

```
Production: https://api.bulkeditapp.com/api/v1/promote/pinterest/callback
PINTEREST_REDIRECT_URI=https://api.bulkeditapp.com/api/v1/promote/pinterest/callback
```

### Instagram / Meta OAuth Redirect URI

Route: `/api/v1/promote/instagram/callback`.

```
Production: https://api.bulkeditapp.com/api/v1/promote/instagram/callback
INSTAGRAM_REDIRECT_URI=https://api.bulkeditapp.com/api/v1/promote/instagram/callback
```

### Stripe Webhook Endpoint

Route: `app/api/v1/billing.py` → `/api/v1/billing/webhook`. Register in the
[Stripe Dashboard](https://dashboard.stripe.com/) → Developers → Webhooks → Add endpoint.

```
Production: https://api.bulkeditapp.com/api/v1/billing/webhook
Staging:    https://api-staging.bulkeditapp.com/api/v1/billing/webhook
```

Copy the webhook signing secret → `STRIPE_WEBHOOK_SECRET=whsec_...`. Stripe checkout success/cancel
and billing-portal return URLs are derived from `FRONTEND_URL`
(`https://www.bulkeditapp.com/billing?success=true`, `.../pricing?canceled=true`, `.../billing`).

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Wrong Etsy redirect URI | OAuth fails with "redirect_uri_mismatch" | Must be `https://api.bulkeditapp.com/api/v1/etsy/callback`, exact match incl. scheme |
| CORS mismatch (http vs https) | API calls fail in browser with CORS error | `BACKEND_CORS_ORIGINS` must use exact scheme of the frontend URL |
| Missing apex redirect | `bulkeditapp.com` doesn't reach the app | Configure apex → `www` 301 redirect at the hosting provider |
| Mixed http/https | Browser blocks mixed content | `NEXT_PUBLIC_BACKEND_URL` must start with `https://` in production |
| HSTS on staging | Staging locked into HTTPS permanently | Only add HSTS where `NODE_ENV=production` — check `next.config.mjs` |
| Multiple Stripe webhooks | Duplicate event processing | Audit and remove stale endpoints in Stripe Dashboard |
| Stripe webhook test key in production | Webhook signature verification fails | Use live webhook signing secret (`whsec_...` from live-mode endpoint) |

## Verification Checklist

After configuring DNS and SSL:

- [ ] `curl -I https://www.bulkeditapp.com/` returns `HTTP/2 200`
- [ ] `curl -I https://api.bulkeditapp.com/api/v1/health` returns `HTTP/2 200`
- [ ] `curl -I https://www.bulkeditapp.com/` response includes `Strict-Transport-Security`
- [ ] `curl -I https://www.bulkeditapp.com/` response includes `Content-Security-Policy`
- [ ] `curl -I https://bulkeditapp.com/` redirects (301/302) to `https://www.bulkeditapp.com`
- [ ] `curl -I http://bulkeditapp.com/` redirects to `https://www.bulkeditapp.com`
- [ ] Etsy OAuth flow completes with the production redirect URI
- [ ] Stripe test webhook delivery succeeds (Stripe Dashboard → Webhooks → Send test event)
