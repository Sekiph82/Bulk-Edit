# Launch Readiness Report

**This is a fill-in template. Complete before each production release.**

---

## Release Info

| Field | Value |
|---|---|
| Release commit SHA | |
| Release date | |
| Deployed by | |
| Target environment | production |
| Backend image tag | |
| Frontend image tag | |

---

## Pre-Launch Checklist

### Tests

| Check | Result | Notes |
|---|---|---|
| Backend tests (count/total) | | e.g. 621/621 |
| Frontend build (routes) | | e.g. 22/22, 0 errors |
| Playwright E2E | | e.g. 17/17 passed |
| CI pipeline (GitHub Actions) | | Pass / Fail |

### Environment Validation

Run: `python apps/backend/scripts/validate_env.py --env production`

| Check | Result | Notes |
|---|---|---|
| `validate_env.py` exit code | | 0 = pass, 1 = errors |
| Errors count | | Must be 0 |
| Warnings count | | Review each |
| No secrets in git diff | | `git diff --cached \| grep sk_live\|whsec_` |

### Infrastructure

| Check | Result | Notes |
|---|---|---|
| Production DB connected | | |
| Production Redis connected | | |
| `GET /api/v1/health` | | `{"status":"ok"}` |
| `GET /api/v1/health/ready` | | `{"status":"ready"}` |
| All frontend routes 200 | | Run smoke_test_deployment |
| Staging smoke test passed | | |
| Production smoke test passed | | |
| Alembic migration current | | `alembic current` matches head |

### Security Headers

Run: `curl -I https://api.bulkeditapp.com/api/v1/health`

| Header | Present | Value |
|---|---|---|
| `X-Content-Type-Options` | | `nosniff` |
| `X-Frame-Options` | | `DENY` |
| `Referrer-Policy` | | `strict-origin-when-cross-origin` |

Run: `curl -I https://www.bulkeditapp.com/`

| Header | Present | Value |
|---|---|---|
| `Content-Security-Policy` | | (not empty) |
| `Strict-Transport-Security` | | `max-age=63072000` |

### Configuration

| Check | Result | Notes |
|---|---|---|
| CORS configured correctly | | No wildcard; exact origin |
| Rate limiting enabled (redis) | | `RATE_LIMIT_ENABLED=true`, `RATE_LIMIT_BACKEND=redis` |
| JWT_SECRET not a placeholder | | Rotated from dev value |
| ENCRYPTION_KEY not a placeholder | | Rotated from dev value |
| `.local-superusers.env` not staged | | `git check-ignore apps/backend/.local-superusers.env` |

### Providers

| Check | Result | Notes |
|---|---|---|
| Stripe live keys configured | | `sk_live_...` |
| Stripe webhook registered | | Endpoint URL matches `BACKEND_URL` |
| Stripe test payment completes | | Use `4242 4242 4242 4242` on staging |
| Etsy OAuth configured | | `ETSY_CLIENT_ID` not placeholder |
| Etsy redirect URI matches | | Registered in Etsy Developer Portal |
| AI provider configured | | |
| Sentry DSN configured | | |
| `SENTRY_ENVIRONMENT=production` | | |

### Security Checks

| Check | Result | Notes |
|---|---|---|
| Admin nav hidden for normal users | | Login as non-superuser, check nav |
| Admin nav visible for superusers | | Login as superuser, check nav |
| `/admin` returns 403 for normal user | | Shows "Access Denied" UI |
| `/api/v1/admin/*` returns 403 for normal user | | |
| No password_hash in any API response | | |
| No Etsy tokens in any API response | | |
| No Stripe secret keys in any API response | | |
| Pre-write backup snapshots confirmed working | | Run a test bulk edit in staging |

### Monitoring

| Check | Result | Notes |
|---|---|---|
| Uptime monitor configured | | (e.g. UptimeRobot, Better Uptime) |
| Sentry receiving events | | Trigger test 404, verify in Sentry |
| Stripe webhook dashboard clean | | No failed deliveries |
| Redis rate limiter active | | Send 11+ login requests, get 429 |

---

## Database State

| Item | Value |
|---|---|
| Latest migration revision | |
| `alembic current` output | |
| Pre-launch backup taken | Yes / No |
| Backup location | |

---

## Known Risks

| Risk | Severity | Mitigation |
|---|---|---|
| | | |
| | | |

---

## Go / No-Go Decision

| Person | Role | Decision | Date |
|---|---|---|---|
| | Owner | GO / NO-GO | |

**Final Decision:** GO / NO-GO

**Reason if NO-GO:**

---

## Deployment Steps Executed

- [ ] `validate_env.py --env production` — exit 0
- [ ] Database backup taken
- [ ] `alembic upgrade head` — applied cleanly
- [ ] Backend image deployed
- [ ] Frontend image deployed
- [ ] Smoke test passed against production
- [ ] Sentry shows no new P0 errors

---

## Post-Launch Checks (T+1h, T+24h)

**T+1h:**

- [ ] No P0 errors in Sentry (production environment)
- [ ] Stripe webhooks delivered successfully (check Dashboard)
- [ ] Rate limit counters nominal (check Admin → System Health)
- [ ] User registration flow works end-to-end

**T+24h:**

- [ ] No P0 errors in Sentry
- [ ] Admin dashboard shows expected user/org counts
- [ ] Billing events recorded correctly for test subscription
- [ ] No unexpected Redis memory growth

---

## Incident Log

| Time | Event | Resolution |
|---|---|---|
| | | |
