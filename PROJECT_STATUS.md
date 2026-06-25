# PROJECT_STATUS.md

## Current Phase

**Sprint 4 — Etsy OAuth2 PKCE Flow — COMPLETE**

## Status

`Sprint 4 COMPLETE — Ready for Sprint 5`

## Last Updated

2026-06-25

## Active Skills

None (between sprints)

## Completed Sprints

- Sprint 0: Project Memory and Operating System ✓
- Sprint 1: Monorepo Skeleton ✓
- Sprint 2: Auth + Organization ✓
- Sprint 3: Stripe Billing and Feature Gates ✓
- Sprint 4: Etsy OAuth2 PKCE Flow ✓

## Blockers

None

## Known Issues

- `anyio==4.6.2` in requirements-dev.txt is yanked. Works fine. Upgrade when 4.7.0 stable.
- Frontend `npm install` not run — node_modules absent. Run `npm install` or `docker compose up`.
- Stripe live testing requires real `sk_test_*` key + `stripe listen` CLI for local webhooks.
- `stripe.Webhook.construct_event` blocks event loop (sync call in async route). Fix in Sprint 18 hardening.
- Etsy OAuth requires real `ETSY_CLIENT_ID` in .env — placeholder returns 503 by design.
- `fetch_etsy_shop` uses `user_id` from token response — Etsy token exchange response format should be verified against live API.

## Test Results

| Test File | Result |
|---|---|
| `pytest tests/test_health.py` | 4/4 PASSED |
| `pytest tests/test_auth.py` | 14/14 PASSED |
| `pytest tests/test_billing.py` | 26/26 PASSED |
| `pytest tests/test_etsy.py` | 15/15 PASSED |
| **Full suite `pytest`** | **59/59 PASSED, 0 warnings** |

## Etsy Endpoints

| Endpoint | Auth | Status |
|---|---|---|
| GET /api/v1/etsy/authorize | Bearer | ✓ (503 w/o ETSY_CLIENT_ID) |
| GET /api/v1/etsy/callback | None | ✓ (always redirects) |
| GET /api/v1/etsy/shops | Bearer | ✓ |
| DELETE /api/v1/etsy/shops/{id} | Bearer | ✓ |

## Port Configuration

| Service | Host Port | Container Port |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Metrics

| Metric | Value |
|---|---|
| Sprints complete | 5 / 18 |
| Backend Python files | 50+ |
| Frontend TypeScript files | 18 |
| Total tests | 59 |
| Open blockers | 0 |

## Next Action

Begin Sprint 5: Etsy Listing Sync. See HANDOFF.md for exact prompt.
