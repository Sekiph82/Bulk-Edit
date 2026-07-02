# Cloudflare DNS, Access, TLS & Email

`bulkeditapp.com` was purchased through Cloudflare, so Cloudflare is the source of
truth for DNS, redirects, staging access protection, and email-auth DNS.

**Do not enter DNS target values until DigitalOcean shows the real ingress
hostnames.** Placeholders below are marked `<DO ...>`.

## DNS records

| Name | Type | Value | Proxy | Notes |
|---|---|---|---|---|
| `staging` | CNAME | `<DO staging-web ingress>` | **Proxied** | Cloudflare Access requires proxied |
| `api-staging` | CNAME | `<DO staging-api ingress>` | **Proxied** | Enables WAF/rate rules; still public for XHR |
| `bulkeditapp.com` (apex) | CNAME/A | `<DO prod-web ingress>` | Proxied | Production (later) |
| `www` | CNAME | `<DO prod-web ingress>` | Proxied | 301→apex via middleware + CF rule |
| `app` | CNAME | `<DO prod-web ingress>` | Proxied | Production app (later) |
| `api` | CNAME | `<DO prod-api ingress>` | Proxied | Production API (later) |

Proxied vs DNS-only:
- **Proxied (orange):** all web/app/api hosts — gives TLS, WAF, Access, caching.
- **DNS-only (grey):** email/verification records (SPF/DKIM/DMARC, domain-verify
  TXT) and anything that must resolve to the true origin. Never proxy MX/TXT email
  records.

## TLS / SSL

- Cloudflare SSL/TLS mode: **Full (strict)**. DO App Platform serves a valid cert;
  Cloudflare validates the origin. Never use "Flexible" (causes redirect loops /
  insecure origin hop).
- Enable **Always Use HTTPS** and **Automatic HTTPS Rewrites**.
- HSTS is already emitted by the app in production (`next.config.mjs`); enabling CF
  HSTS too is fine once the domain is stable (hard to undo — see DNS_SSL.md).

## www -> apex redirect

Handled two ways (belt + suspenders):
1. App middleware `middleware.ts` 301s `www` → apex.
2. Optional Cloudflare **Redirect Rule**: `www.bulkeditapp.com/*` →
   `https://bulkeditapp.com/$1` (301). Either suffices; the app rule is canonical.

## Staging protection (Cloudflare Access)

Protect the **frontend** with Cloudflare Access (Zero Trust):
- Zero Trust → Access → Applications → Add **self-hosted** app for
  `staging.bulkeditapp.com`.
- Policy: Allow → emails/email-domain of your team (or one-time PIN).
- Session duration to taste.

`api-staging.bulkeditapp.com` is **left reachable** for browser API calls (decision:
option 2). It is protected instead by:
- **Strict CORS** — backend allows only `https://staging.bulkeditapp.com`
  (`BACKEND_CORS_ORIGINS` in `app.staging-backend.yaml`).
- **JWT auth** on all non-public endpoints (unauth → 401).
- **noindex** — `X-Robots-Tag` + `robots.txt Disallow: /` on the app; api responses
  are non-HTML and not indexed.
- **Staging-only DB + Redis**, **Stripe test keys**, no production secrets.
- **Optional Cloudflare WAF / rate-limit rules** on `api-staging` (see below) — nice
  to have, not a Phase 1 blocker.

Do NOT put Access directly in front of `api-staging` yet (it would block the
staging frontend's XHR unless using the shared-domain cookie approach, which we are
deferring). Revisit the shared-`.bulkeditapp.com`-cookie Access model after staging
is stable.

## Optional WAF / rate limiting (later, not Phase 1 blocker)

- Rate-limit rules on `api-staging` / `api`: e.g. cap `/api/v1/auth/login`,
  `/api/v1/ai/*`, `/api/v1/*/sync`, upload/CSV endpoints per IP.
- WAF managed ruleset on all proxied hosts.
- These complement app-level rate limiting (`RATE_LIMIT_BACKEND=redis`).

## Email (Resend) — SPF / DKIM / DMARC

Records are entered in Cloudflare DNS (DNS-only). Exact values come from the Resend
dashboard after adding the domain. Template:

| Name | Type | Value (from Resend) | Proxy |
|---|---|---|---|
| `bulkeditapp.com` | TXT (SPF) | `v=spf1 include:_spf.resend.com ~all` | DNS-only |
| `resend._domainkey` (or as Resend specifies) | TXT/CNAME (DKIM) | `<from Resend>` | DNS-only |
| `_dmarc` | TXT (DMARC) | `v=DMARC1; p=quarantine; rua=mailto:security@bulkeditapp.com; fo=1` | DNS-only |
| MX (if receiving) | MX | provider MX | DNS-only |

- Start DMARC at `p=none` (monitor), move to `p=quarantine` then `p=reject`.
- Transactional from `noreply@bulkeditapp.com`; role inboxes `support@`, `hello@`,
  `security@` (+ later `billing@`, `notifications@`).
- Full email flows + provider setup: Phase 3 (see EMAIL doc, added then).

## Verification

- [ ] `dig staging.bulkeditapp.com` resolves to CF; Access challenge appears.
- [ ] `curl -I https://api-staging.bulkeditapp.com/api/v1/health` → 200.
- [ ] CORS: browser XHR from staging frontend to api-staging succeeds; a request
      from any other origin is rejected.
- [ ] `curl https://staging.bulkeditapp.com/robots.txt` → `Disallow: /`.
- [ ] Response headers on staging include `X-Robots-Tag: noindex`.
