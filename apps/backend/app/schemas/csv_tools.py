from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class CSVJobOut(BaseModel):
    id: str
    organization_id: str
    user_id: Optional[str]
    job_type: str
    status: str
    filename: Optional[str]
    original_filename: Optional[str]
    row_count: int
    valid_row_count: int
    invalid_row_count: int
    changed_row_count: int
    unchanged_row_count: int
    ignored_column_count: int
    ignored_columns: Optional[list[str]]
    summary: Optional[dict[str, Any]]
    error_message: Optional[str]
    converted_bulk_edit_session_id: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CSVRowOut(BaseModel):
    id: str
    organization_id: str
    csv_job_id: str
    row_number: int
    listing_id: Optional[str]
    etsy_listing_id: Optional[str]
    listing_title: Optional[str]
    raw_data: dict[str, Any]
    normalized_data: Optional[dict[str, Any]]
    diff: Optional[dict[str, Any]]
    status: str
    validation_errors: Optional[list[str]]
    validation_warnings: Optional[list[str]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CSVPreviewPageOut(BaseModel):
    items: list[CSVRowOut]
    total: int
    page: int
    per_page: int
    csv_job_id: str


class CSVConvertRequest(BaseModel):
    ignore_invalid: bool = False


class CSVConvertResponse(BaseModel):
    bulk_edit_session_id: str
    converted_rows: int
    created_changes: int
    message: str


class CSVImportSummaryOut(BaseModel):
    job_id: str
    status: str
    row_count: int
    valid_row_count: int
    invalid_row_count: int
    changed_row_count: int
    unchanged_row_count: int
    ignored_columns: list[str]
    message: str
