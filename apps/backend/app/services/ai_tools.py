"""
AI listing optimization service.
AI output is NEVER written to Etsy directly.
Flow: create session → run (AI generates suggestions) → user accepts/rejects → convert to BulkEditSession.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.plans import get_plan_limits
from app.models.ai_session import AISession
from app.models.ai_suggestion import AISuggestion
from app.models.ai_usage_log import AIUsageLog
from app.models.bulk_edit_change import BulkEditChange
from app.models.bulk_edit_session import BulkEditSession
from app.models.listing import Listing
from app.models.subscription import Subscription
from app.models.usage_counter import UsageCounter
from app.services.billing import (
    ensure_subscription_exists,
    get_or_create_usage,
    _current_period_key,
)
from app.services.ai_provider import get_provider, AIProviderError
from app.services.ai_prompts import (
    build_title_prompt,
    build_description_prompt,
    build_tags_prompt,
    build_alt_text_prompt,
    build_seo_score_prompt,
)


class AIToolsError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def assert_ai_usage_allowed(org_id: str, db: AsyncSession) -> None:
    from app.core.plans import VALID_PAID_PLANS
    sub = await ensure_subscription_exists(org_id, db)
    if sub.plan not in VALID_PAID_PLANS:
        raise AIToolsError("AI tools require a paid plan. Upgrade to access AI features.", 402)
    limits = get_plan_limits(sub.plan)
    limit = limits.get("ai_credits_per_month", 0)
    counter = await get_or_create_usage(org_id, db)
    if counter.ai_credits_used >= limit:
        raise AIToolsError(
            f"AI credit limit reached ({limit}/month). Upgrade your plan for more credits.", 402
        )


async def _get_listing_context(listing_id: str, org_id: str, db: AsyncSession) -> dict:
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.organization_id == org_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise AIToolsError("Listing not found", 404)
    return {
        "title": listing.title or "",
        "description": listing.description or "",
        "tags": listing.tags or [],
        "materials": listing.materials or [],
        "taxonomy_id": listing.taxonomy_id,
    }


async def create_ai_session(
    org_id: str,
    user_id: str,
    listing_id: str,
    tool: str,
    extra_context: dict,
    db: AsyncSession,
) -> AISession:
    listing_context = await _get_listing_context(listing_id, org_id, db)
    input_payload = {**listing_context, **extra_context}
    session = AISession(
        organization_id=org_id,
        created_by_user_id=user_id,
        listing_id=listing_id,
        tool=tool,
        status="pending",
        input_payload=input_payload,
        ai_provider=settings.AI_PROVIDER,
        ai_model=_model_for_provider(),
    )
    db.add(session)
    await db.flush()
    await db.commit()
    result2 = await db.execute(
        select(AISession).where(AISession.id == session.id)
        .options(selectinload(AISession.suggestions))
    )
    return result2.scalar_one()


def _model_for_provider() -> str:
    p = settings.AI_PROVIDER.lower()
    if p == "openai":
        return settings.OPENAI_MODEL
    if p == "anthropic":
        return settings.ANTHROPIC_MODEL
    return "mock"


def _build_prompt(tool: str, context: dict) -> tuple[str, str]:
    """Returns (prompt, schema_name)."""
    if tool == "title":
        return build_title_prompt(context), "title"
    if tool == "description":
        return build_description_prompt(context), "description"
    if tool == "tags":
        return build_tags_prompt(context), "tags"
    if tool == "alt_text":
        return build_alt_text_prompt(context), "alt_text"
    if tool == "seo_score":
        return build_seo_score_prompt(context), "seo_score"
    raise AIToolsError(f"Unknown tool: {tool}", 400)


def _extract_suggestions(tool: str, output: dict) -> list[dict[str, Any]]:
    """Extract field/value/reasoning from raw AI output."""
    if tool == "title":
        return [{"field": "title", "value": output.get("suggested_title", ""), "reasoning": output.get("reasoning")}]
    if tool == "description":
        return [{"field": "description", "value": output.get("suggested_description", ""), "reasoning": output.get("reasoning")}]
    if tool == "tags":
        return [{"field": "tags", "value": output.get("suggested_tags", []), "reasoning": output.get("reasoning")}]
    if tool == "alt_text":
        return [{"field": "alt_text", "value": output.get("suggested_alt_text", ""), "reasoning": output.get("reasoning")}]
    if tool == "seo_score":
        return [{"field": "seo_score", "value": output, "reasoning": None}]
    return []


async def run_ai_session(session_id: str, org_id: str, db: AsyncSession) -> AISession:
    result = await db.execute(
        select(AISession).where(AISession.id == session_id, AISession.organization_id == org_id)
        .options(selectinload(AISession.suggestions))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise AIToolsError("Session not found", 404)
    if session.status not in ("pending", "failed"):
        raise AIToolsError(f"Session is already {session.status}", 400)

    await assert_ai_usage_allowed(org_id, db)

    session.status = "running"
    db.add(session)
    await db.flush()

    provider = get_provider()
    usage_status = "success"
    try:
        prompt, schema_name = _build_prompt(session.tool, session.input_payload)
        output = await provider.generate_json(prompt, schema_name, session.input_payload)
        suggestions_data = _extract_suggestions(session.tool, output)

        for s_data in suggestions_data:
            suggestion = AISuggestion(
                organization_id=org_id,
                ai_session_id=session.id,
                listing_id=session.listing_id,
                field=s_data["field"],
                suggested_value=s_data["value"],
                reasoning=s_data.get("reasoning"),
                status="pending",
            )
            db.add(suggestion)

        session.status = "completed"
        session.suggestion_count = len(suggestions_data)

    except (AIProviderError, Exception) as exc:
        session.status = "failed"
        session.error_message = str(exc) if isinstance(exc, AIProviderError) else "AI request failed"
        usage_status = "error"
    finally:
        counter = await get_or_create_usage(org_id, db)
        counter.ai_credits_used += 1
        db.add(counter)

        log = AIUsageLog(
            organization_id=org_id,
            ai_session_id=session.id,
            tool=session.tool,
            provider=settings.AI_PROVIDER,
            model=_model_for_provider(),
            credits_used=1,
            status=usage_status,
        )
        db.add(log)
        db.add(session)
        await db.commit()
        await db.refresh(session)

    result2 = await db.execute(
        select(AISession).where(AISession.id == session_id)
        .options(selectinload(AISession.suggestions))
    )
    return result2.scalar_one()


async def get_ai_session(session_id: str, org_id: str, db: AsyncSession) -> AISession:
    result = await db.execute(
        select(AISession).where(AISession.id == session_id, AISession.organization_id == org_id)
        .options(selectinload(AISession.suggestions))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise AIToolsError("Session not found", 404)
    return session


async def list_ai_sessions(
    org_id: str,
    db: AsyncSession,
    listing_id: str | None = None,
    tool: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AISession], int]:
    q = select(AISession).where(AISession.organization_id == org_id)
    if listing_id:
        q = q.where(AISession.listing_id == listing_id)
    if tool:
        q = q.where(AISession.tool == tool)
    total_r = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_r.scalar_one()
    q = q.order_by(AISession.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    q = q.options(selectinload(AISession.suggestions))
    rows = await db.execute(q)
    return list(rows.scalars().all()), total


async def accept_suggestion(suggestion_id: str, org_id: str, db: AsyncSession) -> AISuggestion:
    result = await db.execute(
        select(AISuggestion).where(AISuggestion.id == suggestion_id, AISuggestion.organization_id == org_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise AIToolsError("Suggestion not found", 404)
    if s.status not in ("pending",):
        raise AIToolsError(f"Suggestion already {s.status}", 400)
    s.status = "accepted"
    s.accepted_at = datetime.now(timezone.utc)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


async def reject_suggestion(suggestion_id: str, org_id: str, db: AsyncSession) -> AISuggestion:
    result = await db.execute(
        select(AISuggestion).where(AISuggestion.id == suggestion_id, AISuggestion.organization_id == org_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise AIToolsError("Suggestion not found", 404)
    if s.status not in ("pending",):
        raise AIToolsError(f"Suggestion already {s.status}", 400)
    s.status = "rejected"
    s.rejected_at = datetime.now(timezone.utc)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


async def convert_to_bulk_edit(
    session_id: str,
    org_id: str,
    user_id: str,
    db: AsyncSession,
) -> BulkEditSession:
    """Convert accepted suggestions into a BulkEditSession. AI never writes to Etsy."""
    result = await db.execute(
        select(AISession).where(AISession.id == session_id, AISession.organization_id == org_id)
        .options(selectinload(AISession.suggestions))
    )
    ai_session = result.scalar_one_or_none()
    if not ai_session:
        raise AIToolsError("Session not found", 404)
    if ai_session.status != "completed":
        raise AIToolsError("Session must be completed before converting", 400)

    accepted = [s for s in ai_session.suggestions if s.status == "accepted"]
    if not accepted:
        raise AIToolsError("No accepted suggestions to convert", 400)

    listing_id = ai_session.listing_id
    if not listing_id:
        raise AIToolsError("Session has no listing associated", 400)

    bulk_session = BulkEditSession(
        organization_id=org_id,
        created_by_user_id=user_id,
        name=f"AI: {ai_session.tool} suggestions",
        status="draft",
        selected_listing_ids=[listing_id],
        selected_count=1,
        change_count=len(accepted),
    )
    db.add(bulk_session)
    await db.flush()

    op_map = {
        "title": "set",
        "description": "set",
        "tags": "set",
        "alt_text": "set",
    }

    for s in accepted:
        change = BulkEditChange(
            bulk_edit_session_id=bulk_session.id,
            listing_id=listing_id,
            field_name=s.field,
            operation=op_map.get(s.field, "set"),
            new_value=s.suggested_value,
            validation_status="pending",
        )
        db.add(change)
        s.converted_to_session_id = bulk_session.id
        db.add(s)

    await db.commit()
    await db.refresh(bulk_session)
    return bulk_session


async def get_ai_usage(org_id: str, db: AsyncSession) -> dict:
    sub = await ensure_subscription_exists(org_id, db)
    limits = get_plan_limits(sub.plan)
    limit = limits.get("ai_credits_per_month", 0)
    counter = await get_or_create_usage(org_id, db)
    period = _current_period_key()
    return {
        "ai_credits_used": counter.ai_credits_used,
        "ai_credits_limit": limit,
        "period_key": period,
    }
