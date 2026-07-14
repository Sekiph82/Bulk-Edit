"""
Sprint 15 tests: Dynamic Pricing — job creation, calculation, preview, accept/reject, convert.

Dynamic pricing NEVER writes directly to Etsy.
Convert creates BulkEditSession (draft) only.
"""
import pytest
from sqlalchemy import select

from app.services.dynamic_pricing import (
    apply_rounding_rule,
    apply_margin_floor,
    apply_price_cap,
    calculate_diff,
    calculate_recommendation_for_listing,
    DynamicPricingError,
)

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
JOBS_URL = "/api/v1/dynamic-pricing/jobs"
RECS_URL = "/api/v1/dynamic-pricing/recommendations"


# ── helpers ───────────────────────────────────────────────────────────────────

async def _register_and_login(client, user: dict) -> str:
    payload = {**user}
    if "organization_name" not in payload:
        payload["organization_name"] = payload.get("full_name", "Org") + " Org"
    payload.setdefault("terms_accepted", True)
    await client.post(REGISTER_URL, json=payload)
    r = await client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.json()["access_token"]


async def _get_org_id(db_session) -> str:
    from app.models.organization_member import OrganizationMember
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    return result.scalar_one().organization_id


async def _setup_listing(db_session, org_id: str, etsy_id: str = "DP001", **kwargs):
    from app.models.listing import Listing
    from app.models.etsy_shop import EtsyShop
    from app.models.etsy_token import EtsyToken
    from app.core.encryption import encrypt_token
    from datetime import datetime, timezone, timedelta

    shop_etsy_id = f"dp_shop_{org_id[:8]}"
    existing = await db_session.execute(
        select(EtsyShop).where(EtsyShop.etsy_shop_id == shop_etsy_id)
    )
    shop = existing.scalar_one_or_none()
    if not shop:
        shop = EtsyShop(
            organization_id=org_id,
            etsy_shop_id=shop_etsy_id,
            shop_name="DP Test Shop",
            is_connected=True,
        )
        db_session.add(shop)
        await db_session.flush()
        token = EtsyToken(
            etsy_shop_id=shop.id,
            access_token_enc=encrypt_token("fake_dp_token"),
            refresh_token_enc=encrypt_token("fake_r"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scopes="listings_r listings_w",
        )
        db_session.add(token)
        await db_session.flush()

    defaults = dict(
        organization_id=org_id,
        etsy_shop_id=shop.id,
        etsy_listing_id=etsy_id,
        title=f"Test Product {etsy_id}",
        state="active",
        price_amount=2000,
        price_divisor=100,
        currency_code="USD",
        quantity=5,
        tags=["handmade"],
        has_variations=False,
    )
    defaults.update(kwargs)
    from app.models.listing import Listing as L
    listing = L(**defaults)
    db_session.add(listing)
    await db_session.commit()
    return listing


async def _upgrade_to_pro(db_session, org_id: str) -> None:
    from app.models.subscription import Subscription
    result = await db_session.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.plan = "pro_monthly"
        sub.status = "active"
    else:
        sub = Subscription(organization_id=org_id, plan="pro_monthly", status="active")
        db_session.add(sub)
    await db_session.commit()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Unit tests — calculation ───────────────────────────────────────────────────

def test_rounding_ending_99_from_exact_dollar():
    # $25.00 (2500) → $24.99 (2499)
    assert apply_rounding_rule(2500, "ending_99") == 2499


def test_rounding_ending_99_already():
    assert apply_rounding_rule(2499, "ending_99") == 2499


def test_rounding_ending_99_rounds_up():
    # $25.55 — dist to 2599 is 44, dist to 2499 is 56 → rounds up to 2599
    assert apply_rounding_rule(2555, "ending_99") == 2599


def test_rounding_ending_95():
    # $25.00 (2500) → $24.95 (2495) — dist down=5, dist up=95 → down wins
    assert apply_rounding_rule(2500, "ending_95") == 2495


def test_rounding_ending_95_already():
    assert apply_rounding_rule(2495, "ending_95") == 2495


def test_rounding_nearest_50():
    # 2543 → nearest 50 = 2550
    assert apply_rounding_rule(2543, "nearest_50") == 2550


def test_rounding_nearest_50_down():
    # 2520 → nearest 50 = 2500
    assert apply_rounding_rule(2520, "nearest_50") == 2500


def test_rounding_nearest_100():
    # 2543 → nearest 100 = 2500
    assert apply_rounding_rule(2543, "nearest_100") == 2500


def test_rounding_nearest_100_up():
    # 2550 → nearest 100 = 2600
    assert apply_rounding_rule(2550, "nearest_100") == 2600


def test_rounding_none():
    assert apply_rounding_rule(2543, "none") == 2543


def test_margin_floor_raises_price():
    result, warnings = apply_margin_floor(800, cost_amount=700, minimum_margin_percent=30, minimum_price_amount=None)
    # Required for 30% margin: 700/(1-0.3) = 1000
    assert result == 1000
    assert len(warnings) == 1


def test_minimum_price_floor():
    result, warnings = apply_margin_floor(500, cost_amount=None, minimum_margin_percent=None, minimum_price_amount=999)
    assert result == 999
    assert len(warnings) == 1


def test_minimum_price_floor_no_change_needed():
    result, warnings = apply_margin_floor(1200, cost_amount=None, minimum_margin_percent=None, minimum_price_amount=999)
    assert result == 1200
    assert len(warnings) == 0


def test_price_cap():
    result, warnings = apply_price_cap(5000, max_price_amount=3999)
    assert result == 3999
    assert len(warnings) == 1


def test_price_cap_no_change():
    result, warnings = apply_price_cap(2999, max_price_amount=3999)
    assert result == 2999
    assert len(warnings) == 0


def test_calculate_diff():
    diff_amount, diff_pct = calculate_diff(2000, 2200)
    assert diff_amount == 200
    assert float(diff_pct) == pytest.approx(10.0, abs=0.01)


def test_percentage_adjustment_calculation(db_session):
    from app.models.listing import Listing
    listing = Listing(
        id="fake-id",
        organization_id="org",
        etsy_shop_id="shop",
        etsy_listing_id="E001",
        price_amount=2000,
        has_variations=False,
    )
    result = calculate_recommendation_for_listing(
        listing, "percentage_adjustment", {"percent": 10}, None
    )
    assert result["status"] == "recommended"
    assert result["recommended_price_amount"] == 2200


def test_fixed_amount_adjustment_calculation(db_session):
    from app.models.listing import Listing
    listing = Listing(
        id="fake-id2",
        organization_id="org",
        etsy_shop_id="shop",
        etsy_listing_id="E002",
        price_amount=2000,
        has_variations=False,
    )
    result = calculate_recommendation_for_listing(
        listing, "fixed_amount_adjustment", {"amount_delta": 250}, None
    )
    assert result["status"] == "recommended"
    assert result["recommended_price_amount"] == 2250


def test_set_price_calculation(db_session):
    from app.models.listing import Listing
    listing = Listing(
        id="fake-id3",
        organization_id="org",
        etsy_shop_id="shop",
        etsy_listing_id="E003",
        price_amount=2000,
        has_variations=False,
    )
    result = calculate_recommendation_for_listing(
        listing, "set_price", {"price_amount": 2499}, None
    )
    assert result["status"] == "recommended"
    assert result["recommended_price_amount"] == 2499


def test_variation_listing_skipped(db_session):
    from app.models.listing import Listing
    listing = Listing(
        id="var-id",
        organization_id="org",
        etsy_shop_id="shop",
        etsy_listing_id="V001",
        price_amount=2000,
        has_variations=True,
    )
    result = calculate_recommendation_for_listing(
        listing, "set_price", {"price_amount": 1999}, None
    )
    assert result["status"] == "skipped"


def test_no_price_listing_invalid(db_session):
    from app.models.listing import Listing
    listing = Listing(
        id="np-id",
        organization_id="org",
        etsy_shop_id="shop",
        etsy_listing_id="NP001",
        price_amount=None,
        has_variations=False,
    )
    result = calculate_recommendation_for_listing(
        listing, "percentage_adjustment", {"percent": 10}, None
    )
    assert result["status"] == "invalid"


def test_negative_final_price_invalid(db_session):
    from app.models.listing import Listing
    listing = Listing(
        id="neg-id",
        organization_id="org",
        etsy_shop_id="shop",
        etsy_listing_id="NEG001",
        price_amount=500,
        has_variations=False,
    )
    # -200% would make price negative
    result = calculate_recommendation_for_listing(
        listing, "percentage_adjustment", {"percent": -200}, None
    )
    assert result["status"] == "invalid"


def test_reference_price_minus_percent(db_session):
    from app.models.listing import Listing
    listing = Listing(
        id="ref-id",
        organization_id="org",
        etsy_shop_id="shop",
        etsy_listing_id="R001",
        price_amount=2000,
        has_variations=False,
    )
    result = calculate_recommendation_for_listing(
        listing,
        "reference_price",
        {
            "mode": "reference_minus_percent",
            "default_reference_price_amount": 3000,
            "percent": 10,
        },
        None,
    )
    assert result["status"] == "recommended"
    # 3000 - 10% = 2700
    assert result["recommended_price_amount"] == 2700


# ── API tests ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_job_requires_auth(client, db_session):
    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": ["x"],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 1000},
    })
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_job_rejects_empty_listing_ids(client, db_session):
    token = await _register_and_login(client, {"email": "dp1@test.com", "password": "Pw12345!", "full_name": "DP1"})
    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 1000},
    }, headers=_auth(token))
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_job_rejects_unknown_rule_type(client, db_session):
    token = await _register_and_login(client, {"email": "dp2@test.com", "password": "Pw12345!", "full_name": "DP2"})
    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": ["fake-id"],
        "rule_type": "magic_discount",
        "rule_payload": {},
    }, headers=_auth(token))
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_job_rejects_other_org_listing(client, db_session):
    token_a = await _register_and_login(client, {"email": "dp3a@test.com", "password": "Pw12345!", "full_name": "DP3A"})
    org_a = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_a)
    listing = await _setup_listing(db_session, org_a, "OA001")

    token_b = await _register_and_login(client, {"email": "dp3b@test.com", "password": "Pw12345!", "full_name": "DP3B"})
    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 1000},
    }, headers=_auth(token_b))
    assert r.status_code in (404, 400)


