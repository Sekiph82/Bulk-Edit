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
