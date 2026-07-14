"""
Sprint 24 tests: Profit & Cost Calculator engine and API endpoints.
All calculations use Decimal for monetary precision.
"""
import pytest
from decimal import Decimal

from app.services.profit import calculate_profit, profit_status

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ZERO = Decimal("0")


async def _register_and_login(client, email: str, org: str) -> str:
    await client.post(REGISTER_URL, json={
        "email": email, "password": "Test1234!", "full_name": "Test", "organization_name": org,
        "terms_accepted": True,
    })
    r = await client.post(LOGIN_URL, json={"email": email, "password": "Test1234!"})
    return r.json()["access_token"]


# ── Unit tests for the profit calculation engine ───────────────────────────────

def test_basic_profit_calculation():
    result = calculate_profit(
        sale_price=Decimal("20.00"),
        product_cost=Decimal("5.00"),
    )
    # gross = 20, txn_fee = 20*0.065 = 1.30, pmt_fee = 20*0.03 + 0.25 = 0.85, listing = 0.20
    # total_etsy = 2.35, total_costs = 2.35 + 5.00 = 7.35
    # net_profit = 20 - 7.35 = 12.65
    assert result["gross_revenue"] == Decimal("20.00")
    assert result["etsy_transaction_fee"] == Decimal("1.30")
    assert result["etsy_payment_fee"] == Decimal("0.85")
    assert result["etsy_listing_fee"] == Decimal("0.20")
    assert result["net_profit"] == Decimal("12.65")
    assert result["margin_percent"] > Decimal("60")


def test_shipping_charged_adds_to_gross_revenue():
    result = calculate_profit(
        sale_price=Decimal("20.00"),
        shipping_charged=Decimal("5.00"),
    )
    assert result["gross_revenue"] == Decimal("25.00")


def test_transaction_fee_percent():
    result = calculate_profit(sale_price=Decimal("100.00"), transaction_fee_percent=Decimal("0.065"))
    assert result["etsy_transaction_fee"] == Decimal("6.50")


def test_payment_fee_percent_plus_fixed():
    result = calculate_profit(
        sale_price=Decimal("100.00"),
        payment_fee_percent=Decimal("0.030"),
        payment_fixed_fee=Decimal("0.25"),
    )
    assert result["etsy_payment_fee"] == Decimal("3.25")


def test_offsite_ads_not_applied_by_default():
    result = calculate_profit(sale_price=Decimal("20.00"), include_offsite_ads=False)
    assert result["etsy_offsite_ads_fee"] == ZERO


def test_offsite_ads_applied_when_enabled():
    result = calculate_profit(
        sale_price=Decimal("20.00"),
        include_offsite_ads=True,
        offsite_ads_percent=Decimal("0.15"),
    )
    assert result["etsy_offsite_ads_fee"] == Decimal("3.00")


def test_profit_status_profitable():
    status = profit_status(
        net_profit=Decimal("10.00"),
        margin_percent=Decimal("40.00"),
        target_margin_percent=Decimal("0.30"),
    )
    assert status == "profitable"


def test_profit_status_low_margin():
    status = profit_status(
        net_profit=Decimal("1.00"),
        margin_percent=Decimal("10.00"),
        target_margin_percent=Decimal("0.30"),
    )
    assert status == "low_margin"


def test_profit_status_loss():
    status = profit_status(
        net_profit=Decimal("-1.00"),
        margin_percent=Decimal("-5.00"),
        target_margin_percent=Decimal("0.30"),
    )
    assert status == "loss"


def test_break_even_price_positive():
    result = calculate_profit(
        sale_price=Decimal("20.00"),
        product_cost=Decimal("5.00"),
    )
    assert result["break_even_price"] > ZERO
    # At break-even price, profit should be ~0
    be = result["break_even_price"]
    verify = calculate_profit(
        sale_price=be,
        product_cost=Decimal("5.00"),
    )
    assert abs(verify["net_profit"]) < Decimal("0.10")  # within 10 cents due to rounding


def test_recommended_min_price_gte_break_even():
    result = calculate_profit(
        sale_price=Decimal("20.00"),
        product_cost=Decimal("5.00"),
        target_margin_percent=Decimal("0.30"),
    )
    assert result["recommended_min_price"] >= result["break_even_price"]