@pytest.mark.asyncio
async def test_create_percentage_job_success(client, db_session):
    token = await _register_and_login(client, {"email": "dp4@test.com", "password": "Pw12345!", "full_name": "DP4"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "PCT001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "percentage_adjustment",
        "rule_payload": {"percent": 10},
    }, headers=_auth(token))
    assert r.status_code == 201
    data = r.json()
    assert data["rule_type"] == "percentage_adjustment"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_create_fixed_amount_job_success(client, db_session):
    token = await _register_and_login(client, {"email": "dp5@test.com", "password": "Pw12345!", "full_name": "DP5"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "FX001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "fixed_amount_adjustment",
        "rule_payload": {"amount_delta": 200},
    }, headers=_auth(token))
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_create_set_price_job_success(client, db_session):
    token = await _register_and_login(client, {"email": "dp6@test.com", "password": "Pw12345!", "full_name": "DP6"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "SP001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 2499},
    }, headers=_auth(token))
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_create_reference_price_job_success(client, db_session):
    token = await _register_and_login(client, {"email": "dp7@test.com", "password": "Pw12345!", "full_name": "DP7"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "RP001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "reference_price",
        "rule_payload": {
            "mode": "reference_minus_percent",
            "default_reference_price_amount": 3000,
            "percent": 10,
        },
    }, headers=_auth(token))
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_preview_creates_recommendations(client, db_session):
    token = await _register_and_login(client, {"email": "dp8@test.com", "password": "Pw12345!", "full_name": "DP8"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "PV001", price_amount=2000)

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "percentage_adjustment",
        "rule_payload": {"percent": 10},
    }, headers=_auth(token))
    job_id = r.json()["id"]

    r2 = await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))
    assert r2.status_code == 200
    data = r2.json()
    assert data["status"] == "preview_ready"
    assert data["recommended_count"] == 1

    r3 = await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))
    assert r3.status_code == 200
    recs = r3.json()["items"]
    assert len(recs) == 1
    assert recs[0]["recommended_price_amount"] == 2200  # 2000 + 10%


