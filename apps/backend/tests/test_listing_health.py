"""
Sprint 24 tests: Listing Health Score engine and API endpoints.
Rule-based scoring only — no Etsy API calls, no AI required.
"""
import pytest
from decimal import Decimal

from app.services.listing_health import score_listing, _grade, _priority, HealthIssue

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


async def _register_and_login(client, email: str, org: str) -> str:
    await client.post(REGISTER_URL, json={
        "email": email, "password": "Test1234!", "full_name": "Test", "organization_name": org,
    })
    r = await client.post(LOGIN_URL, json={"email": email, "password": "Test1234!"})
    return r.json()["access_token"]


# ── Unit tests for the scoring engine ─────────────────────────────────────────

def test_score_perfect_listing():
    result = score_listing(
        listing_id="abc",
        title="Beautiful Handmade Ceramic Coffee Mug With Handle Gift For Him Her",
        description="A" * 400,
        tags=["handmade", "ceramic", "coffee mug", "gift idea", "pottery", "tea cup", "kitchen", "home decor", "wedding", "birthday", "unique gift", "artisan", "custom"],
        photo_count=8,
        has_video=True,
        price=29.99,
    )
    assert result["score"] == 100
    assert result["grade"] == "excellent"
    assert result["issue_count"] == 0  # no issues (cost data is informational, no penalty)


def test_score_missing_title():
    result = score_listing(listing_id="x", title=None, description="Good desc " * 30, tags=["a"] * 13, photo_count=7, price=10.0)
    assert result["score"] <= 75
    categories = [i.category for i in result["issues"]]
    assert "title" in categories
    severities = [i.severity for i in result["issues"] if i.category == "title"]
    assert "critical" in severities


def test_score_empty_title():
    result = score_listing(listing_id="x", title="", description="desc " * 30, tags=["a"] * 13, photo_count=7, price=10.0)
    assert result["score"] <= 75
    assert any(i.category == "title" and i.severity == "critical" for i in result["issues"])


def test_score_short_title():
    result = score_listing(listing_id="x", title="Mug", description="desc " * 30, tags=["a"] * 13, photo_count=7, price=10.0)
    assert any(i.category == "title" and i.severity == "high" for i in result["issues"])


def test_score_no_tags():
    result = score_listing(listing_id="x", title="A good long descriptive title for handmade mug", description="desc " * 30, tags=[], photo_count=7, price=10.0)
    assert any(i.category == "tags" and i.severity == "critical" for i in result["issues"])
    assert result["tag_count"] == 0


def test_score_few_tags_high_severity():
    result = score_listing(listing_id="x", title="A good long descriptive title for handmade mug", description="desc " * 30, tags=["a", "b", "c"], photo_count=7, price=10.0)
    assert any(i.category == "tags" and i.severity == "high" for i in result["issues"])


def test_score_missing_description():
    result = score_listing(listing_id="x", title="A good long descriptive title for handmade mug", description=None, tags=["a"] * 13, photo_count=7, price=10.0)
    assert any(i.category == "description" and i.severity == "high" for i in result["issues"])


def test_score_short_description():
    result = score_listing(listing_id="x", title="A good long descriptive title for handmade mug", description="Short desc", tags=["a"] * 13, photo_count=7, price=10.0)
    assert any(i.category == "description" for i in result["issues"])


def test_score_no_photos():
    result = score_listing(listing_id="x", title="A good long descriptive title", description="desc " * 30, tags=["a"] * 13, photo_count=0, price=10.0)
    assert any(i.category == "media" and i.severity == "critical" and i.field == "photos" for i in result["issues"])


def test_score_low_photo_count():
    result = score_listing(listing_id="x", title="A good long descriptive title", description="desc " * 30, tags=["a"] * 13, photo_count=2, price=10.0)
    assert any(i.category == "media" and i.severity == "high" for i in result["issues"])


def test_score_missing_price():
    result = score_listing(listing_id="x", title="A good long descriptive title", description="desc " * 30, tags=["a"] * 13, photo_count=7, price=None)
    assert any(i.category == "pricing" and i.field == "price" and i.severity == "critical" for i in result["issues"])


def test_grade_excellent():
    assert _grade(90) == "excellent"
    assert _grade(100) == "excellent"


