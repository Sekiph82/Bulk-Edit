# Database Migration Guide

## Overview

Bulk-Edit uses Alembic for database schema migrations. Migrations run automatically on backend startup in development (Docker), but **must be applied manually and verified in staging/production** before deploying new application code.

## Current Migration State

```bash
# Show which migration is currently applied
cd apps/backend
alembic current

# Show all pending migrations
alembic heads

# Full migration history
alembic history --verbose
```

## Migrations Reference

| Revision | Description |
|---|---|
| 0001 | Initial schema (users, organizations, members) |
| 0002 | Billing (subscriptions, billing_events, usage_counters) |
| 0003 | Etsy OAuth (etsy_shops, etsy_tokens, etsy_oauth_states) |
| 0004 | Listings (listings, listing_images, listing_videos, listing_variations, sync_jobs) |
| 0005 | Bulk edit (bulk_edit_sessions, bulk_edit_changes, bulk_edit_preview_items) |
| 0006 | Apply/revert infrastructure (listing_backup_snapshots, bulk_edit_apply_jobs, bulk_edit_apply_results, audit_logs) |
| 0007 | Magic revert (revert_jobs, revert_results) |
| 0008 | Media bulk edit (bulk_edit_media_jobs, bulk_edit_media_results, listing_media_backup_snapshots) |
| 0009 | Variation bulk edit (bulk_edit_variation_jobs, bulk_edit_variation_preview_items, bulk_edit_variation_results, listing_variation_backup_snapshots) |
| 0010 | AI tools (ai_sessions, ai_suggestions, ai_usage_logs) |
| 0011 | CSV import/export (csv_jobs, csv_rows) + target_listing_ids on bulk_edit_changes |
| 0012 | Dynamic pricing (dynamic_pricing_jobs, dynamic_pricing_recommendations) |
| 0013 | Scheduled jobs (scheduled_jobs, scheduled_job_runs) |

## Applying Migrations

### Development (Docker Compose)

Migrations run automatically on backend startup via the FastAPI lifespan hook. No manual step needed.

### Staging / Production

**Always backup before migrating:**

```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

Apply migrations:

```bash
cd apps/backend
alembic upgrade head
```

Verify:

```bash
alembic current   # Should show latest revision hash
curl $BACKEND_URL/api/v1/health/ready  # Should return {"status":"ready"}
```

## Rolling Back

**Warning:** Rolling back is rarely safe if new application code has already run against the new schema — new rows may reference columns that the downgrade removes. Prefer restoring from a backup.

If you must roll back one step:

```bash
alembic downgrade -1
```

Check that the migration has a `downgrade()` implementation before attempting. Many Bulk-Edit migrations are upgrade-only.

## Migration Safety Rules

1. **Backup first.** Always `pg_dump` before `alembic upgrade head` in production.
2. **Stage first.** Apply and verify on staging before production.
3. **No destructive migrations without review.** Dropping columns, tables, or constraints requires explicit approval.
4. **Test on production-scale data.** Large `ALTER TABLE` statements can lock tables. Test with a snapshot of production data when possible.
5. **Never edit a committed migration.** Create a new one instead.
6. **Zero-downtime pattern.** For large tables, add nullable columns first (no table rewrite), backfill data in a background job, then add the NOT NULL constraint separately.

## Post-Migration Smoke Test

```bash
# 1. Migration state
alembic current

# 2. Health probe
curl $BACKEND_URL/api/v1/health/ready

# 3. Backend tests
python -m pytest --tb=short -q

# 4. Login test
curl -s -X POST $BACKEND_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"YOUR_TEST_USER","password":"..."}' | python3 -m json.tool
```

## If Migration Fails

1. **Do not restart the backend repeatedly** — each restart re-runs migrations and may apply partial state again.
2. Note the exact error from `alembic upgrade head` output.
3. If data may be corrupted, restore from your pre-migration backup immediately.
4. Fix the migration file on a clean local DB and re-test.
5. Re-apply on staging after confirming the fix.