@pytest.mark.asyncio
async def test_recommendation_summary_correct(client, db_session):
    token = await _register_and_login(client, {"email": "dp9@test.com", "password": "Pw12345!", "full_name": "DP9"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    l1 = await _setup_listing(db_session, org_id, "SM001", price_amount=1000)
    l2 = await _setup_listing(db_session, org_id, "SM002", price_amount=2000)

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [l1.id, l2.id],
        "rule_type": "fixed_amount_adjustment",
        "rule_payload": {"amount_delta": 100},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))

    r2 = await client.get(f"{JOBS_URL}/{job_id}/summary", headers=_auth(token))
    assert r2.status_code == 200
    s = r2.json()
    assert s["current_total_price"] == 3000
    assert s["recommended_total_price"] == 3200
    assert s["total_diff_amount"] == 200


@pytest.mark.asyncio
async def test_accept_recommendation(client, db_session):
    token = await _register_and_login(client, {"email": "dp10@test.com", "password": "Pw12345!", "full_name": "DP10"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "ACC001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 2499},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))

    recs = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))).json()["items"]
    rec_id = recs[0]["id"]

    r2 = await client.post(f"{RECS_URL}/{rec_id}/accept", headers=_auth(token))
    assert r2.status_code == 200
    assert r2.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_reject_recommendation(client, db_session):
    token = await _register_and_login(client, {"email": "dp11@test.com", "password": "Pw12345!", "full_name": "DP11"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "REJ001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 2499},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))

    recs = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))).json()["items"]
    rec_id = recs[0]["id"]

    r2 = await client.post(f"{RECS_URL}/{rec_id}/reject", headers=_auth(token))
    assert r2.status_code == 200
    assert r2.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_cannot_accept_other_org_recommendation(client, db_session):
    token_a = await _register_and_login(client, {"email": "dp12a@test.com", "password": "Pw12345!", "full_name": "DP12A"})
    org_a = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_a)
    listing = await _setup_listing(db_session, org_a, "ISO001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 1999},
    }, headers=_auth(token_a))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token_a))
    recs = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token_a))).json()["items"]
    rec_id = recs[0]["id"]

    token_b = await _register_and_login(client, {"email": "dp12b@test.com", "password": "Pw12345!", "full_name": "DP12B"})
    r2 = await client.post(f"{RECS_URL}/{rec_id}/accept", headers=_auth(token_b))
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_accept_all(client, db_session):
    token = await _register_and_login(client, {"email": "dp13@test.com", "password": "Pw12345!", "full_name": "DP13"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    l1 = await _setup_listing(db_session, org_id, "AA001", price_amount=1000)
    l2 = await _setup_listing(db_session, org_id, "AA002", price_amount=2000)

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [l1.id, l2.id],
        "rule_type": "percentage_adjustment",
        "rule_payload": {"percent": 5},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))

    r2 = await client.post(f"{JOBS_URL}/{job_id}/accept-all", headers=_auth(token))
    assert r2.status_code == 200
    assert r2.json()["accepted_count"] == 2

    recs = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))).json()["items"]
    assert all(r["status"] == "accepted" for r in recs)


