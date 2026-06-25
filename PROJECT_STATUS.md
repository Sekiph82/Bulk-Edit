# PROJECT_STATUS.md

## Current Phase

**Sprint 6 — Listings Grid UX — COMPLETE**

## Status

`Sprint 6 COMPLETE — Ready for Sprint 7`

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
- Sprint 6: Listings Grid UX ✓

## Blockers

None

## Known Issues

- `anyio==4.6.2` in requirements-dev.txt is yanked. Works fine. Upgrade when 4.7.0 stable.
- Frontend `npm install` not run — node_modules absent. Run `npm install` or `docker compose up`.
- Etsy access token auto-refresh not fully implemented. Full auto-refresh in Sprint 8.
- `fetch_listing_videos` best-effort: returns empty list on 404/405.
- Inline sync blocks HTTP thread. Celery background task deferred to Sprint 8.
- Bulk edit button in listings grid is disabled placeholder — activates in Sprint 7.

## Test Results

| Test File | Result |
|---|---|
| `pytest tests/test_health.py` | 4/4 PASSED |
| `pytest tests/test_auth.py` | 14/14 PASSED |
| `pytest tests/test_billing.py` | 26/26 PASSED |
| `pytest tests/test_etsy.py` | 15/15 PASSED |
| `pytest tests/test_listings.py` | 34/34 PASSED |
| **Full suite `pytest`** | **93/93 PASSED** |

## Listings API — GET /listings filters

| Filter | Type | Status |
|---|---|---|
| shop_id | str | ✓ |
| state | str | ✓ |
| search | str (ILIKE title) | ✓ |
| tag | str (ILIKE JSON cast) | ✓ |
| has_variations | bool | ✓ |
| price_min / price_max | int (cents) | ✓ |
| quantity_min / quantity_max | int | ✓ |
| section_id | str | ✓ |
| taxonomy_id | str | ✓ |
| is_personalizable | bool | ✓ |
| is_customizable | bool | ✓ |
| sort_by (whitelist) | str | ✓ (400 on invalid) |
| sort_dir | asc/desc | ✓ (400 on invalid) |

## Frontend — Sprint 6 additions

| File | Description |
|---|---|
| `apps/frontend/lib/api.ts` | Typed API client (all endpoints) |
| `apps/frontend/app/listings/page.tsx` | Full grid: state tabs, advanced filters, saved views, column visibility, multi-select, sortable headers, thumbnails, detail sidebar, summary cards |

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
| Frontend TypeScript files | 22 |
| Total tests | 93 |
| Open blockers | 0 |

## Next Action

Begin Sprint 7: Bulk Edit Preview Engine. See HANDOFF.md for exact prompt.
