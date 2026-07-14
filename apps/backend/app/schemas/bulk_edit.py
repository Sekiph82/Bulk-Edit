from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Any


class BulkEditSessionCreateRequest(BaseModel):
    listing_ids: list[str]
    name: str | None = None

    @field_validator("listing_ids")
    @classmethod
    def must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("listing_ids must not be empty")
        return list(dict.fromkeys(v))  # deduplicate preserving order


class BulkEditSessionResponse(BaseModel):
    id: str
    organization_id: str
    created_by_user_id: str | None
    name: str | None
    status: str
    selected_listing_ids: Any
    selected_count: int
    change_count: int
    preview_generated_at: datetime | None
    applied_at: datetime | None
    canceled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BulkEditChangeCreateRequest(BaseModel):
    field_name: str
    operation: str
    operation_value: Any = None


class BulkEditChangeResponse(BaseModel):
    id: str
    bulk_edit_session_id: str
    listing_id: str | None
    field_name: str
    operation: str
    old_value: Any
    new_value: Any
    operation_value: Any
    validation_status: str
    validation_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BulkEditPreviewSummary(BaseModel):
    selected_count: int
    preview_items: int
    valid: int
    warning: int
    invalid: int
    stale_listing_count: int = 0


class BulkEditPreviewGenerateResponse(BaseModel):
    session: BulkEditSessionResponse
    summary: BulkEditPreviewSummary


class BulkEditPreviewItemResponse(BaseModel):
    id: str
    bulk_edit_session_id: str
    listing_id: str
    listing_title: str | None
    before_data: Any
    after_data: Any
    diff: Any
    validation_status: str
    validation_messages: Any
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BulkEditPreviewPageResponse(BaseModel):
    items: list[BulkEditPreviewItemResponse]
    page: int
    per_page: int
    total: int
    session_id: str


class BulkEditSessionDetailResponse(BulkEditSessionResponse):
    changes: list[BulkEditChangeResponse]
    preview_item_count: int
