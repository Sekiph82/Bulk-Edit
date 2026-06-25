from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


VALID_OPERATION_TYPES = {
    "set_variation_price",
    "adjust_variation_price_percent",
    "adjust_variation_price_fixed",
    "set_variation_quantity",
    "adjust_variation_quantity_fixed",
    "set_variation_sku",
    "replace_variation_sku_text",
    "set_variation_availability",
}


class VariationJobCreate(BaseModel):
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


class VariationJobOut(BaseModel):
    id: str
    organization_id: str
    created_by_user_id: str | None
    operation_type: str
    operation_payload: Any | None
    selected_listing_ids: Any | None
    status: str
    selected_count: int
    preview_count: int
    success_count: int
    failure_count: int
    skipped_count: int
    preview_generated_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VariationPreviewItemOut(BaseModel):
    id: str
    organization_id: str
    variation_job_id: str
    listing_id: str
    etsy_listing_id: str
    listing_title: str | None
    before_variations: Any
    after_variations: Any
    diff: Any
    validation_status: str
    validation_messages: Any | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VariationPreviewPageOut(BaseModel):
    items: list[VariationPreviewItemOut]
    page: int
    per_page: int
    total: int
    variation_job_id: str


class VariationResultOut(BaseModel):
    id: str
    organization_id: str
    variation_job_id: str
    listing_id: str
    etsy_listing_id: str
    status: str
    request_payload: Any | None
    response_payload: Any | None
    error_message: str | None
    attempted_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VariationResultPageOut(BaseModel):
    items: list[VariationResultOut]
    page: int
    per_page: int
    total: int
    variation_job_id: str


class VariationBackupSnapshotOut(BaseModel):
    id: str
    organization_id: str
    variation_job_id: str | None
    listing_id: str
    etsy_listing_id: str
    snapshot_type: str
    local_variations_snapshot: Any | None
    etsy_inventory_snapshot: Any | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
