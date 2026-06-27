"""Usage — credit and bulk edit usage summary."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_org_id, require_active_user

router = APIRouter(prefix="/usage", tags=["usage"])


class UsageSummary(BaseModel):
    ai_credits_used: int
    ai_credits_limit: int
    bulk_edits_used: int
    bulk_edits_limit: int
    period: str
    note: str


@router.get("/summary", response_model=UsageSummary)
async def get_usage_summary(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
):
    return UsageSummary(
        ai_credits_used=0,
        ai_credits_limit=100,
        bulk_edits_used=0,
        bulk_edits_limit=500,
        period="current_month",
        note="Usage tracking will reflect live data once billing integration is complete.",
    )
