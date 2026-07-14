"""
Sprint 12 tests: bulk variation edit jobs, preview, apply, results, backups, org isolation.

All Etsy calls are mocked. No real Etsy API calls.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from app.models.listing_variation import ListingVariation
from app.models.listing_variation_backup_snapshot import ListingVariationBackupSnapshot
from app.services.etsy_variation_write import (
    normalize_etsy_inventory_tree,
    patch_inventory_tree_for_variation_operation,
    MAX_SKU_LENGTH,
    EtsyVariationWriteError,
)
from app.services.bulk_edit_variation import (
    validate_variation_job_payload,
    build_variation_preview_for_listing,
)

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
JOBS_URL = "/api/v1/bulk-edit/variations/jobs"


# ── helpers ───────────────────────────────────────────────────────────────────

async def _register_and_login(client, user: dict) -> str:
    await client.post(REGISTER_URL, json={**user, "terms_accepted": True})
    r = await client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.json()["access_token"]


async def _get_org_id(db_session) -> str:
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    return result.scalar_one().organization_id


async def _setup_variation_listing(db_session, org_id: str, etsy_id: str = "V1001"):
    from app.models.listing import Listing
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token
    from datetime import datetime, timezone, timedelta

    shop_etsy_id = f"var_shop_{org_id[:8]}"
    existing = await db_session.execute(
        select(EtsyShop).where(EtsyShop.etsy_shop_id == shop_etsy_id)
    )
    shop = existing.scalar_one_or_none()
    if not shop:
        shop = EtsyShop(
            organization_id=org_id,
            etsy_shop_id=shop_etsy_id,
            shop_name="Variation Shop",
            is_connected=True,
        )
        db_session.add(shop)
        await db_session.flush()
        token = EtsyToken(
            etsy_shop_id=shop.id,
            access_token_enc=encrypt_token("fake_var_token"),
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
        title=f"Variation Listing {etsy_id}",
        state="active",
        price_amount=2000,
        quantity=10,
        has_variations=True,
        currency_code="USD",
    )
    db_session.add(listing)
    await db_session.commit()
    return listing, shop


async def _add_variation(db_session, listing, property_name="Size", value_name="Large",
                         price_amount=2000, quantity=5, sku="SKU-L", is_available=True):
    v = ListingVariation(
        listing_id=listing.id,
        property_name=property_name,
        value_name=value_name,
        price_amount=price_amount,
        price_divisor=100,
        currency_code="USD",
        quantity=quantity,
        sku=sku,
        is_available=is_available,
    )
    db_session.add(v)
    await db_session.commit()
    return v


def _etsy_settings():
    m = MagicMock()
    m.is_etsy_configured.return_value = True
    return m


FAKE_INVENTORY = {
    "products": [
        {
            "product_id": "PROD001",
            "sku": "SKU-L",
            "is_deleted": False,
            "offerings": [
                {
                    "offering_id": "OFF001",
                    "quantity": 5,
                    "is_enabled": True,
                    "price": {"amount": 2000, "divisor": 100, "currency_code": "USD"},
                }
            ],
            "property_values": [
                {"property_id": "100", "property_name": "Size", "values": ["Large"], "value_ids": ["200"]}
            ],
        }
    ],
    "price_on_property": ["100"],
    "quantity_on_property": [],
    "sku_on_property": [],
}


# ── Unit tests: normalize_etsy_inventory_tree ─────────────────────────────────

def test_normalize_strips_deleted_products():
    tree = {
        "products": [
            {"product_id": "A", "sku": "S1", "is_deleted": False, "offerings": [], "property_values": []},
            {"product_id": "B", "sku": "S2", "is_deleted": True, "offerings": [], "property_values": []},
        ],
        "price_on_property": [],
        "quantity_on_property": [],
        "sku_on_property": [],
    }
    result = normalize_etsy_inventory_tree(tree)
    assert len(result["products"]) == 1
    assert result["products"][0]["sku"] == "S1"


def test_normalize_preserves_offering_price():
    result = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    assert result["products"][0]["offerings"][0]["price"]["amount"] == 2000


# ── Unit tests: patch_inventory_tree_for_variation_operation ──────────────────

def test_patch_set_variation_price():
    tree = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    result = patch_inventory_tree_for_variation_operation(
        tree, "set_variation_price", {"price_amount": 3000}
    )
    assert result["products"][0]["offerings"][0]["price"]["amount"] == 3000


def test_patch_adjust_variation_price_percent():
    tree = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    result = patch_inventory_tree_for_variation_operation(
        tree, "adjust_variation_price_percent", {"percent": 10}
    )
    assert result["products"][0]["offerings"][0]["price"]["amount"] == 2200


def test_patch_adjust_variation_price_fixed():
    tree = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    result = patch_inventory_tree_for_variation_operation(
        tree, "adjust_variation_price_fixed", {"amount_delta": -500}
    )
    assert result["products"][0]["offerings"][0]["price"]["amount"] == 1500


def test_patch_set_variation_quantity():
    tree = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    result = patch_inventory_tree_for_variation_operation(
        tree, "set_variation_quantity", {"quantity": 20}
    )
    assert result["products"][0]["offerings"][0]["quantity"] == 20


def test_patch_adjust_variation_quantity_fixed():
    tree = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    result = patch_inventory_tree_for_variation_operation(
        tree, "adjust_variation_quantity_fixed", {"quantity_delta": 3}
    )
    assert result["products"][0]["offerings"][0]["quantity"] == 8


def test_patch_set_variation_sku():
    tree = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    result = patch_inventory_tree_for_variation_operation(
        tree, "set_variation_sku", {"sku": "NEW-SKU"}
    )
    assert result["products"][0]["sku"] == "NEW-SKU"


def test_patch_replace_variation_sku_text():
    tree = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    result = patch_inventory_tree_for_variation_operation(
        tree, "replace_variation_sku_text", {"find": "SKU", "replace": "ITEM"}
    )
    assert result["products"][0]["sku"] == "ITEM-L"


def test_patch_set_variation_availability():
    tree = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    result = patch_inventory_tree_for_variation_operation(
        tree, "set_variation_availability", {"is_available": False}
    )
    assert result["products"][0]["offerings"][0]["is_enabled"] is False


def test_patch_negative_price_raises():
    tree = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    with pytest.raises(EtsyVariationWriteError):
        patch_inventory_tree_for_variation_operation(
            tree, "adjust_variation_price_fixed", {"amount_delta": -99999}
        )


def test_patch_negative_quantity_raises():
    tree = normalize_etsy_inventory_tree(FAKE_INVENTORY)
    with pytest.raises(EtsyVariationWriteError):
        patch_inventory_tree_for_variation_operation(
            tree, "adjust_variation_quantity_fixed", {"quantity_delta": -99}
        )


def test_patch_selector_only_matches_target():
    import copy
    tree = copy.deepcopy(FAKE_INVENTORY)
    tree["products"].append({
        "product_id": "PROD002",
        "sku": "SKU-S",
        "is_deleted": False,
        "offerings": [
            {"offering_id": "OFF002", "quantity": 3, "is_enabled": True,
             "price": {"amount": 1500, "divisor": 100, "currency_code": "USD"}}
        ],
        "property_values": [
            {"property_id": "100", "property_name": "Size", "values": ["Small"], "value_ids": ["201"]}
        ],
    })
    normalized = normalize_etsy_inventory_tree(tree)
    result = patch_inventory_tree_for_variation_operation(
        normalized,
        "set_variation_price",
        {"price_amount": 9999, "selector": {"property_name": "Size", "value_name": "Large"}},
    )
    large_price = result["products"][0]["offerings"][0]["price"]["amount"]
    small_price = result["products"][1]["offerings"][0]["price"]["amount"]
    assert large_price == 9999
    assert small_price == 1500


# ── Unit tests: validate_variation_job_payload ────────────────────────────────

def test_validate_set_variation_price_valid():
    errs = validate_variation_job_payload("set_variation_price", {"price_amount": 1500})
    assert errs == []


def test_validate_set_variation_price_negative():
    errs = validate_variation_job_payload("set_variation_price", {"price_amount": -1})
    assert errs


def test_validate_replace_sku_requires_find():
    errs = validate_variation_job_payload("replace_variation_sku_text", {"find": "", "replace": "NEW"})
    assert errs


def test_validate_sku_too_long():
    errs = validate_variation_job_payload("set_variation_sku", {"sku": "X" * (MAX_SKU_LENGTH + 1)})
    assert errs


def test_validate_set_availability_requires_bool():
    errs = validate_variation_job_payload("set_variation_availability", {"is_available": "yes"})
    assert errs


def test_validate_set_availability_valid():
    errs = validate_variation_job_payload("set_variation_availability", {"is_available": True})
    assert errs == []


# ── Unit tests: build_variation_preview_for_listing ───────────────────────────

def test_preview_listing_without_variations_is_invalid():
    from app.models.listing import Listing
    l = Listing(id="L1", organization_id="O1", etsy_shop_id="S1",
                etsy_listing_id="E1", has_variations=False)
    before, after, diff, status, msgs = build_variation_preview_for_listing(
        l, [], "set_variation_price", {"price_amount": 1000}
    )
    assert status == "invalid"


def test_preview_no_local_variations_is_warning():
    from app.models.listing import Listing
    l = Listing(id="L1", organization_id="O1", etsy_shop_id="S1",
                etsy_listing_id="E1", has_variations=True)
    before, after, diff, status, msgs = build_variation_preview_for_listing(
        l, [], "set_variation_price", {"price_amount": 1000}
    )
    assert status == "warning"


def test_preview_selector_no_match_is_warning():
    from app.models.listing import Listing
    l = Listing(id="L1", organization_id="O1", etsy_shop_id="S1",
                etsy_listing_id="E1", has_variations=True)
    v = ListingVariation(
        id="V1", listing_id="L1",
        property_name="Color", value_name="Red",
        price_amount=1000, quantity=5, sku="RED", is_available=True,
    )
    before, after, diff, status, msgs = build_variation_preview_for_listing(
        l, [v], "set_variation_price",
        {"price_amount": 2000, "selector": {"property_name": "Size", "value_name": "Large"}},
    )
    assert status == "warning"
    assert any("No variation matched" in (m.get("message") or "") for m in (msgs or []))


def test_preview_set_price_with_no_selector_applies_to_all():
    from app.models.listing import Listing
    l = Listing(id="L1", organization_id="O1", etsy_shop_id="S1",
                etsy_listing_id="E1", has_variations=True)
    v1 = ListingVariation(id="V1", listing_id="L1", property_name="Size", value_name="S",
                          price_amount=1000, quantity=3, sku="S", is_available=True)
    v2 = ListingVariation(id="V2", listing_id="L1", property_name="Size", value_name="L",
                          price_amount=2000, quantity=5, sku="L", is_available=True)
    before, after, diff, status, msgs = build_variation_preview_for_listing(
        l, [v1, v2], "set_variation_price", {"price_amount": 9999}
    )
    assert status == "valid"
    assert after[0]["price_amount"] == 9999
    assert after[1]["price_amount"] == 9999
    assert len(diff) == 2


# ── API tests: auth ───────────────────────────────────────────────────────────

async def test_create_variation_job_requires_auth(client, db_session):
    r = await client.post(JOBS_URL, json={
        "listing_ids": ["fake"], "operation_type": "set_variation_price", "payload": {"price_amount": 100}
    })
    assert r.status_code in (401, 403)


# ── API tests: validation ─────────────────────────────────────────────────────

async def test_rejects_empty_listing_ids(client, db_session):
    token = await _register_and_login(client, {
        "email": "vv1@example.com", "password": "password123",
        "full_name": "VV1", "organization_name": "VV1 Org",
    })
    r = await client.post(JOBS_URL, json={
        "listing_ids": [], "operation_type": "set_variation_price", "payload": {"price_amount": 100}
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422


async def test_rejects_unknown_operation_type(client, db_session):
    token = await _register_and_login(client, {
        "email": "vv2@example.com", "password": "password123",
        "full_name": "VV2", "organization_name": "VV2 Org",
    })
    r = await client.post(JOBS_URL, json={
        "listing_ids": ["x"], "operation_type": "delete_everything", "payload": {}
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422


async def test_rejects_other_org_listing(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "viso_a@example.com", "password": "password123",
        "full_name": "IsoA", "organization_name": "VisoA Org",
    })
    org_a = await _get_org_id(db_session)
    listing_a, _ = await _setup_variation_listing(db_session, org_a, "V9001")

    token_b = await _register_and_login(client, {
        "email": "viso_b@example.com", "password": "password123",
        "full_name": "IsoB", "organization_name": "VisoB Org",
    })
    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing_a.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 1000},
    }, headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404


# ── API tests: create job ─────────────────────────────────────────────────────

async def test_create_set_variation_price_job(client, db_session):
    token = await _register_and_login(client, {
        "email": "vcreate1@example.com", "password": "password123",
        "full_name": "VC1", "organization_name": "VC1 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V2001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 1500},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    data = r.json()
    assert data["operation_type"] == "set_variation_price"
    assert data["status"] == "draft"
    assert data["selected_count"] == 1


async def test_create_adjust_variation_price_percent_job(client, db_session):
    token = await _register_and_login(client, {
        "email": "vcreate2@example.com", "password": "password123",
        "full_name": "VC2", "organization_name": "VC2 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V2002")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "adjust_variation_price_percent",
        "payload": {"percent": -10},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    assert r.json()["operation_type"] == "adjust_variation_price_percent"


async def test_create_set_variation_quantity_job(client, db_session):
    token = await _register_and_login(client, {
        "email": "vcreate3@example.com", "password": "password123",
        "full_name": "VC3", "organization_name": "VC3 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V2003")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_quantity",
        "payload": {"quantity": 20},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201


async def test_create_set_variation_sku_job(client, db_session):
    token = await _register_and_login(client, {
        "email": "vcreate4@example.com", "password": "password123",
        "full_name": "VC4", "organization_name": "VC4 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V2004")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_sku",
        "payload": {"sku": "NEW-SKU-001"},
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201


# ── API tests: preview ────────────────────────────────────────────────────────

async def test_preview_creates_one_item_per_listing(client, db_session):
    token = await _register_and_login(client, {
        "email": "vprev1@example.com", "password": "password123",
        "full_name": "VP1", "organization_name": "VP1 Org",
    })
    org_id = await _get_org_id(db_session)
    l1, _ = await _setup_variation_listing(db_session, org_id, "V3001")
    l2, _ = await _setup_variation_listing(db_session, org_id, "V3002")
    await _add_variation(db_session, l1)
    await _add_variation(db_session, l2)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [l1.id, l2.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 2500},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    r2 = await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "preview_ready"
    assert r2.json()["preview_count"] == 2

    r3 = await client.get(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    assert r3.json()["total"] == 2


async def test_preview_applies_selector_correctly(client, db_session):
    token = await _register_and_login(client, {
        "email": "vprev2@example.com", "password": "password123",
        "full_name": "VP2", "organization_name": "VP2 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V3003")
    await _add_variation(db_session, listing, "Size", "Large", price_amount=2000, sku="LG")
    await _add_variation(db_session, listing, "Size", "Small", price_amount=1500, sku="SM")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 9999, "selector": {"property_name": "Size", "value_name": "Large"}},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})
    r2 = await client.get(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})
    items = r2.json()["items"]
    assert len(items) == 1
    after = items[0]["after_variations"]
    # Large should be updated, Small should not
    large = next((v for v in after if v["value_name"] == "Large"), None)
    small = next((v for v in after if v["value_name"] == "Small"), None)
    assert large and large["price_amount"] == 9999
    assert small and small["price_amount"] == 1500


async def test_preview_no_selector_applies_to_all(client, db_session):
    token = await _register_and_login(client, {
        "email": "vprev3@example.com", "password": "password123",
        "full_name": "VP3", "organization_name": "VP3 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V3004")
    await _add_variation(db_session, listing, "Size", "Large", price_amount=2000)
    await _add_variation(db_session, listing, "Size", "Small", price_amount=1500)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 3000},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})
    r2 = await client.get(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})
    after = r2.json()["items"][0]["after_variations"]
    assert all(v["price_amount"] == 3000 for v in after)


# ── API tests: apply safety gates ─────────────────────────────────────────────

async def test_apply_requires_preview_ready(client, db_session):
    token = await _register_and_login(client, {
        "email": "vapply_gate1@example.com", "password": "password123",
        "full_name": "AG1", "organization_name": "AG1 Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V4001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 1000},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]

    # No preview generated — status is "draft"
    r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 400
    assert "preview_ready" in r2.json()["detail"]


async def test_apply_blocked_without_etsy_configured(client, db_session):
    token = await _register_and_login(client, {
        "email": "vapply_noetsy@example.com", "password": "password123",
        "full_name": "NoEtsy", "organization_name": "NoEtsy Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V4002")
    await _add_variation(db_session, listing)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 1000},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})

    # ETSY_CLIENT_ID is placeholder → is_etsy_configured() returns False
    r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 503
    assert "Etsy" in r2.json()["detail"]


async def test_apply_blocked_with_invalid_preview_item(client, db_session):
    token = await _register_and_login(client, {
        "email": "vapply_invalid@example.com", "password": "password123",
        "full_name": "Invalid", "organization_name": "Invalid Org",
    })
    org_id = await _get_org_id(db_session)
    # Listing with has_variations=False → preview will be "invalid"
    from app.models.listing import Listing
    from app.models.etsy_shop import EtsyShop
    shop_etsy_id = f"inv_shop_{org_id[:6]}"
    existing = await db_session.execute(
        select(EtsyShop).where(EtsyShop.etsy_shop_id == shop_etsy_id)
    )
    shop = existing.scalar_one_or_none()
    if not shop:
        shop = EtsyShop(organization_id=org_id, etsy_shop_id=shop_etsy_id,
                        shop_name="Inv Shop", is_connected=True)
        db_session.add(shop)
        await db_session.flush()
    no_var_listing = Listing(
        organization_id=org_id, etsy_shop_id=shop.id,
        etsy_listing_id="NOVAR001", title="No Var",
        state="active", price_amount=1000, has_variations=False,
    )
    db_session.add(no_var_listing)
    await db_session.commit()

    r = await client.post(JOBS_URL, json={
        "listing_ids": [no_var_listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 1000},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with patch("app.services.bulk_edit_variation.settings", _etsy_settings()):
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.status_code == 400
    assert "invalid" in r2.json()["detail"].lower()


# ── API tests: full apply flow ────────────────────────────────────────────────

async def test_apply_fetches_etsy_inventory_before_writing(client, db_session):
    token = await _register_and_login(client, {
        "email": "vapply_fetch@example.com", "password": "password123",
        "full_name": "Fetch", "organization_name": "Fetch Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V5001")
    await _add_variation(db_session, listing)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 3000},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with patch("app.services.bulk_edit_variation.settings", _etsy_settings()), \
         patch("app.services.bulk_edit_variation.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.bulk_edit_variation.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = FAKE_INVENTORY
        mock_put.return_value = FAKE_INVENTORY
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.status_code == 200
    assert mock_fetch.called


async def test_apply_creates_backup_snapshot_before_write(client, db_session):
    token = await _register_and_login(client, {
        "email": "vapply_backup@example.com", "password": "password123",
        "full_name": "Backup", "organization_name": "Backup Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V6001")
    await _add_variation(db_session, listing, sku="BACKUP-SKU")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 4000},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with patch("app.services.bulk_edit_variation.settings", _etsy_settings()), \
         patch("app.services.bulk_edit_variation.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.bulk_edit_variation.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = FAKE_INVENTORY
        mock_put.return_value = FAKE_INVENTORY
        await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    r2 = await client.get(f"{JOBS_URL}/{job_id}/backups", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    backups = r2.json()
    assert len(backups) == 1
    assert backups[0]["etsy_inventory_snapshot"] is not None
    assert backups[0]["local_variations_snapshot"] is not None


async def test_apply_calls_put_etsy_listing_inventory(client, db_session):
    token = await _register_and_login(client, {
        "email": "vapply_put@example.com", "password": "password123",
        "full_name": "Put", "organization_name": "Put Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V7001")
    await _add_variation(db_session, listing)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_quantity",
        "payload": {"quantity": 10},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with patch("app.services.bulk_edit_variation.settings", _etsy_settings()), \
         patch("app.services.bulk_edit_variation.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.bulk_edit_variation.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = FAKE_INVENTORY
        mock_put.return_value = FAKE_INVENTORY
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.status_code == 200
    assert mock_put.called
    assert r2.json()["success_count"] == 1
    assert r2.json()["status"] == "completed"


async def test_apply_success_updates_local_variations(client, db_session):
    token = await _register_and_login(client, {
        "email": "vapply_local@example.com", "password": "password123",
        "full_name": "Local", "organization_name": "Local Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V8001")
    await _add_variation(db_session, listing, price_amount=1000)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 5000},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with patch("app.services.bulk_edit_variation.settings", _etsy_settings()), \
         patch("app.services.bulk_edit_variation.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.bulk_edit_variation.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = FAKE_INVENTORY
        mock_put.return_value = FAKE_INVENTORY
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["success_count"] == 1

    # Verify result row status
    r3 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token}"})
    assert r3.json()["items"][0]["status"] == "success"


async def test_apply_failure_does_not_update_local_variations(client, db_session):
    token = await _register_and_login(client, {
        "email": "vapply_fail@example.com", "password": "password123",
        "full_name": "Fail", "organization_name": "Fail Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V8002")
    var = await _add_variation(db_session, listing, price_amount=1000)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 9000},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with patch("app.services.bulk_edit_variation.settings", _etsy_settings()), \
         patch("app.services.bulk_edit_variation.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.bulk_edit_variation.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = FAKE_INVENTORY
        mock_put.side_effect = EtsyVariationWriteError("Etsy error", status_code=500)
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    assert r2.json()["failure_count"] == 1

    # Local variation should still have original price
    vars_q = await db_session.execute(
        select(ListingVariation).where(ListingVariation.listing_id == listing.id)
    )
    local_vars = vars_q.scalars().all()
    assert all(v.price_amount == 1000 for v in local_vars)


async def test_partial_failure_returns_completed_with_errors(client, db_session):
    token = await _register_and_login(client, {
        "email": "vpartial@example.com", "password": "password123",
        "full_name": "Partial", "organization_name": "Partial Org",
    })
    org_id = await _get_org_id(db_session)
    l1, _ = await _setup_variation_listing(db_session, org_id, "V9001")
    l2, _ = await _setup_variation_listing(db_session, org_id, "V9002")
    await _add_variation(db_session, l1)
    await _add_variation(db_session, l2)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [l1.id, l2.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 1234},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})

    call_count = 0

    async def sometimes_fail_put(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise EtsyVariationWriteError("Rate limit", status_code=429)
        return FAKE_INVENTORY

    with patch("app.services.bulk_edit_variation.settings", _etsy_settings()), \
         patch("app.services.bulk_edit_variation.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.bulk_edit_variation.put_etsy_listing_inventory", side_effect=sometimes_fail_put):
        mock_fetch.return_value = FAKE_INVENTORY
        r2 = await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    data = r2.json()
    assert data["status"] == "completed_with_errors"
    assert data["success_count"] == 1
    assert data["failure_count"] == 1


# ── API tests: org isolation ──────────────────────────────────────────────────

async def test_result_endpoint_org_scoped(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "vres_a@example.com", "password": "password123",
        "full_name": "ResA", "organization_name": "VResA Org",
    })
    org_a = await _get_org_id(db_session)
    listing_a, _ = await _setup_variation_listing(db_session, org_a, "V10001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing_a.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 1000},
    }, headers={"Authorization": f"Bearer {token_a}"})
    job_id = r.json()["id"]

    token_b = await _register_and_login(client, {
        "email": "vres_b@example.com", "password": "password123",
        "full_name": "ResB", "organization_name": "VResB Org",
    })
    r2 = await client.get(f"{JOBS_URL}/{job_id}/results", headers={"Authorization": f"Bearer {token_b}"})
    assert r2.status_code == 404


async def test_backup_endpoint_org_scoped(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "vbak_a@example.com", "password": "password123",
        "full_name": "BakA", "organization_name": "VBakA Org",
    })
    org_a = await _get_org_id(db_session)
    listing_a, _ = await _setup_variation_listing(db_session, org_a, "V11001")

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing_a.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 1000},
    }, headers={"Authorization": f"Bearer {token_a}"})
    job_id = r.json()["id"]

    token_b = await _register_and_login(client, {
        "email": "vbak_b@example.com", "password": "password123",
        "full_name": "BakB", "organization_name": "VBakB Org",
    })
    r2 = await client.get(f"{JOBS_URL}/{job_id}/backups", headers={"Authorization": f"Bearer {token_b}"})
    assert r2.status_code == 404


async def test_list_jobs_only_returns_own_org(client, db_session):
    token_a = await _register_and_login(client, {
        "email": "vlist_a@example.com", "password": "password123",
        "full_name": "ListA", "organization_name": "VListA Org",
    })
    org_a = await _get_org_id(db_session)
    listing_a, _ = await _setup_variation_listing(db_session, org_a, "V12001")

    await client.post(JOBS_URL, json={
        "listing_ids": [listing_a.id],
        "operation_type": "set_variation_quantity",
        "payload": {"quantity": 10},
    }, headers={"Authorization": f"Bearer {token_a}"})

    token_b = await _register_and_login(client, {
        "email": "vlist_b@example.com", "password": "password123",
        "full_name": "ListB", "organization_name": "VListB Org",
    })
    r = await client.get(JOBS_URL, headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 200
    assert len(r.json()) == 0


# ── API tests: audit logs ─────────────────────────────────────────────────────

async def test_apply_writes_audit_logs(client, db_session):
    token = await _register_and_login(client, {
        "email": "vaudit@example.com", "password": "password123",
        "full_name": "Audit", "organization_name": "VAudit Org",
    })
    org_id = await _get_org_id(db_session)
    listing, _ = await _setup_variation_listing(db_session, org_id, "V13001")
    await _add_variation(db_session, listing)

    r = await client.post(JOBS_URL, json={
        "listing_ids": [listing.id],
        "operation_type": "set_variation_price",
        "payload": {"price_amount": 1500},
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers={"Authorization": f"Bearer {token}"})

    with patch("app.services.bulk_edit_variation.settings", _etsy_settings()), \
         patch("app.services.bulk_edit_variation.fetch_etsy_listing_inventory", new_callable=AsyncMock) as mock_fetch, \
         patch("app.services.bulk_edit_variation.put_etsy_listing_inventory", new_callable=AsyncMock) as mock_put:
        mock_fetch.return_value = FAKE_INVENTORY
        mock_put.return_value = FAKE_INVENTORY
        await client.post(f"{JOBS_URL}/{job_id}/apply", headers={"Authorization": f"Bearer {token}"})

    from app.models.audit_log import AuditLog
    logs_q = await db_session.execute(
        select(AuditLog).where(AuditLog.entity_id == job_id).order_by(AuditLog.created_at.asc())
    )
    event_types = [l.event_type for l in logs_q.scalars().all()]
    assert "bulk_edit_variation_job_started" in event_types
    assert "bulk_edit_variation_job_finished" in event_types
