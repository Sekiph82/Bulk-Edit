from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ScheduledJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    job_type: str
    schedule_type: str
    schedule_payload: dict[str, Any]
    job_payload: dict[str, Any] | None = None
    timezone: str = "UTC"
    max_runs: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ScheduledJobUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    job_payload: dict[str, Any] | None = None
    schedule_payload: dict[str, Any] | None = None
    timezone: str | None = None
    max_runs: int | None = None
    ends_at: datetime | None = None


class ScheduledJobOut(BaseModel):
    id: str
    organization_id: str
    created_by_user_id: str | None
    name: str
    job_type: str
    status: str
    schedule_type: str
    schedule_payload: dict[str, Any]
    job_payload: dict[str, Any] | None
    timezone: str
    next_run_at: datetime | None
    last_run_at: datetime | None
    run_count: int
    failure_count: int
    max_runs: int | None
    starts_at: datetime | None
    ends_at: datetime | None
    disabled_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduledJobRunOut(BaseModel):
    id: str
    organization_id: str
    scheduled_job_id: str
    triggered_by_user_id: str | None
    trigger_type: str
    job_type: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    output_payload: dict[str, Any] | None
    error_message: str | None
    created_resource_type: str | None
    created_resource_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunDueResponse(BaseModel):
    executed: int
    run_ids: list[str]
