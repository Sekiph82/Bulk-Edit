# Launch Checklist

Production deployment checklist for Bulk-Edit SaaS platform. Complete all items before flipping DNS.

---

## 1. Infrastructure

- [ ] Production PostgreSQL 16+ provisioned and accessible
- [ ] Production Redis 7+ provisioned (required for rate limiting + Celery)
- [ ] S3-compatible object storage configured (AWS S3 or MinIO)
- [ ] Hosting platform chosen (Railway, Render, Fly.io, AWS ECS, etc.)
- [ ] Domain registered and pointed to hosting
- [ ] DNS propagated
- [ ] SSL certificate active (Let's Encrypt or platform-managed)

---

## 2. Environment Variables

All required variables must be set. See `docs/operations/ENVIRONMENT.md` for full reference.

- [ ] `DATABASE_URL` points to production PostgreSQL
- [ ] `REDIS_URL` points to production Redis
- [ ] `JWT_SECRET` — fresh 64-char random hex (not the dev default)
- [ ] `ENCRYPTION_KEY` — fresh Fernet key (not the dev default)
- [ ] `STRIPE_SECRET_KEY` — live key (starts `sk_live_`)
- [ ] `STRIPE_WEBHOOK_SECRET` — from Stripe dashboard (`whsec_...`)
- [ ] `ETSY_CLIENT_ID` — from Etsy developer portal
- [ ] `ETSY_CLIENT_SECRET` — from Etsy developer portal
- [ ] `ETSY_REDIRECT_URI` — production callback URL registered in Etsy app
- [ ] `NEXT_PUBLIC_BACKEND_URL` — production backend URL
- [ ] `NEXT_PUBLIC_APP_URL` — production frontend URL
- [ ] `BACKEND_CORS_ORIGINS` — production frontend URL only (not localhost)
- [ ] `AI_PROVIDER` — `openai` or `anthropic` (not `mock`)
- [ ] `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` — real key
- [ ] `RATE_LIMIT_ENABLED=true`
- [ ] `RATE_LIMIT_BACKEND=redis`
- [ ] `DEBUG=false`
- [ ] No `.env` files committed to git
- [ ] `apps/backend/.local-superusers.env` confirmed gitignored

---

## 3. Stripe

- [ ] Live Stripe secret key configured (`sk_live_...`)
- [ ] Live Stripe publishable key in frontend env
- [ ] Webhook endpoint registered in Stripe dashboard: `https://yourdomain.com/api/v1/billing/webhook`
- [ ] `STRIPE_WEBHOOK_SECRET` set from Stripe dashboard (`whsec_...`)
- [ ] Live products created in Stripe dashboard
- [ ] Live prices created: basic_monthly, pro_monthly, basic_yearly, pro_yearly
- [ ] `STRIPE_PRICE_ID_*` env vars set to live price IDs
- [ ] Test payment completed with Stripe test card on staging
- [ ] Failed payment scenario verified (card declined)
- [ ] Subscription upgrade/downgrade flow tested

---

## 4. Etsy OAuth

- [ ] Production Etsy app created in Etsy Developer Portal
- [ ] `ETSY_CLIENT_ID` set
- [ ] `ETSY_CLIENT_SECRET` set
- [ ] `ETSY_REDIRECT_URI` set to production callback URL
- [ ] OAuth redirect URI registered in Etsy app settings (exact match)
- [ ] Test OAuth flow with a real Etsy shop
- [ ] Listing sync tested (read-only first)
- [ ] Safe write flow tested end-to-end: preview → user confirms → backup created → write to Etsy → audit log written

---

## 5. AI Provider

- [ ] `AI_PROVIDER` set to `openai` or `anthropic`
- [ ] API key configured and valid
- [ ] Usage cost monitoring set up (OpenAI dashboard or Anthropic console alerts)
- [ ] Test AI session completes successfully
- [ ] AI output confirmed preview-only — never auto-applied to Etsy without user approval

---

## 6. Admin Panel

- [ ] At least one superuser account created in production DB (via `local_seed.py` run or direct DB insert)
- [ ] Superuser can log in and see Admin nav link
- [ ] Normal user cannot see Admin nav link
- [ ] `/admin` returns "Access Denied" for normal users
- [ ] Admin dashboard loads all 6 tabs for superuser (Overview, Users, Billing, Etsy, Usage, System)
- [ ] No secrets visible in any admin API response

---

## 7. Security

- [ ] CSP headers active on frontend (`Content-Security-Policy` in response headers)
- [ ] `X-Content-Type-Options: nosniff` on all responses (frontend + backend)
- [ ] `X-Frame-Options: DENY` on all responses (frontend + backend)
- [ ] `Referrer-Policy: strict-origin-when-cross-origin` active
- [ ] Rate limiting enabled (`RATE_LIMIT_ENABLED=true`)
- [ ] Rate limiting backed by Redis (`RATE_LIMIT_BACKEND=redis`)
- [ ] Login endpoint: 10 attempts/min per IP
- [ ] Register endpoint: 5 attempts/min per IP
- [ ] Health endpoint public and unauthenticated (load balancer health check)
- [ ] No stack traces in error responses (`DEBUG=false`)
- [ ] No `password_hash`, `etsy_access_token`, `etsy_refresh_token` in any API response
- [ ] Scheduled external penetration test or OWASP ZAP scan planned

**CSP Hardening (deferred to Sprint 21):**
The current CSP includes `'unsafe-inline'` for scripts to support the anti-flash theme
script injected by `app/layout.tsx`. Production hardening requires nonce-based CSP:
Next.js middleware injects a per-request nonce into both the inline script and the
`Content-Security-Policy` header, then `'unsafe-inline'` can be removed.
See: https://nextjs.org/docs/app/building-your-application/configuring/content-security-policy

---

## 8. E2E / QA

- [ ] Playwright smoke tests pass: `cd apps/frontend && npm run e2e:install && npm run e2e`
- [ ] Manual QA pass on production URL:
  - [ ] Home page loads, title correct
  - [ ] /features, /faq, /contact-us, /pricing all load
  - [ ] Register new account (use a test email)
  - [ ] Login with that account
  - [ ] Dashboard loads
  - [ ] Connect an Etsy shop (if shop available for testing)
  - [ ] Create a bulk edit session with ≥1 listing
  - [ ] Preview changes (verify they look correct)
  - [ ] Do NOT apply to Etsy until fully confident
  - [ ] Billing page loads, plan visible
  - [ ] Admin nav hidden for normal user
  - [ ] Superuser login → Admin nav visible → /admin loads → all 6 tabs present

---

## 9. Go / No-Go

Before flipping DNS to production:

- [ ] All checklist sections above complete
- [ ] DB backup taken immediately before go-live
- [ ] Previous Docker image tagged for rollback
- [ ] Rollback procedure documented and tested
- [ ] Support email reachable: `support@bulk-edit.com`
- [ ] Error monitoring active (Sentry DSN configured or equivalent)
- [ ] Daily DB backup scheduled (pg_dump cron or managed backups)
- [ ] At least one full manual smoke test on staging with production-equivalent config

---

## 10. Post-Launch (first 24h)

- [ ] Monitor error logs every hour for the first 6h
- [ ] Verify Stripe webhooks delivering (check Stripe dashboard → Webhooks → recent events)
- [ ] Verify Etsy OAuth works for at least one real user shop
- [ ] Review rate limit counters — adjust limits if too aggressive or too permissive
- [ ] Confirm no secrets in logs or error responses
- [ ] Schedule nonce-based CSP hardening (Sprint 21)
- [ ] Schedule Celery production worker deployment (Sprint 21)
- [ ] Schedule monitoring/alerting setup (Sprint 21)
