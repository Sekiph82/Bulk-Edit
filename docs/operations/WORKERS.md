# Background Workers

## Current Architecture (Sprint 21)

Bulk-Edit does **not** currently run a Celery worker process. Scheduled jobs are stored in the database as `ScheduledJob` records and executed inline via the FastAPI request cycle. The admin dashboard shows job status and counts.

No separate worker container is needed for the current feature set.

---

## What Scheduled Jobs Currently Do

- Stored in `scheduled_jobs` table with `status`, `schedule_type`, `next_run_at`
- Users create jobs via `/api/v1/scheduled-jobs`
- Jobs execute within the HTTP request or are queued to a simple in-process queue
- Jobs never auto-write to Etsy without explicit user confirmation (safety gate enforced)

---

## Future Celery Architecture (Sprint 22+)

When background task volume warrants a dedicated worker, the recommended setup:

### Dependencies to add

```
celery[redis]==5.4.0
```

### Worker app (apps/backend/app/worker.py)

```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "bulk_edit",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.config_from_object("app.core.celery_config")
```

### Start worker

```bash
celery -A app.worker.celery_app worker --loglevel=info --concurrency=4
```

### Start beat (for scheduled tasks)

```bash
celery -A app.worker.celery_app beat --loglevel=info --scheduler=celery.beat.PersistentScheduler
```

### Docker Compose addition (optional, commented until needed)

```yaml
# worker:
#   build:
#     context: ./apps/backend
#     dockerfile: Dockerfile
#   command: celery -A app.worker.celery_app worker --loglevel=info
#   environment:
#     - REDIS_URL=redis://redis:6379/0
#   depends_on:
#     - redis
#     - postgres
#   restart: unless-stopped
```

### Health check

```bash
celery -A app.worker.celery_app inspect ping
```

---

## Scheduled External Job: Snapshot/CSV Retention Cleanup

`app/services/retention_cleanup.py::delete_expired_snapshots()` deletes rows in `listing_backup_snapshots`, `listing_media_backup_snapshots`, `listing_variation_backup_snapshots`, and `csv_jobs` whose `expires_at` (30 days from creation, see `ETSY_DATA_RETENTION.md`) has passed. Same pattern as `ScheduledJob`'s `run-due` endpoint — no live worker, so this ships as a standalone script:

```bash
# Preview only — reports per-table + total expired-row counts, deletes nothing:
docker compose exec backend python scripts/run_retention_cleanup.py --dry-run

# Actual cleanup — deletes expired rows, prints per-table + total deleted counts:
docker compose exec backend python scripts/run_retention_cleanup.py
```

Both commands print aggregate counts only — no listing content, titles, descriptions, tags, user data, emails, Etsy IDs, or tokens are ever printed. The script exits non-zero on any database/query failure (no error is swallowed) and exits `0` on success. `delete_expired_snapshots` commits once after all four tables' deletes, and re-running it after a successful run is a no-op (each table's `WHERE expires_at < now()` matches nothing left to delete) — safe to run more than once without side effects.

**Production schedule:** deployed as a DigitalOcean App Platform job component named `retention-cleanup` on `bulk-edit-prod-api`, `kind: SCHEDULED`, `schedule.cron: "30 3 * * *"` (03:30 daily; DO Scheduled Jobs run in UTC — there is no timezone override field in the App Platform job spec, confirmed via `doctl apps propose` against the live app). Spec tracked at `ops/app-specs/bulk-edit-prod-api.yaml`. It runs the real (non-dry-run) command, inherits `DATABASE_URL`/`ENVIRONMENT` the same way the existing `migrate` `PRE_DEPLOY` job does, has no public route or domain (job components never get one), and runs as a single instance on the smallest available size (`apps-s-1vcpu-0.5gb`).

Note: DigitalOcean App Platform's job `kind` enum for time-based execution is `SCHEDULED`, not `CRON` — confirmed directly against the API (`doctl apps propose`) after `kind: CRON` was rejected as an unknown enum value. Anything describing this as a "CRON job component" elsewhere in this repo's docs means a `SCHEDULED`-kind DO job configured with a cron expression, not a literal `kind: CRON`.

**First real execution confirmed:** 2026-07-15, 03:31:29–03:31:31 UTC (invocation `afa4c26d-30fa-4a83-ae84-a415c0afacd6`) — clean `COMMIT`, 0 rows deleted across all four tables, no errors. **Second consecutive successful run confirmed:** 2026-07-16, 03:31:30–03:31:33 UTC (invocation `ad207ee4-f05c-4038-b244-6e54bf9fd13a`), phase `SUCCEEDED`. The scheduler is not just configured, it is running successfully on its daily schedule in production.

When a real Celery worker is added (see Future Celery Architecture above), migrate this into a Celery Beat periodic task rather than the DO Scheduled Job.

**Manual recovery:** if the scheduled job is ever paused, deleted, or fails silently, retention is not lost — `expires_at` is stored on every row regardless of whether cleanup has run, and reverts against an expired-but-undeleted snapshot already fail safely with "backup snapshot no longer available" rather than serving stale data. To catch up manually: `doctl apps create-deployment <app-id>` does not trigger a one-off job run; instead run `docker compose exec backend python scripts/run_retention_cleanup.py --dry-run` first to confirm counts are sane, then the same command without `--dry-run` inside the production container (e.g. via `doctl apps console`), or re-deploy after fixing the underlying issue so the next scheduled run catches up on its own.

**Monitoring:** `doctl apps logs` takes the component name as a positional argument, not a `--component` flag, and for a `SCHEDULED` job (not tied to the current deployment the way `PRE_DEPLOY` jobs are) you need the specific invocation ID before it will return anything:

```bash
# 1. Find recent invocations and their status/timestamps:
doctl apps list-job-invocations <app-id> --job-name retention-cleanup \
  --format ID,Jobname,Created,Started,Completed,Phase

# 2. Fetch that invocation's run logs:
doctl apps logs <app-id> retention-cleanup --job-invocation <invocation-id> --type run
```

Or use the DO App Platform console's Activity tab for the app. A failed run exits non-zero and is visible there; it does not silently disappear.

---

## Admin System Health

`GET /api/v1/admin/system-health` returns `"worker_status": "not_configured"` indicating no Celery worker is deployed.

When Celery is added, this field should be updated to `"configured"` and augmented with:
- `worker_active_tasks: int`
- `worker_queued_tasks: int`

---

## Safety Guarantees

Regardless of worker architecture, these safety rules are enforced in code:

- No background task auto-writes to Etsy
- All Etsy writes require: preview → user confirmation → backup snapshot → write → audit log
- AI output is never auto-applied to listings
- Worker failures are logged and surfaced in admin dashboard; they never silently corrupt data
