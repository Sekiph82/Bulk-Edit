# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-25
**Sprint:** 3 — Stripe Billing and Feature Gates — COMPLETE
**Completed:** Subscription/BillingEvent/UsageCounter models, plan limits config, 6 billing endpoints, feature gate service, webhook handler with idempotency, /pricing and /billing frontend pages. 44/44 tests pass. Committed and pushed.

## Current State

Full billing module on top of Sprint 2 auth:

**Backend (`apps/backend/`):**
- `app/core/plans.py` — plan limits for free/basic_monthly/pro_monthly/basic_yearly/pro_yearly
- `app/core/config.py` — STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_* env vars + helper methods
- `app/core/deps.py` — get_current_org_id dependency added
- `app/models/subscription.py` — Subscription model (unique per org, all Stripe fields)
- `app/models/billing_event.py` — BillingEvent (stripe_event_id unique, payload JSON)
- `app/models/usage_counter.py` — UsageCounter (period_key YYYY-MM, unique per org+period)
- `app/services/billing.py` — ensure_subscription_exists, checkout, portal, process_webhook_event, usage
- `app/api/v1/billing.py` — 6 endpoints: plans, subscription, checkout, portal, webhook, usage
- `alembic/versions/0002_create_billing_tables.py` — migration for 3 tables
- `tests/test_billing.py` — 26 tests

**Frontend (`apps/frontend/`):**
- `app/pricing/page.tsx` — 5-plan grid, GET /billing/plans, POST /billing/checkout
- `app/billing/page.tsx` — subscription status, POST /billing/portal, success/canceled banners
- `app/dashboard/page.tsx` — links to /pricing and /billing

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Next Task

**Start Sprint 4: Etsy OAuth**

Implement:
- `EtsyShop` model (id UUID, organization_id FK, etsy_shop_id UNIQUE, shop_name, is_connected, last_synced_at, timestamps)
- `EtsyToken` model (id UUID, etsy_shop_id FK, access_token_enc TEXT encrypted with Fernet, refresh_token_enc TEXT, expires_at, scopes, timestamps)
- Alembic migration for both tables
- Etsy OAuth2 PKCE flow:
  - `GET /api/v1/etsy/authorize` — generate PKCE code_verifier/code_challenge, store in Redis, return Etsy auth URL
  - `GET /api/v1/etsy/callback` — exchange code for tokens, encrypt and store, return redirect to /dashboard
- `DELETE /api/v1/etsy/shops/{shop_id}/disconnect` — disconnect shop (set is_connected=False, delete token)
- `GET /api/v1/etsy/shops` — list connected shops for the org
- Fernet encryption for token storage (`cryptography` package already in requirements.txt)
- `ENCRYPTION_KEY` env var (Fernet key) — already in .env.example
- Frontend `/shops` page — list connected shops, "Connect Etsy Shop" button
- Frontend connect flow — redirects to Etsy OAuth, handles callback
- Backend tests for OAuth flow (mock Etsy API)

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.
Read docs/technical/ETSY_INTEGRATION.md.

Start Sprint 4: implement Etsy OAuth2 PKCE flow, encrypted token storage,
EtsyShop/EtsyToken models, connect/callback/disconnect endpoints, frontend
shop connect page, and backend tests.

Active skills: 11 etsy-integration, 06 database-modeling, 07 backend-api, 08 frontend-ui, 20 testing-qa.
```

## Known Issues

- Stripe live testing: set real `STRIPE_SECRET_KEY=sk_test_...` and run `stripe listen --forward-to localhost:8100/api/v1/billing/webhook` for local webhook testing.
- `stripe.Webhook.construct_event` is synchronous (blocks event loop). Acceptable for Sprint 3; fix with `anyio.to_thread.run_sync` in Sprint 18 hardening.
- Frontend `npm install` not run yet — `node_modules/` absent. Run `npm install` or `docker compose up`.

## Push Status

Pushed successfully to: https://github.com/Sekiph82/Bulk-Edit (main)
