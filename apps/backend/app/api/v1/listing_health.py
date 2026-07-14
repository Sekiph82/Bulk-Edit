"""
Listing Health Score API.
Rule-based scoring. AI suggestions optional (feature-gated).
Never writes to Etsy.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from collections import Counter

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_active_user
from app.db.session import get_db
from app.models.listing import Listing
from app.models.listing_image import ListingImage
from app.models.listing_video import ListingVideo
from app.models.listing_cost import ListingCost
from app.schemas.listing_health import (
    AISuggestionsOut,
    HealthIssueOut,
    ListingHealthDetail,
    ListingHealthPage,
    ListingHealthRow,
    ListingHealthSummary,
)
from app.services.listing_health import score_listing

router = APIRouter(prefix="/listing-health", tags=["listing-health"])


def _price_float(listing: Listing) -> Optional[float]:
    if listing.price_amount is not None and listing.price_divisor:
        return listing.price_amount / listing.price_divisor
    return None


def _issues_to_out(issues: list) -> list[HealthIssueOut]:
    return [
        HealthIssueOut(
            category=i.category,
            severity=i.severity,
            field=i.field,
            message=i.message,
            recommended_fix=i.recommended_fix,
            ai_can_help=i.ai_can_help,
        )
        for i in issues
    ]


async def _score_listings(
    listings: list[Listing],
    photo_counts: dict[str, int],
    video_flags: dict[str, bool],
    cost_ids: set[str],
) -> list[dict]:
    scored = []
    for listing in listings:
        tags: list = listing.tags if isinstance(listing.tags, list) else []
        photo_count = photo_counts.get(listing.id, 0)
        has_video = video_flags.get(listing.id, False)
        has_cost = listing.id in cost_ids
        price = _price_float(listing)

        result = score_listing(
            listing_id=listing.id,
            title=listing.title,
            description=listing.description,
            tags=tags,
            photo_count=photo_count,
            has_video=has_video,
            price=price,
            has_cost_data=has_cost,
        )
        result["listing"] = listing
        result["price"] = price
        scored.append(result)
    return scored


async def _fetch_photo_counts(db: AsyncSession, listing_ids: list[str]) -> dict[str, int]:
    if not listing_ids:
        return {}
    rows = await db.execute(
        select(ListingImage.listing_id, ListingImage.id)
        .where(ListingImage.listing_id.in_(listing_ids))
    )
    counts: dict[str, int] = {}
    for row in rows.all():
        lid = row[0]
        counts[lid] = counts.get(lid, 0) + 1
    return counts


async def _fetch_video_flags(db: AsyncSession, listing_ids: list[str]) -> dict[str, bool]:
    if not listing_ids:
        return {}
    rows = await db.execute(
        select(ListingVideo.listing_id).where(ListingVideo.listing_id.in_(listing_ids))
    )
    return {row[0]: True for row in rows.all()}


async def _fetch_cost_ids(db: AsyncSession, org_id: str, listing_ids: list[str]) -> set[str]:
    if not listing_ids:
        return set()
    rows = await db.execute(
        select(ListingCost.listing_id)
        .where(ListingCost.organization_id == org_id, ListingCost.listing_id.in_(listing_ids))
    )
    return {row[0] for row in rows.all()}


@router.get("/summary", response_model=ListingHealthSummary)
async def get_health_summary(
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    result = await db.execute(select(Listing).where(Listing.organization_id == org_id))
    listings = list(result.scalars().all())

    if not listings:
        return ListingHealthSummary(
            average_score=0.0,
            total_listings=0,
            excellent_count=0,
            good_count=0,
            needs_work_count=0,
            critical_count=0,
            high_priority_count=0,
            top_issue_categories=[],
            last_calculated_at=datetime.now(timezone.utc),
        )

    ids = [l.id for l in listings]
    photo_counts = await _fetch_photo_counts(db, ids)
    video_flags = await _fetch_video_flags(db, ids)
    cost_ids = await _fetch_cost_ids(db, org_id, ids)

    scored = await _score_listings(listings, photo_counts, video_flags, cost_ids)

    total = len(scored)
    scores = [s["score"] for s in scored]
    avg_score = round(sum(scores) / total, 1) if total else 0.0

    excellent = sum(1 for s in scored if s["grade"] == "excellent")
    good = sum(1 for s in scored if s["grade"] == "good")
    needs_work = sum(1 for s in scored if s["grade"] == "needs_work")
    critical = sum(1 for s in scored if s["grade"] == "critical")
    high_prio = sum(1 for s in scored if s["priority"] in ("critical", "high"))

    cat_counter: Counter = Counter()
    for s in scored:
        for issue in s["issues"]:
            if issue.severity in ("critical", "high"):
                cat_counter[issue.category] += 1

    return ListingHealthSummary(
        average_score=avg_score,
        total_listings=total,
        excellent_count=excellent,
        good_count=good,
        needs_work_count=needs_work,
        critical_count=critical,
        high_priority_count=high_prio,
        top_issue_categories=[cat for cat, _ in cat_counter.most_common(5)],
        last_calculated_at=datetime.now(timezone.utc),
    )


@router.get("/listings", response_model=ListingHealthPage)
async def list_health_listings(
    grade: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: str = Query("score_asc"),  # score_asc, score_desc, issue_count_desc, title_asc
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    q = select(Listing).where(Listing.organization_id == org_id)
    if search:
        q = q.where(Listing.title.ilike(f"%{search}%"))

    result = await db.execute(q)
    listings = list(result.scalars().all())

    ids = [l.id for l in listings]
    photo_counts = await _fetch_photo_counts(db, ids)
    video_flags = await _fetch_video_flags(db, ids)
    cost_ids = await _fetch_cost_ids(db, org_id, ids)

    scored = await _score_listings(listings, photo_counts, video_flags, cost_ids)

    if grade:
        scored = [s for s in scored if s["grade"] == grade]
    if priority:
        scored = [s for s in scored if s["priority"] == priority]

    if sort == "score_asc":
        scored.sort(key=lambda s: s["score"])
    elif sort == "score_desc":
        scored.sort(key=lambda s: s["score"], reverse=True)
    elif sort == "issue_count_desc":
        scored.sort(key=lambda s: s["issue_count"], reverse=True)
    elif sort == "title_asc":
        scored.sort(key=lambda s: (s["listing"].title or "").lower())

    total = len(scored)
    offset = (page - 1) * page_size
    page_items = scored[offset: offset + page_size]

    rows = []
    for s in page_items:
        lst: Listing = s["listing"]
        rows.append(ListingHealthRow(
            listing_id=lst.id,
            title=lst.title,
            state=lst.state,
            score=s["score"],
            grade=s["grade"],
            priority=s["priority"],
            issue_count=s["issue_count"],
            top_issues=_issues_to_out(s["top_issues"]),
            photo_count=s["photo_count"],
            tag_count=s["tag_count"],
            has_video=s["has_video"],
            price=s["price"],
            currency=lst.currency_code,
            last_synced_at=lst.last_synced_at,
        ))

    return ListingHealthPage(items=rows, total=total, page=page, page_size=page_size)


@router.get("/listings/{listing_id}", response_model=ListingHealthDetail)
async def get_listing_health(
    listing_id: str,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.organization_id == org_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")

    photo_counts = await _fetch_photo_counts(db, [listing_id])
    video_flags = await _fetch_video_flags(db, [listing_id])
    cost_ids = await _fetch_cost_ids(db, org_id, [listing_id])

    tags: list = listing.tags if isinstance(listing.tags, list) else []
    price = _price_float(listing)

    s = score_listing(
        listing_id=listing_id,
        title=listing.title,
        description=listing.description,
        tags=tags,
        photo_count=photo_counts.get(listing_id, 0),
        has_video=video_flags.get(listing_id, False),
        price=price,
        has_cost_data=listing_id in cost_ids,
    )

    return ListingHealthDetail(
        listing_id=listing_id,
        title=listing.title,
        state=listing.state,
        score=s["score"],
        grade=s["grade"],
        priority=s["priority"],
        issue_count=s["issue_count"],
        top_issues=_issues_to_out(s["top_issues"]),
        all_issues=_issues_to_out(s["issues"]),
        suggested_actions=s["suggested_actions"],
        photo_count=s["photo_count"],
        tag_count=s["tag_count"],
        has_video=s["has_video"],
        price=price,
        currency=listing.currency_code,
        last_synced_at=listing.last_synced_at,
    )


@router.post("/listings/{listing_id}/ai-suggestions", response_model=AISuggestionsOut)
async def get_ai_suggestions(
    listing_id: str,
    org_id: str = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_active_user),
):
    """
    Returns AI suggestions for listing improvement.
    Never writes to Etsy. Suggestions must be reviewed by user before applying.
    Feature-gated: requires paid plan.
    """
    from app.core.config import settings
    from app.services.ai_tools import AIToolsError, assert_ai_usage_allowed

    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.organization_id == org_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")

    # Check if AI is available (provider configured)
    ai_available = settings.AI_PROVIDER != "mock" and (
        settings.is_openai_configured() or settings.is_anthropic_configured()
    )

    if not ai_available:
        return AISuggestionsOut(
            listing_id=listing_id,
            ai_available=False,
            message="AI suggestions are not configured in this environment. Set AI_PROVIDER and API keys to enable.",
        )

    # Etsy compliance gate: this listing's title/description/tags are
    # Etsy-synced data. Do not send them to a live AI provider unless Etsy
    # has authorized it. See ETSY_SUPPORT_QUESTIONS.md Q2.
    if not settings.ALLOW_ETSY_DATA_TO_AI:
        return AISuggestionsOut(
            listing_id=listing_id,
            ai_available=False,
            message=(
                "AI suggestions for synced Etsy listings are temporarily disabled "
                "pending Etsy's confirmation that sharing listing content with an "
                "AI provider is permitted."
            ),
        )

    # Feature gate: paid plan required
    try:
        await assert_ai_usage_allowed(org_id, db)
    except AIToolsError as exc:
        if exc.status_code == 402:
            return AISuggestionsOut(
                listing_id=listing_id,
                ai_available=True,
                message=exc.message,
            )
        raise

    # Call AI provider
    try:
        from app.services.ai_provider import get_provider
        provider = get_provider()
        tags_list: list = listing.tags if isinstance(listing.tags, list) else []
        context = {
            "title": listing.title or "",
            "description": listing.description or "",
            "tags": tags_list,
        }
        result_data = await provider.generate_json(
            prompt=(
                f"Improve this Etsy listing for better search visibility and conversion.\n"
                f"Title: {listing.title or '(none)'}\n"
                f"Tags: {', '.join(str(t) for t in tags_list) or '(none)'}\n"
                f"Description preview: {(listing.description or '')[:200]}\n\n"
                "Return JSON with: improved_title, suggested_tags (list of 13 strings), "
                "improved_description, explanation, confidence (low/medium/high)"
            ),
            schema_name="listing_health",
            context=context,
        )
        return AISuggestionsOut(
            listing_id=listing_id,
            improved_title=result_data.get("improved_title") or result_data.get("suggested_title"),
            suggested_tags=result_data.get("suggested_tags"),
            improved_description=result_data.get("improved_description") or result_data.get("suggested_description"),
            explanation=result_data.get("explanation") or result_data.get("reasoning"),
            confidence=result_data.get("confidence", "medium"),
            ai_available=True,
            message="Suggestions generated. Review before applying — never auto-applied to Etsy.",
        )
    except Exception:
        return AISuggestionsOut(
            listing_id=listing_id,
            ai_available=True,
            message="AI suggestion generation failed. Try again later.",
        )


@router.post("/recalculate")
async def recalculate_health(
    org_id: str = Depends(get_current_org_id),
    _user=Depends(require_active_user),
):
    """Health scores are calculated dynamically. This endpoint confirms recalculation."""
    return {"message": "Health scores are calculated dynamically on each request.", "status": "ok"}
