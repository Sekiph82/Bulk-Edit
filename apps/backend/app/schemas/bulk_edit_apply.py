from datetime import datetime
from typing import Any
from pydantic import BaseModel


class ApplyJobOut(BaseModel):
    id: str
    organization_id: str
    bulk_edit_session_id: str
    created_by_user_id: str | None
    status: str
    total_items: int
    success_count: int
    failure_count: int
    skipped_count: int
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplyResultOut(BaseModel):
    id: str
    organization_id: str
    apply_job_id: str
    bulk_edit_session_id: str
    listing_id: str
    etsy_listing_id: str
    status: str
    request_payload: Any | None
    response_payload: Any | None
    error_message: str | None
    backup_snapshot_id: str | None
    attempted_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BackupSnapshotOut(BaseModel):
    id: str
    organization_id: str
    bulk_edit_session_id: str | None
    listing_id: str
    etsy_shop_id: str
    etsy_listing_id: str
    snapshot_type: str
    snapshot_data: Any
    created_by_user_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplyJobWithResultsOut(BaseModel):
    job: ApplyJobOut
    results: list[ApplyResultOut]
