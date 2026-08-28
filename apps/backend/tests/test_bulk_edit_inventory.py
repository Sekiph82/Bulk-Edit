"""
Sprint 10 tests: Etsy Inventory Writes (price and quantity).

Tests cover:
  - build_etsy_inventory_payload unit tests (9 tests)
  - Apply flow: inventory endpoint called for price/quantity changes (6 tests)
  - Revert flow: inventory endpoint called when snapshot has price/quantity (3 tests)
  - Structured request payload format (1 test)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from app.services.etsy_write import build_etsy_inventory_payload

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
SESSIONS_URL = "/api/v1/bulk-edit/sessions"
APPLY_JOBS_URL = "/api/v1/bulk-edit/apply-jobs"


def _mock_etsy_settings():
    m = MagicMock()
    m.is_etsy_configured.return_value = True
    return m


# ── helpers ────────────────────────────────────────────────────────────────────

class _MockListing:
    def __init__(
        self,
        price_amount=2000,
        quantity=5,
        currency_code="USD",
        price_divisor=100,
        has_variations=False,
        sku="",
    ):
        self.price_amount = price_amount
        self.quantity = quantity
        self.currency_code = currency_code
        self.price_divisor = price_divisor
        self.has_variations = has_variations
        self.sku = sku


async def _register_and_login(client, user: dict) -> str:
    await client.post(REGISTER_URL, json={**user, "terms_accepted": True})
    r = await client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.json()["access_token"]


async def _get_org_id_for_user(db_session, user_email: str) -> str:
    from app.models.user import User
    from app.models.organization_member import OrganizationMember

    u_r = await db_session.execute(select(User).where(User.email == user_email))
    u = u_r.scalar_one()
    m_r = await db_session.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == u.id).limit(1)
    )
    return m_r.scalar_one().organization_id


async def _setup_listing(db_session, org_id: str, etsy_id: str = "10001", **kwargs):
    from app.models.listing import Listing
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token
    from datetime import datetime, timezone, timedelta

    shop_etsy_id = f"inv_shop_{org_id[:8]}"
    existing = await db_session.execute(
        select(EtsyShop).where(EtsyShop.etsy_shop_id == shop_etsy_id)
    )
    shop = existing.scalar_one_or_none()
    if not shop:
        shop = EtsyShop(
            organization_id=org_id,
            etsy_shop_id=shop_etsy_id,
            shop_name="Inventory Shop",
            is_connected=True,
        )
        db_session.add(shop)
        await db_session.flush()
        tok = EtsyToken(
            etsy_shop_id=shop.id,
            access_token_enc=encrypt_token("fake_inv_token"),
            refresh_token_enc=encrypt_token("fake_r"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scopes="listings_r listings_w",
        )
        db_session.add(tok)

    listing = Listing(
        organization_id=org_id,
        etsy_shop_id=shop.id,
        etsy_listing_id=etsy_id,
        title=kwargs.get("title", f"Inventory Listing {etsy_id}"),
        state="active",
        price_amount=kwargs.get("price_amount", 2000),
        price_divisor=kwargs.get("price_divisor", 100),
        currency_code=kwargs.get("currency_code", "USD"),
        quantity=kwargs.get("quantity", 5),
        tags=kwargs.get("tags", ["handmade"]),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ("title", "price_amount", "price_divisor", "currency_code", "quantity", "tags")
        },
    )
    db_session.add(listing)
    await db_session.commit()
    return listing


async def _create_price_session(client, db_session, token, org_id, etsy_prefix, new_price=3000):
    """Create session with price_amount change only. Returns (session_id, listing)."""
    listing = await _setup_listing(
        db_session, org_id, f"{etsy_prefix}_01",
        title=f"Price Test Listing {etsy_prefix}",
        price_amount=2000,
        currency_code="USD",
    )
    r = await client.post(
        SESSIONS_URL,
        json={"listing_ids": [listing.id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.json()
    session_id = r.json()["id"]

    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "price_amount", "operation": "set", "operation_value": new_price},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"{SESSIONS_URL}/{session_id}/preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    return session_id, listing


async def _create_qty_session(client, db_session, token, org_id, etsy_prefix, new_qty=10):
    """Create session with quantity change only. Returns (session_id, listing)."""
    listing = await _setup_listing(
        db_session, org_id, f"{etsy_prefix}_01",
        title=f"Qty Test Listing {etsy_prefix}",
        quantity=5,
        currency_code="USD",
    )
    r = await client.post(
        SESSIONS_URL,
        json={"listing_ids": [listing.id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.json()
    session_id = r.json()["id"]

    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "quantity", "operation": "set", "operation_value": new_qty},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"{SESSIONS_URL}/{session_id}/preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    return session_id, listing


async def _create_title_and_price_session(client, db_session, token, org_id, etsy_prefix):
    """Create session with both title and price changes. Returns (session_id, listing)."""
    listing = await _setup_listing(
        db_session, org_id, f"{etsy_prefix}_01",
        title=f"Combo Test Listing {etsy_prefix}",
        price_amount=2000,
        currency_code="USD",
    )
    r = await client.post(
        SESSIONS_URL,
        json={"listing_ids": [listing.id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.json()
    session_id = r.json()["id"]

    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "append", "operation_value": " — SALE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "price_amount", "operation": "set", "operation_value": 3500},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"{SESSIONS_URL}/{session_id}/preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    return session_id, listing


# ── unit tests: build_etsy_inventory_payload ───────────────────────────────────

def test_build_inventory_payload_returns_none_when_no_change():
    listing = _MockListing(price_amount=2000, quantity=5)
    after_data = {"price_amount": 2000, "quantity": 5}
    assert build_etsy_inventory_payload(listing, after_data) is None


def test_build_inventory_payload_price_changed():
    listing = _MockListing(price_amount=2000, quantity=5)
    after_data = {"price_amount": 3000, "quantity": 5}
    payload = build_etsy_inventory_payload(listing, after_data)
    assert payload is not None
    offering = payload["products"][0]["offerings"][0]
    assert offering["price"]["amount"] == 3000
    assert offering["price"]["currency_code"] == "USD"
    assert offering["quantity"] == 5


def test_build_inventory_payload_quantity_changed():
    listing = _MockListing(price_amount=2000, quantity=5)
    after_data = {"price_amount": 2000, "quantity": 10}
    payload = build_etsy_inventory_payload(listing, after_data)
    assert payload is not None
    assert payload["products"][0]["offerings"][0]["quantity"] == 10


def test_build_inventory_payload_both_price_and_qty_changed():
    listing = _MockListing(price_amount=2000, quantity=5)
    after_data = {"price_amount": 4000, "quantity": 8}
    payload = build_etsy_inventory_payload(listing, after_data)
    assert payload is not None
    offering = payload["products"][0]["offerings"][0]
    assert offering["price"]["amount"] == 4000
    assert offering["quantity"] == 8


def test_build_inventory_payload_returns_none_for_variation_listing():
    listing = _MockListing(has_variations=True, price_amount=2000)
    after_data = {"price_amount": 3000, "quantity": 10}
    assert build_etsy_inventory_payload(listing, after_data) is None


def test_build_inventory_payload_returns_none_when_currency_code_missing():
    listing = _MockListing(price_amount=2000, currency_code=None)
    after_data = {"price_amount": 3000}
    assert build_etsy_inventory_payload(listing, after_data) is None


def test_build_inventory_payload_uses_price_divisor_from_after_data():
    listing = _MockListing(price_amount=2000, price_divisor=100)
    after_data = {"price_amount": 3000, "price_divisor": 200}
    payload = build_etsy_inventory_payload(listing, after_data)
    assert payload["products"][0]["offerings"][0]["price"]["divisor"] == 200


def test_build_inventory_payload_falls_back_to_listing_price_divisor():
    listing = _MockListing(price_amount=2000, price_divisor=100)
    after_data = {"price_amount": 3000}
    payload = build_etsy_inventory_payload(listing, after_data)
    assert payload["products"][0]["offerings"][0]["price"]["divisor"] == 100


def test_build_inventory_payload_structure():
    listing = _MockListing(price_amount=2000, quantity=5, sku="SKU123")
    after_data = {"price_amount": 3500}
    payload = build_etsy_inventory_payload(listing, after_data)
    assert "products" in payload
    assert len(payload["products"]) == 1
    product = payload["products"][0]
    assert product["sku"] == "SKU123"
    assert product["property_values"] == []
    assert len(product["offerings"]) == 1
    offering = product["offerings"][0]
    assert offering["is_enabled"] is True
    assert "price" in offering


def test_build_inventory_payload_includes_required_top_level_property_keys():
    """
    Regression guard: Etsy's updateListingInventory schema requires
    price_on_property/quantity_on_property/sku_on_property at the top level
    even for a non-variation listing (empty lists). Omitting them caused a
    uniform HTTP 400 on the live price-apply attempt after the URL fix —
    see DECISIONS.md, 2026-08-28 second follow-up.
    """
    listing = _MockListing(price_amount=2000, quantity=5, sku="SKU123")
    after_data = {"price_amount": 3500}
    payload = build_etsy_inventory_payload(listing, after_data)
    assert payload["price_on_property"] == []
    assert payload["quantity_on_property"] == []
    assert payload["sku_on_property"] == []


# ── apply integration tests ────────────────────────────────────────────────────

async def test_apply_calls_inventory_endpoint_when_price_changed(client, db_session):
    token = await _register_and_login(client, {
        "email": "inv_ap_price@example.com", "password": "password123",
        "full_name": "P1", "organization_name": "InvApPrice Org",
    })
    org_id = await _get_org_id_for_user(db_session, "inv_ap_price@example.com")
    session_id, _ = await _create_price_session(client, db_session, token, org_id, "inv_ap_price")

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch, \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_patch.return_value = {"state": "active"}
        mock_inv.return_value = {"products": []}
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    mock_inv.assert_called_once()
    # listing PATCH not called — price is excluded from PATCH endpoint
    mock_patch.assert_not_called()


async def test_apply_calls_inventory_endpoint_when_quantity_changed(client, db_session):
    token = await _register_and_login(client, {
        "email": "inv_ap_qty@example.com", "password": "password123",
        "full_name": "Q1", "organization_name": "InvApQty Org",
    })
    org_id = await _get_org_id_for_user(db_session, "inv_ap_qty@example.com")
    session_id, _ = await _create_qty_session(client, db_session, token, org_id, "inv_ap_qty")

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch, \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_patch.return_value = {"state": "active"}
        mock_inv.return_value = {"products": []}
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    mock_inv.assert_called_once()
    mock_patch.assert_not_called()


async def test_apply_calls_both_endpoints_when_title_and_price_changed(client, db_session):
    token = await _register_and_login(client, {
        "email": "inv_ap_both@example.com", "password": "password123",
        "full_name": "B1", "organization_name": "InvApBoth Org",
    })
    org_id = await _get_org_id_for_user(db_session, "inv_ap_both@example.com")
    session_id, _ = await _create_title_and_price_session(client, db_session, token, org_id, "inv_ap_both")

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch, \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_patch.return_value = {"state": "active"}
        mock_inv.return_value = {"products": []}
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    mock_patch.assert_called_once()
    mock_inv.assert_called_once()
    data = r.json()
    assert data["success_count"] >= 1


async def test_apply_updates_local_price_after_inventory_success(client, db_session):
    from app.models.listing import Listing

    token = await _register_and_login(client, {
        "email": "inv_ap_upd@example.com", "password": "password123",
        "full_name": "U1", "organization_name": "InvApUpd Org",
    })
    org_id = await _get_org_id_for_user(db_session, "inv_ap_upd@example.com")
    session_id, listing = await _create_price_session(
        client, db_session, token, org_id, "inv_ap_upd", new_price=3000
    )

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock), \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_inv.return_value = {"products": []}
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    assert r.json()["success_count"] >= 1

    await db_session.refresh(listing)
    assert listing.price_amount == 3000


async def test_apply_does_not_update_local_price_if_inventory_fails(client, db_session):
    from app.models.listing import Listing
    from app.services.etsy_write import EtsyWriteError

    token = await _register_and_login(client, {
        "email": "inv_ap_fail@example.com", "password": "password123",
        "full_name": "F1", "organization_name": "InvApFail Org",
    })
    org_id = await _get_org_id_for_user(db_session, "inv_ap_fail@example.com")
    session_id, listing = await _create_price_session(
        client, db_session, token, org_id, "inv_ap_fail", new_price=3000
    )

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock), \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_inv.side_effect = EtsyWriteError("Inventory update failed", 422)
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    data = r.json()
    assert data["failure_count"] >= 1
    assert data["success_count"] == 0

    await db_session.refresh(listing)
    assert listing.price_amount == 2000  # unchanged


async def test_apply_skips_inventory_for_variation_listing(client, db_session):
    token = await _register_and_login(client, {
        "email": "inv_ap_var@example.com", "password": "password123",
        "full_name": "V1", "organization_name": "InvApVar Org",
    })
    org_id = await _get_org_id_for_user(db_session, "inv_ap_var@example.com")

    # Variation listing with price change
    listing = await _setup_listing(
        db_session, org_id, "inv_ap_var_01",
        title="Variation Listing Test Here",
        price_amount=2000,
        currency_code="USD",
        has_variations=True,
    )
    r = await client.post(
        SESSIONS_URL,
        json={"listing_ids": [listing.id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = r.json()["id"]
    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "price_amount", "operation": "set", "operation_value": 3000},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch, \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_patch.return_value = {"state": "active"}
        mock_inv.return_value = {"products": []}
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    data = r.json()
    # Variation listing — inventory skipped, text fields only (no text change here)
    assert data["skipped_count"] >= 1
    mock_inv.assert_not_called()


# ── revert integration tests ───────────────────────────────────────────────────

async def _setup_apply_with_price_change(client, db_session, email, org_name, etsy_prefix):
    """Register user, create listing, apply price change with mocked inventory. Returns (token, apply_job_id, listing)."""
    token = await _register_and_login(client, {
        "email": email, "password": "password123",
        "full_name": "Rv Inv", "organization_name": org_name,
    })
    org_id = await _get_org_id_for_user(db_session, email)
    session_id, listing = await _create_price_session(
        client, db_session, token, org_id, etsy_prefix, new_price=3000
    )

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock), \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_inv.return_value = {"products": []}
        r_apply = await client.post(
            f"{SESSIONS_URL}/{session_id}/apply",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r_apply.status_code == 202
    assert r_apply.json()["success_count"] >= 1
    apply_job_id = r_apply.json()["id"]

    # Listing price should now be 3000
    await db_session.refresh(listing)
    assert listing.price_amount == 3000

    return token, apply_job_id, listing


async def test_revert_calls_inventory_endpoint_when_snapshot_has_price(client, db_session):
    token, apply_job_id, listing = await _setup_apply_with_price_change(
        client, db_session,
        email="inv_rv_call@example.com",
        org_name="InvRvCall Org",
        etsy_prefix="inv_rv_call",
    )

    with patch("app.services.bulk_edit_revert.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_revert.patch_etsy_listing", new_callable=AsyncMock) as mock_patch, \
         patch("app.services.bulk_edit_revert.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_patch.return_value = {"state": "active"}
        mock_inv.return_value = {"products": []}
        r = await client.post(
            f"{APPLY_JOBS_URL}/{apply_job_id}/revert",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r.status_code == 202
    mock_inv.assert_called_once()


async def test_revert_updates_local_price_after_inventory_revert_success(client, db_session):
    token, apply_job_id, listing = await _setup_apply_with_price_change(
        client, db_session,
        email="inv_rv_upd@example.com",
        org_name="InvRvUpd Org",
        etsy_prefix="inv_rv_upd",
    )

    with patch("app.services.bulk_edit_revert.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_revert.patch_etsy_listing", new_callable=AsyncMock) as mock_patch, \
         patch("app.services.bulk_edit_revert.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_patch.return_value = {"state": "active"}
        mock_inv.return_value = {"products": []}
        r = await client.post(
            f"{APPLY_JOBS_URL}/{apply_job_id}/revert",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r.status_code == 202
    assert r.json()["success_count"] >= 1

    await db_session.refresh(listing)
    assert listing.price_amount == 2000  # restored to original


async def test_revert_does_not_update_local_price_if_inventory_revert_fails(client, db_session):
    from app.services.etsy_write import EtsyWriteError

    token, apply_job_id, listing = await _setup_apply_with_price_change(
        client, db_session,
        email="inv_rv_fail@example.com",
        org_name="InvRvFail Org",
        etsy_prefix="inv_rv_fail",
    )

    with patch("app.services.bulk_edit_revert.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_revert.patch_etsy_listing", new_callable=AsyncMock) as mock_patch, \
         patch("app.services.bulk_edit_revert.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_patch.return_value = {"state": "active"}
        mock_inv.side_effect = EtsyWriteError("Inventory revert rejected", 422)
        r = await client.post(
            f"{APPLY_JOBS_URL}/{apply_job_id}/revert",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r.status_code == 202
    data = r.json()
    assert data["failure_count"] >= 1

    await db_session.refresh(listing)
    assert listing.price_amount == 3000  # not reverted


# ── inventory PUT URL shape (Etsy v3 endpoint regression guard) ───────────────
# Sprint 1 follow-up: the endpoint incorrectly included /shops/{shop_id} in the
# path (copy-pasted from the shop-scoped listing endpoints), which 404s on
# Etsy's real API since getListingInventory/updateListingInventory are
# listing-scoped only. This guards against that regressing.

async def test_patch_etsy_listing_inventory_uses_listing_scoped_url():
    from app.services.etsy_write import patch_etsy_listing_inventory

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"products": []}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.put = AsyncMock(return_value=mock_resp)

    with patch("app.services.etsy_write.httpx.AsyncClient", return_value=mock_client), \
         patch("app.services.etsy_write.etsy_api_key_header", return_value="fake_key:fake_secret"):
        await patch_etsy_listing_inventory(
            access_token="fake_token",
            shop_etsy_id="99999999",
            listing_etsy_id="1234567890",
            payload={"products": []},
        )

    called_url = mock_client.put.call_args.args[0]
    assert called_url == "https://openapi.etsy.com/v3/application/listings/1234567890/inventory"
    assert "shops" not in called_url


# ── writable inventory PUT payload shape (root cause of the post-URL-fix 400) ──
# Fourth follow-up: PR #94's apply_single_listing_price_quantity() PUT the
# normalized GET tree essentially unchanged — still carrying Money-object
# prices ({"amount","divisor","currency_code"}) and response-only IDs
# (product_id, offering_id). Etsy's official docs (Third Variation Tutorial)
# and a community reference implementation both confirm the writable
# updateListingInventory body is NOT the same shape as the GET response:
# offering.price is a plain decimal number, and product_id/offering_id/
# listing_id never appear in the request body. This section tests the new
# build_writable_inventory_payload_from_tree() conversion and the updated
# apply_single_listing_price_quantity() that now uses it.

_FAKE_LIVE_INVENTORY = {
    "products": [
        {
            "product_id": 555111222,
            "sku": "SKU-LIVE",
            "property_values": [],
            "offerings": [
                {
                    "offering_id": 999888777,
                    "quantity": 5,
                    "is_enabled": True,
                    "price": {"amount": 2000, "divisor": 100, "currency_code": "USD"},
                }
            ],
        }
    ],
    "price_on_property": [],
    "quantity_on_property": [],
    "sku_on_property": [],
}

_FAKE_LIVE_INVENTORY_WITH_VARIATION_PROPERTIES = {
    "products": [
        {
            "product_id": 555111222,
            "sku": "SKU-LIVE",
            "property_values": [
                {
                    "property_id": 513,
                    "property_name": "Color",
                    "scale_id": None,
                    "value_ids": [1],
                    "values": ["Red"],
                },
                {
                    "property_id": 514,
                    "property_name": "Size",
                    "scale_id": 7,
                    "value_ids": [2],
                    "values": ["Medium"],
                },
            ],
            "offerings": [
                {
                    "offering_id": 999888777,
                    "quantity": 5,
                    "is_enabled": True,
                    "readiness_state_id": 1020304051823,
                    "price": {"amount": 2000, "divisor": 100, "currency_code": "USD"},
                }
            ],
        }
    ],
    "price_on_property": [513],
    "quantity_on_property": [],
    "sku_on_property": [],
}


def test_build_writable_inventory_payload_converts_money_object_to_decimal():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY)
    offering = payload["products"][0]["offerings"][0]
    assert offering["price"] == 20.0
    assert not isinstance(offering["price"], dict)


def test_build_writable_inventory_payload_converts_6288_cents_to_62_88():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    tree = {
        "products": [{
            "sku": "S", "property_values": [],
            "offerings": [{"quantity": 1, "is_enabled": True, "price": {"amount": 6288, "divisor": 100, "currency_code": "USD"}}],
        }],
        "price_on_property": [], "quantity_on_property": [], "sku_on_property": [],
    }
    payload = build_writable_inventory_payload_from_tree(tree)
    assert payload["products"][0]["offerings"][0]["price"] == 62.88


def test_build_writable_inventory_payload_omits_product_id():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY)
    assert "product_id" not in payload["products"][0]


def test_build_writable_inventory_payload_omits_offering_id():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY)
    assert "offering_id" not in payload["products"][0]["offerings"][0]


def test_build_writable_inventory_payload_omits_listing_id():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY)
    assert "listing_id" not in payload
    for product in payload["products"]:
        assert "listing_id" not in product


def test_build_writable_inventory_payload_preserves_sku_quantity_enabled_property_values():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY_WITH_VARIATION_PROPERTIES)
    product = payload["products"][0]
    offering = product["offerings"][0]
    assert product["sku"] == "SKU-LIVE"
    assert offering["quantity"] == 5
    assert offering["is_enabled"] is True
    assert len(product["property_values"]) == 2


def test_build_writable_inventory_payload_preserves_readiness_state_id():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY_WITH_VARIATION_PROPERTIES)
    assert payload["products"][0]["offerings"][0]["readiness_state_id"] == 1020304051823


def test_build_writable_inventory_payload_preserves_readiness_state_on_property_if_present():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    tree = dict(_FAKE_LIVE_INVENTORY)
    tree["readiness_state_on_property"] = [513]
    payload = build_writable_inventory_payload_from_tree(tree)
    assert payload["readiness_state_on_property"] == [513]


def test_build_writable_inventory_payload_readiness_state_on_property_defaults_empty():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY)
    assert payload["readiness_state_on_property"] == []


def test_build_writable_inventory_payload_preserves_price_quantity_sku_on_property():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY_WITH_VARIATION_PROPERTIES)
    assert payload["price_on_property"] == [513]
    assert payload["quantity_on_property"] == []
    assert payload["sku_on_property"] == []


def test_build_writable_inventory_payload_omits_none_scale_id():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY_WITH_VARIATION_PROPERTIES)
    color_pv = next(pv for pv in payload["products"][0]["property_values"] if pv["property_name"] == "Color")
    assert "scale_id" not in color_pv


def test_build_writable_inventory_payload_preserves_real_scale_id():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY_WITH_VARIATION_PROPERTIES)
    size_pv = next(pv for pv in payload["products"][0]["property_values"] if pv["property_name"] == "Size")
    assert size_pv["scale_id"] == 7


def test_build_writable_inventory_payload_preserves_property_id_and_values():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY_WITH_VARIATION_PROPERTIES)
    size_pv = next(pv for pv in payload["products"][0]["property_values"] if pv["property_name"] == "Size")
    assert size_pv["property_id"] == 514
    assert size_pv["value_ids"] == [2]
    assert size_pv["values"] == ["Medium"]


def test_build_writable_inventory_payload_non_variation_produces_empty_property_values():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree

    payload = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY)
    assert payload["products"][0]["property_values"] == []


def test_build_writable_inventory_payload_raises_on_missing_divisor():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree, EtsyWriteError

    tree = {
        "products": [{
            "sku": "S", "property_values": [],
            "offerings": [{"quantity": 1, "is_enabled": True, "price": {"amount": 2000, "divisor": 0, "currency_code": "USD"}}],
        }],
        "price_on_property": [], "quantity_on_property": [], "sku_on_property": [],
    }
    with pytest.raises(EtsyWriteError) as exc_info:
        build_writable_inventory_payload_from_tree(tree)
    assert exc_info.value.status_code == 400


def test_build_writable_inventory_payload_raises_on_missing_amount():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree, EtsyWriteError

    tree = {
        "products": [{
            "sku": "S", "property_values": [],
            "offerings": [{"quantity": 1, "is_enabled": True, "price": {"divisor": 100, "currency_code": "USD"}}],
        }],
        "price_on_property": [], "quantity_on_property": [], "sku_on_property": [],
    }
    with pytest.raises(EtsyWriteError):
        build_writable_inventory_payload_from_tree(tree)


async def test_apply_single_listing_price_quantity_mutates_only_price():
    from app.services.etsy_write import apply_single_listing_price_quantity

    with patch("app.services.etsy_variation_write.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.etsy_variation_write.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = _FAKE_LIVE_INVENTORY
        mock_put.return_value = {"products": []}

        await apply_single_listing_price_quantity(
            access_token="fake_token",
            shop_etsy_id="44263504",
            listing_etsy_id="1874506717",
            price_amount=6288,
            quantity=None,
        )

    mock_put.assert_called_once()
    put_payload = mock_put.call_args.args[3]
    offering = put_payload["products"][0]["offerings"][0]
    assert offering["price"] == 62.88
    assert not isinstance(offering["price"], dict)
    assert offering["quantity"] == 5  # untouched — quantity was not part of this change


async def test_apply_single_listing_price_quantity_mutates_only_quantity():
    """Quantity-only update still converts price to writable decimal (requirement #12)."""
    from app.services.etsy_write import apply_single_listing_price_quantity

    with patch("app.services.etsy_variation_write.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.etsy_variation_write.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = _FAKE_LIVE_INVENTORY
        mock_put.return_value = {"products": []}

        await apply_single_listing_price_quantity(
            access_token="fake_token",
            shop_etsy_id="44263504",
            listing_etsy_id="1874506717",
            price_amount=None,
            quantity=12,
        )

    put_payload = mock_put.call_args.args[3]
    offering = put_payload["products"][0]["offerings"][0]
    assert offering["quantity"] == 12
    assert offering["price"] == 20.0  # unchanged fetched price, but still converted to writable decimal


async def test_apply_single_listing_price_quantity_omits_product_and_offering_ids_from_put():
    """
    Inverts the prior round's (now-known-wrong) assumption that product_id/
    offering_id belong in the writable PUT body — Etsy's docs confirm they
    are response-only.
    """
    from app.services.etsy_write import apply_single_listing_price_quantity

    with patch("app.services.etsy_variation_write.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.etsy_variation_write.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = _FAKE_LIVE_INVENTORY
        mock_put.return_value = {"products": []}

        await apply_single_listing_price_quantity(
            access_token="fake_token",
            shop_etsy_id="44263504",
            listing_etsy_id="1874506717",
            price_amount=6288,
            quantity=None,
        )

    put_payload = mock_put.call_args.args[3]
    product = put_payload["products"][0]
    offering = product["offerings"][0]
    assert "product_id" not in product
    assert "offering_id" not in offering
    assert product["sku"] == "SKU-LIVE"
    # top-level schema keys still present
    assert put_payload["price_on_property"] == []
    assert put_payload["quantity_on_property"] == []
    assert put_payload["sku_on_property"] == []
    assert put_payload["readiness_state_on_property"] == []


async def test_apply_single_listing_price_quantity_raises_etsy_write_error_on_fetch_failure():
    from app.services.etsy_write import apply_single_listing_price_quantity, EtsyWriteError
    from app.services.etsy_variation_write import EtsyVariationWriteError

    with patch("app.services.etsy_variation_write.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.etsy_variation_write.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.side_effect = EtsyVariationWriteError("Fetch inventory failed for listing 1874506717: HTTP 404", 404)

        with pytest.raises(EtsyWriteError) as exc_info:
            await apply_single_listing_price_quantity(
                access_token="fake_token",
                shop_etsy_id="44263504",
                listing_etsy_id="1874506717",
                price_amount=6288,
                quantity=None,
            )

    assert exc_info.value.status_code == 404
    mock_put.assert_not_called()  # never reached the write step


async def test_apply_single_listing_price_quantity_raises_etsy_write_error_on_put_failure():
    from app.services.etsy_write import apply_single_listing_price_quantity, EtsyWriteError
    from app.services.etsy_variation_write import EtsyVariationWriteError

    with patch("app.services.etsy_variation_write.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.etsy_variation_write.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = _FAKE_LIVE_INVENTORY
        mock_put.side_effect = EtsyVariationWriteError(
            "Inventory PUT failed for listing 1874506717: HTTP 400", 400, response_body={"error": "invalid request"}
        )

        with pytest.raises(EtsyWriteError) as exc_info:
            await apply_single_listing_price_quantity(
                access_token="fake_token",
                shop_etsy_id="44263504",
                listing_etsy_id="1874506717",
                price_amount=6288,
                quantity=None,
            )

    assert exc_info.value.status_code == 400


# ── safe Etsy error-body diagnostics (post-PR96 failure audit) ────────────────
# Fifth follow-up: PR #96's payload-shape fix still 400d live. The raw Etsy
# error body was captured into response_payload but never sanitized, size-
# limited, or surfaced anywhere — so nobody (owner or Claude) could see the
# actual Etsy validation reason for a failure. These tests cover the new
# sanitizer that replaces EtsyWriteError.response_body with a safe summary.

def test_sanitize_etsy_response_body_extracts_dict_error_fields():
    from app.services.etsy_write import _sanitize_etsy_response_body

    result = _sanitize_etsy_response_body({"error": "bad_request", "error_description": "price is required"})
    assert result["safe_etsy_error_code"] == "bad_request"
    assert result["safe_etsy_error_message"] == "price is required"
    assert set(result["safe_response_keys"]) == {"error", "error_description"}


def test_sanitize_etsy_response_body_truncates_long_message():
    from app.services.etsy_write import _sanitize_etsy_response_body, _MAX_SAFE_ERROR_LEN

    long_msg = "x" * 2000
    result = _sanitize_etsy_response_body({"message": long_msg})
    assert len(result["safe_etsy_error_message"]) == _MAX_SAFE_ERROR_LEN


def test_sanitize_etsy_response_body_never_includes_forbidden_keys():
    from app.services.etsy_write import _sanitize_etsy_response_body

    raw = {"error": "bad_request", "Authorization": "Bearer secret_should_never_appear", "access_token": "leaked_token_value"}
    result = _sanitize_etsy_response_body(raw)
    assert "Authorization" not in result["safe_response_keys"]
    assert "access_token" not in result["safe_response_keys"]
    result_str = str(result)
    assert "secret_should_never_appear" not in result_str
    assert "leaked_token_value" not in result_str


def test_sanitize_etsy_response_body_handles_string_body():
    from app.services.etsy_write import _sanitize_etsy_response_body

    result = _sanitize_etsy_response_body("plain text error")
    assert result["safe_etsy_error_message"] == "plain text error"
    assert result["safe_response_keys"] == []


def test_sanitize_etsy_response_body_handles_none():
    from app.services.etsy_write import _sanitize_etsy_response_body

    result = _sanitize_etsy_response_body(None)
    assert result["safe_etsy_error_message"] is None
    assert result["safe_etsy_error_code"] is None


def test_inventory_payload_shape_summary_reports_decimal_price():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree, _inventory_payload_shape_summary

    writable = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY)
    summary = _inventory_payload_shape_summary(writable)
    assert summary["price_format_sent"] == "decimal_number"
    assert summary["products_count"] == 1
    assert summary["offerings_count"] == 1
    assert summary["has_product_id_in_payload"] is False
    assert summary["has_offering_id_in_payload"] is False


def test_inventory_payload_shape_summary_reports_readiness_state():
    from app.services.etsy_write import build_writable_inventory_payload_from_tree, _inventory_payload_shape_summary

    writable = build_writable_inventory_payload_from_tree(_FAKE_LIVE_INVENTORY_WITH_VARIATION_PROPERTIES)
    summary = _inventory_payload_shape_summary(writable)
    assert summary["has_readiness_state_id"] is True
    assert summary["property_values_count"] == 2


async def test_apply_single_listing_price_quantity_put_failure_diagnostics_are_sanitized():
    """
    response_body on the raised EtsyWriteError must be the safe diagnostics
    dict, never the raw Etsy body or any token/header value.
    """
    from app.services.etsy_write import apply_single_listing_price_quantity, EtsyWriteError
    from app.services.etsy_variation_write import EtsyVariationWriteError

    with patch("app.services.etsy_variation_write.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.etsy_variation_write.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = _FAKE_LIVE_INVENTORY
        mock_put.side_effect = EtsyVariationWriteError(
            "Inventory PUT failed for listing 1874506717: HTTP 400",
            400,
            response_body={"error": "invalid_price", "error_description": "offering.price must be a positive number"},
        )

        with pytest.raises(EtsyWriteError) as exc_info:
            await apply_single_listing_price_quantity(
                access_token="secret_token_value",
                shop_etsy_id="44263504",
                listing_etsy_id="1874506717",
                price_amount=6288,
                quantity=None,
            )

    diagnostics = exc_info.value.response_body
    assert diagnostics["operation"] == "inventory_put"
    assert diagnostics["endpoint_category"] == "inventory"
    assert diagnostics["method"] == "PUT"
    assert diagnostics["listing_id"] == "1874506717"
    assert diagnostics["status_code"] == 400
    assert diagnostics["safe_etsy_error_code"] == "invalid_price"
    assert diagnostics["safe_etsy_error_message"] == "offering.price must be a positive number"
    assert diagnostics["retry_recommended"] is False
    assert diagnostics["payload_shape_summary"]["price_format_sent"] == "decimal_number"
    assert diagnostics["payload_shape_summary"]["has_product_id_in_payload"] is False
    # no token/header value anywhere in the diagnostics
    assert "secret_token_value" not in str(diagnostics)


async def test_apply_single_listing_price_quantity_fetch_failure_diagnostics_are_sanitized():
    from app.services.etsy_write import apply_single_listing_price_quantity, EtsyWriteError
    from app.services.etsy_variation_write import EtsyVariationWriteError

    with patch("app.services.etsy_variation_write.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.etsy_variation_write.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.side_effect = EtsyVariationWriteError(
            "Fetch inventory failed for listing 1874506717: HTTP 404", 404, response_body={"error": "not_found"}
        )

        with pytest.raises(EtsyWriteError) as exc_info:
            await apply_single_listing_price_quantity(
                access_token="fake_token",
                shop_etsy_id="44263504",
                listing_etsy_id="1874506717",
                price_amount=6288,
                quantity=None,
            )

    diagnostics = exc_info.value.response_body
    assert diagnostics["operation"] == "inventory_get"
    assert diagnostics["method"] == "GET"
    assert diagnostics["status_code"] == 404
    # fetch failure has no payload to summarize — no write was attempted
    assert "payload_shape_summary" not in diagnostics
    mock_put.assert_not_called()


# ── listing PATCH URL shape (Etsy v3 endpoint regression guard) ───────────────
# Second follow-up: patch_etsy_listing() (title/description PATCH) was
# missing /shops/{shop_id} — the opposite bug from the inventory endpoint.
# Etsy's updateListing is shop-scoped (matches this codebase's shop-scoped
# image/video writes in etsy_media_write.py), unlike updateListingInventory
# which is listing-scoped only. This guards against either regressing.

async def test_patch_etsy_listing_uses_shop_scoped_url():
    from app.services.etsy_write import patch_etsy_listing

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"listing_id": 1234567890}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.patch = AsyncMock(return_value=mock_resp)

    with patch("app.services.etsy_write.httpx.AsyncClient", return_value=mock_client), \
         patch("app.services.etsy_write.etsy_api_key_header", return_value="fake_key:fake_secret"):
        await patch_etsy_listing(
            access_token="fake_token",
            shop_etsy_id="99999999",
            etsy_listing_id="1234567890",
            payload={"title": "New Title"},
        )

    called_url = mock_client.patch.call_args.args[0]
    assert called_url == "https://openapi.etsy.com/v3/application/shops/99999999/listings/1234567890"

    called_headers = mock_client.patch.call_args.kwargs["headers"]
    assert called_headers["Authorization"] == "Bearer fake_token"
    assert called_headers["x-api-key"] == "fake_key:fake_secret"


async def test_patch_etsy_listing_raises_on_http_404_without_leaking_token():
    from app.services.etsy_write import patch_etsy_listing, EtsyWriteError

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"error": "Listing not found"}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.patch = AsyncMock(return_value=mock_resp)

    with patch("app.services.etsy_write.httpx.AsyncClient", return_value=mock_client), \
         patch("app.services.etsy_write.etsy_api_key_header", return_value="fake_key:fake_secret"):
        with pytest.raises(EtsyWriteError) as exc_info:
            await patch_etsy_listing(
                access_token="secret_token_value",
                shop_etsy_id="99999999",
                etsy_listing_id="1234567890",
                payload={"title": "New Title"},
            )

    assert exc_info.value.status_code == 404
    assert "secret_token_value" not in exc_info.value.message


# ── item-level failure reason surfaced via apply-job detail ───────────────────

async def test_apply_job_detail_exposes_item_level_failure_reason(client, db_session):
    from app.services.etsy_write import EtsyWriteError

    token = await _register_and_login(client, {
        "email": "inv_ap_reason@example.com", "password": "password123",
        "full_name": "R1", "organization_name": "InvApReason Org",
    })
    org_id = await _get_org_id_for_user(db_session, "inv_ap_reason@example.com")
    session_id, listing = await _create_price_session(
        client, db_session, token, org_id, "inv_ap_reason", new_price=3000
    )

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock), \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_inv.side_effect = EtsyWriteError("missing property_values", 400, response_body={"error": "bad request"})
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    job_id = r.json()["id"]

    detail = await client.get(f"{APPLY_JOBS_URL}/{job_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    results = detail.json()["results"]
    assert len(results) == 1
    failed = results[0]
    assert failed["status"] == "failed"
    assert failed["error_message"] is not None
    assert "missing property_values" in failed["error_message"]
    # no auth/token material leaks through the safe error message field
    assert "access_token" not in failed["error_message"]
    assert "Authorization" not in failed["error_message"]


async def test_apply_job_detail_exposes_sanitized_inventory_diagnostics_via_api(client, db_session):
    """
    End-to-end: the sanitized diagnostics dict apply_single_listing_price_quantity()
    now raises survives the DB round-trip and comes back through
    GET /apply-jobs/{id} intact, safe, and usable by the frontend's
    extractSafeEtsyDetail() helper — proving the fix is actually wired up,
    not just unit-tested in isolation.
    """
    from app.services.etsy_write import EtsyWriteError

    token = await _register_and_login(client, {
        "email": "inv_ap_diag@example.com", "password": "password123",
        "full_name": "D1", "organization_name": "InvApDiag Org",
    })
    org_id = await _get_org_id_for_user(db_session, "inv_ap_diag@example.com")
    session_id, listing = await _create_price_session(
        client, db_session, token, org_id, "inv_ap_diag", new_price=6288
    )

    safe_diagnostics = {
        "operation": "inventory_put",
        "endpoint_category": "inventory",
        "method": "PUT",
        "listing_id": listing.etsy_listing_id,
        "status_code": 400,
        "safe_etsy_error_code": "invalid_price",
        "safe_etsy_error_message": "offering.price must be a positive number",
        "safe_response_keys": ["error", "error_description"],
        "payload_shape_summary": {
            "products_count": 1, "offerings_count": 1, "property_values_count": 0,
            "price_format_sent": "decimal_number",
            "has_product_id_in_payload": False, "has_offering_id_in_payload": False,
            "has_readiness_state_id": False, "has_readiness_state_on_property": False,
        },
        "retry_recommended": False,
    }

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock), \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_inv.side_effect = EtsyWriteError("Inventory PUT failed: HTTP 400", 400, response_body=safe_diagnostics)
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    job_id = r.json()["id"]
    detail = await client.get(f"{APPLY_JOBS_URL}/{job_id}", headers={"Authorization": f"Bearer {token}"})
    failed = detail.json()["results"][0]

    response_payload = failed["response_payload"]
    inv_error = response_payload["inventory_patch_error"]["response"]
    assert inv_error["safe_etsy_error_code"] == "invalid_price"
    assert inv_error["safe_etsy_error_message"] == "offering.price must be a positive number"
    assert inv_error["payload_shape_summary"]["price_format_sent"] == "decimal_number"
    # never a raw/unsanitized body, never token-shaped keys
    payload_str = str(response_payload)
    assert "Authorization" not in payload_str
    assert "access_token" not in payload_str


async def test_apply_calls_listing_patch_with_shop_and_etsy_listing_id(client, db_session):
    """
    Confirms the apply loop passes shop_etsy_id (Etsy's real shop ID) and
    etsy_listing_id (Etsy's real listing ID) to patch_etsy_listing() — not
    the local DB UUID for either. Regression guard for the shop-scoped URL fix.
    """
    token = await _register_and_login(client, {
        "email": "title_ap_ids@example.com", "password": "password123",
        "full_name": "T1", "organization_name": "TitleApIds Org",
    })
    org_id = await _get_org_id_for_user(db_session, "title_ap_ids@example.com")
    session_id, listing = await _create_title_and_price_session(
        client, db_session, token, org_id, "title_ap_ids"
    )

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch, \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_patch.return_value = {"listing_id": listing.etsy_listing_id}
        mock_inv.return_value = {"products": []}
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    mock_patch.assert_called_once()
    call_kwargs = mock_patch.call_args.kwargs
    assert call_kwargs["etsy_listing_id"] == listing.etsy_listing_id
    assert call_kwargs["etsy_listing_id"] != listing.id
    assert "shop_etsy_id" in call_kwargs
    assert call_kwargs["shop_etsy_id"] != listing.id


async def test_apply_job_detail_exposes_title_patch_404_as_safe_item_level_error(client, db_session):
    from app.services.etsy_write import EtsyWriteError

    token = await _register_and_login(client, {
        "email": "title_ap_404@example.com", "password": "password123",
        "full_name": "T2", "organization_name": "TitleAp404 Org",
    })
    org_id = await _get_org_id_for_user(db_session, "title_ap_404@example.com")
    listing = await _setup_listing(
        db_session, org_id, "title_ap_404_01",
        title="Original Title", currency_code="USD",
    )
    r = await client.post(SESSIONS_URL, json={"listing_ids": [listing.id]}, headers={"Authorization": f"Bearer {token}"})
    session_id = r.json()["id"]
    await client.post(
        f"{SESSIONS_URL}/{session_id}/changes",
        json={"field_name": "title", "operation": "set", "operation_value": "New Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(f"{SESSIONS_URL}/{session_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch:
        mock_patch.side_effect = EtsyWriteError(
            f"Etsy PATCH {listing.etsy_listing_id} failed: HTTP 404", 404, response_body={"error": "not found"}
        )
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    job_id = r.json()["id"]
    data = r.json()
    assert data["failure_count"] == 1

    detail = await client.get(f"{APPLY_JOBS_URL}/{job_id}", headers={"Authorization": f"Bearer {token}"})
    failed = detail.json()["results"][0]
    assert failed["status"] == "failed"
    assert "404" in failed["error_message"]
    assert "access_token" not in failed["error_message"]
    assert "Authorization" not in failed["error_message"]


# ── structured payload test ────────────────────────────────────────────────────

async def test_apply_result_has_structured_payload_when_inventory_involved(client, db_session):
    from app.models.bulk_edit_apply_result import BulkEditApplyResult

    token = await _register_and_login(client, {
        "email": "inv_struct@example.com", "password": "password123",
        "full_name": "S1", "organization_name": "InvStruct Org",
    })
    org_id = await _get_org_id_for_user(db_session, "inv_struct@example.com")
    session_id, listing = await _create_title_and_price_session(
        client, db_session, token, org_id, "inv_struct"
    )

    with patch("app.services.bulk_edit_apply.settings", _mock_etsy_settings()), \
         patch("app.services.bulk_edit_apply.patch_etsy_listing", new_callable=AsyncMock) as mock_patch, \
         patch("app.services.bulk_edit_apply.apply_single_listing_price_quantity", new_callable=AsyncMock) as mock_inv:
        mock_patch.return_value = {"listing_id": listing.etsy_listing_id, "state": "active"}
        mock_inv.return_value = {"products": []}
        r = await client.post(f"{SESSIONS_URL}/{session_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 202
    assert r.json()["success_count"] >= 1

    result_q = await db_session.execute(
        select(BulkEditApplyResult).where(
            BulkEditApplyResult.listing_id == listing.id,
        )
    )
    result = result_q.scalar_one()
    assert result.request_payload is not None
    assert "listing_patch" in result.request_payload
    assert "inventory_patch" in result.request_payload
    assert "title" in result.request_payload["listing_patch"]