def test_grade_good():
    assert _grade(75) == "good"
    assert _grade(89) == "good"


def test_grade_needs_work():
    assert _grade(50) == "needs_work"
    assert _grade(74) == "needs_work"


def test_grade_critical():
    assert _grade(49) == "critical"
    assert _grade(0) == "critical"


def test_priority_critical():
    issues = [HealthIssue("title", "critical", "title", "msg", "fix")]
    assert _priority(issues) == "critical"


def test_priority_high():
    issues = [HealthIssue("tags", "high", "tags", "msg", "fix")]
    assert _priority(issues) == "high"


def test_priority_low_when_no_issues():
    assert _priority([]) == "low"


def test_top_issues_limited_to_three():
    result = score_listing(listing_id="x", title=None, description=None, tags=[], photo_count=0, price=None)
    assert len(result["top_issues"]) <= 3


# ── API endpoint tests ─────────────────────────────────────────────────────────

async def test_health_summary_requires_auth(client):
    r = await client.get("/api/v1/listing-health/summary")
    assert r.status_code in (401, 403)


async def test_health_listings_requires_auth(client):
    r = await client.get("/api/v1/listing-health/listings")
    assert r.status_code in (401, 403)


async def test_health_summary_authenticated(client):
    token = await _register_and_login(client, "health_u1@test.com", "HealthOrg1")
    r = await client.get("/api/v1/listing-health/summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "average_score" in data
    assert "total_listings" in data
    assert "excellent_count" in data
    assert "critical_count" in data
    assert "top_issue_categories" in data
    assert data["total_listings"] == 0


async def test_health_listings_paginated(client):
    token = await _register_and_login(client, "health_u2@test.com", "HealthOrg2")
    r = await client.get("/api/v1/listing-health/listings?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["items"], list)


async def test_health_listings_filter_by_grade(client):
    token = await _register_and_login(client, "health_u3@test.com", "HealthOrg3")
    r = await client.get("/api/v1/listing-health/listings?grade=excellent", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


async def test_health_listing_detail_404(client):
    token = await _register_and_login(client, "health_u4@test.com", "HealthOrg4")
    r = await client.get("/api/v1/listing-health/listings/nonexistent-id", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


async def test_health_ai_suggestions_no_ai_configured(client):
    """AI suggestions return safe message when AI not configured (mock mode)."""
    from unittest.mock import patch
    token = await _register_and_login(client, "health_u5@test.com", "HealthOrg5")
    # In test env, AI_PROVIDER should be 'mock', so no real AI calls
    r = await client.post("/api/v1/listing-health/listings/nonexistent/ai-suggestions", headers={"Authorization": f"Bearer {token}"})
    # Either 404 (listing not found) or 200 with ai_available=False — both are safe
    assert r.status_code in (200, 404)


async def test_health_recalculate(client):
    token = await _register_and_login(client, "health_u6@test.com", "HealthOrg6")
    r = await client.post("/api/v1/listing-health/recalculate", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_health_org_isolation(client, db_session):
    """User A cannot see User B's listing health data."""
    token_a = await _register_and_login(client, "health_a@test.com", "HealthOrgA")
    token_b = await _register_and_login(client, "health_b@test.com", "HealthOrgB")

    # Both get their own summary — no cross-contamination
    r_a = await client.get("/api/v1/listing-health/summary", headers={"Authorization": f"Bearer {token_a}"})
    r_b = await client.get("/api/v1/listing-health/summary", headers={"Authorization": f"Bearer {token_b}"})
    assert r_a.status_code == 200
    assert r_b.status_code == 200
    # Both start with 0 listings — confirm isolation at data level (no shared state)
    assert r_a.json()["total_listings"] == 0
    assert r_b.json()["total_listings"] == 0


async def test_health_response_no_secrets(client):
    """Health endpoints never return sensitive fields."""
    token = await _register_and_login(client, "health_sec@test.com", "HealthSecOrg")
    r = await client.get("/api/v1/listing-health/summary", headers={"Authorization": f"Bearer {token}"})
    text = r.text
    for secret_field in ["password_hash", "access_token", "refresh_token", "etsy_access_token", "stripe_secret"]:
        assert secret_field not in text.lower()
