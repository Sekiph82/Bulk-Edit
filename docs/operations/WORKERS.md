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
