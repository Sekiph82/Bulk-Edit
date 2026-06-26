from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, field_validator

VALID_TOOLS = {"title", "description", "tags", "alt_text", "seo_score"}


class AISessionCreate(BaseModel):
    listing_id: str
    tool: str
    extra_context: dict[str, Any] = {}

    @field_validator("tool")
    @classmethod
    def tool_must_be_valid(cls, v: str) -> str:
        if v not in VALID_TOOLS:
            raise ValueError(f"tool must be one of: {', '.join(sorted(VALID_TOOLS))}")
        return v


class AISuggestionOut(BaseModel):
    id: str
    organization_id: str
    ai_session_id: str
    listing_id: Optional[str]
    field: str
    suggested_value: Any
    reasoning: Optional[str]
    status: str
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    converted_to_session_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AISessionOut(BaseModel):
    id: str
    organization_id: str
    created_by_user_id: Optional[str]
    listing_id: Optional[str]
    tool: str
    status: str
    input_payload: dict[str, Any]
    ai_provider: Optional[str]
    ai_model: Optional[str]
    error_message: Optional[str]
    suggestion_count: int
    created_at: datetime
    updated_at: datetime
    suggestions: list[AISuggestionOut] = []

    model_config = {"from_attributes": True}


class AISessionPageOut(BaseModel):
    items: list[AISessionOut]
    total: int
    page: int
    page_size: int


class AIUsageOut(BaseModel):
    ai_credits_used: int
    ai_credits_limit: int
    period_key: str


class ConvertToSessionOut(BaseModel):
    bulk_edit_session_id: str
    message: str
