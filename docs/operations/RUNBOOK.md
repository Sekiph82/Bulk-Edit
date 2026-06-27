# Operations Runbook

Incident response procedures for Bulk-Edit production operations.

---

## App Down

Symptom: All routes return errors or are unreachable.

1. `docker compose -p bulk-edit ps` — check all 4 containers running
2. `docker compose -p bulk-edit logs backend --tail=50` — check startup errors
3. `curl http://localhost:8100/api/v1/health` — if no response, backend process dead
4. Restart: `docker compose -p bulk-edit restart backend`
5. If still failing: check DB with `/api/v1/health/ready`

---

## Backend Health Failing

Symptom: `GET /api/v1/health` returns non-200 or times out.

1. Check logs: `docker compose -p bulk-edit logs backend --tail=100`
2. Common causes: missing env var, import error, port conflict
3. Fix env, then rebuild: `docker compose -p bulk-edit up -d --build backend`
4. Verify: `curl http://localhost:8100/api/v1/health`

---

## Readiness Failing

Symptom: `GET /api/v1/health/ready` returns 503 or `{"database":"error"}`.

1. `docker compose -p bulk-edit ps` — check postgres container health
2. `docker compose -p bulk-edit logs postgres --tail=30`
3. Restart postgres: `docker compose -p bulk-edit restart postgres`
4. Wait 10s, then restart backend: `docker compose -p bulk-edit restart backend`
5. Verify: `curl http://localhost:8100/api/v1/health/ready`

---

## Database Unavailable

1. Check disk: `df -h` — ensure not full
2. Postgres logs for FATAL errors: `docker compose -p bulk-edit logs postgres`
3. If data corrupt: restore from last `pg_dump` backup
4. Connection pool exhausted: restart backend, check for leaked connections in code

---

## Redis Unavailable

Rate limiting falls back to in-memory automatically (warning logged). Celery task queue fails if configured.

1. `docker compose -p bulk-edit restart redis`
2. Verify: `docker exec bulk-edit-redis-1 redis-cli ping` → `PONG`
3. Rate limiting auto-recovers on next request; no manual action needed

---

## Stripe Webhook Failing

1. Stripe Dashboard → Developers → Webhooks → recent attempts
2. Verify endpoint URL is correct and reachable from the internet
3. Verify `STRIPE_WEBHOOK_SECRET` matches the Stripe dashboard value
4. If endpoint URL changed after redeploy: update in Stripe Dashboard
5. Replay failed events from Stripe Dashboard after fix

---

## Etsy OAuth Failures

1. Verify `ETSY_CLIENT_ID`, `ETSY_CLIENT_SECRET`, `ETSY_REDIRECT_URI` are correct
2. Confirm redirect URI registered in Etsy Developer Portal matches exactly (including trailing slash)
3. Token expired: user must reconnect shop via `/shops` page
4. Etsy API outage: check https://status.etsy.com

---

## High Rate Limit / Suspicious Login Activity

Signs: spike in 429s in logs, unusual login attempts.

1. `grep -i "429\|rate limit" /logs` (or check Sentry)
2. If single IP attacking: block at reverse proxy / Cloudflare
3. If legitimate users locked out: temporarily set `RATE_LIMIT_LOGIN_PER_MINUTE=30`
4. Switch to Redis backend if still on memory: `RATE_LIMIT_BACKEND=redis`
5. Monitor for 1h after incident

---

## High 500 Error Rate

1. Check Sentry for new error groups
2. `docker compose -p bulk-edit logs backend --tail=200`
3. Common: DB migration not run after deploy → run `alembic upgrade head`
4. If bug deployed: roll back (see Rollback Procedure)

---

## Failed Scheduled Jobs

1. Admin Dashboard → System tab → recent_failed_scheduled_runs
2. Check backend logs for job failure stack traces
3. Scheduled jobs are safe to re-run — they never auto-write to Etsy without user confirmation
4. If bulk edit job stuck in "processing": manually set status to "failed" in DB

---

## Admin Locked Out

Superuser cannot log in.

1. Verify `.local-superusers.env` credentials are correct
2. Restart backend to re-run seed: `docker compose -p bulk-edit restart backend`
3. Check user in DB:
   ```sql
   SELECT email, is_superuser, is_active FROM users WHERE is_superuser = true;
   ```
4. If user disabled accidentally: `UPDATE users SET is_active = true WHERE email = 'admin@example.com';`

---

## Rollback Procedure

Before each deploy, tag the current image:
```bash
docker tag bulk-edit-backend:latest bulk-edit-backend:prev
docker tag bulk-edit-frontend:latest bulk-edit-frontend:prev
```

To roll back after a failed deploy:
```bash
docker tag bulk-edit-backend:prev bulk-edit-backend:latest
docker tag bulk-edit-frontend:prev bulk-edit-frontend:latest
docker compose -p bulk-edit up -d
```

**DB migrations:** Forward only. If rollback requires a DB schema change, write a manual down-migration and apply it before rolling back the app.

Notify affected users if downtime > 5 minutes.

---

## Secret Rotation

### JWT_SECRET

Rotating invalidates all active sessions — users must log in again.

1. `python -c "import secrets; print(secrets.token_hex(64))"`
2. Update `JWT_SECRET` in production env
3. Restart backend
4. Monitor for unexpected 401 errors

### ENCRYPTION_KEY

Used for Etsy token encryption at rest. Rotating requires re-encrypting all stored tokens.

**Do NOT rotate without an encryption migration script.** Contact engineering team.

### Stripe Keys

1. Regenerate in Stripe Dashboard
2. Update `STRIPE_SECRET_KEY` and restart backend
3. `STRIPE_WEBHOOK_SECRET` is separate — regenerate in webhook settings if compromised

### Etsy Credentials

1. Regenerate in Etsy Developer Portal
2. All connected shops must re-authorize via `/shops` after client secret rotation

### AI Provider Keys

1. Rotate in OpenAI/Anthropic console
2. Update `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` and restart backend
3. No user sessions are affected — AI keys are server-side only
