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
    await client.post(REGISTER_URL, json=user)
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
    assert len(product["offerings"]) == 1
    offering = product["offerings"][0]
    assert offering["is_enabled"] is True
    assert "price" in offering


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
         patch("app.services.bulk_edit_apply.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
         patch("app.services.bulk_edit_apply.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
         patch("app.services.bulk_edit_apply.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
         patch("app.services.bulk_edit_apply.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
         patch("app.services.bulk_edit_apply.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
         patch("app.services.bulk_edit_apply.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
         patch("app.services.bulk_edit_apply.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
         patch("app.services.bulk_edit_revert.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
         patch("app.services.bulk_edit_revert.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
         patch("app.services.bulk_edit_revert.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
         patch("app.services.bulk_edit_apply.patch_etsy_listing_inventory", new_callable=AsyncMock) as mock_inv:
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
