# PROJECT_STATUS.md

## Current Phase

**Sprint 5 — Etsy Listing Sync — COMPLETE**

## Status

`Sprint 5 COMPLETE — Ready for Sprint 6`

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
- Sprint 5: Etsy Listing Sync ✓

## Blockers

None

## Known Issues

- `anyio==4.6.2` in requirements-dev.txt is yanked. Works fine. Upgrade when 4.7.0 stable.
- Frontend `npm install` not run — node_modules absent. Run `npm install` or `docker compose up`.
- Etsy access token auto-refresh not fully implemented. If token expired, sync logs warning but continues (Etsy may still accept briefly). Full auto-refresh in Sprint 8.
- `fetch_listing_videos` best-effort: some Etsy shops don't have a video API endpoint. Returns empty list on 404/405.
- Inline sync blocks HTTP thread. Celery background task deferred to Sprint 8 hardening.

## Test Results

| Test File | Result |
|---|---|
| `pytest tests/test_health.py` | 4/4 PASSED |
| `pytest tests/test_auth.py` | 14/14 PASSED |
| `pytest tests/test_billing.py` | 26/26 PASSED |
| `pytest tests/test_etsy.py` | 15/15 PASSED |
| `pytest tests/test_listings.py` | 16/16 PASSED |
| **Full suite `pytest`** | **75/75 PASSED** |

## Listing Sync Endpoints

| Endpoint | Auth | Status |
|---|---|---|
| POST /api/v1/shops/{id}/sync | Bearer | ✓ (inline, future: Celery) |
| GET /api/v1/shops/{id}/sync-status | Bearer | ✓ |
| GET /api/v1/listings | Bearer | ✓ (paginated, filterable) |
| GET /api/v1/listings/{id} | Bearer | ✓ |
| GET /api/v1/listings/{id}/images | Bearer | ✓ |
| GET /api/v1/listings/{id}/videos | Bearer | ✓ |
| GET /api/v1/listings/{id}/variations | Bearer | ✓ |

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
| Sprints complete | 6 / 18 |
| Backend Python files | 65+ |
| Frontend TypeScript files | 20 |
| Total tests | 75 |
| Open blockers | 0 |

## Next Action

Begin Sprint 6: Listings Grid UX. See HANDOFF.md for exact prompt.
