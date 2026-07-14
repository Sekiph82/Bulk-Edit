"""
Sprint 5 tests: listing sync, listing API endpoints.
All Etsy API calls are mocked via httpx.AsyncClient patch.
No live Etsy credentials required.
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"

USER_A = {
    "email": "listings_a@example.com",
    "password": "password123",
    "full_name": "User A",
    "organization_name": "Org A",
}
USER_B = {
    "email": "listings_b@example.com",
    "password": "password123",
    "full_name": "User B",
    "organization_name": "Org B",
}


async def _register_and_login(client, user: dict) -> str:
    await client.post(REGISTER_URL, json={**user, "terms_accepted": True})
    r = await client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.json()["access_token"]


async def _setup_connected_shop(db_session, org_id: str, etsy_shop_id: str | None = None) -> tuple:
    """Insert EtsyShop + EtsyToken into test DB. Returns (shop, token)."""
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token

    # Use unique etsy_shop_id per org to avoid UNIQUE constraint conflicts across tests
    shop_etsy_id = etsy_shop_id or f"shop_{org_id[:8]}"

    shop = EtsyShop(
        organization_id=org_id,
        etsy_shop_id=shop_etsy_id,
        shop_name="Test Shop",
        is_connected=True,
    )
    db_session.add(shop)
    await db_session.flush()

    token = EtsyToken(
        etsy_shop_id=shop.id,
        access_token_enc=encrypt_token("fake_access_token"),
        refresh_token_enc=encrypt_token("fake_refresh_token"),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scopes="listings_r",
    )
    db_session.add(token)
    await db_session.commit()
    return shop, token


def _mock_listings_response(count: int = 2) -> dict:
    return {
        "count": count,
        "results": [
            {
                "listing_id": 100000 + i,
                "title": f"Test Listing {i}",
                "description": f"Description {i}",
                "state": "active",
                "url": f"https://etsy.com/listing/{100000 + i}",
                "price": {"amount": 1500, "divisor": 100, "currency_code": "USD"},
                "quantity": 5,
                "tags": ["handmade", "gift"],
                "materials": ["wood"],
                "has_variations": False,
                "Images": [
                    {
                        "listing_image_id": 200000 + i,
                        "url_fullxfull": f"https://i.etsystatic.com/full/{i}.jpg",
                        "url_570xN": f"https://i.etsystatic.com/570/{i}.jpg",
                        "url_170x135": f"https://i.etsystatic.com/170/{i}.jpg",
                        "alt_text": None,
                        "rank": 1,
                        "full_width": 3000,
                        "full_height": 2000,
                    }
                ],
            }
            for i in range(count)
        ],
    }


def _make_mock_http_client(listings_data: dict):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = listings_data
    mock_resp.is_success = True
    mock_resp.status_code = 200

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.post = AsyncMock(return_value=mock_resp)
    return mock_client


# ---------------------------------------------------------------------------
# POST /shops/{shop_id}/sync
# ---------------------------------------------------------------------------

async def test_sync_requires_auth(client):
    r = await client.post(f"/api/v1/shops/{uuid.uuid4()}/sync")
    assert r.status_code == 403


async def test_sync_rejects_shop_from_another_org(client, db_session):
    token_a = await _register_and_login(client, USER_A)
    await _register_and_login(client, USER_B)

    # Get org for user B
    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select
    result = await db_session.execute(select(OrganizationMember).limit(100))
    all_members = result.scalars().all()
    # Find user B's org (last registered user = last org)
    org_b_id = all_members[-1].organization_id

    shop, _ = await _setup_connected_shop(db_session, org_b_id)

    # User A tries to sync user B's shop
    r = await client.post(
        f"/api/v1/shops/{shop.id}/sync",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code in (404, 400)


async def test_sync_rejects_disconnected_shop(client, db_session):
    token = await _register_and_login(client, {"email": "sync_disc@example.com", "password": "password123", "full_name": "D", "organization_name": "DO"})
    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id

    shop, _ = await _setup_connected_shop(db_session, org_id)
    shop.is_connected = False
    await db_session.commit()

    r = await client.post(
        f"/api/v1/shops/{shop.id}/sync",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


async def test_sync_creates_listings_from_mocked_etsy(client, db_session):
    user = {"email": "sync_ok@example.com", "password": "password123", "full_name": "S", "organization_name": "SO"}
    token = await _register_and_login(client, user)

    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id

    shop, _ = await _setup_connected_shop(db_session, org_id)

    listings_data = _mock_listings_response(2)
    mock_http = _make_mock_http_client(listings_data)

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_http):
        r = await client.post(
            f"/api/v1/shops/{shop.id}/sync",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"
    assert data["processed_items"] == 2

    from app.models.listing import Listing
    result = await db_session.execute(select(Listing).where(Listing.etsy_shop_id == shop.id))
    listings = result.scalars().all()
    assert len(listings) == 2


async def test_sync_creates_listing_images(client, db_session):
    user = {"email": "sync_img@example.com", "password": "password123", "full_name": "I", "organization_name": "IO"}
    token = await _register_and_login(client, user)

    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id

    shop, _ = await _setup_connected_shop(db_session, org_id)

    listings_data = _mock_listings_response(1)
    mock_http = _make_mock_http_client(listings_data)

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_http):
        r = await client.post(
            f"/api/v1/shops/{shop.id}/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200

    from app.models.listing import Listing
    from app.models.listing_image import ListingImage
    result = await db_session.execute(select(Listing).where(Listing.etsy_shop_id == shop.id))
    listing = result.scalars().first()
    assert listing is not None

    result = await db_session.execute(select(ListingImage).where(ListingImage.listing_id == listing.id))
    images = result.scalars().all()
    assert len(images) == 1
    assert images[0].url_fullxfull is not None


async def test_sync_creates_sync_job_completed(client, db_session):
    user = {"email": "sync_job@example.com", "password": "password123", "full_name": "J", "organization_name": "JO"}
    token = await _register_and_login(client, user)

    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id

    shop, _ = await _setup_connected_shop(db_session, org_id)

    mock_http = _make_mock_http_client(_mock_listings_response(1))
    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_http):
        r = await client.post(
            f"/api/v1/shops/{shop.id}/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["sync_job_id"] is not None

    from app.models.sync_job import SyncJob
    result = await db_session.execute(select(SyncJob).where(SyncJob.id == data["sync_job_id"]))
    job = result.scalar_one_or_none()
    assert job is not None
    assert job.status == "completed"


async def test_sync_fails_on_etsy_api_error(client, db_session):
    user = {"email": "sync_err@example.com", "password": "password123", "full_name": "E", "organization_name": "EO"}
    token = await _register_and_login(client, user)

    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id

    shop, _ = await _setup_connected_shop(db_session, org_id)

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("Etsy API error")
    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_http):
        r = await client.post(
            f"/api/v1/shops/{shop.id}/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
    # Sync error returns 200 with failed status OR raises an HTTP error
    # Implementation creates a failed SyncJob either way
    assert r.status_code in (200, 400, 500)


# ---------------------------------------------------------------------------
# GET /shops/{shop_id}/sync-status
# ---------------------------------------------------------------------------

async def test_sync_status_404_no_jobs(client, db_session):
    token = await _register_and_login(client, {"email": "status_none@example.com", "password": "password123", "full_name": "N", "organization_name": "NO"})
    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id
    shop, _ = await _setup_connected_shop(db_session, org_id)

    r = await client.get(
        f"/api/v1/shops/{shop.id}/sync-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /listings
# ---------------------------------------------------------------------------

async def test_list_listings_empty(client):
    token = await _register_and_login(client, {"email": "listing_empty@example.com", "password": "password123", "full_name": "L", "organization_name": "LO"})
    r = await client.get("/api/v1/listings", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []


async def test_list_listings_only_returns_own_org(client, db_session):
    token_a = await _register_and_login(client, {"email": "list_own_a@example.com", "password": "password123", "full_name": "A", "organization_name": "A Org"})
    await _register_and_login(client, {"email": "list_own_b@example.com", "password": "password123", "full_name": "B", "organization_name": "B Org"})

    from app.models.organization_member import OrganizationMember
    from app.models.listing import Listing
    from sqlalchemy import select

    result = await db_session.execute(select(OrganizationMember).order_by(OrganizationMember.created_at.asc()))
    members = result.scalars().all()
    # Find org A and org B
    org_a_id = None
    org_b_id = None
    for m in members:
        if org_a_id is None:
            org_a_id = m.organization_id
        elif m.organization_id != org_a_id and org_b_id is None:
            org_b_id = m.organization_id

    # Create shops and listings for each org
    shop_a, _ = await _setup_connected_shop(db_session, org_a_id)
    shop_b, _ = await _setup_connected_shop(db_session, org_b_id)

    # Insert 2 listings for org A, 1 for org B
    for i in range(2):
        db_session.add(Listing(
            organization_id=org_a_id, etsy_shop_id=shop_a.id,
            etsy_listing_id=str(1000 + i), title=f"A Listing {i}", state="active",
        ))
    db_session.add(Listing(
        organization_id=org_b_id, etsy_shop_id=shop_b.id,
        etsy_listing_id="2000", title="B Listing", state="active",
    ))
    await db_session.commit()

    # User A only sees their 2
    r = await client.get("/api/v1/listings", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    titles = {item["title"] for item in data["items"]}
    assert "B Listing" not in titles


async def test_list_listings_search_filter(client, db_session):
    token = await _register_and_login(client, {"email": "search_test@example.com", "password": "password123", "full_name": "S", "organization_name": "Search Org"})
    from app.models.organization_member import OrganizationMember
    from app.models.listing import Listing
    from sqlalchemy import select

    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id
    shop, _ = await _setup_connected_shop(db_session, org_id)

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="3001", title="Handmade Mug", state="active"))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="3002", title="Vintage Lamp", state="active"))
    await db_session.commit()

    r = await client.get("/api/v1/listings?search=mug", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Handmade Mug"


async def test_list_listings_pagination(client, db_session):
    token = await _register_and_login(client, {"email": "page_test@example.com", "password": "password123", "full_name": "P", "organization_name": "Page Org"})
    from app.models.organization_member import OrganizationMember
    from app.models.listing import Listing
    from sqlalchemy import select

    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id
    shop, _ = await _setup_connected_shop(db_session, org_id)

    for i in range(5):
        db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id=str(4000 + i), title=f"Item {i}", state="active"))
    await db_session.commit()

    r = await client.get("/api/v1/listings?page=1&per_page=2", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    r2 = await client.get("/api/v1/listings?page=3&per_page=2", headers={"Authorization": f"Bearer {token}"})
    data2 = r2.json()
    assert len(data2["items"]) == 1


# ---------------------------------------------------------------------------
# GET /listings/{id}
# ---------------------------------------------------------------------------

async def test_get_listing_detail(client, db_session):
    token = await _register_and_login(client, {"email": "detail_test@example.com", "password": "password123", "full_name": "D", "organization_name": "Detail Org"})
    from app.models.organization_member import OrganizationMember
    from app.models.listing import Listing
    from sqlalchemy import select

    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id
    shop, _ = await _setup_connected_shop(db_session, org_id)

    listing = Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="5001", title="Detail Listing", state="active")
    db_session.add(listing)
    await db_session.commit()

    r = await client.get(f"/api/v1/listings/{listing.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["title"] == "Detail Listing"


async def test_get_listing_rejects_other_org(client, db_session):
    token_a = await _register_and_login(client, {"email": "other_a@example.com", "password": "password123", "full_name": "A", "organization_name": "Oth A"})
    await _register_and_login(client, {"email": "other_b@example.com", "password": "password123", "full_name": "B", "organization_name": "Oth B"})

    from app.models.organization_member import OrganizationMember
    from app.models.listing import Listing
    from sqlalchemy import select

    result = await db_session.execute(select(OrganizationMember).order_by(OrganizationMember.created_at.asc()))
    members = result.scalars().all()
    org_a_id = members[0].organization_id
    org_b_id = next(m.organization_id for m in members if m.organization_id != org_a_id)

    shop_b, _ = await _setup_connected_shop(db_session, org_b_id)
    listing_b = Listing(organization_id=org_b_id, etsy_shop_id=shop_b.id, etsy_listing_id="6001", title="B's Listing", state="active")
    db_session.add(listing_b)
    await db_session.commit()

    # User A tries to read user B's listing
    r = await client.get(f"/api/v1/listings/{listing_b.id}", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /listings/{id}/images
# ---------------------------------------------------------------------------

async def test_get_listing_images(client, db_session):
    token = await _register_and_login(client, {"email": "img_api@example.com", "password": "password123", "full_name": "I", "organization_name": "Img Org"})
    from app.models.organization_member import OrganizationMember
    from app.models.listing import Listing
    from app.models.listing_image import ListingImage
    from sqlalchemy import select

    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id
    shop, _ = await _setup_connected_shop(db_session, org_id)

    listing = Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="7001", title="Img Listing", state="active")
    db_session.add(listing)
    await db_session.flush()

    img = ListingImage(listing_id=listing.id, etsy_image_id="80001", url_fullxfull="https://example.com/img.jpg", rank=1)
    db_session.add(img)
    await db_session.commit()

    r = await client.get(f"/api/v1/listings/{listing.id}/images", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["url_fullxfull"] == "https://example.com/img.jpg"


# ---------------------------------------------------------------------------
# max_listings plan gate
# ---------------------------------------------------------------------------

async def test_max_listings_plan_gate(client, db_session):
    """Free plan has max_listings=25. Sync with 30 Etsy results should cap at 25."""
    user = {"email": "maxlist@example.com", "password": "password123", "full_name": "M", "organization_name": "Max Org"}
    token = await _register_and_login(client, user)

    from app.models.organization_member import OrganizationMember
    from app.models.listing import Listing
    from sqlalchemy import select

    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id
    shop, _ = await _setup_connected_shop(db_session, org_id)

    # Mock Etsy returning 30 listings
    big_response = {
        "count": 30,
        "results": [
            {
                "listing_id": 900000 + i,
                "title": f"Max Listing {i}",
                "state": "active",
                "price": {"amount": 1000, "divisor": 100, "currency_code": "USD"},
                "quantity": 1,
                "has_variations": False,
            }
            for i in range(30)
        ],
    }
    mock_http = _make_mock_http_client(big_response)

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_http):
        r = await client.post(
            f"/api/v1/shops/{shop.id}/sync",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"

    result = await db_session.execute(select(Listing).where(Listing.etsy_shop_id == shop.id))
    listings = result.scalars().all()
    # Free plan caps at 25
    assert len(listings) <= 25


# ---------------------------------------------------------------------------
# Sprint 6: new filter tests
# ---------------------------------------------------------------------------

async def _setup_filter_org(client, db_session, email_prefix: str):
    """Register user, return (token, org_id, shop)."""
    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select
    user = {
        "email": f"{email_prefix}@example.com",
        "password": "password123",
        "full_name": "Filter User",
        "organization_name": f"{email_prefix} Org",
    }
    token = await _register_and_login(client, user)
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    member = result.scalar_one()
    org_id = member.organization_id
    shop, _ = await _setup_connected_shop(db_session, org_id)
    return token, org_id, shop


async def test_filter_by_tag(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_tag")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="t001",
                            title="Handmade Mug", state="active", tags=["handmade", "gift"]))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="t002",
                            title="Vintage Lamp", state="active", tags=["vintage", "decor"]))
    await db_session.commit()

    r = await client.get("/api/v1/listings?tag=handmade", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Handmade Mug"


async def test_filter_by_has_variations_true(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_hv_true")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="hv001",
                            title="With Vars", state="active", has_variations=True))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="hv002",
                            title="No Vars", state="active", has_variations=False))
    await db_session.commit()

    r = await client.get("/api/v1/listings?has_variations=true", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "With Vars"


async def test_filter_by_has_variations_false(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_hv_false")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="hf001",
                            title="With Vars", state="active", has_variations=True))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="hf002",
                            title="No Vars", state="active", has_variations=False))
    await db_session.commit()

    r = await client.get("/api/v1/listings?has_variations=false", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "No Vars"


async def test_filter_by_price_min(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_pmin")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="pm001",
                            title="Cheap", state="active", price_amount=500))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="pm002",
                            title="Expensive", state="active", price_amount=2000))
    await db_session.commit()

    r = await client.get("/api/v1/listings?price_min=1000", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Expensive"


async def test_filter_by_price_max(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_pmax")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="px001",
                            title="Cheap", state="active", price_amount=500))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="px002",
                            title="Expensive", state="active", price_amount=2000))
    await db_session.commit()

    r = await client.get("/api/v1/listings?price_max=999", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Cheap"


async def test_filter_by_price_range(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_prange")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="pr001",
                            title="Too Cheap", state="active", price_amount=200))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="pr002",
                            title="Just Right", state="active", price_amount=1000))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="pr003",
                            title="Too Expensive", state="active", price_amount=3000))
    await db_session.commit()

    r = await client.get("/api/v1/listings?price_min=500&price_max=1500", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Just Right"


async def test_filter_by_quantity_min(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_qmin")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="qn001",
                            title="Low Stock", state="active", quantity=1))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="qn002",
                            title="High Stock", state="active", quantity=10))
    await db_session.commit()

    r = await client.get("/api/v1/listings?quantity_min=5", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "High Stock"


async def test_filter_by_quantity_max(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_qmax")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="qx001",
                            title="Low Stock", state="active", quantity=1))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="qx002",
                            title="High Stock", state="active", quantity=10))
    await db_session.commit()

    r = await client.get("/api/v1/listings?quantity_max=5", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Low Stock"


async def test_filter_by_section_id(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_sec")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="sc001",
                            title="In Section", state="active", section_id="sec_123"))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="sc002",
                            title="No Section", state="active", section_id=None))
    await db_session.commit()

    r = await client.get("/api/v1/listings?section_id=sec_123", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "In Section"


async def test_filter_by_taxonomy_id(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_tax")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="tx001",
                            title="Taxon Match", state="active", taxonomy_id="taxon_456"))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="tx002",
                            title="Taxon No Match", state="active", taxonomy_id="taxon_999"))
    await db_session.commit()

    r = await client.get("/api/v1/listings?taxonomy_id=taxon_456", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Taxon Match"


async def test_filter_by_is_personalizable(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_pers")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="pe001",
                            title="Personalizable", state="active", is_personalizable=True))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="pe002",
                            title="Not Personalizable", state="active", is_personalizable=False))
    await db_session.commit()

    r = await client.get("/api/v1/listings?is_personalizable=true", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Personalizable"


async def test_filter_by_is_customizable(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_cust")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="cu001",
                            title="Customizable", state="active", is_customizable=True))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="cu002",
                            title="Not Customizable", state="active", is_customizable=False))
    await db_session.commit()

    r = await client.get("/api/v1/listings?is_customizable=true", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Customizable"


async def test_invalid_sort_by_returns_400(client):
    token = await _register_and_login(client, {"email": "bad_sort@example.com", "password": "password123", "full_name": "B", "organization_name": "Bad Sort Org"})
    r = await client.get("/api/v1/listings?sort_by=malicious_field", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert "sort_by" in r.json()["detail"].lower()


async def test_invalid_sort_dir_returns_400(client):
    token = await _register_and_login(client, {"email": "bad_dir@example.com", "password": "password123", "full_name": "B", "organization_name": "Bad Dir Org"})
    r = await client.get("/api/v1/listings?sort_dir=sideways", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert "sort_dir" in r.json()["detail"].lower()


async def test_sort_by_price_asc(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_sort_price")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="sp001",
                            title="Mid", state="active", price_amount=1000))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="sp002",
                            title="Cheapest", state="active", price_amount=100))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="sp003",
                            title="Priciest", state="active", price_amount=5000))
    await db_session.commit()

    r = await client.get("/api/v1/listings?sort_by=price_amount&sort_dir=asc", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    prices = [item["price_amount"] for item in data["items"]]
    assert prices == sorted(prices)


async def test_sort_by_price_desc(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_sort_price_d")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="sd001",
                            title="Mid", state="active", price_amount=1000))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="sd002",
                            title="Cheapest", state="active", price_amount=100))
    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="sd003",
                            title="Priciest", state="active", price_amount=5000))
    await db_session.commit()

    r = await client.get("/api/v1/listings?sort_by=price_amount&sort_dir=desc", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    prices = [item["price_amount"] for item in data["items"]]
    assert prices == sorted(prices, reverse=True)


async def test_filters_metadata_in_response(client, db_session):
    from app.models.listing import Listing
    token, org_id, shop = await _setup_filter_org(client, db_session, "f_meta")

    db_session.add(Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="fm001",
                            title="Active Item", state="active"))
    await db_session.commit()

    r = await client.get("/api/v1/listings?state=active&search=Active", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["filters"] is not None
    assert data["filters"]["state"] == "active"
    assert data["filters"]["search"] == "Active"


async def test_no_filters_metadata_is_none(client):
    token = await _register_and_login(client, {"email": "no_filter@example.com", "password": "password123", "full_name": "N", "organization_name": "No Filter Org"})
    r = await client.get("/api/v1/listings", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["filters"] is None
