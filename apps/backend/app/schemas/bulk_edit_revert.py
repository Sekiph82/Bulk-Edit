from datetime import datetime
from typing import Any
from pydantic import BaseModel


class RevertJobOut(BaseModel):
    id: str
    organization_id: str
    bulk_edit_session_id: str
    apply_job_id: str
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


class RevertResultOut(BaseModel):
    id: str
    organization_id: str
    revert_job_id: str
    apply_job_id: str
    bulk_edit_session_id: str
    listing_id: str
    etsy_listing_id: str
    backup_snapshot_id: str | None
    status: str
    request_payload: Any | None
    response_payload: Any | None
    error_message: str | None
    attempted_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RevertJobWithResultsOut(BaseModel):
    job: RevertJobOut
    results: list[RevertResultOut]


class RevertResultPageOut(BaseModel):
    items: list[RevertResultOut]
    page: int
    per_page: int
    total: int
    revert_job_id: str
