from datetime import datetime
from typing import Any
from pydantic import BaseModel


class ApplyJobOut(BaseModel):
    id: str
    organization_id: str
    bulk_edit_session_id: str
    created_by_user_id: str | None
    status: str
    canonical_state: str | None = None
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


class ApplyJobHistoryItemOut(BaseModel):
    """Safe, decorated apply-job summary for org-wide history views (Magic
    Revert History, Activity & Audit) — adds revert-eligibility on top of the
    plain ApplyJobOut fields, without exposing request/response payloads."""
    id: str
    bulk_edit_session_id: str
    status: str
    canonical_state: str | None = None
    total_items: int
    success_count: int
    failure_count: int
    skipped_count: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    can_revert: bool = False
    revert_blocked_reason: str | None = None
    revert_job_id: str | None = None
    revert_status: str | None = None

    model_config = {"from_attributes": True}


class ApplyJobHistoryPageOut(BaseModel):
    items: list[ApplyJobHistoryItemOut]
    page: int
    per_page: int
    total: int


class FieldAuditLogOut(BaseModel):
    """M06.04 per-item write audit trail — one row per (listing, field) this
    app has written or attempted to write. Read-only, safe to export later;
    export itself is not built this sprint (API-ready shape only)."""
    id: str
    organization_id: str
    user_id: str | None
    entity_id: str | None  # internal listing id
    listing_title: str | None = None  # decorated in from Listing.title, not a real AuditLog column
    field_name: str | None
    result_status: str | None
    apply_job_id: str | None
    revert_job_id: str | None
    revert_status: str | None
    message: str | None
    extra_data: Any | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FieldAuditLogPageOut(BaseModel):
    items: list[FieldAuditLogOut]
    page: int
    per_page: int
    total: int
