from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


VALID_OPERATION_TYPES = {
    "add_image",
    "replace_image",
    "delete_image",
    "add_video",
    "replace_video",
    "delete_video",
}


class MediaJobCreate(BaseModel):
    listing_ids: list[str]
    operation_type: str
    payload: dict[str, Any] = {}

    @field_validator("listing_ids")
    @classmethod
    def listing_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("listing_ids must not be empty")
        return v

    @field_validator("operation_type")
    @classmethod
    def operation_type_valid(cls, v: str) -> str:
        if v not in VALID_OPERATION_TYPES:
            raise ValueError(f"operation_type must be one of: {', '.join(sorted(VALID_OPERATION_TYPES))}")
        return v


class MediaJobOut(BaseModel):
    id: str
    organization_id: str
    bulk_edit_session_id: str | None
    created_by_user_id: str | None
    operation_type: str
    operation_payload: Any | None
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


class MediaResultOut(BaseModel):
    id: str
    organization_id: str
    media_job_id: str
    listing_id: str
    etsy_listing_id: str
    operation_type: str
    status: str
    before_media: Any | None
    after_media: Any | None
    request_payload: Any | None
    response_payload: Any | None
    error_message: str | None
    attempted_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MediaResultPageOut(BaseModel):
    items: list[MediaResultOut]
    page: int
    per_page: int
    total: int
    media_job_id: str


class MediaBackupSnapshotOut(BaseModel):
    id: str
    organization_id: str
    media_job_id: str | None
    listing_id: str
    etsy_listing_id: str
    snapshot_type: str
    images_snapshot: Any | None
    videos_snapshot: Any | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MediaJobWithResultsOut(MediaJobOut):
    results: list[MediaResultOut] = []