@pytest.mark.asyncio
async def test_convert_requires_accepted_recommendation(client, db_session):
    token = await _register_and_login(client, {"email": "dp14@test.com", "password": "Pw12345!", "full_name": "DP14"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "CNV001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 1999},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))

    # Try to convert without accepting
    r2 = await client.post(f"{JOBS_URL}/{job_id}/convert", headers=_auth(token))
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_convert_creates_bulk_edit_session(client, db_session):
    token = await _register_and_login(client, {"email": "dp15@test.com", "password": "Pw12345!", "full_name": "DP15"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "CONV002", price_amount=2000)

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 2499},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))

    recs = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))).json()["items"]
    await client.post(f"{RECS_URL}/{recs[0]['id']}/accept", headers=_auth(token))

    r2 = await client.post(f"{JOBS_URL}/{job_id}/convert", headers=_auth(token))
    assert r2.status_code == 200
    data = r2.json()
    assert "bulk_edit_session_id" in data
    assert data["converted_count"] == 1
    assert data["created_changes"] == 1


@pytest.mark.asyncio
async def test_convert_creates_change_with_target_listing_ids(client, db_session):
    token = await _register_and_login(client, {"email": "dp16@test.com", "password": "Pw12345!", "full_name": "DP16"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "TGT001", price_amount=1500)

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 1999},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))
    recs = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))).json()["items"]
    await client.post(f"{RECS_URL}/{recs[0]['id']}/accept", headers=_auth(token))

    r2 = await client.post(f"{JOBS_URL}/{job_id}/convert", headers=_auth(token))
    session_id = r2.json()["bulk_edit_session_id"]

    from app.models.bulk_edit_change import BulkEditChange
    changes_result = await db_session.execute(
        select(BulkEditChange).where(BulkEditChange.bulk_edit_session_id == session_id)
    )
    changes = changes_result.scalars().all()
    assert len(changes) == 1
    assert changes[0].target_listing_ids == [listing.id]
    assert changes[0].new_value == 1999


