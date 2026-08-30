"""
Full listing-status sync (M03.02) and derived counts (M03.03).

Every test here mocks Etsy's HTTP layer directly (respx-style manual mock of
httpx.AsyncClient) — no live Etsy call is ever made, and no write/status-
mutation Etsy endpoint (PATCH/PUT/DELETE against a listing) is ever invoked
by this service in the first place, only GET.
"""
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


@contextmanager
def _valid_etsy_credentials():
    """Fake, non-placeholder ETSY_CLIENT_ID/SECRET so etsy_api_key_header()
    (called to build the x-api-key header before any Etsy GET) doesn't raise
    EtsyConfigurationError. Not real credentials -- every Etsy HTTP call in
    these tests is mocked. CI leaves the real settings blank on purpose (to
    exercise the is_etsy_configured() 503 gate elsewhere), so this must be
    patched explicitly rather than relying on ambient env values. Same
    pattern as tests/test_etsy.py's helper of the same name."""
    with (
        patch("app.services.etsy_http.settings.ETSY_CLIENT_ID", "test_keystring_never_logged"),
        patch("app.services.etsy_http.settings.ETSY_CLIENT_SECRET", "test_shared_secret_never_logged"),
    ):
        yield

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


def _make_get_side_effect(
    listings_by_state: dict,
    raise_for_state: set[str] | None = None,
    page_limit_hint: int = 100,
    http_error_for_state: dict[str, tuple[int, object]] | None = None,
):
    """Returns an async callable usable as httpx.AsyncClient.get's side_effect.

    Enforces the real (post-hotfix) request shape as it dispatches:
    - `active` MUST hit `/listings/active` with no `state` param and
      `includes=Images,MainImage` (the endpoint proven working pre-PR-#120).
    - every other status MUST hit the general `/listings` endpoint with a
      `state` param and NO `includes` param.
    Any other shape raises AssertionError — this is what would have caught
    the production 400 before it shipped.
    """
    raise_for_state = raise_for_state or set()
    http_error_for_state = http_error_for_state or {}
    calls: list[dict] = []

    async def _get(url, headers=None, params=None, **kwargs):
        params = dict(params or {})
        calls.append({"url": url, "params": params})
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

        if url.endswith("/listings/active"):
            state = "active"
            assert "state" not in params, "active must use the dedicated endpoint, not a state= query param"
            assert params.get("includes") == "Images,MainImage", "active must keep the proven-working includes value"
        elif url.endswith("/listings"):
            state = params.get("state")
            assert state in ("inactive", "draft", "expired", "sold_out"), f"unexpected state on general endpoint: {state}"
            assert "includes" not in params, "includes must not be sent to the general listings-by-shop endpoint (unverified there)"
        else:
            raise AssertionError(f"unexpected listings URL: {url}")

        if state in http_error_for_state:
            status_code, body = http_error_for_state[state]
            err_resp = MagicMock()
            err_resp.status_code = status_code
            err_resp.json.return_value = body
            err_resp.text = str(body)
            raise httpx.HTTPStatusError(f"Client error '{status_code}' for url: {url}", request=MagicMock(), response=err_resp)
        if state in raise_for_state:
            raise RuntimeError(f"simulated Etsy failure for state={state}")

        items = listings_by_state.get(state, [])
        offset = int(params.get("offset", 0))
        limit = int(params.get("limit", page_limit_hint))
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

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client), _valid_etsy_credentials():
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

    # active hits the dedicated endpoint (no state param); the other 4 hit
    # the general endpoint with a state param — exact real request shapes,
    # not the single unified shape that 400'd in production.
    active_calls = [c for c in get_side_effect.calls if c["url"].endswith("/listings/active")]
    assert len(active_calls) >= 1
    general_calls = [c for c in get_side_effect.calls if c["url"].endswith("/listings") and not c["url"].endswith("/listings/active")]
    queried_states = {c["params"].get("state") for c in general_calls}
    assert queried_states == {"inactive", "draft", "expired", "sold_out"}


async def test_sync_never_calls_a_write_or_status_mutation_method(client, db_session):
    """Read-only proof: only GET is ever used; POST/PATCH/PUT/DELETE would raise in the mock."""
    from app.services.etsy_sync import sync_shop_listings

    token, org_id = await _register_and_get_org(client, db_session, "readonly@example.com")
    shop = await _setup_shop_with_token(db_session, org_id)

    listings_by_state = {"active": [_fake_listing(10, "active")]}
    mock_client = _mock_client(_make_get_side_effect(listings_by_state))

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client), _valid_etsy_credentials():
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
        _valid_etsy_credentials(),
    ):
        job = await sync_shop_listings(db_session, org_id, shop.id)

    assert job.status == "completed"
    assert job.processed_items == 3

    active_calls = [c for c in mock_client.get.side_effect.calls if c["url"].endswith("/listings/active")]
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

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client), _valid_etsy_credentials():
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


