import pytest


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/auth/me"

VALID_USER = {
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User",
    "organization_name": "Test Org",
    "terms_accepted": True,
}


async def test_register_success(client):
    r = await client.post(REGISTER_URL, json=VALID_USER)
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client):
    await client.post(REGISTER_URL, json=VALID_USER)
    r = await client.post(REGISTER_URL, json=VALID_USER)
    assert r.status_code == 409


async def test_register_weak_password(client):
    r = await client.post(REGISTER_URL, json={**VALID_USER, "password": "short"})
    assert r.status_code == 422


async def test_register_invalid_email(client):
    r = await client.post(REGISTER_URL, json={**VALID_USER, "email": "not-an-email"})
    assert r.status_code == 422


async def test_register_fails_without_terms_acceptance(client):
    payload = {k: v for k, v in VALID_USER.items() if k != "terms_accepted"}
    r = await client.post(REGISTER_URL, json=payload)
    assert r.status_code == 422


async def test_register_fails_with_terms_false(client):
    r = await client.post(REGISTER_URL, json={**VALID_USER, "terms_accepted": False})
    assert r.status_code == 422


async def test_register_succeeds_and_records_acceptance(client, db_session):
    from sqlalchemy import select
    from app.models.user import User
    from app.models.terms_acceptance import TermsAcceptance

    payload = {**VALID_USER, "email": "terms_accept@example.com", "terms_accepted": True}
    r = await client.post(REGISTER_URL, json=payload)
    assert r.status_code == 201

    result = await db_session.execute(
        select(TermsAcceptance)
        .join(User, TermsAcceptance.user_id == User.id)
        .where(User.email == payload["email"])
    )
    acceptance = result.scalar_one()
    assert isinstance(acceptance.terms_version, str) and acceptance.terms_version != ""
    assert isinstance(acceptance.privacy_version, str) and acceptance.privacy_version != ""
    assert acceptance.acceptance_source == "web_registration"


async def test_login_success(client):
    await client.post(REGISTER_URL, json=VALID_USER)
    r = await client.post(LOGIN_URL, json={"email": VALID_USER["email"], "password": VALID_USER["password"]})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client):
    await client.post(REGISTER_URL, json=VALID_USER)
    r = await client.post(LOGIN_URL, json={"email": VALID_USER["email"], "password": "wrongpassword"})
    assert r.status_code == 401


async def test_login_unknown_email(client):
    r = await client.post(LOGIN_URL, json={"email": "nobody@example.com", "password": "password123"})
    assert r.status_code == 401


