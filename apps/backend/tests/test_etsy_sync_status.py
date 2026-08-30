"""
Full listing-status sync (M03.02) and derived counts (M03.03).

Every test here mocks Etsy's HTTP layer directly (respx-style manual mock of
httpx.AsyncClient) — no live Etsy call is ever made, and no write/status-
mutation Etsy endpoint (PATCH/PUT/DELETE against a listing) is ever invoked
by this service in the first place, only GET.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"

VALID_USER = {
    "email": "sync_status_test@example.com",
    "password": "password123",
    "full_name": "Sync Status Tester",
    "organization_name": "Sync Status Test Org",
    "terms_accepted": True,
}


async def _register_and_get_org(client, db_session, email: str) -> tuple[str, str]:
    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select

    payload = {**VALID_USER, "email": email}
    await client.post(REGISTER_URL, json=payload)
    r = await client.post(LOGIN_URL, json={"email": email, "password": payload["password"]})
    access_token = r.json()["access_token"]

    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    org_id = result.scalar_one().organization_id
    return access_token, org_id


async def _setup_shop_with_token(db_session, org_id: str):
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token

    shop = EtsyShop(
        organization_id=org_id,
        etsy_shop_id=f"status_sync_{uuid.uuid4().hex[:8]}",
        shop_name="Status Sync Test Shop",
        is_connected=True,
    )
    db_session.add(shop)
    await db_session.flush()

    token = EtsyToken(
        etsy_shop_id=shop.id,
        access_token_enc=encrypt_token("valid_access_token"),
        refresh_token_enc=encrypt_token("valid_refresh_token"),
        expires_at=datetime.now(timezone.utc).replace(year=2099),  # far future, never triggers refresh
        scopes="listings_r listings_w shops_r profile_r",
    )
    db_session.add(token)
    await db_session.commit()
    return shop


def _fake_listing(listing_id: int, state: str) -> dict:
    return {
        "listing_id": listing_id,
        "title": f"Test listing {listing_id} ({state})",
        "description": "desc",
        "state": state,
        "url": "https://etsy.com/listing/x",
        "price": {"amount": 1000, "divisor": 100, "currency_code": "USD"},
        "quantity": 5,
        "sku": "SKU1",
        "tags": [],
        "materials": [],
        "has_variations": False,
        "Images": [],  # inline empty -> upsert_listing_images skipped, no extra GET
        "last_modified_tsz": 1700000000,
    }


def _make_get_side_effect(listings_by_state: dict, raise_for_state: set[str] | None = None, page_limit_hint: int = 100):
    """Returns an async callable usable as httpx.AsyncClient.get's side_effect.
    Dispatches by URL suffix (listings-by-shop vs images/videos/inventory) and
    by the `state` query param for the listings-by-shop endpoint."""
    raise_for_state = raise_for_state or set()
    calls: list[dict] = []

    async def _get(url, headers=None, params=None, **kwargs):
        calls.append({"url": url, "params": dict(params or {})})
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.is_success = True
        resp.status_code = 200

        if url.endswith("/videos") or url.endswith("/inventory"):
            resp.status_code = 404
            resp.json.return_value = {}
            return resp
        if url.endswith("/images"):
            resp.json.return_value = {"results": []}
            return resp

        # Listings-by-shop endpoint
        state = (params or {}).get("state", "active")
        if state in raise_for_state:
            raise RuntimeError(f"simulated Etsy failure for state={state}")

        items = listings_by_state.get(state, [])
        offset = int((params or {}).get("offset", 0))
        limit = int((params or {}).get("limit", page_limit_hint))
        page_items = items[offset: offset + limit]
        resp.json.return_value = {"count": len(items), "results": page_items}
        return resp

    _get.calls = calls
    return _get


def _mock_client(get_side_effect):
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=get_side_effect)
    # No write methods configured at all — if sync_shop_listings ever called
    # .post/.patch/.put/.delete on this client, the test would fail loudly
    # with an AttributeError/MagicMock-default rather than silently succeeding.
    mock_client.post = AsyncMock(side_effect=AssertionError("sync must never POST to Etsy"))
    mock_client.patch = AsyncMock(side_effect=AssertionError("sync must never PATCH (write) to Etsy"))
    mock_client.put = AsyncMock(side_effect=AssertionError("sync must never PUT (write) to Etsy"))
    mock_client.delete = AsyncMock(side_effect=AssertionError("sync must never DELETE on Etsy"))
    return mock_client


async def test_full_status_sync_covers_all_five_states(client, db_session):
    """M03.02: active/inactive/draft/expired/sold_out are all fetched and upserted."""
    from app.services.etsy_sync import sync_shop_listings

    token, org_id = await _register_and_get_org(client, db_session, "full_status@example.com")
    shop = await _setup_shop_with_token(db_session, org_id)

    listings_by_state = {
        "active": [_fake_listing(1, "active"), _fake_listing(2, "active")],
        "inactive": [_fake_listing(3, "inactive")],
        "draft": [_fake_listing(4, "draft")],
        "expired": [_fake_listing(5, "expired")],
        "sold_out": [_fake_listing(6, "sold_out")],
    }
    get_side_effect = _make_get_side_effect(listings_by_state)
    mock_client = _mock_client(get_side_effect)

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client):
        job = await sync_shop_listings(db_session, org_id, shop.id)

    assert job.status == "completed"
    assert job.processed_items == 6

    from app.models.listing import Listing
    from sqlalchemy import select
    result = await db_session.execute(select(Listing.state, Listing.etsy_listing_id).where(Listing.etsy_shop_id == shop.id))
    rows = {(r[0], r[1]) for r in result.all()}
    assert rows == {
        ("active", "1"), ("active", "2"), ("inactive", "3"),
        ("draft", "4"), ("expired", "5"), ("sold_out", "6"),
    }

    # Every state was queried against the general listings-by-shop endpoint with a state param
    queried_states = {c["params"].get("state") for c in get_side_effect.calls if c["url"].endswith("/listings")}
    assert queried_states == {"active", "inactive", "draft", "expired", "sold_out"}
    for c in get_side_effect.calls:
        if c["url"].endswith("/listings"):
            assert "/listings/active" not in c["url"]  # general endpoint, not the old active-only convenience route


async def test_sync_never_calls_a_write_or_status_mutation_method(client, db_session):
    """Read-only proof: only GET is ever used; POST/PATCH/PUT/DELETE would raise in the mock."""
    from app.services.etsy_sync import sync_shop_listings

    token, org_id = await _register_and_get_org(client, db_session, "readonly@example.com")
    shop = await _setup_shop_with_token(db_session, org_id)

    listings_by_state = {"active": [_fake_listing(10, "active")]}
    mock_client = _mock_client(_make_get_side_effect(listings_by_state))

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client):
        job = await sync_shop_listings(db_session, org_id, shop.id)

    assert job.status == "completed"
    mock_client.post.assert_not_called()
    mock_client.patch.assert_not_called()
    mock_client.put.assert_not_called()
    mock_client.delete.assert_not_called()


async def test_sync_paginates_within_a_single_state(client, db_session):
    """M03.02 pagination: a state with more items than one page's limit is fully fetched across multiple pages."""
    from app.services.etsy_sync import sync_shop_listings

    token, org_id = await _register_and_get_org(client, db_session, "pagination@example.com")
    shop = await _setup_shop_with_token(db_session, org_id)

    listings_by_state = {"active": [_fake_listing(i, "active") for i in range(20, 23)]}  # 3 items
    mock_client = _mock_client(_make_get_side_effect(listings_by_state, page_limit_hint=1))

    with (
        patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client),
        patch("app.services.etsy_sync.PAGE_LIMIT", 1),  # force 1-item pages -> 3 pages for this state
    ):
        job = await sync_shop_listings(db_session, org_id, shop.id)

    assert job.status == "completed"
    assert job.processed_items == 3

    active_calls = [c for c in mock_client.get.side_effect.calls if c["params"].get("state") == "active"]
    # 3 pages of real data + 1 trailing empty-results call that ends the loop
    assert len(active_calls) == 4
    assert [c["params"]["offset"] for c in active_calls] == [0, 1, 2, 3]


