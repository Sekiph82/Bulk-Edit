"""
Sprint 13 tests: AI listing optimization — sessions, suggestions, accept/reject, convert, usage.

All AI provider calls mocked. No real API calls.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select

from app.services.ai_provider import MockProvider, AIProviderError
from app.services.ai_prompts import (
    build_title_prompt,
    build_description_prompt,
    build_tags_prompt,
    build_alt_text_prompt,
    build_seo_score_prompt,
)

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
SESSIONS_URL = "/api/v1/ai/sessions"
USAGE_URL = "/api/v1/ai/usage"


# ── helpers ───────────────────────────────────────────────────────────────────

async def _register_and_login(client, user: dict) -> str:
    payload = {**user}
    if "organization_name" not in payload:
        payload["organization_name"] = payload.get("full_name", "Org") + " Org"
    await client.post(REGISTER_URL, json=payload)
    r = await client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.json()["access_token"]


async def _get_org_id(db_session) -> str:
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    return result.scalar_one().organization_id


async def _setup_listing(db_session, org_id: str, etsy_id: str = "AI001") -> str:
    from app.models.listing import Listing
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token
    from datetime import datetime, timezone, timedelta

    shop_etsy_id = f"ai_shop_{org_id[:8]}"
    existing = await db_session.execute(
        select(EtsyShop).where(EtsyShop.etsy_shop_id == shop_etsy_id)
    )
    shop = existing.scalar_one_or_none()
    if not shop:
        shop = EtsyShop(
            organization_id=org_id,
            etsy_shop_id=shop_etsy_id,
            shop_name="AI Test Shop",
            is_connected=True,
        )
        db_session.add(shop)
        await db_session.flush()
        token = EtsyToken(
            etsy_shop_id=shop.id,
            access_token_enc=encrypt_token("fake_ai_token"),
            refresh_token_enc=encrypt_token("fake_r"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scopes="listings_r listings_w",
        )
        db_session.add(token)
        await db_session.flush()

    listing = Listing(
        organization_id=org_id,
        etsy_shop_id=shop.id,
        etsy_listing_id=etsy_id,
        title=f"Handmade Ceramic Mug {etsy_id}",
        description="A beautiful handmade ceramic mug.",
        state="active",
        tags=["mug", "handmade", "ceramic"],
        materials=["clay", "glaze"],
        taxonomy_id=1,
        price_amount=2500,
        price_divisor=100,
        currency_code="USD",
        quantity=10,
        has_variations=False,
    )
    db_session.add(listing)
    await db_session.flush()
    await db_session.commit()
    return str(listing.id)


async def _give_ai_credits(db_session, org_id: str) -> None:
    from app.models.subscription import Subscription
    result = await db_session.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.plan = "pro_monthly"
    else:
        sub = Subscription(organization_id=org_id, plan="pro_monthly", status="active")
        db_session.add(sub)
    await db_session.commit()


# ── unit tests — prompt builders ──────────────────────────────────────────────

def test_build_title_prompt_contains_title():
    ctx = {"title": "Blue Ceramic Mug", "tags": ["mug", "handmade"], "taxonomy_id": 1}
    prompt = build_title_prompt(ctx)
    assert "Blue Ceramic Mug" in prompt
    assert "140" in prompt


def test_build_description_prompt_contains_title():
    ctx = {"title": "Red Vase", "description": "A red vase.", "materials": ["clay"]}
    prompt = build_description_prompt(ctx)
    assert "Red Vase" in prompt
    assert "clay" in prompt


def test_build_tags_prompt_includes_current_tags():
    ctx = {"title": "Silk Scarf", "tags": ["scarf", "silk", "fashion"], "materials": ["silk"]}
    prompt = build_tags_prompt(ctx)
    assert "scarf" in prompt
    assert "13" in prompt


def test_build_alt_text_prompt_contains_title():
    ctx = {"title": "Wooden Bowl", "image_position": 2, "current_alt_text": ""}
    prompt = build_alt_text_prompt(ctx)
    assert "Wooden Bowl" in prompt
    assert "125" in prompt


def test_build_seo_score_prompt_contains_tags():
    ctx = {"title": "Ring", "description": "Nice ring.", "tags": ["ring", "silver", "jewelry"]}
    prompt = build_seo_score_prompt(ctx)
    assert "ring" in prompt
    assert "score" in prompt.lower()


# ── unit tests — mock provider ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mock_provider_title():
    p = MockProvider()
    result = await p.generate_json("prompt", "title", {"title": "Test"})
    assert "suggested_title" in result
    assert "reasoning" in result


@pytest.mark.asyncio
async def test_mock_provider_description():
    p = MockProvider()
    result = await p.generate_json("prompt", "description", {"title": "Mug"})
    assert "suggested_description" in result


@pytest.mark.asyncio
async def test_mock_provider_tags():
    p = MockProvider()
    result = await p.generate_json("prompt", "tags", {"title": "Ring"})
    assert "suggested_tags" in result
    assert isinstance(result["suggested_tags"], list)
    assert len(result["suggested_tags"]) > 0


@pytest.mark.asyncio
async def test_mock_provider_alt_text():
    p = MockProvider()
    result = await p.generate_json("prompt", "alt_text", {"title": "Vase"})
    assert "suggested_alt_text" in result


@pytest.mark.asyncio
async def test_mock_provider_seo_score():
    p = MockProvider()
    result = await p.generate_json("prompt", "seo_score", {"title": "Hat"})
    assert "score" in result
    assert isinstance(result["score"], int)


# ── API tests — auth ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_session_requires_auth(client):
    r = await client.post(SESSIONS_URL, json={"listing_id": "x", "tool": "title"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_get_session_requires_auth(client):
    r = await client.get(f"{SESSIONS_URL}/nonexistent")
    assert r.status_code == 403


# ── API tests — session create ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_session_invalid_tool(client, db_session):
    token = await _register_and_login(client, {"email": "ai1@test.com", "password": "Pw12345!", "full_name": "AI1"})
    org_id = await _get_org_id(db_session)
    listing_id = await _setup_listing(db_session, org_id, "AI_T01")
    r = await client.post(
        SESSIONS_URL,
        json={"listing_id": listing_id, "tool": "invalid_tool"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_session_listing_not_found(client, db_session):
    token = await _register_and_login(client, {"email": "ai2@test.com", "password": "Pw12345!", "full_name": "AI2"})
    r = await client.post(
        SESSIONS_URL,
        json={"listing_id": "00000000-0000-0000-0000-000000000000", "tool": "title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_session_success(client, db_session):
    token = await _register_and_login(client, {"email": "ai3@test.com", "password": "Pw12345!", "full_name": "AI3"})
    org_id = await _get_org_id(db_session)
    listing_id = await _setup_listing(db_session, org_id, "AI_T02")
    r = await client.post(
        SESSIONS_URL,
        json={"listing_id": listing_id, "tool": "title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["tool"] == "title"
    assert data["status"] == "pending"
    assert data["listing_id"] == listing_id


# ── API tests — run session ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_session_no_credits(client, db_session):
    token = await _register_and_login(client, {"email": "ai4@test.com", "password": "Pw12345!", "full_name": "AI4"})
    org_id = await _get_org_id(db_session)
    listing_id = await _setup_listing(db_session, org_id, "AI_T03")
    r = await client.post(
        SESSIONS_URL,
        json={"listing_id": listing_id, "tool": "title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = r.json()["id"]
    r2 = await client.post(
        f"{SESSIONS_URL}/{session_id}/run",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 402


@pytest.mark.asyncio
async def test_run_session_success_with_mock(client, db_session):
    token = await _register_and_login(client, {"email": "ai5@test.com", "password": "Pw12345!", "full_name": "AI5"})
    org_id = await _get_org_id(db_session)
    await _give_ai_credits(db_session, org_id)
    listing_id = await _setup_listing(db_session, org_id, "AI_T04")
    r = await client.post(
        SESSIONS_URL,
        json={"listing_id": listing_id, "tool": "title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = r.json()["id"]
    r2 = await client.post(
        f"{SESSIONS_URL}/{session_id}/run",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["status"] == "completed"
    assert data["suggestion_count"] == 1
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["field"] == "title"


@pytest.mark.asyncio
async def test_run_session_not_found(client, db_session):
    token = await _register_and_login(client, {"email": "ai6@test.com", "password": "Pw12345!", "full_name": "AI6"})
    r = await client.post(
        f"{SESSIONS_URL}/00000000-0000-0000-0000-000000000000/run",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_run_session_already_completed(client, db_session):
    token = await _register_and_login(client, {"email": "ai7@test.com", "password": "Pw12345!", "full_name": "AI7"})
    org_id = await _get_org_id(db_session)
    await _give_ai_credits(db_session, org_id)
    listing_id = await _setup_listing(db_session, org_id, "AI_T05")
    r = await client.post(
        SESSIONS_URL,
        json={"listing_id": listing_id, "tool": "tags"},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = r.json()["id"]
    await client.post(f"{SESSIONS_URL}/{session_id}/run", headers={"Authorization": f"Bearer {token}"})
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/run", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 400


# ── API tests — suggestions accept/reject ─────────────────────────────────────

@pytest.mark.asyncio
async def test_accept_suggestion(client, db_session):
    token = await _register_and_login(client, {"email": "ai8@test.com", "password": "Pw12345!", "full_name": "AI8"})
    org_id = await _get_org_id(db_session)
    await _give_ai_credits(db_session, org_id)
    listing_id = await _setup_listing(db_session, org_id, "AI_T06")
    r = await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "description"}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/run", headers={"Authorization": f"Bearer {token}"})
    suggestion_id = r2.json()["suggestions"][0]["id"]
    r3 = await client.post(f"/api/v1/ai/suggestions/{suggestion_id}/accept", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "accepted"
    assert r3.json()["accepted_at"] is not None


@pytest.mark.asyncio
async def test_reject_suggestion(client, db_session):
    token = await _register_and_login(client, {"email": "ai9@test.com", "password": "Pw12345!", "full_name": "AI9"})
    org_id = await _get_org_id(db_session)
    await _give_ai_credits(db_session, org_id)
    listing_id = await _setup_listing(db_session, org_id, "AI_T07")
    r = await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "tags"}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/run", headers={"Authorization": f"Bearer {token}"})
    suggestion_id = r2.json()["suggestions"][0]["id"]
    r3 = await client.post(f"/api/v1/ai/suggestions/{suggestion_id}/reject", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_accept_already_accepted(client, db_session):
    token = await _register_and_login(client, {"email": "ai10@test.com", "password": "Pw12345!", "full_name": "AI10"})
    org_id = await _get_org_id(db_session)
    await _give_ai_credits(db_session, org_id)
    listing_id = await _setup_listing(db_session, org_id, "AI_T08")
    r = await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "title"}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/run", headers={"Authorization": f"Bearer {token}"})
    suggestion_id = r2.json()["suggestions"][0]["id"]
    await client.post(f"/api/v1/ai/suggestions/{suggestion_id}/accept", headers={"Authorization": f"Bearer {token}"})
    r3 = await client.post(f"/api/v1/ai/suggestions/{suggestion_id}/accept", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 400


# ── API tests — convert to bulk edit ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_convert_no_accepted_suggestions(client, db_session):
    token = await _register_and_login(client, {"email": "ai11@test.com", "password": "Pw12345!", "full_name": "AI11"})
    org_id = await _get_org_id(db_session)
    await _give_ai_credits(db_session, org_id)
    listing_id = await _setup_listing(db_session, org_id, "AI_T09")
    r = await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "title"}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    await client.post(f"{SESSIONS_URL}/{session_id}/run", headers={"Authorization": f"Bearer {token}"})
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/convert", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_convert_session_not_completed(client, db_session):
    token = await _register_and_login(client, {"email": "ai12@test.com", "password": "Pw12345!", "full_name": "AI12"})
    org_id = await _get_org_id(db_session)
    listing_id = await _setup_listing(db_session, org_id, "AI_T10")
    r = await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "title"}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/convert", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_convert_success(client, db_session):
    token = await _register_and_login(client, {"email": "ai13@test.com", "password": "Pw12345!", "full_name": "AI13"})
    org_id = await _get_org_id(db_session)
    await _give_ai_credits(db_session, org_id)
    listing_id = await _setup_listing(db_session, org_id, "AI_T11")
    r = await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "title"}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/run", headers={"Authorization": f"Bearer {token}"})
    suggestion_id = r2.json()["suggestions"][0]["id"]
    await client.post(f"/api/v1/ai/suggestions/{suggestion_id}/accept", headers={"Authorization": f"Bearer {token}"})
    r3 = await client.post(f"{SESSIONS_URL}/{session_id}/convert", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    data = r3.json()
    assert "bulk_edit_session_id" in data
    assert data["bulk_edit_session_id"]


# ── API tests — usage ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_usage(client, db_session):
    token = await _register_and_login(client, {"email": "ai14@test.com", "password": "Pw12345!", "full_name": "AI14"})
    r = await client.get(USAGE_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "ai_credits_used" in data
    assert "ai_credits_limit" in data
    assert "period_key" in data


@pytest.mark.asyncio
async def test_usage_credits_increment_after_run(client, db_session):
    token = await _register_and_login(client, {"email": "ai15@test.com", "password": "Pw12345!", "full_name": "AI15"})
    org_id = await _get_org_id(db_session)
    await _give_ai_credits(db_session, org_id)
    listing_id = await _setup_listing(db_session, org_id, "AI_T12")
    r0 = await client.get(USAGE_URL, headers={"Authorization": f"Bearer {token}"})
    used_before = r0.json()["ai_credits_used"]
    r = await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "seo_score"}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    await client.post(f"{SESSIONS_URL}/{session_id}/run", headers={"Authorization": f"Bearer {token}"})
    r1 = await client.get(USAGE_URL, headers={"Authorization": f"Bearer {token}"})
    assert r1.json()["ai_credits_used"] == used_before + 1


# ── API tests — org isolation ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_org_isolation_session(client, db_session):
    token_a = await _register_and_login(client, {"email": "ai16a@test.com", "password": "Pw12345!", "full_name": "AI16A"})
    token_b = await _register_and_login(client, {"email": "ai16b@test.com", "password": "Pw12345!", "full_name": "AI16B"})
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).offset(1).limit(1)
    )
    org_a = result.scalar_one().organization_id
    listing_id = await _setup_listing(db_session, org_a, "AI_T13")
    r = await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "title"}, headers={"Authorization": f"Bearer {token_a}"})
    session_id = r.json()["id"]
    r2 = await client.get(f"{SESSIONS_URL}/{session_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_org_isolation_suggestion_accept(client, db_session):
    token_a = await _register_and_login(client, {"email": "ai17a@test.com", "password": "Pw12345!", "full_name": "AI17A"})
    token_b = await _register_and_login(client, {"email": "ai17b@test.com", "password": "Pw12345!", "full_name": "AI17B"})
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).offset(1).limit(1)
    )
    org_a = result.scalar_one().organization_id
    await _give_ai_credits(db_session, org_a)
    listing_id = await _setup_listing(db_session, org_a, "AI_T14")
    r = await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "title"}, headers={"Authorization": f"Bearer {token_a}"})
    session_id = r.json()["id"]
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/run", headers={"Authorization": f"Bearer {token_a}"})
    suggestion_id = r2.json()["suggestions"][0]["id"]
    r3 = await client.post(f"/api/v1/ai/suggestions/{suggestion_id}/accept", headers={"Authorization": f"Bearer {token_b}"})
    assert r3.status_code == 404


# ── API tests — list sessions ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_sessions(client, db_session):
    token = await _register_and_login(client, {"email": "ai18@test.com", "password": "Pw12345!", "full_name": "AI18"})
    org_id = await _get_org_id(db_session)
    listing_id = await _setup_listing(db_session, org_id, "AI_T15")
    await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "title"}, headers={"Authorization": f"Bearer {token}"})
    await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "tags"}, headers={"Authorization": f"Bearer {token}"})
    r = await client.get(SESSIONS_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_list_sessions_filter_by_tool(client, db_session):
    token = await _register_and_login(client, {"email": "ai19@test.com", "password": "Pw12345!", "full_name": "AI19"})
    org_id = await _get_org_id(db_session)
    listing_id = await _setup_listing(db_session, org_id, "AI_T16")
    await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "title"}, headers={"Authorization": f"Bearer {token}"})
    await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "description"}, headers={"Authorization": f"Bearer {token}"})
    r = await client.get(f"{SESSIONS_URL}?tool=title", headers={"Authorization": f"Bearer {token}"})
    data = r.json()
    assert all(s["tool"] == "title" for s in data["items"])


@pytest.mark.asyncio
async def test_seo_score_session_run(client, db_session):
    token = await _register_and_login(client, {"email": "ai20@test.com", "password": "Pw12345!", "full_name": "AI20"})
    org_id = await _get_org_id(db_session)
    await _give_ai_credits(db_session, org_id)
    listing_id = await _setup_listing(db_session, org_id, "AI_T17")
    r = await client.post(SESSIONS_URL, json={"listing_id": listing_id, "tool": "seo_score"}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    r2 = await client.post(f"{SESSIONS_URL}/{session_id}/run", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    data = r2.json()
    assert data["status"] == "completed"
    assert data["suggestions"][0]["field"] == "seo_score"
    score_value = data["suggestions"][0]["suggested_value"]
    assert "score" in score_value
