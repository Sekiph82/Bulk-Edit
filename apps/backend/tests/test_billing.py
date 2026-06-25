"""
Billing tests.

Stripe is not configured in the test environment (keys are placeholders),
so checkout/portal return 503. Webhook tests mock stripe.Webhook.construct_event.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

REGISTER_URL = "/api/v1/auth/register"
PLANS_URL = "/api/v1/billing/plans"
SUBSCRIPTION_URL = "/api/v1/billing/subscription"
CHECKOUT_URL = "/api/v1/billing/checkout"
PORTAL_URL = "/api/v1/billing/portal"
WEBHOOK_URL = "/api/v1/billing/webhook"
USAGE_URL = "/api/v1/billing/usage"


@pytest.fixture
async def auth_headers(client):
    r = await client.post(REGISTER_URL, json={
        "email": "billing@example.com",
        "password": "password123",
        "full_name": "Billing User",
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─── Plans ────────────────────────────────────────────────────────────────────

async def test_get_plans_no_auth(client):
    r = await client.get(PLANS_URL)
    assert r.status_code == 200
    data = r.json()
    assert "plans" in data
    assert "free" in data["plans"]
    assert "basic_monthly" in data["plans"]
    assert "pro_monthly" in data["plans"]
    assert "basic_yearly" in data["plans"]
    assert "pro_yearly" in data["plans"]


async def test_free_plan_limits(client):
    r = await client.get(PLANS_URL)
    free = r.json()["plans"]["free"]
    assert free["max_listings"] == 25
    assert free["bulk_edits_per_month"] == 10
    assert free["can_use_magic_revert"] == False
    assert free["can_bulk_edit_photos"] == False


async def test_pro_plan_limits(client):
    r = await client.get(PLANS_URL)
    pro = r.json()["plans"]["pro_monthly"]
    assert pro["max_listings"] == 10000
    assert pro["bulk_edits_per_month"] == 5000
    assert pro["can_use_magic_revert"] == True
    assert pro["can_use_dynamic_pricing"] == True


# ─── Subscription ─────────────────────────────────────────────────────────────

async def test_get_subscription_requires_auth(client):
    r = await client.get(SUBSCRIPTION_URL)
    assert r.status_code == 403


async def test_get_subscription_creates_free(client, auth_headers):
    r = await client.get(SUBSCRIPTION_URL, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["plan"] == "free"
    assert data["status"] == "free"
    assert data["stripe_customer_id"] is None
    assert "limits" in data
    assert data["limits"]["max_listings"] == 25


async def test_get_subscription_idempotent(client, auth_headers):
    await client.get(SUBSCRIPTION_URL, headers=auth_headers)
    r = await client.get(SUBSCRIPTION_URL, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["plan"] == "free"


# ─── Checkout ─────────────────────────────────────────────────────────────────

async def test_checkout_requires_auth(client):
    r = await client.post(CHECKOUT_URL, json={"plan": "basic_monthly"})
    assert r.status_code == 403


async def test_checkout_rejects_free_plan(client, auth_headers):
    r = await client.post(CHECKOUT_URL, json={"plan": "free"}, headers=auth_headers)
    assert r.status_code == 400
    assert "free" in r.json()["detail"].lower()


async def test_checkout_rejects_invalid_plan(client, auth_headers):
    r = await client.post(CHECKOUT_URL, json={"plan": "diamond"}, headers=auth_headers)
    assert r.status_code == 422


async def test_checkout_503_stripe_not_configured(client, auth_headers):
    r = await client.post(CHECKOUT_URL, json={"plan": "basic_monthly"}, headers=auth_headers)
    assert r.status_code == 503
    assert "Stripe" in r.json()["detail"]


async def test_checkout_503_for_all_paid_plans(client, auth_headers):
    for plan in ("basic_monthly", "pro_monthly", "basic_yearly", "pro_yearly"):
        r = await client.post(CHECKOUT_URL, json={"plan": plan}, headers=auth_headers)
        assert r.status_code == 503, f"Expected 503 for plan={plan}, got {r.status_code}"


# ─── Portal ───────────────────────────────────────────────────────────────────

async def test_portal_requires_auth(client):
    r = await client.post(PORTAL_URL)
    assert r.status_code == 403


async def test_portal_503_stripe_not_configured(client, auth_headers):
    r = await client.post(PORTAL_URL, headers=auth_headers)
    assert r.status_code == 503


# ─── Usage ────────────────────────────────────────────────────────────────────

async def test_usage_requires_auth(client):
    r = await client.get(USAGE_URL)
    assert r.status_code == 403


async def test_usage_returns_counters_and_limits(client, auth_headers):
    r = await client.get(USAGE_URL, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "period_key" in data
    assert "usage" in data
    assert "limits" in data
    assert "bulk_edits_used" in data["usage"]
    assert "ai_credits_used" in data["usage"]
    assert data["usage"]["bulk_edits_used"] == 0
    assert data["limits"]["bulk_edits_per_month"] == 10


async def test_usage_period_key_format(client, auth_headers):
    r = await client.get(USAGE_URL, headers=auth_headers)
    period = r.json()["period_key"]
    assert len(period) == 7
    assert period[4] == "-"


# ─── Feature gate (service-level unit tests) ──────────────────────────────────

async def test_feature_gate_free_plan():
    from app.core.plans import get_plan_limits
    limits = get_plan_limits("free")
    assert limits["can_use_magic_revert"] == False
    assert limits["can_bulk_edit_photos"] == False
    assert limits["can_use_dynamic_pricing"] == False
    assert limits["can_schedule_jobs"] == False
    assert limits["bulk_edits_per_month"] == 10
    assert limits["ai_credits_per_month"] == 5


async def test_feature_gate_basic_plan():
    from app.core.plans import get_plan_limits
    limits = get_plan_limits("basic_monthly")
    assert limits["can_use_magic_revert"] == True
    assert limits["can_bulk_edit_photos"] == True
    assert limits["can_use_dynamic_pricing"] == False
    assert limits["can_schedule_jobs"] == True
    assert limits["bulk_edits_per_month"] == 250


async def test_feature_gate_pro_plan():
    from app.core.plans import get_plan_limits
    limits = get_plan_limits("pro_monthly")
    assert limits["can_use_magic_revert"] == True
    assert limits["can_use_dynamic_pricing"] == True
    assert limits["can_bulk_edit_variations"] == True
    assert limits["bulk_edits_per_month"] == 5000


async def test_yearly_plans_same_limits_as_monthly():
    from app.core.plans import get_plan_limits
    assert get_plan_limits("basic_yearly") == get_plan_limits("basic_monthly")
    assert get_plan_limits("pro_yearly") == get_plan_limits("pro_monthly")


async def test_unknown_plan_defaults_to_free():
    from app.core.plans import get_plan_limits
    limits = get_plan_limits("enterprise_ultra")
    assert limits == get_plan_limits("free")


# ─── Webhook ──────────────────────────────────────────────────────────────────

async def test_webhook_503_no_secret(client):
    r = await client.post(WEBHOOK_URL, content=b'{"type":"test"}')
    assert r.status_code == 503
    assert "webhook" in r.json()["detail"].lower()


async def test_webhook_400_invalid_signature(client):
    from unittest.mock import MagicMock
    mock_settings = MagicMock()
    mock_settings.is_stripe_webhook_configured.return_value = True
    mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"

    with patch("app.api.v1.billing.settings", mock_settings), \
         patch("stripe.Webhook.construct_event", side_effect=ValueError("No signatures found")):
        r = await client.post(
            WEBHOOK_URL,
            content=b'{"id":"evt_test","type":"test"}',
            headers={"stripe-signature": "t=invalid,v1=invalid"},
        )
    assert r.status_code == 400


async def test_webhook_duplicate_event_idempotent(client, db_session):
    from app.models.billing_event import BillingEvent
    from app.services.billing import process_webhook_event

    fake_event = {
        "id": "evt_duplicate_test_001",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {},
                "customer": None,
                "subscription": None,
            }
        },
    }

    await process_webhook_event(fake_event, db_session)
    await process_webhook_event(fake_event, db_session)

    from sqlalchemy import select
    result = await db_session.execute(
        select(BillingEvent).where(BillingEvent.stripe_event_id == "evt_duplicate_test_001")
    )
    events = result.scalars().all()
    assert len(events) == 1


async def test_webhook_processes_checkout_completed(client, db_session, auth_headers):
    from app.services.billing import ensure_subscription_exists, process_webhook_event

    r = await client.get(SUBSCRIPTION_URL, headers=auth_headers)
    org_id = r.json()["organization_id"]

    fake_event = {
        "id": "evt_checkout_001",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"organization_id": org_id, "plan": "pro_monthly"},
                "customer": "cus_test_001",
                "subscription": "sub_test_001",
            }
        },
    }

    await process_webhook_event(fake_event, db_session)

    from sqlalchemy import select
    from app.models.subscription import Subscription
    result = await db_session.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    sub = result.scalar_one_or_none()
    assert sub is not None
    assert sub.plan == "pro_monthly"
    assert sub.status == "active"
    assert sub.stripe_customer_id == "cus_test_001"
    assert sub.stripe_subscription_id == "sub_test_001"


async def test_webhook_subscription_deleted_reverts_to_free(client, db_session, auth_headers):
    from app.services.billing import ensure_subscription_exists, process_webhook_event
    from app.models.subscription import Subscription
    from sqlalchemy import select

    r = await client.get(SUBSCRIPTION_URL, headers=auth_headers)
    org_id = r.json()["organization_id"]

    checkout_event = {
        "id": "evt_checkout_002",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"organization_id": org_id, "plan": "basic_monthly"},
                "customer": "cus_test_002",
                "subscription": "sub_test_002",
            }
        },
    }
    await process_webhook_event(checkout_event, db_session)

    delete_event = {
        "id": "evt_delete_002",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {"id": "sub_test_002"}
        },
    }
    await process_webhook_event(delete_event, db_session)

    result = await db_session.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    sub = result.scalar_one_or_none()
    assert sub.plan == "free"
    assert sub.status == "canceled"
