# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-25
**Sprint:** 4 — Etsy OAuth2 PKCE Flow — COMPLETE
**Completed:** EtsyShop/EtsyToken/EtsyOAuthState models, Fernet encryption module, PKCE helpers, 4 Etsy endpoints (authorize/callback/shops/disconnect), etsy service layer, Alembic migration 0003, 15 Etsy tests, frontend /shops page. 59/59 tests pass. Committed and pushed.

## Current State

Full Etsy OAuth2 PKCE flow on top of Sprint 3 billing + Sprint 2 auth:

**Backend (`apps/backend/`):**
- `app/core/config.py` — ENCRYPTION_KEY, ETSY_CLIENT_ID, ETSY_REDIRECT_URI, ETSY_SCOPES + is_etsy_configured()
- `app/core/encryption.py` — Fernet encrypt_token/decrypt_token, dev fallback key for local use
- `app/models/etsy_shop.py` — EtsyShop (org-scoped, etsy_shop_id UNIQUE, is_connected)
- `app/models/etsy_token.py` — EtsyToken (etsy_shop_id FK UNIQUE, encrypted access/refresh, expires_at)
- `app/models/etsy_oauth_state.py` — EtsyOAuthState (state UNIQUE, code_verifier, expires_at, consumed_at)
- `app/schemas/etsy.py` — response schemas
- `app/services/etsy.py` — PKCE, OAuth flow, token exchange, shop fetch, list/disconnect
- `app/api/v1/etsy.py` — 4 endpoints: authorize, callback, shops, disconnect
- `alembic/versions/0003_create_etsy_tables.py` — migration
- `tests/test_etsy.py` — 15 tests
- `tests/conftest.py` — updated to shared-memory SQLite URI for cross-fixture visibility

**Frontend (`apps/frontend/`):**
- `app/shops/page.tsx` — list shops, connect button (calls /etsy/authorize, redirects to Etsy), disconnect, success/error banners
- `app/dashboard/page.tsx` — added Etsy Shops link

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Next Task

**Start Sprint 5: Etsy Listing Sync**

Implement:
- `Listing` model (etsy_shop_id FK, etsy_listing_id BIGINT UNIQUE, title, description, price, quantity, tags TEXT[], materials TEXT[], status, category_id, section_id, has_variations, shipping_profile_id, return_policy_id, personalization fields, weight/dimension fields, timestamps)
- `ListingImage` model (listing_id FK, etsy_image_id BIGINT, url_fullxfull, url_570xN, alt_text, rank)
- `ListingVariation` model (listing_id FK, etsy_product_id BIGINT, property_name, value, price, quantity, sku, is_available)
- Alembic migration 0004 for all three tables
- `GET /api/v1/shops/{shop_id}/sync` — trigger full sync (background Celery task or sync for MVP)
- `GET /api/v1/shops/{shop_id}/sync-status` — get sync job status
- `GET /api/v1/listings` — list listings (paginated, filterable by shop_id/status/search/page/per_page/sort_by/sort_dir)
- `GET /api/v1/listings/{id}` — single listing detail
- `GET /api/v1/listings/{id}/images` — listing images
- `GET /api/v1/listings/{id}/variations` — listing variations
- Etsy API integration: `GET /application/listings/active` for shop listings, `GET /application/listings/{listing_id}/images`, handle pagination
- Use `decrypt_token()` from encryption.py to get stored access token; call `refresh_etsy_token()` if expired
- max_listings feature gate (from PLAN_LIMITS) to cap how many listings are synced
- Frontend `/listings` page — list view with search, filters, pagination
- Backend tests for sync and listing endpoints

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Start Sprint 5: implement Etsy listing sync — Listing/ListingImage/ListingVariation models,
sync endpoints, listings list/detail endpoints, Etsy API integration with encrypted token
decryption, max_listings feature gate, frontend /listings page, and backend tests.

Active skills: 11 etsy-integration, 06 database-modeling, 07 backend-api, 08 frontend-ui, 20 testing-qa.
```

## Known Issues

- Etsy live OAuth: set real `ETSY_CLIENT_ID` in .env and register `http://localhost:8100/api/v1/etsy/callback` as redirect URI in Etsy developer portal.
- `fetch_etsy_shop` extracts `user_id` from token response field `user_id` — verify against live Etsy OAuth token response format.
- Etsy access tokens expire in ~1 hour. `refresh_etsy_token()` stub exists but not hooked into sync flow yet (Sprint 5 task).
- `stripe.Webhook.construct_event` blocks event loop. Fix in Sprint 18.

## Push Status

Pushed successfully to: https://github.com/Sekiph82/Bulk-Edit (main)
