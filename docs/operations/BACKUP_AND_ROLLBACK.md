# Backup and Rollback Guide

## Database Backup

### Managed Postgres (Recommended)

Use your hosting platform's automated backup:

| Platform | Backup Type | Notes |
|---|---|---|
| AWS RDS | Automated snapshots | Enable in settings; point-in-time recovery |
| Railway | Daily backups | Retained 7 days on paid plans |
| Neon | Branch snapshots | Point-in-time recovery |
| Supabase | Daily backups | Point-in-time recovery on Pro |

### Manual pg_dump

```bash
# Full backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup (recommended)
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore from backup
psql $DATABASE_URL < backup_20260101_120000.sql
# or
gunzip -c backup_20260101_120000.sql.gz | psql $DATABASE_URL
```

### Encryption

Backups contain user data. Encrypt before storing externally:

```bash
pg_dump $DATABASE_URL | gzip | gpg --symmetric --cipher-algo AES256 -o backup.sql.gz.gpg
```

### Retention Policy

| Frequency | Retain |
|---|---|
| Daily | 7 days |
| Weekly | 4 weeks |
| Monthly | 12 months |

### Backup Verification

Periodically restore a backup to a test database and verify:

```bash
createdb bulk_edit_restore_test
pg_restore -d bulk_edit_restore_test backup_20260101.sql
psql bulk_edit_restore_test -c "SELECT COUNT(*) FROM users;"
dropdb bulk_edit_restore_test
```

---

## Redis Backup

Redis in Bulk-Edit stores:

| Data | Loss Impact |
|---|---|
| Rate limiting counters | Non-critical — counters reset, no data loss |
| Celery task queue | Tasks must be re-queued if lost |

For rate limiting only: Redis persistence is optional. Counters reset harmlessly on restart.

If Celery tasks are active: enable `appendonly yes` in redis.conf and back up the AOF file.

---

## Application Rollback

### Docker Image Rollback

Tag images before deploying:

```bash
docker tag bulk-edit-backend:latest bulk-edit-backend:prev
docker tag bulk-edit-frontend:latest bulk-edit-frontend:prev
```

Roll back:

```bash
docker tag bulk-edit-backend:prev bulk-edit-backend:latest
docker tag bulk-edit-frontend:prev bulk-edit-frontend:latest
docker compose -p bulk-edit up -d
```

### GitHub Actions SHA-Tagged Images

If CI publishes images with commit SHA tags:

```bash
# Roll back to previous commit
IMAGE_TAG=<previous-commit-sha> docker compose -f docker-compose.prod.example.yml up -d
```

### Database Schema Rollback

Only attempt if you have confirmed the migration's `downgrade()` function is safe.
See [MIGRATIONS.md](MIGRATIONS.md) for downgrade commands.

**Warning:** Rolling back the schema after new application code has written new records is dangerous — you risk foreign key violations or missing column errors.

When in doubt: restore the full database from backup rather than attempting a schema downgrade.

### Environment Variable Rollback

If a bad env var was pushed:

1. Fix the value in your hosting platform's settings
2. Trigger a redeploy or restart the service
3. Verify: `curl $BACKEND_URL/api/v1/health/ready`

---

## Stripe and Etsy Considerations

### Stripe

If the webhook endpoint URL changes:
1. Register the new URL in Stripe Dashboard → Developers → Webhooks
2. Remove or disable the old endpoint after the new one is verified
3. Stripe retries failed webhook deliveries for 72 hours — events are not lost during brief downtime

### Etsy OAuth

If `ETSY_REDIRECT_URI` changes:
1. Update the redirect URI in Etsy Developer Portal → App settings
2. Existing connected shops retain their stored (encrypted) tokens — shop connections are not affected

---

## Emergency Rollback Checklist

When something breaks in production:

- [ ] 1. Stop writes if possible — disable scheduled jobs in the Admin → Scheduled Jobs tab
- [ ] 2. Take an immediate DB snapshot before any destructive changes
- [ ] 3. Preserve logs: `docker compose -p bulk-edit logs --no-color > incident_$(date +%Y%m%d_%H%M%S).log`
- [ ] 4. Identify root cause from logs
- [ ] 5. Roll back app image to last known-good version
- [ ] 6. Run `alembic current` to verify migration state
- [ ] 7. Restart backend: `docker compose -p bulk-edit restart backend`
- [ ] 8. Verify: `curl $BACKEND_URL/api/v1/health/ready`
- [ ] 9. Verify login works: `curl -X POST $BACKEND_URL/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"...","password":"..."}'`
- [ ] 10. Verify admin dashboard loads for superuser
- [ ] 11. Notify affected users if downtime exceeded 5 minutes
- [ ] 12. Write incident report and add to DECISIONS.md

---

## Related Docs

- [MIGRATIONS.md](MIGRATIONS.md) — Alembic migration commands
- [RUNBOOK.md](RUNBOOK.md) — Incident response scenarios
- [MONITORING.md](MONITORING.md) — Health endpoints and alerting
