# Etsy Integration

## API Version
Etsy Open API v3

## Authentication
OAuth2 with PKCE (Proof Key for Code Exchange)

---

## OAuth2 PKCE Flow

```
1. Generate code_verifier (random 43-128 char string)
2. Generate code_challenge = BASE64URL(SHA256(code_verifier))
3. Redirect user to Etsy authorization URL:
   https://www.etsy.com/oauth/connect
     ?response_type=code
     &client_id={ETSY_CLIENT_ID}
     &redirect_uri={ETSY_REDIRECT_URI}
     &scope={scopes}
     &state={random_state}
     &code_challenge={code_challenge}
     &code_challenge_method=S256
4. User authorizes app on Etsy
5. Etsy redirects to callback with code and state
6. Verify state matches
7. Exchange code for tokens:
   POST https://api.etsy.com/v3/public/oauth/token
     grant_type=authorization_code
     client_id={ETSY_CLIENT_ID}
     redirect_uri={ETSY_REDIRECT_URI}
     code={code}
     code_verifier={code_verifier}
8. Store encrypted access_token and refresh_token
```

## Required Scopes

```
listings_r listings_w shops_r transactions_r
```

---

## Token Management

- Access token expiry: 3600 seconds (1 hour)
- Refresh token expiry: Not specified by Etsy (treat as long-lived)
- Refresh: `POST https://api.etsy.com/v3/public/oauth/token` with `grant_type=refresh_token`
- Store: Both tokens encrypted in `etsy_tokens` table (AES-256 via Fernet)
- Auto-refresh: Middleware checks expiry before each Etsy API call

---

## Rate Limits

- Default: 10 requests/second per API key
- Burst: ~25 requests
- Daily limit: Not publicly documented but monitor for 429s
- Strategy: Exponential backoff on 429. Celery task retry with 2^n seconds delay.

---

## Key Endpoints Used

### Read Listing
`GET https://openapi.etsy.com/v3/application/listings/{listing_id}`

### Find All Active Listings in a Shop
`GET https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/active`
Params: `limit=100&offset=0&includes=Images,MainImage`

### Update Listing
`PATCH https://openapi.etsy.com/v3/application/listings/{listing_id}`
Body: only fields being changed

### Upload Listing Image
`POST https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/images`

### Delete Listing Image
`DELETE https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/images/{listing_image_id}`

### Get Listing Variations
`GET https://openapi.etsy.com/v3/application/listings/{listing_id}/variation-images`

### Update Listing Inventory (Variations)
`PUT https://openapi.etsy.com/v3/application/listings/{listing_id}/inventory`

---

## Field Mapping: Etsy API → Internal Model

| Etsy API Field | Internal Field |
|---|---|
| `listing_id` | `etsy_listing_id` |
| `title` | `title` |
| `description` | `description` |
| `price.amount / price.divisor` | `price` (DECIMAL) |
| `quantity` | `quantity` |
| `tags` | `tags` (array) |
| `materials` | `materials` (array) |
| `state` | `status` |
| `taxonomy_id` | `category_id` |
| `shop_section_id` | `section_id` |
| `has_variations` | `has_variations` |
| `is_personalizable` | `is_personalizable` |
| `personalization_instructions` | `personalization_instructions` |
| `item_weight` | `weight_value` |
| `item_weight_unit` | `weight_unit` |
| `item_length` | `length_value` |
| `item_width` | `width_value` |
| `item_height` | `height_value` |
| `item_dimensions_unit` | `dimension_unit` |

---

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 400 | Bad request | Log error, mark listing as failed in batch |
| 401 | Unauthorized | Refresh token, retry once |
| 403 | Forbidden | Log, notify user to reconnect shop |
| 404 | Listing not found | Mark as deleted in DB |
| 429 | Rate limited | Exponential backoff, retry |
| 500 | Etsy server error | Retry up to 3 times with backoff |

---

## Sync Strategy

- **Full sync:** Fetch all active listings page by page (100 per page). Upsert by `etsy_listing_id`.
- **Incremental sync:** Fetch listings modified since `last_synced_at`. Update changed fields only.
- **Sync frequency:** Manual trigger (Free), or scheduled via Celery Beat (Pro).
- **Deletion detection:** During full sync, listings present in DB but not returned by Etsy are marked as `status=expired`.

---

## Blockers

If `ETSY_CLIENT_ID` and `ETSY_CLIENT_SECRET` are not set, Etsy OAuth cannot be tested live. Use fixture data for unit tests.