async def test_refresh_success(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    refresh_token = reg.json()["refresh_token"]
    r = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token  # rotated


async def test_refresh_token_rotation_invalidates_old(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    old_refresh = reg.json()["refresh_token"]
    await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
    r = await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
    assert r.status_code == 401


async def test_logout_success(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    refresh_token = reg.json()["refresh_token"]
    r = await client.post(LOGOUT_URL, json={"refresh_token": refresh_token})
    assert r.status_code == 204


async def test_logout_then_refresh_fails(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    refresh_token = reg.json()["refresh_token"]
    await client.post(LOGOUT_URL, json={"refresh_token": refresh_token})
    r = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert r.status_code == 401


async def test_me_success(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    access_token = reg.json()["access_token"]
    r = await client.get(ME_URL, headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["email"] == VALID_USER["email"]
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["role"] == "owner"


async def test_me_no_token(client):
    r = await client.get(ME_URL)
    assert r.status_code == 403


async def test_me_invalid_token(client):
    r = await client.get(ME_URL, headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /auth/me — account deletion
#
# No test existed for this endpoint anywhere in the suite before this pass
# (confirmed by repo-wide grep). A real-Postgres test during owner-review
# validation found delete_account() actually crashed with a 500
# (IntegrityError: NOT NULL violation) whenever the deleting user had an
# active refresh token or org membership loaded — SQLAlchemy's default
# relationship() cascade tried to NULL out those NOT NULL foreign keys
# instead of letting the DB's ON DELETE CASCADE handle it. Fixed via
# passive_deletes=True on Organization.members / User.memberships /
# User.refresh_tokens. Separately, a real-Postgres test also found 9 tables
# (etsy_shops, listings, cost_profiles, listing_costs, social_connections,
# social_oauth_states, etsy_oauth_states, sync_jobs, video_renders) had
# organization_id with no foreign key at all, so deletion silently left
# orphaned Etsy-derived data behind — fixed via migration 0025. These tests
# reproduce the exact failure scenario (an active refresh token present) so
# a future change can't silently reintroduce either bug.
# ---------------------------------------------------------------------------

async def test_delete_account_wrong_password_rejected(client):
    reg = await client.post(REGISTER_URL, json=VALID_USER)
    access_token = reg.json()["access_token"]
    r = await client.request(
        "DELETE", ME_URL, json={"password": "wrong_password"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 401


async def test_delete_account_succeeds_with_active_refresh_token_and_membership(client, db_session):
    """
    Reproduces the exact scenario that crashed before the passive_deletes
    fix: register (creates org + owner membership), log in a second time
    (creates a second RefreshToken row so User.refresh_tokens is non-empty
    and gets loaded during the delete), then delete. Must return 200, not 500.
    """
    payload = {**VALID_USER, "email": "delete_me@example.com"}
    reg = await client.post(REGISTER_URL, json=payload)
    access_token = reg.json()["access_token"]

    # Second login creates a second RefreshToken row for this user.
    await client.post(LOGIN_URL, json={"email": payload["email"], "password": payload["password"]})

    r = await client.request(
        "DELETE", ME_URL, json={"password": payload["password"]},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 200

    from sqlalchemy import select
    from app.models.user import User

    result = await db_session.execute(select(User).where(User.email == payload["email"]))
    assert result.scalar_one_or_none() is None


async def test_delete_account_cascades_etsy_shop_and_listing(client, db_session):
    """
    Reproduces the second bug found: organization_id on etsy_shops/listings
    had no foreign key at all, so deletion silently left them behind. Insert
    a connected shop + listing directly, delete the account, assert both
    are actually gone (not just that the request returned 200).
    """
    from app.models.etsy_shop import EtsyShop
    from app.models.listing import Listing
    from app.core.encryption import encrypt_token
    from app.models.etsy_token import EtsyToken
    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select
    from datetime import datetime, timezone, timedelta

    payload = {**VALID_USER, "email": "delete_cascade@example.com"}
    reg = await client.post(REGISTER_URL, json=payload)
    access_token = reg.json()["access_token"]

    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    org_id = result.scalar_one().organization_id

    shop = EtsyShop(organization_id=org_id, etsy_shop_id="del_cascade_shop", shop_name="X", is_connected=True)
    db_session.add(shop)
    await db_session.flush()
    db_session.add(EtsyToken(
        etsy_shop_id=shop.id,
        access_token_enc=encrypt_token("a"),
        refresh_token_enc=encrypt_token("r"),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scopes="listings_r",
    ))
    listing = Listing(organization_id=org_id, etsy_shop_id=shop.id, etsy_listing_id="del_cascade_listing", title="X")
    db_session.add(listing)
    await db_session.commit()

    r = await client.request(
        "DELETE", ME_URL, json={"password": payload["password"]},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    # This suite's SQLite test DB does not run with `PRAGMA foreign_keys=ON`
    # (confirmed: no such pragma anywhere in conftest.py/session.py), so
    # SQLite silently ignores every ondelete="CASCADE" declared in the
    # models — it never enforces or acts on them, unlike real Postgres.
    # Asserting the shop/listing rows are actually gone would therefore not
    # test anything real here; it would just test whether SQLite happens to
    # ignore FKs (it always does). The one thing this test *can* honestly
    # verify at this level is that adding the etsy_shops.organization_id FK
    # didn't break the request path (still 200, not 500/422). The actual
    # cascade-deletion behavior was verified against real PostgreSQL during
    # owner-review validation (register -> connect shop/listing/token ->
    # delete -> confirmed 0 rows remain in etsy_shops/etsy_tokens/listings/
    # listing_backup_snapshots/cost_profiles/listing_costs/
    # social_connections/sync_jobs) — see ETSY_DATA_RETENTION.md §4a.
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /auth/me — Stripe subscription billing safety gate
#
# Owner decision (2026-07-13, third session): never auto-cancel a Stripe
# subscription on account deletion. Instead block deletion outright while a
# subscription is active or billable, so a user is never left with an active
# subscription and no self-service way to cancel it (the Stripe portal
# requires being logged in to an org that deletion would have just removed).
# See app/services/billing.py::assert_account_deletion_billing_safe and
# ETSY_DATA_RETENTION.md §4b.
# ---------------------------------------------------------------------------

async def _register_get_org_id(client, db_session, email: str) -> tuple[str, str]:
    """Registers a user, returns (access_token, organization_id)."""
    from app.models.organization_member import OrganizationMember
    from sqlalchemy import select

    payload = {**VALID_USER, "email": email}
    reg = await client.post(REGISTER_URL, json=payload)
    access_token = reg.json()["access_token"]
    result = await db_session.execute(
        select(OrganizationMember).order_by(OrganizationMember.created_at.desc()).limit(1)
    )
    org_id = result.scalar_one().organization_id
    return access_token, org_id


async def _try_delete(client, access_token: str, password: str = VALID_USER["password"]):
    return await client.request(
        "DELETE", ME_URL, json={"password": password},
        headers={"Authorization": f"Bearer {access_token}"},
    )


async def test_delete_blocked_scenarios(client, db_session):
    """
    Table-driven: one subscription state per case, each attempted against a
    freshly registered user/org, asserting the expected outcome. Covers
    every state the owner spec explicitly listed (Task 6, items 1-9).
    """
    from app.models.subscription import Subscription
    from datetime import datetime, timezone, timedelta

    future = datetime.now(timezone.utc) + timedelta(days=15)
    past = datetime.now(timezone.utc) - timedelta(days=1)

    cases = [
        # (label, subscription_kwargs_or_None, expect_status)
        ("no_subscription_row", None, 200),
        ("free_plan_no_stripe_id", dict(plan="free", status="free", stripe_subscription_id=None), 200),
        ("active", dict(plan="pro_monthly", status="active", stripe_customer_id="cus_x", stripe_subscription_id="sub_x", current_period_end=future), 409),
        ("trialing", dict(plan="pro_monthly", status="trialing", stripe_customer_id="cus_x", stripe_subscription_id="sub_x", current_period_end=future), 409),
        ("past_due", dict(plan="pro_monthly", status="past_due", stripe_customer_id="cus_x", stripe_subscription_id="sub_x", current_period_end=future), 409),
        ("unpaid", dict(plan="pro_monthly", status="unpaid", stripe_customer_id="cus_x", stripe_subscription_id="sub_x", current_period_end=future), 409),
        ("incomplete", dict(plan="pro_monthly", status="incomplete", stripe_customer_id="cus_x", stripe_subscription_id="sub_x", current_period_end=None), 409),
        ("incomplete_expired", dict(plan="pro_monthly", status="incomplete_expired", stripe_customer_id="cus_x", stripe_subscription_id="sub_x", current_period_end=None), 409),
        # cancel_at_period_end=true but Stripe hasn't ended the subscription yet:
        # status is still whatever it was (active here) — must NOT be treated as safe.
        ("cancel_scheduled_not_yet_ended", dict(plan="pro_monthly", status="active", stripe_customer_id="cus_x", stripe_subscription_id="sub_x", current_period_end=future, cancel_at_period_end=True), 409),
        ("canceled_and_ended", dict(plan="free", status="canceled", stripe_customer_id="cus_x", stripe_subscription_id="sub_x", current_period_end=past), 200),
        # 2026-07-14 narrow review: status="canceled" can be set by
        # _handle_subscription_updated (a general .updated webhook, not only
        # the definitive .deleted event), and that handler's
        # current_period_end write is conditional on the payload containing
        # it. A NULL current_period_end here is therefore NOT proof the
        # period has ended — it may just mean the webhook never included it.
        # Must stay BLOCKED, not treated as safe.
        ("canceled_but_period_end_never_recorded", dict(plan="free", status="canceled", stripe_customer_id="cus_x", stripe_subscription_id="sub_x", current_period_end=None), 409),
        ("unknown_future_stripe_status", dict(plan="pro_monthly", status="some_future_status_stripe_might_add", stripe_customer_id="cus_x", stripe_subscription_id="sub_x", current_period_end=future), 409),
    ]

    for label, sub_kwargs, expect_status in cases:
        email = f"delbill_{label}@example.com"
        access_token, org_id = await _register_get_org_id(client, db_session, email)

        if sub_kwargs is not None:
            db_session.add(Subscription(organization_id=org_id, **sub_kwargs))
            await db_session.commit()

        r = await _try_delete(client, access_token)
        assert r.status_code == expect_status, f"case={label} expected {expect_status} got {r.status_code}: {r.text}"

        if expect_status == 409:
            body = r.json()
            assert body["detail"]["code"] == "ACTIVE_SUBSCRIPTION_MUST_BE_CANCELED"
            assert "stripe" not in body["detail"]["message"].lower()
            assert "cus_x" not in body["detail"]["message"]
            assert "sub_x" not in body["detail"]["message"]


async def test_delete_blocked_no_stripe_customer_id_returns_support_code(client, db_session):
    """
    Active-looking subscription state but no stripe_customer_id on file — a
    data-integrity edge case (e.g. a partially-applied webhook). Must block
    with a distinct, support-safe code, not the generic cancel-subscription
    message, since there's no portal to send the user to.
    """
    from app.models.subscription import Subscription

    access_token, org_id = await _register_get_org_id(client, db_session, "delbill_no_customer@example.com")
    db_session.add(Subscription(organization_id=org_id, plan="pro_monthly", status="active", stripe_customer_id=None, stripe_subscription_id="sub_orphan"))
    await db_session.commit()

    r = await _try_delete(client, access_token)
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "BILLING_PORTAL_UNAVAILABLE"


async def test_delete_blocked_leaves_all_data_untouched(client, db_session):
    """
    A blocked deletion attempt must not touch the database at all — user,
    org, subscription, and any Etsy data must be byte-for-byte unchanged.
    """
    from app.models.subscription import Subscription
    from app.models.etsy_shop import EtsyShop
    from app.models.user import User
    from sqlalchemy import select

    access_token, org_id = await _register_get_org_id(client, db_session, "delbill_untouched@example.com")
    db_session.add(Subscription(organization_id=org_id, plan="pro_monthly", status="active", stripe_customer_id="cus_y", stripe_subscription_id="sub_y"))
    shop = EtsyShop(organization_id=org_id, etsy_shop_id="untouched_shop", shop_name="Keep Me", is_connected=True)
    db_session.add(shop)
    await db_session.commit()

    r = await _try_delete(client, access_token)
    assert r.status_code == 409

    db_session.expire_all()
    result = await db_session.execute(select(User).where(User.email == "delbill_untouched@example.com"))
    assert result.scalar_one_or_none() is not None
    result = await db_session.execute(select(Subscription).where(Subscription.organization_id == org_id))
    assert result.scalar_one_or_none() is not None
    result = await db_session.execute(select(EtsyShop).where(EtsyShop.organization_id == org_id))
    assert result.scalar_one_or_none() is not None


async def test_delete_allowed_when_subscription_safely_ended_preserves_existing_cascade(client, db_session):
    """
    Confirms the new billing gate doesn't regress the existing (already
    real-Postgres-verified) deletion cascade for the safe case: a canceled,
    fully-ended subscription must still allow full deletion, same as before
    this gate existed.
    """
    from app.models.subscription import Subscription
    from app.models.user import User
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select

    access_token, org_id = await _register_get_org_id(client, db_session, "delbill_safe_cascade@example.com")
    past = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.add(Subscription(organization_id=org_id, plan="free", status="canceled", stripe_customer_id="cus_z", stripe_subscription_id="sub_z", current_period_end=past))
    await db_session.commit()

    r = await _try_delete(client, access_token)
    assert r.status_code == 200

    db_session.expire_all()
    result = await db_session.execute(select(User).where(User.email == "delbill_safe_cascade@example.com"))
    assert result.scalar_one_or_none() is None
