# Monitoring Guide

## Health Endpoints

| Endpoint | Purpose | Expected Response |
|---|---|---|
| `GET /api/v1/health` | Liveness — is the process up? | `{"status":"ok","service":"bulk-edit-api"}` |
| `GET /api/v1/health/ready` | Readiness — is the DB connected? | `{"status":"ready","database":"connected"}` |
| `GET /api/v1/admin/system-health` | Operational dashboard (superuser only) | See admin dashboard |

Configure your uptime monitor (Better Uptime, UptimeRobot, Pingdom, etc.) to hit `/api/v1/health/ready` every 30–60 seconds.

Alert on: any non-200 response, response time > 5s.

---

## Error Monitoring (Sentry)

Set `SENTRY_DSN` in production to enable automatic error tracking.

```env
SENTRY_DSN=https://your-key@sentry.io/your-project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.05
```

**Frontend Sentry:** Run `npx @sentry/wizard@latest -i nextjs` in `apps/frontend/` at deploy time.
Required env var: `NEXT_PUBLIC_SENTRY_DSN` (public — not secret, safe to expose in HTML).

### Scrubbing Rules

The backend scrubs these fields before any event reaches Sentry:
- `password`, `password_hash`
- `access_token`, `refresh_token`
- `etsy_access_token`, `etsy_refresh_token`
- `stripe_secret_key`, `openai_api_key`, `anthropic_api_key`
- `authorization` header, `cookie` header

**Never** log or send raw tokens.

### Verify Sentry

After configuring DSN, hit a known-bad endpoint and verify the event appears in Sentry within 30 seconds.

---

## Rate Limiting Monitoring

Rate limit hits are logged at WARNING level.

Production thresholds: login 10/min/IP, register 5/min/IP, contact 5/hour/IP.

Alert if login 429 rate spikes: may indicate credential stuffing or user lockout.

Production backend: `RATE_LIMIT_BACKEND=redis` — keys expire automatically.

Redis memory footprint for rate limiting: negligible (sorted sets with short TTLs).

---

## Stripe Webhooks

Monitor Stripe Dashboard → Developers → Webhooks for failed deliveries.

Alert if webhook failure rate > 5% over 1 hour.

Common failures:
- Expired SSL certificate
- Wrong endpoint URL after redeploy
- Wrong `STRIPE_WEBHOOK_SECRET`

---

## Etsy OAuth

Monitor backend logs for `etsy_oauth` or `etsy_token` error patterns.

Alert if Etsy OAuth error rate > 10% of connect attempts over 15 minutes.

Common failures:
- Redirect URI mismatch
- Expired Etsy app credentials
- Etsy API downtime (check Etsy status page)

---

## Scheduled Jobs

Check admin dashboard → System tab → scheduled jobs count.

Alert if active scheduled job count drops to 0 unexpectedly.

Failed job counts visible at `GET /api/v1/admin/system-health` (superuser).

---

## Database Backups

Schedule daily `pg_dump` to object storage (S3/MinIO).

```bash
pg_dump $DATABASE_URL | gzip > backup-$(date +%Y%m%d).sql.gz
```

Test restore: monthly.

Alert if backup job fails to produce output.

---

## Redis

Monitor with `INFO memory` and `INFO clients`.

Alert thresholds:
- `used_memory` > 80% of `maxmemory`
- `connected_clients` > 80% of `maxclients`

If Redis goes down, rate limiting falls back to in-memory automatically (warning logged).

---

## Admin Dashboard Checks (Weekly)

1. Log in as superuser
2. Verify all 6 admin tabs load (Overview, Users, Billing, Etsy, Usage, System)
3. Confirm no secrets visible in any tab
4. Check `sentry_configured: true` in System tab (production)
5. Check `redis_status: "ok"` in System tab (production)

---

## Daily Post-Launch Checklist

- [ ] Uptime monitor shows green
- [ ] Sentry shows 0 new P0 errors
- [ ] Stripe dashboard shows no failed webhooks
- [ ] No unusual rate limit spike in logs
- [ ] Admin user count trending as expected
- [ ] Backend `/api/v1/health/ready` returns 200
