"""Shop Insights — listing performance analytics summary."""

from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.deps import get_current_org_id, require_active_user

router = APIRouter(prefix="/insights", tags=["insights"])


class InsightSummary(BaseModel):
    date_from: str
    date_to: str
    total_views: int
    total_favourites: int
    total_revenue_cents: int
    currency: str
    listing_count: int
    note: str


@router.get("/summary", response_model=InsightSummary)
async def get_insights_summary(
    date_from: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
):
    """Return aggregated insights for the org's shop. Live Etsy analytics require Etsy API access."""
    today = date.today()
    resolved_to = date.fromisoformat(date_to) if date_to else today
    resolved_from = date.fromisoformat(date_from) if date_from else today - timedelta(days=30)

    return InsightSummary(
        date_from=resolved_from.isoformat(),
        date_to=resolved_to.isoformat(),
        total_views=0,
        total_favourites=0,
        total_revenue_cents=0,
        currency="USD",
        listing_count=0,
        note="Analytics data will appear here once your Etsy shop is connected and synced.",
    )