async def test_fetch_shop_listings_active_uses_dedicated_endpoint_no_state_param():
    """Direct regression test for the 2026-08-31 production 400.

    PR #120 built `active` as GET /shops/{id}/listings?state=active&...&
    includes=Images,MainImage — Etsy rejected that shape with a 400 in
    production (owner report), for `active` and every other state. This
    asserts fetch_shop_listings("active", ...) no longer produces that URL:
    it must hit the dedicated /listings/active endpoint with no `state`
    param at all, exactly like the pre-PR-#120 code that was proven working
    for this app's entire history."""
    from app.services.etsy_sync import fetch_shop_listings

    captured = {}

    async def _get(url, headers=None, params=None, **kwargs):
        captured["url"] = url
        captured["params"] = dict(params or {})
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"count": 0, "results": []}
        return resp

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=_get)

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client), _valid_etsy_credentials():
        await fetch_shop_listings("fake_token", "44263504", state="active", limit=100, offset=0)

    assert captured["url"] == "https://openapi.etsy.com/v3/application/shops/44263504/listings/active"
    assert "state" not in captured["params"]
    assert captured["params"]["includes"] == "Images,MainImage"
    # The exact broken shape from the owner's report must never be produced for active:
    assert captured["url"] != "https://openapi.etsy.com/v3/application/shops/44263504/listings"


async def test_fetch_shop_listings_non_active_uses_general_endpoint_no_includes():
    """Companion regression test: non-active states use the general endpoint
    with `state`, and — unverified whether the general endpoint accepts the
    same `includes` values as /listings/active — no `includes` param, relying
    on the existing per-listing image-fetch fallback instead."""
    from app.services.etsy_sync import fetch_shop_listings

    captured = {}

    async def _get(url, headers=None, params=None, **kwargs):
        captured["url"] = url
        captured["params"] = dict(params or {})
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"count": 0, "results": []}
        return resp

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=_get)

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client), _valid_etsy_credentials():
        await fetch_shop_listings("fake_token", "44263504", state="draft", limit=100, offset=0)

    assert captured["url"] == "https://openapi.etsy.com/v3/application/shops/44263504/listings"
    assert captured["params"]["state"] == "draft"
    assert "includes" not in captured["params"]


async def test_active_sync_still_completes_when_all_other_states_400(client, db_session):
    """Reproduces the owner's exact production scenario at the sync-job level:
    every non-active state returns a real Etsy 400, but active (now on the
    dedicated endpoint) succeeds. The job must be completed_with_errors, not
    failed — active listings must still be synced, not lost."""
    from app.services.etsy_sync import sync_shop_listings
    from app.models.listing import Listing
    from sqlalchemy import select

    token, org_id = await _register_and_get_org(client, db_session, "prod_repro@example.com")
    shop = await _setup_shop_with_token(db_session, org_id)

    listings_by_state = {"active": [_fake_listing(50, "active"), _fake_listing(51, "active")]}
    bad_request_body = {"error": "invalid state or includes parameter"}
    mock_client = _mock_client(_make_get_side_effect(
        listings_by_state,
        http_error_for_state={
            "inactive": (400, bad_request_body),
            "draft": (400, bad_request_body),
            "expired": (400, bad_request_body),
            "sold_out": (400, bad_request_body),
        },
    ))

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client), _valid_etsy_credentials():
        job = await sync_shop_listings(db_session, org_id, shop.id)

    assert job.status == "completed_with_errors"
    assert job.processed_items == 2
    assert job.error_message is not None
    for s in ("inactive", "draft", "expired", "sold_out"):
        assert s in job.error_message
    # Sanitized reason from Etsy's body must appear, not just a bare "400 Bad Request"
    assert "invalid state or includes parameter" in job.error_message
    # No raw URL, token, or secret ever lands in the stored error message
    assert "openapi.etsy.com" not in job.error_message
    assert "valid_access_token" not in job.error_message

    result = await db_session.execute(select(Listing.etsy_listing_id).where(Listing.etsy_shop_id == shop.id))
    synced_ids = {r[0] for r in result.all()}
    assert synced_ids == {"50", "51"}


async def test_etsy_error_body_is_sanitized_not_raw(client, db_session):
    """A response body containing something that looks secret-shaped must
    never reach job.error_message even if Etsy's real response ever did."""
    from app.services.etsy_sync import sync_shop_listings

    token, org_id = await _register_and_get_org(client, db_session, "sanitize@example.com")
    shop = await _setup_shop_with_token(db_session, org_id)

    suspicious_body = {
        "error": "invalid state",
        "access_token": "should_never_appear_in_stored_error",
        "authorization": "Bearer should_never_appear_either",
    }
    mock_client = _mock_client(_make_get_side_effect(
        {"active": [_fake_listing(60, "active")]},
        http_error_for_state={
            "inactive": (400, suspicious_body), "draft": (400, suspicious_body),
            "expired": (400, suspicious_body), "sold_out": (400, suspicious_body),
        },
    ))

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client), _valid_etsy_credentials():
        job = await sync_shop_listings(db_session, org_id, shop.id)

    assert job.status == "completed_with_errors"
    assert "should_never_appear_in_stored_error" not in (job.error_message or "")
    assert "should_never_appear_either" not in (job.error_message or "")
    assert "invalid state" in job.error_message


async def test_all_states_failing_marks_job_failed_without_raising(client, db_session):
    from app.services.etsy_sync import sync_shop_listings

    token, org_id = await _register_and_get_org(client, db_session, "all_fail@example.com")
    shop = await _setup_shop_with_token(db_session, org_id)

    mock_client = _mock_client(_make_get_side_effect({}, raise_for_state={"active", "inactive", "draft", "expired", "sold_out"}))

    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client), _valid_etsy_credentials():
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
    with patch("app.services.etsy_sync.httpx.AsyncClient", return_value=mock_client), _valid_etsy_credentials():
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