@pytest.mark.asyncio
async def test_convert_does_not_update_listing_price(client, db_session):
    """Convert must NOT update Listing.price_amount directly."""
    token = await _register_and_login(client, {"email": "dp17@test.com", "password": "Pw12345!", "full_name": "DP17"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "NOUPD001", price_amount=1000)

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 5000},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))
    recs = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))).json()["items"]
    await client.post(f"{RECS_URL}/{recs[0]['id']}/accept", headers=_auth(token))
    await client.post(f"{JOBS_URL}/{job_id}/convert", headers=_auth(token))

    from app.models.listing import Listing
    await db_session.refresh(listing)
    # price_amount must still be 1000 — we never write to Listing directly
    assert listing.price_amount == 1000


@pytest.mark.asyncio
async def test_convert_marks_recommendations_converted(client, db_session):
    token = await _register_and_login(client, {"email": "dp18@test.com", "password": "Pw12345!", "full_name": "DP18"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "CONV003", price_amount=1200)

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "percentage_adjustment",
        "rule_payload": {"percent": 20},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))
    recs = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))).json()["items"]
    rec_id = recs[0]["id"]
    await client.post(f"{RECS_URL}/{rec_id}/accept", headers=_auth(token))
    await client.post(f"{JOBS_URL}/{job_id}/convert", headers=_auth(token))

    recs2 = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))).json()["items"]
    assert recs2[0]["status"] == "converted"


