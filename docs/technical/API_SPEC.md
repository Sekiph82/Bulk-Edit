# API Specification

Base URL: `/api/v1`
Auth: Bearer JWT in Authorization header
Content-Type: `application/json`

---

## Auth

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Register new user | None |
| POST | `/auth/login` | Login, returns JWT pair | None |
| POST | `/auth/refresh` | Refresh access token | Refresh token |
| POST | `/auth/logout` | Blacklist refresh token | Access token |
| POST | `/auth/verify-email` | Verify email with token | None |
| POST | `/auth/forgot-password` | Send reset email | None |
| POST | `/auth/reset-password` | Reset password with token | None |
| GET | `/auth/me` | Get current user | Access token |

---

## Etsy OAuth

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/auth/etsy/authorize` | Start Etsy OAuth PKCE flow | Access token |
| GET | `/auth/etsy/callback` | Handle Etsy OAuth callback | None |
| DELETE | `/shops/{shop_id}/disconnect` | Disconnect Etsy shop | Access token |

---

## Shops

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/shops` | List organization's shops | Access token |
| GET | `/shops/{shop_id}` | Get shop detail | Access token |
| POST | `/shops/{shop_id}/sync` | Trigger listing sync | Access token |
| GET | `/shops/{shop_id}/sync-status` | Get sync job status | Access token |

---

## Listings

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/listings` | List listings (paginated, filterable) | Access token |
| GET | `/listings/{id}` | Get single listing | Access token |
| GET | `/listings/{id}/images` | Get listing images | Access token |
| GET | `/listings/{id}/variations` | Get listing variations | Access token |
| GET | `/listings/{id}/snapshots` | Get listing snapshots | Access token + Pro |

Query params for `GET /listings`:
- `shop_id` — filter by shop
- `status` — active/inactive/draft
- `search` — full-text search on title
- `page` — default 1
- `per_page` — default 50, max 200
- `sort_by` — title/price/created_at
- `sort_dir` — asc/desc

---

## Bulk Edit

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/bulk-edit/sessions` | Create bulk edit session | Access token |
| GET | `/bulk-edit/sessions/{id}` | Get session status | Access token |
| GET | `/bulk-edit/sessions/{id}/preview` | Get before/after diff | Access token |
| POST | `/bulk-edit/sessions/{id}/apply` | Apply changes to Etsy | Access token + Pro (for >10/month) |
| DELETE | `/bulk-edit/sessions/{id}` | Discard session | Access token |
| GET | `/bulk-edit/sessions` | List past sessions | Access token |

---

## Snapshots and Revert

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/snapshots` | List snapshots | Access token + Pro |
| GET | `/snapshots/{id}` | Get snapshot data | Access token + Pro |
| POST | `/snapshots/{id}/revert` | Revert to snapshot | Access token + Pro |
| GET | `/revert-logs` | List revert history | Access token + Pro |

---

## Media

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/media/upload-url` | Get presigned S3 upload URL | Access token + Pro |
| POST | `/media` | Save media metadata after upload | Access token + Pro |
| GET | `/media` | List media assets | Access token + Pro |
| GET | `/media/{id}` | Get media asset | Access token + Pro |
| DELETE | `/media/{id}` | Delete media asset | Access token + Pro |

---

## AI Tools

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/ai/optimize-titles` | Generate optimized titles | Access token |
| POST | `/ai/write-descriptions` | Generate descriptions | Access token + Pro |
| POST | `/ai/generate-tags` | Generate tags | Access token |
| POST | `/ai/generate-alt-text` | Generate alt text for images | Access token + Pro |
| POST | `/ai/seo-score` | Score listings for SEO | Access token + Pro |
| POST | `/ai/suggest-categories` | Suggest Etsy categories | Access token + Pro |

---

## Billing (Sprint 3 — IMPLEMENTED)

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/billing/plans` | Get all plan configs + limits | None |
| GET | `/billing/subscription` | Get/create current subscription | Access token |
| POST | `/billing/checkout` | Create Stripe checkout session | Access token |
| POST | `/billing/portal` | Create Stripe customer portal session | Access token |
| POST | `/billing/webhook` | Stripe webhook handler | Stripe-Signature header |
| GET | `/billing/usage` | Current period usage + plan limits | Access token |
| GET | `/billing/invoices` | List invoices (future) | Access token |

### POST /billing/checkout

Request: `{ "plan": "basic_monthly" | "pro_monthly" | "basic_yearly" | "pro_yearly" }`
Returns: `{ "checkout_url": "https://checkout.stripe.com/..." }`
Errors:
- 400 if plan="free"
- 400 if plan invalid
- 503 if Stripe not configured

### POST /billing/webhook

Returns: `{ "received": true }`
Errors:
- 503 if STRIPE_WEBHOOK_SECRET not configured
- 400 if signature invalid

---

## CSV

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/csv/export` | Start CSV export job | Access token + Pro |
| POST | `/csv/import` | Upload and validate CSV | Access token + Pro |
| GET | `/csv/import/{id}/preview` | Preview import changes | Access token + Pro |
| POST | `/csv/import/{id}/apply` | Apply CSV import | Access token + Pro |
| GET | `/csv/jobs/{id}` | Get job status | Access token + Pro |

---

## Scheduling

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/schedules` | List scheduled jobs | Access token + Pro |
| POST | `/schedules` | Create scheduled job | Access token + Pro |
| PUT | `/schedules/{id}` | Update scheduled job | Access token + Pro |
| DELETE | `/schedules/{id}` | Delete scheduled job | Access token + Pro |

---

## Admin

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/admin/users` | List all users | Admin token |
| GET | `/admin/subscriptions` | List all subscriptions | Admin token |
| GET | `/admin/audit-logs` | View audit logs | Admin token |
| GET | `/admin/health` | System health | Admin token |

---

## Health

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/health` | Liveness check | None |
| GET | `/ready` | Readiness check (DB + Redis) | None |

---

## Standard Response Formats

### Success
```json
{
  "data": { ... },
  "meta": { "page": 1, "per_page": 50, "total": 423 }
}
```

### Error
```json
{
  "error": {
    "code": "SUBSCRIPTION_REQUIRED",
    "message": "This feature requires a Pro subscription.",
    "details": {}
  }
}
```

### Pagination
All list endpoints are paginated. Use `page` and `per_page` query params.
