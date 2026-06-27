# DNS and SSL Guide

## Recommended Domain Structure

| Subdomain | Purpose |
|---|---|
| `bulk-edit.com` | Marketing + app (homepage, features, pricing, FAQ, contact, dashboard) |
| `api.bulk-edit.com` | Backend API |
| `staging.bulk-edit.com` | Staging frontend |
| `api-staging.bulk-edit.com` | Staging backend |

An `app.bulk-edit.com` subdomain is optional if you want to split marketing from the authenticated app. Currently the Next.js App Router handles both in the same codebase.

## DNS Records

### Production Frontend (Vercel / Netlify / Railway)

```
Type   Name                 Value
A      bulk-edit.com        <hosting provider IP>
CNAME  www                  bulk-edit.com
```

Or use your hosting platform's nameservers (Vercel/Netlify provide full NS delegation).

### Production Backend

```
CNAME  api.bulk-edit.com    <backend hosting target>
```

### Staging

```
CNAME  staging.bulk-edit.com      <staging frontend target>
CNAME  api-staging.bulk-edit.com  <staging backend target>
```

## SSL / TLS

Use your hosting platform's automatic TLS — no manual certificate management required:

| Platform | TLS |
|---|---|
| Vercel | Automatic Let's Encrypt, wildcard certs |
| Netlify | Automatic Let's Encrypt |
| Railway | Automatic TLS on custom domains |
| Render | Automatic Let's Encrypt |
| Fly.io | Automatic Let's Encrypt |
| Self-hosted | Use Caddy (automatic) or certbot + nginx |

### HSTS

HSTS is enabled in `apps/frontend/next.config.mjs` for `NODE_ENV=production`:

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

**Do not enable HSTS on staging** unless you fully control that domain long-term — HSTS preloading is difficult to undo and can lock browsers into HTTPS for years.

## CORS Configuration

### Production

```
BACKEND_CORS_ORIGINS=https://bulk-edit.com
```

### Staging

```
BACKEND_CORS_ORIGINS=https://staging.bulk-edit.com
```

**Never use `*` (wildcard) CORS in production or staging.** The `validate_env.py` script catches this.

## OAuth and Webhook Callback URLs

### Etsy OAuth Redirect URI

Register in [Etsy Developer Portal](https://www.etsy.com/developers) under your app settings.

```
Production: https://bulk-edit.com/etsy/callback
Staging:    https://staging.bulk-edit.com/etsy/callback
```

The URL must match **exactly** — no trailing slash, correct scheme (https).

Set `ETSY_REDIRECT_URI` accordingly:

```
ETSY_REDIRECT_URI=https://bulk-edit.com/etsy/callback
```

### Stripe Webhook Endpoint

Register in [Stripe Dashboard](https://dashboard.stripe.com/) → Developers → Webhooks → Add endpoint.

```
Production: https://api.bulk-edit.com/api/v1/billing/webhook
Staging:    https://api-staging.bulk-edit.com/api/v1/billing/webhook
```

Copy the webhook signing secret → `STRIPE_WEBHOOK_SECRET=whsec_...`

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Wrong Etsy redirect URI | OAuth callback fails with "redirect_uri_mismatch" | Update Etsy Developer Portal — must match exactly, including scheme |
| CORS mismatch (http vs https) | API calls fail in browser with CORS error | Ensure `BACKEND_CORS_ORIGINS` uses exact scheme of the frontend URL |
| Missing www redirect | www.bulk-edit.com shows DNS error | Add CNAME www → apex or configure redirect in hosting settings |
| Mixed http/https | Browser blocks mixed content | Ensure `NEXT_PUBLIC_BACKEND_URL` starts with `https://` in production |
| HSTS on staging | Staging locked into HTTPS permanently | Only add HSTS where `NODE_ENV=production` — check `next.config.mjs` |
| Multiple Stripe webhooks | Duplicate event processing | Audit and remove stale endpoints in Stripe Dashboard |
| Stripe webhook test key in production | Webhook signature verification fails | Use live webhook signing secret (`whsec_...` from live mode endpoint) |

## Verification Checklist

After configuring DNS and SSL:

- [ ] `curl -I https://bulk-edit.com/` returns `HTTP/2 200`
- [ ] `curl -I https://api.bulk-edit.com/api/v1/health` returns `HTTP/2 200`
- [ ] `curl -I https://bulk-edit.com/` response includes `Strict-Transport-Security` header
- [ ] `curl -I https://bulk-edit.com/` response includes `Content-Security-Policy` header
- [ ] `http://bulk-edit.com` redirects to `https://bulk-edit.com` (301/302)
- [ ] Etsy OAuth flow completes with correct redirect URI
- [ ] Stripe test webhook delivery succeeds (Stripe Dashboard → Webhooks → Send test event)
