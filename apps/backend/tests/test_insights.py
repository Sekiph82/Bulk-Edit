"""Tests for the Shop Insights endpoint — real listing-derived data, no fake analytics."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


async def _register_and_login(client, email: str, org: str) -> str:
    await client.post(REGISTER_URL, json={
        "email": email, "password": "Test1234!", "full_name": "Test", "organization_name": org,
        "terms_accepted": True,
    })
    r = await client.post(LOGIN_URL, json={"email": email, "password": "Test1234!"})
    return r.json()["access_token"]


async def _get_org_id(db_session, email: str) -> str:
    from app.models.user import User
    from app.models.organization_member import OrganizationMember

    user_result = await db_session.execute(select(User).where(User.email == email))
    user = user_result.scalar_one()
    member_result = await db_session.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    )
    return member_result.scalar_one().organization_id


async def _seed_shop_and_listings(db_session, org_id: str) -> None:
    from app.models.etsy_shop import EtsyShop
    from app.models.listing import Listing
    from app.models.listing_image import ListingImage
    from datetime import datetime, timezone

    shop = EtsyShop(
        organization_id=org_id,
        etsy_shop_id=f"insights_shop_{org_id[:8]}",
        shop_name="Insights Test Shop",
        is_connected=True,
        last_synced_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    listing_1 = Listing(
        organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="1",
        title="Well-tagged listing", state="active", price_amount=2500,
        tags=["handmade", "gift", "custom"],
    )
    listing_2 = Listing(
        organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="2",
        title="No tags listing", state="active", price_amount=1500, tags=None,
    )
    listing_3 = Listing(
        organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="3",
        title="Draft listing", state="draft", price_amount=1000, tags=["draft"],
    )
    db_session.add_all([listing_1, listing_2, listing_3])
    await db_session.flush()

    # listing_1 gets photos (above the low-photo threshold), listing_2/3 get none.
    db_session.add_all([
        ListingImage(listing_id=listing_1.id, etsy_image_id="i1", rank=1),
        ListingImage(listing_id=listing_1.id, etsy_image_id="i2", rank=2),
        ListingImage(listing_id=listing_1.id, etsy_image_id="i3", rank=3),
        ListingImage(listing_id=listing_1.id, etsy_image_id="i4", rank=4),
    ])
    await db_session.commit()


@pytest.mark.anyio
async def test_insights_summary_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/insights/summary")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_insights_summary_empty_state_no_shop(client: AsyncClient):
    """No connected shop, no synced listings — must not fabricate any numbers."""
    token = await _register_and_login(client, "ins_u1@test.com", "InsOrg1")
    resp = await client.get(
        "/api/v1/insights/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["shop_connected"] is False
    assert data["total_listings"] == 0
    assert data["listings_by_state"] == []
    assert data["listings_missing_tags"] == 0
    assert data["listings_low_photo_count"] == 0
    assert data["average_price_cents"] is None
    assert "Connect an Etsy shop" in data["note"]
    # Never claim fake analytics fields
    assert "total_views" not in data
    assert "total_revenue_cents" not in data
    assert "total_favourites" not in data


@pytest.mark.anyio
async def test_insights_summary_with_real_synced_listings(client: AsyncClient, db_session):
    """With synced listings present, counts/tag-gaps/photo-gaps/prices must be real, not zero."""
    token = await _register_and_login(client, "ins_seeded@test.com", "InsSeededOrg")
    org_id = await _get_org_id(db_session, "ins_seeded@test.com")
    await _seed_shop_and_listings(db_session, org_id)

    resp = await client.get(
        "/api/v1/insights/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["shop_connected"] is True
    assert data["last_synced_at"] is not None
    assert data["total_listings"] == 3
    states = {row["state"]: row["count"] for row in data["listings_by_state"]}
    assert states == {"active": 2, "draft": 1}
    assert data["listings_missing_tags"] == 1  # listing_2 has no tags
    assert data["listings_low_photo_count"] == 2  # listing_2 and listing_3 have 0 photos
    assert data["min_price_cents"] == 1000
    assert data["max_price_cents"] == 2500
    assert data["average_price_cents"] == round((2500 + 1500 + 1000) / 3)


@pytest.mark.anyio
async def test_insights_summary_org_isolation(client: AsyncClient):
    """Two orgs never see each other's listing counts."""
    token_a = await _register_and_login(client, "ins_a@test.com", "InsOrgA")
    token_b = await _register_and_login(client, "ins_b@test.com", "InsOrgB")

    resp_a = await client.get(
        "/api/v1/insights/summary", headers={"Authorization": f"Bearer {token_a}"}
    )
    resp_b = await client.get(
        "/api/v1/insights/summary", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    assert resp_a.json()["total_listings"] == 0
    assert resp_b.json()["total_listings"] == 0
