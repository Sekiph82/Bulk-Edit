# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-25
**Sprint:** 2 — Auth + Organization — COMPLETE
**Completed:** Full auth module. 18/18 tests pass. Committed and pushed.

## Current State

Repository has full auth module on top of Sprint 1 skeleton:

**Backend (`apps/backend/`):**
- `app/core/security.py` — bcrypt hash/verify, JWT access token, SHA-256 refresh token hash
- `app/core/deps.py` — `get_current_user`, `require_active_user`, `require_superuser` FastAPI deps
- `app/models/user.py` — User model (UUID PK, email, password_hash, full_name, flags)
- `app/models/organization.py` — Organization (UUID PK, name, owner_id FK)
- `app/models/organization_member.py` — OrganizationMember (unique org+user, role)
- `app/models/refresh_token.py` — RefreshToken (token_hash SHA-256, expires_at, revoked)
- `app/schemas/auth.py` — Pydantic schemas for all auth requests/responses
- `app/services/auth.py` — register_user, login_user, refresh_tokens, logout_user, AuthError
- `app/api/v1/auth.py` — 5 endpoints: register, login, refresh, logout, me
- `alembic/versions/0001_create_auth_tables.py` — migration for all 4 tables
- `tests/conftest.py` — SQLite+aiosqlite per-test engine, get_db override
- `tests/test_auth.py` — 14 auth tests (all pass)

**Frontend (`apps/frontend/`):**
- `app/register/page.tsx` — client component, Tailwind form, localStorage token storage
- `app/login/page.tsx` — client component, Tailwind form, localStorage token storage
- `app/dashboard/page.tsx` — shows auth state, email in nav, logout button

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Next Task

**Start Sprint 3: Stripe Billing and Feature Gates**

Implement:
- `Subscription` model (id UUID, organization_id FK, plan: free/monthly/yearly, status: active/canceled/past_due, stripe_customer_id, stripe_subscription_id, current_period_end, timestamps)
- `BillingEvent` model (id UUID, organization_id FK, stripe_event_id unique, event_type, payload JSON, created_at)
- Alembic migration for both tables
- `POST /api/v1/billing/checkout` — create Stripe checkout session, return URL
- `POST /api/v1/billing/portal` — create Stripe customer portal session, return URL
- `POST /api/v1/billing/webhook` — handle Stripe events (checkout.session.completed, customer.subscription.updated, customer.subscription.deleted, invoice.payment_failed)
- `GET /api/v1/billing/subscription` — return current org subscription status
- Feature gate middleware: `require_plan(plan: str)` FastAPI dep that checks org subscription
- Frontend pricing page: `/pricing` with 3-tier cards (Free, Monthly $X, Yearly $X)
- Frontend billing page: `/billing` showing current plan, upgrade/portal button
- Backend pytest tests for billing endpoints (mock Stripe)
- Stripe webhook signature verification using `STRIPE_WEBHOOK_SECRET`

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Start Sprint 3: implement Stripe billing, subscription model, checkout/portal endpoints,
webhook handler, feature gate middleware, and frontend pricing/billing pages.

Active skills: 03 stripe-billing, 06 database-modeling, 07 backend-api, 08 frontend-ui, 20 testing-qa.
```

## Known Issues

- `anyio==4.6.2` is yanked on PyPI (mistagged). Works fine. Update when `anyio>=4.7.0` is available.
- Frontend `npm install` not run yet — `node_modules/` absent. Run `npm install` or `docker compose up` to resolve.
- Frontend auth uses `localStorage` (temporary). Will migrate to HTTP-only cookies in Sprint 18 hardening.

## Push Status

Pushed successfully to: https://github.com/Sekiph82/Bulk-Edit (main)