async def test_partial_state_failure_does_not_wipe_other_states_and_reports_error(client, db_session):
    """Part 4.4: if one status fails, listings already synced from other statuses this run are kept, not wiped, and the failure is reported safely."""
    from app.services.etsy_sync import sync_shop_listings
    from app.models.listing import Listing
    from sqlalchemy import select

    token, org_id = await _register_and_get_org(client, db_session, "partial_fail@example.com")
    shop = await _setup_shop_with_token(db_session, org_id)

    listings_by_state = {
        "active": [_fake_listing(30, "active")],
        "draft": [_fake_listing(31, "draft")],
    }
    mock_client = _mock_client(_make_get_side_effect(listings_by_state, raise_for_state={"expired"}))

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client):
        job = await sync_shop_listings(db_session, org_id, shop.id)

    assert job.status == "completed_with_errors"
    assert job.processed_items == 2  # active + draft still synced
    assert job.error_message is not None
    assert "expired" in job.error_message
    # No secrets/tokens in the error message
    assert "valid_access_token" not in job.error_message

    result = await db_session.execute(select(Listing.etsy_listing_id).where(Listing.etsy_shop_id == shop.id))
    synced_ids = {r[0] for r in result.all()}
    assert synced_ids == {"30", "31"}


async def test_all_states_failing_marks_job_failed_without_raising(client, db_session):
    from app.services.etsy_sync import sync_shop_listings

    token, org_id = await _register_and_get_org(client, db_session, "all_fail@example.com")
    shop = await _setup_shop_with_token(db_session, org_id)

    mock_client = _mock_client(_make_get_side_effect({}, raise_for_state={"active", "inactive", "draft", "expired", "sold_out"}))

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client):
        job = await sync_shop_listings(db_session, org_id, shop.id)

    assert job.status == "failed"
    assert job.processed_items == 0
    assert job.error_message


async def test_status_counts_endpoint_matches_synced_local_data(client, db_session):
    """M03.03: GET /listings/status-counts reflects real post-sync local data, not a hardcoded assumption."""
    from app.services.etsy_sync import sync_shop_listings

    token, org_id = await _register_and_get_org(client, db_session, "counts@example.com")
    shop = await _setup_shop_with_token(db_session, org_id)

    listings_by_state = {
        "active": [_fake_listing(40, "active"), _fake_listing(41, "active"), _fake_listing(42, "active")],
        "inactive": [_fake_listing(43, "inactive")],
        "draft": [],
        "expired": [_fake_listing(44, "expired")],
        "sold_out": [_fake_listing(45, "sold_out"), _fake_listing(46, "sold_out")],
    }
    mock_client = _mock_client(_make_get_side_effect(listings_by_state))
    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client):
        await sync_shop_listings(db_session, org_id, shop.id)

    r = await client.get("/api/v1/listings/status-counts", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["active"] == 3
    assert data["inactive"] == 1
    assert data["draft"] == 0
    assert data["expired"] == 1
    assert data["sold_out"] == 2
    assert data["all"] == 7


async def test_status_counts_requires_auth(client):
    r = await client.get("/api/v1/listings/status-counts")
    assert r.status_code == 403