@pytest.mark.asyncio
async def test_org_isolation_job_detail(client, db_session):
    token_a = await _register_and_login(client, {"email": "dp19a@test.com", "password": "Pw12345!", "full_name": "DP19A"})
    org_a = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_a)
    listing = await _setup_listing(db_session, org_a, "ISO_A001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 1500},
    }, headers=_auth(token_a))
    job_id = r.json()["id"]

    token_b = await _register_and_login(client, {"email": "dp19b@test.com", "password": "Pw12345!", "full_name": "DP19B"})
    r2 = await client.get(f"{JOBS_URL}/{job_id}", headers=_auth(token_b))
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_org_isolation_recommendations(client, db_session):
    token_a = await _register_and_login(client, {"email": "dp20a@test.com", "password": "Pw12345!", "full_name": "DP20A"})
    org_a = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_a)
    listing = await _setup_listing(db_session, org_a, "ISO_B001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 1500},
    }, headers=_auth(token_a))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token_a))

    token_b = await _register_and_login(client, {"email": "dp20b@test.com", "password": "Pw12345!", "full_name": "DP20B"})
    r2 = await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token_b))
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_org_isolation_convert(client, db_session):
    token_a = await _register_and_login(client, {"email": "dp21a@test.com", "password": "Pw12345!", "full_name": "DP21A"})
    org_a = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_a)
    listing = await _setup_listing(db_session, org_a, "ISO_C001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 1500},
    }, headers=_auth(token_a))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token_a))

    token_b = await _register_and_login(client, {"email": "dp21b@test.com", "password": "Pw12345!", "full_name": "DP21B"})
    r2 = await client.post(f"{JOBS_URL}/{job_id}/convert", headers=_auth(token_b))
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_paid_feature_gate_free_plan(client, db_session):
    token = await _register_and_login(client, {"email": "dp22@test.com", "password": "Pw12345!", "full_name": "DP22"})
    org_id = await _get_org_id(db_session)
    listing = await _setup_listing(db_session, org_id, "FREE001")

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 1999},
    }, headers=_auth(token))
    job_id = r.json()["id"]

    # Preview should fail — free plan can't use dynamic pricing
    r2 = await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))
    assert r2.status_code == 402


@pytest.mark.asyncio
async def test_accept_all_skips_invalid(client, db_session):
    """accept-all must not accept skipped/invalid recommendations."""
    token = await _register_and_login(client, {"email": "dp23@test.com", "password": "Pw12345!", "full_name": "DP23"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    # Normal listing
    l1 = await _setup_listing(db_session, org_id, "AA2001", price_amount=1000)
    # Variation listing (will be skipped)
    l2 = await _setup_listing(db_session, org_id, "AA2002", has_variations=True, price_amount=2000)

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [l1.id, l2.id],
        "rule_type": "percentage_adjustment",
        "rule_payload": {"percent": 5},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))

    r2 = await client.post(f"{JOBS_URL}/{job_id}/accept-all", headers=_auth(token))
    assert r2.status_code == 200
    # Only 1 accepted (the non-variation listing)
    assert r2.json()["accepted_count"] == 1

    recs = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))).json()["items"]
    statuses = {r["status"] for r in recs}
    assert "skipped" in statuses
    assert "accepted" in statuses


@pytest.mark.asyncio
async def test_list_jobs_auth(client, db_session):
    r = await client.get(JOBS_URL)
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_jobs_returns_own_jobs(client, db_session):
    token = await _register_and_login(client, {"email": "dp24@test.com", "password": "Pw12345!", "full_name": "DP24"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "LST001")

    await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 999},
    }, headers=_auth(token))

    r = await client.get(JOBS_URL, headers=_auth(token))
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_warning_when_no_price_change(client, db_session):
    """Same-price recommendation should be warning status."""
    token = await _register_and_login(client, {"email": "dp25@test.com", "password": "Pw12345!", "full_name": "DP25"})
    org_id = await _get_org_id(db_session)
    await _upgrade_to_pro(db_session, org_id)
    listing = await _setup_listing(db_session, org_id, "SAME001", price_amount=2499)

    r = await client.post(JOBS_URL, json={
        "selected_listing_ids": [listing.id],
        "rule_type": "set_price",
        "rule_payload": {"price_amount": 2499},
    }, headers=_auth(token))
    job_id = r.json()["id"]
    await client.post(f"{JOBS_URL}/{job_id}/preview", headers=_auth(token))

    recs = (await client.get(f"{JOBS_URL}/{job_id}/recommendations", headers=_auth(token))).json()["items"]
    assert recs[0]["status"] == "warning"
    assert "No price change" in recs[0]["reason"]
