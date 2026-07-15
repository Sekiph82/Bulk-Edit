# Production Smoke Test

**Superseded (2026-07-15)** — written for the original Vercel + Render plan, which was never
provisioned in production. Current hosting is DigitalOcean App Platform + Cloudflare; use
`scripts/smoke_test_deployment.ps1` / `.sh` (health, readiness, routes) plus the checks in
`docs/operations/RUNBOOK.md` and `MONITORING.md` for the live equivalent. Kept below as historical
reference for the general shape of a post-deploy smoke pass — domain/host-specific steps no longer apply.

Run after every production deploy (Vercel frontend + Render backend). Fast pass/fail on the live
`bulkeditapp.com` domain. Stop and roll back if a ❌ item fails.

## 1. Domains & TLS

- [ ] `https://www.bulkeditapp.com` loads, valid SSL (padlock, no cert warning)
- [ ] `https://bulkeditapp.com` redirects (301/302) to `https://www.bulkeditapp.com`
- [ ] `https://api.bulkeditapp.com` has valid SSL

## 2. Backend health

- [ ] `curl -I https://api.bulkeditapp.com/api/v1/health` → `200`
- [ ] `curl -s https://api.bulkeditapp.com/api/v1/health/ready` → ready/ok
- [ ] `curl -s https://api.bulkeditapp.com/api/v1/health/db` → db ok
- [ ] `curl -s https://api.bulkeditapp.com/api/v1/health/redis` → redis ok

## 3. Frontend app

- [ ] Register a new test account (or log in)
- [ ] Dashboard loads after auth
- [ ] `/promote` loads
- [ ] `/video-generator` loads
- [ ] `/pricing`, `/billing` load

## 4. Frontend ↔ backend wiring

- [ ] Browser DevTools → Network: API calls go to `https://api.bulkeditapp.com` (not localhost)
- [ ] No CORS errors in the console
- [ ] No mixed-content warnings (everything https)

## 5. Payments & OAuth (as applicable to launch mode)

- [ ] Stripe checkout opens (test or live mode as configured)
- [ ] Stripe webhook delivers: Stripe Dashboard → Webhooks → recent events → `200`
- [ ] Etsy OAuth completes against `https://api.bulkeditapp.com/api/v1/etsy/callback`
- [ ] (If enabled) Pinterest / Instagram connect flows reach their callbacks

## 6. Security / hygiene

- [ ] No `localhost` URLs anywhere in the Network tab
- [ ] No secrets in API responses (no `password_hash`, tokens, `*_secret`, `*_api_key`)
- [ ] `/docs` and `/redoc` are disabled (404) — `DEBUG=false` in production
- [ ] Security headers present: `curl -I https://www.bulkeditapp.com/` shows
      `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options`
- [ ] (If configured) Sentry receives a test error; secrets are scrubbed

## 7. Post-check

- [ ] Render logs show a successful `alembic upgrade head` on deploy
- [ ] No error spikes in Render logs / Sentry for the first 30 min
