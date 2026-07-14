"""
Deletes expired Etsy-derived snapshot/job data past its retention window.
See ETSY_DATA_RETENTION.md for the policy this enforces (30-day cap).

Not wired to a live worker — no Celery worker is deployed yet (see
PROJECT_STATUS.md / docs/operations/WORKERS.md). Invoke via
scripts/run_retention_cleanup.py on an external scheduler (cron, DO App
Platform scheduled job, etc.) until a real worker exists.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing_backup_snapshot import ListingBackupSnapshot
from app.models.listing_media_backup_snapshot import ListingMediaBackupSnapshot
from app.models.listing_variation_backup_snapshot import ListingVariationBackupSnapshot
from app.models.csv_job import CSVJob


async def delete_expired_snapshots(db: AsyncSession) -> dict[str, int]:
    """Deletes all rows whose expires_at has passed. Returns per-table delete counts."""
    now = datetime.now(timezone.utc)
    counts: dict[str, int] = {}
    for model in (
        ListingBackupSnapshot,
        ListingMediaBackupSnapshot,
        ListingVariationBackupSnapshot,
        CSVJob,
    ):
        result = await db.execute(delete(model).where(model.expires_at < now))
        counts[model.__tablename__] = result.rowcount or 0
    await db.commit()
    return counts
