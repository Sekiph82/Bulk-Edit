# Security Model

## Authentication

- JWT access tokens: 15 minute expiry
- JWT refresh tokens: 7 day expiry, single use (rotated on refresh)
- Token blacklist: refresh tokens stored in Redis on logout/revoke
- Password hashing: bcrypt, cost factor 12 minimum
- Email verification required before first Etsy connection

## Authorization

- All API routes require valid access token (except /auth/* and /health)
- Organization-scoped data: every service layer query filters by `organization_id` from JWT claims
- Admin routes: separate `require_admin` dependency checks `user.role == 'admin'`
- Subscription gates: `require_pro` dependency on all Pro-only endpoints

## JWT Claims

```json
{
  "sub": "user_uuid",
  "org": "organization_uuid",
  "role": "user",
  "plan": "pro_monthly",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "unique_token_id"
}
```

## Etsy Token Security

- Access and refresh tokens encrypted with Fernet (AES-128-CBC + HMAC-SHA256)
- Encryption key stored in `ENCRYPTION_KEY` environment variable
- Tokens never logged, never included in API responses
- Tokens decrypted in memory only during Etsy API calls

## Input Validation

- All request bodies validated with Pydantic schemas
- All query parameters typed and range-checked
- File uploads validated for type, size, and content-type header

## Rate Limiting

Applied via Redis-backed middleware:
- Auth endpoints: 5 requests/minute per IP
- AI endpoints: per-plan monthly limits
- Etsy write endpoints: 10 requests/second (Etsy compliance)
- General API: 300 requests/minute per authenticated user

## CORS

```python
ALLOWED_ORIGINS = [env.FRONTEND_URL]
# Never allow * in production
```

## Security Headers

Applied via FastAPI middleware:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'self'`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Audit Log

Every external write operation logs:
- `organization_id`
- `user_id`
- `action` (e.g., `bulk_edit.apply`)
- `resource_type` and `resource_id`
- `metadata` (field names, listing count)
- `ip_address`
- `created_at`

## Secret Management

- All secrets in environment variables
- `.env` in `.gitignore`
- `.env.example` contains only placeholder values
- Production secrets managed via hosting provider's secret manager
- No secrets in Docker images, git history, or logs

---

## Billing Security (Sprint 3)

### Stripe Webhook Verification

Every webhook request verified before processing:
1. `STRIPE_WEBHOOK_SECRET` must start with `whsec_` (503 otherwise)
2. `stripe.Webhook.construct_event(raw_body, stripe-signature, secret)` — cryptographic HMAC-SHA256 verification
3. Invalid signature → 400, event dropped
4. Duplicate `stripe_event_id` → silently ignored (idempotent)
5. Raw request body used for verification (not parsed JSON)

### Feature Gate Security

- Backend is sole source of truth for subscription/feature access
- Frontend cannot grant itself access — all feature checks hit DB
- `ensure_subscription_exists` creates free plan if none exists — no null plan states possible
- `can_use_feature(subscription, feature)` reads `PLAN_LIMITS` dict — not user-supplied values
- Free plan fallback prevents any nil-pointer / access errors on missing subscription

### Stripe Key Security

- `STRIPE_SECRET_KEY` never logged or returned in API responses
- Checkout/portal only called when key is configured (`sk_test_` or `sk_live_` prefix)
- Test keys (`sk_test_`) never used in production (environment config check)
- Price IDs contain "placeholder" substring check — prevents phantom Stripe calls with invalid IDs

---

## Bulk Edit Safety (Sprint 7)

### Safe Write Protocol (enforced from Sprint 8)

Every Etsy write triggered by bulk edit must follow this sequence in order:
1. Generate preview (diff before/after, no Etsy calls)
2. User reviews diff — explicit confirmation required
3. Snapshot backup: INSERT INTO listing_snapshots (full listing JSON)
4. Subscription gate check (bulk_edits_used < plan limit)
5. Write audit_log entry (action='bulk_edit.apply', before apply)
6. Execute Etsy PATCH /listings/{id}
7. Confirm success and log result

No step may be skipped. Sprint 7 apply endpoint is a 409 stub — no Etsy writes possible.

### Org Isolation

- `BulkEditSession.organization_id` enforced on every service call
- `get_bulk_edit_session` returns 404 (not 403) on cross-org access to avoid enumeration
- `create_bulk_edit_session` rejects listing IDs not belonging to the caller's org (400)
- Preview items inherit session org — no direct listing_id lookup bypasses org check

### Validation Before Write

- `validate_listing_data` rejects invalid states before any Etsy call
- Sessions with `invalid` preview items should be blocked from apply (enforced Sprint 8)
- `apply_change_to_listing_data` is a pure function — no DB side effects during preview
