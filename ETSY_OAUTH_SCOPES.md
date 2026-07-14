# ETSY_OAUTH_SCOPES.md

## Scopes requested (unchanged by this branch — already minimal)

`apps/backend/app/core/config.py:42`: `ETSY_SCOPES: str = "listings_r listings_w shops_r profile_r"`

| Scope | Why requested | Feature(s) requiring it | Endpoint(s) it authorizes |
|---|---|---|---|
| `listings_r` | Read listing data to sync into local DB | Listing Sync, Bulk Edit (preview source), CSV Export, AI Tools context, Listing Health Score, Profit Calculator, Video Generator (source images), Promote (listing picker) | `GET /v3/application/shops/{shop_id}/listings`, `.../images`, `.../videos`, `.../inventory` |
| `listings_w` | Write listing changes back to Etsy | Bulk Edit Apply/Revert, Photo/Video Bulk Editor, Variation Editor, Dynamic Pricing (via bulk-edit convert), CSV Import (via bulk-edit convert) | `PATCH /v3/application/listings/{id}`, `PUT .../inventory`, image/video `POST`/`DELETE` |
| `shops_r` | Read shop identity to link a connection to an `EtsyShop` row | OAuth Shop Connection | `GET /v3/application/users/{user_id}/shops` |
| `profile_r` | Read the Etsy user profile associated with the OAuth grant | OAuth Shop Connection (used to resolve the acting user, not stored beyond the session) | Etsy user profile endpoint |

**Scopes explicitly NOT requested**, per this task's own instruction to request only what's minimally required:

- `transaction_r` / any order or transaction scope — not requested. No order/transaction feature exists in the app.
- `email_r` / buyer email — not requested. Per Etsy's commercial-access criteria, `buyer_email` requires a **separate** request even when `transaction_r` is granted; since `transaction_r` itself is never requested, this is doubly out of scope.
- Any billing/payment-account scope — not requested. Billing in this app is entirely Stripe, unrelated to Etsy's own payment scopes.

## Bugs found and fixed in this branch

1. **Granted-scope storage bug** (`apps/backend/app/services/etsy.py:113`, before fix):
   ```python
   scopes=token_data.get("token_type", ""),   # WRONG — stores "Bearer"
   ```
   Etsy's token response includes a `scope` field (space-separated list of scopes actually granted, which can be a subset of what was requested if Etsy partially grants). The code was storing the token *type* instead. Fixed to:
   ```python
   scopes=token_data.get("scope", settings.ETSY_SCOPES),
   ```
   This is corrected in both the initial connect path (`handle_oauth_callback`) and does not require a change to `refresh_etsy_token` (refresh responses don't change the granted scope set).

2. **No distinction between requested and granted scopes** — the app previously had no way to detect if Etsy granted fewer scopes than requested (e.g., a partial commercial-access grant). After the fix, `EtsyToken.scopes` reflects what Etsy actually returned, so a future check can compare it against `settings.ETSY_SCOPES` and warn if they diverge. Not implemented as a UI warning in this branch (no evidence Etsy currently partial-grants for this app's scope set) — flagged in `ETSY_SUPPORT_QUESTIONS.md` as worth confirming.

## Cross-organization authorization check

- `EtsyOAuthState.organization_id` binds a given OAuth attempt to the organization that initiated it; `handle_oauth_callback` writes the resulting `EtsyShop`/`EtsyToken` under `oauth_state.organization_id`, not any value from the callback request itself, so a forged callback cannot attach a token to an attacker-chosen organization. **Verified correct, classification A, no change needed.**
- Every Etsy-scoped endpoint (`shops.py`, `listings.py`, `bulk_edit*.py`) filters by `Listing.organization_id == org_id` / `EtsyShop.organization_id == org_id` — confirmed by the existing `test_security_hardening.py` org-isolation test suite (45 tests, includes org-isolation assertions).

## Shop ownership checks

- `disconnect_shop`, `sync_shop_listings`, and all bulk-edit/media/variation write paths take `org_id` from the authenticated JWT (`get_current_org_id` dependency) and always filter the target `EtsyShop`/`Listing` by that `org_id` before acting — an org cannot disconnect or write to a shop it doesn't own. **Classification A.**

## Revoked-token handling

- `refresh_etsy_token` calls Etsy's token endpoint with `grant_type=refresh_token`; if Etsy has revoked the underlying grant (e.g., the seller revoked access from their own Etsy account settings), the call will fail with a non-2xx response and `resp.raise_for_status()` raises. **Gap found:** the caller of `refresh_etsy_token` did not previously catch this and mark the shop as needing reconnection — it propagated as a generic 500. **Correction (this branch, verified against actual code, not just described):** `get_valid_etsy_access_token` (in `etsy_sync.py`) now proactively calls `refresh_etsy_token` whenever the stored token is expired or within `TOKEN_REFRESH_BUFFER_SECONDS` of expiry (previously it just logged a warning and used the stale token anyway). If the refresh itself fails (`httpx.HTTPStatusError` — Etsy rejected it, most commonly a revoked grant), the shop is marked `is_connected = False` and the existing `SyncError` exception is raised with status `401` and the message "Etsy access has expired or was revoked. Please reconnect your shop." This reuses the pre-existing `SyncError` type (already handled by every sync-path caller) rather than introducing a new exception class — no `EtsyReauthRequiredError` type exists in the codebase.

## No password collection

- Confirmed: no field, form, or code path anywhere collects an Etsy password. OAuth-only. **Classification A.**