def test_no_division_by_zero_when_price_zero():
    result = calculate_profit(sale_price=ZERO, product_cost=Decimal("5.00"))
    assert result["gross_revenue"] == ZERO
    assert result["margin_percent"] == ZERO
    assert result["net_profit"] < ZERO  # costs still apply → loss


def test_all_costs_included_in_total():
    result = calculate_profit(
        sale_price=Decimal("50.00"),
        product_cost=Decimal("10.00"),
        shipping_cost=Decimal("3.00"),
        packaging_cost=Decimal("1.00"),
        ad_cost=Decimal("2.00"),
        other_cost=Decimal("0.50"),
    )
    direct_total = Decimal("10.00") + Decimal("3.00") + Decimal("1.00") + Decimal("2.00") + Decimal("0.50")
    assert result["total_costs"] == result["total_etsy_fees"] + direct_total


# ── API endpoint tests ─────────────────────────────────────────────────────────

async def test_profit_summary_requires_auth(client):
    r = await client.get("/api/v1/profit/summary")
    assert r.status_code in (401, 403)


async def test_profit_listings_requires_auth(client):
    r = await client.get("/api/v1/profit/listings")
    assert r.status_code in (401, 403)


async def test_profit_cost_profiles_requires_auth(client):
    r = await client.get("/api/v1/profit/cost-profiles")
    assert r.status_code in (401, 403)


async def test_profit_summary_authenticated(client):
    token = await _register_and_login(client, "profit_u1@test.com", "ProfitOrg1")
    r = await client.get("/api/v1/profit/summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "listings_with_costs" in data
    assert "listings_missing_costs" in data
    assert "low_margin_count" in data
    assert "loss_making_count" in data
    assert "currency" in data


async def test_profit_listings_authenticated(client):
    token = await _register_and_login(client, "profit_u2@test.com", "ProfitOrg2")
    r = await client.get("/api/v1/profit/listings", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


async def test_create_cost_profile(client):
    token = await _register_and_login(client, "profit_u3@test.com", "ProfitOrg3")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "My Fee Profile",
        "currency": "USD",
        "transaction_fee_percent": "0.065",
        "payment_fee_percent": "0.030",
        "payment_fixed_fee": "0.25",
        "listing_fee": "0.20",
        "offsite_ads_percent": "0.15",
        "currency_conversion_percent": "0.025",
        "default_shipping_cost": "0.0",
        "default_packaging_cost": "0.0",
        "target_margin_percent": "0.30",
        "is_default": True,
    }
    r = await client.post("/api/v1/profit/cost-profiles", json=payload, headers=headers)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "My Fee Profile"
    assert data["currency"] == "USD"
    assert "id" in data


async def test_upsert_listing_costs_404_for_unknown_listing(client):
    token = await _register_and_login(client, "profit_u4@test.com", "ProfitOrg4")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"product_cost": "5.00", "shipping_cost": "2.00", "packaging_cost": "0.50", "ad_cost": "0.00", "other_cost": "0.00", "include_offsite_ads": False}
    r = await client.put("/api/v1/profit/listings/nonexistent-listing-id/costs", json=payload, headers=headers)
    assert r.status_code == 404


async def test_profit_org_isolation(client):
    token_a = await _register_and_login(client, "profit_a@test.com", "ProfitOrgA")
    token_b = await _register_and_login(client, "profit_b@test.com", "ProfitOrgB")

    # Each user gets their own summary — no cross-contamination
    r_a = await client.get("/api/v1/profit/summary", headers={"Authorization": f"Bearer {token_a}"})
    r_b = await client.get("/api/v1/profit/summary", headers={"Authorization": f"Bearer {token_b}"})
    assert r_a.status_code == 200
    assert r_b.status_code == 200
    assert r_a.json()["listings_with_costs"] == 0
    assert r_b.json()["listings_with_costs"] == 0


async def test_profit_response_no_secrets(client):
    token = await _register_and_login(client, "profit_sec@test.com", "ProfitSecOrg")
    r = await client.get("/api/v1/profit/summary", headers={"Authorization": f"Bearer {token}"})
    text = r.text
    for secret_field in ["password_hash", "etsy_access_token", "stripe_secret", "api_key"]:
        assert secret_field not in text.lower()


async def test_profit_listing_detail_404(client):
    token = await _register_and_login(client, "profit_u5@test.com", "ProfitOrg5")
    r = await client.get("/api/v1/profit/listings/nonexistent", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
