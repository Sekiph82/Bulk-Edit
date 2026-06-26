"""
Tests for the local superuser seed service and startup hook.
Tests run against the in-memory SQLite test DB from conftest.
Login tests use the standard auth endpoint — login logic is unchanged.
"""
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import select

from app.core.security import verify_password
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.subscription import Subscription
from app.models.user import User
from app.services.local_seed import (
    SeedConfigError,
    _require,
    load_seed_config,
    seed_on_startup,
    seed_superuser,
)


# ── helpers ────────────────────────────────────────────────────────────────

def _make_env_file(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
    f.write(content)
    f.flush()
    f.close()
    return Path(f.name)


EXAMPLE_ENV = (
    "FREE_SUPERUSER_EMAIL=free@startup.test\n"
    "FREE_SUPERUSER_PASSWORD=FreePass1!\n"
    "FREE_SUPERUSER_FULL_NAME=Free Startup User\n"
    "FREE_SUPERUSER_ORG_NAME=Free Startup Org\n"
    "PAID_SUPERUSER_EMAIL=paid@startup.test\n"
    "PAID_SUPERUSER_PASSWORD=PaidPass1!\n"
    "PAID_SUPERUSER_FULL_NAME=Paid Startup User\n"
    "PAID_SUPERUSER_ORG_NAME=Paid Startup Org\n"
    "PAID_SUPERUSER_PLAN=pro_monthly\n"
)


# ── load_seed_config tests ─────────────────────────────────────────────────

def test_load_seed_config_missing_file_raises():
    with pytest.raises(SeedConfigError) as exc_info:
        load_seed_config(Path("/nonexistent/path/.local-superusers.env"))
    msg = str(exc_info.value)
    assert "not found" in msg.lower() or "seed config" in msg.lower()
    assert ".env.example" in msg or "example" in msg.lower()


def test_load_seed_config_missing_file_mentions_copy_instructions():
    with pytest.raises(SeedConfigError) as exc_info:
        load_seed_config(Path("/nonexistent/.local-superusers.env"))
    msg = str(exc_info.value)
    assert "copy" in msg.lower() or "Copy" in msg


def test_load_seed_config_parses_example_style_env():
    tmp = _make_env_file(EXAMPLE_ENV)
    try:
        config = load_seed_config(tmp)
        assert config["FREE_SUPERUSER_EMAIL"] == "free@startup.test"
        assert config["FREE_SUPERUSER_PASSWORD"] == "FreePass1!"
        assert config["FREE_SUPERUSER_FULL_NAME"] == "Free Startup User"
        assert config["PAID_SUPERUSER_EMAIL"] == "paid@startup.test"
        assert config["PAID_SUPERUSER_PLAN"] == "pro_monthly"
        assert "#" not in config
    finally:
        tmp.unlink(missing_ok=True)


def test_load_seed_config_skips_blank_and_comment_lines():
    tmp = _make_env_file("# header\n\nKEY=value\n")
    try:
        config = load_seed_config(tmp)
        assert config == {"KEY": "value"}
    finally:
        tmp.unlink(missing_ok=True)


def test_require_raises_on_missing_key():
    with pytest.raises(SeedConfigError):
        _require({}, "MISSING_KEY")


def test_require_returns_value():
    assert _require({"K": "v"}, "K") == "v"


# ── seed_on_startup tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_seed_on_startup_skips_when_file_missing(db_session):
    """Backend starts normally even when .local-superusers.env is absent."""
    nonexistent = Path("/nonexistent/.local-superusers.env")
    await seed_on_startup(db_session, env_path=nonexistent)  # must not raise

    # No user was created
    result = await db_session.execute(select(User).where(User.email.like("%startup%")))
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_seed_on_startup_creates_both_users(db_session):
    tmp = _make_env_file(EXAMPLE_ENV)
    try:
        await seed_on_startup(db_session, env_path=tmp)
        free_row = await db_session.execute(select(User).where(User.email == "free@startup.test"))
        paid_row = await db_session.execute(select(User).where(User.email == "paid@startup.test"))
        assert free_row.scalar_one() is not None
        assert paid_row.scalar_one() is not None
    finally:
        tmp.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_seed_on_startup_does_not_crash_on_bad_config(db_session):
    """Backend must not crash if env file is malformed."""
    tmp = _make_env_file("FREE_SUPERUSER_EMAIL=only-free@test.com\n")  # missing PAID keys
    try:
        await seed_on_startup(db_session, env_path=tmp)  # must not raise
    finally:
        tmp.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_seed_on_startup_is_idempotent(db_session):
    tmp = _make_env_file(EXAMPLE_ENV)
    try:
        await seed_on_startup(db_session, env_path=tmp)
        await seed_on_startup(db_session, env_path=tmp)  # second run must not fail or duplicate

        users = await db_session.execute(select(User).where(User.email == "free@startup.test"))
        assert len(users.scalars().all()) == 1
    finally:
        tmp.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_seed_on_startup_free_user_has_free_plan(db_session):
    tmp = _make_env_file(EXAMPLE_ENV)
    try:
        await seed_on_startup(db_session, env_path=tmp)
        user_row = await db_session.execute(select(User).where(User.email == "free@startup.test"))
        user = user_row.scalar_one()
        org_row = await db_session.execute(
            select(Organization).where(Organization.owner_id == user.id)
        )
        org = org_row.scalar_one()
        sub_row = await db_session.execute(
            select(Subscription).where(Subscription.organization_id == org.id)
        )
        sub = sub_row.scalar_one()
        assert sub.plan == "free"
        assert sub.status == "active"
    finally:
        tmp.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_seed_on_startup_paid_user_has_pro_plan(db_session):
    tmp = _make_env_file(EXAMPLE_ENV)
    try:
        await seed_on_startup(db_session, env_path=tmp)
        user_row = await db_session.execute(select(User).where(User.email == "paid@startup.test"))
        user = user_row.scalar_one()
        org_row = await db_session.execute(
            select(Organization).where(Organization.owner_id == user.id)
        )
        org = org_row.scalar_one()
        sub_row = await db_session.execute(
            select(Subscription).where(Subscription.organization_id == org.id)
        )
        sub = sub_row.scalar_one()
        assert sub.plan == "pro_monthly"
        assert sub.status == "active"
    finally:
        tmp.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_seeded_user_can_login_via_normal_endpoint(client, db_session):
    """Critical: seeded users must be able to login via the standard /auth/login endpoint.
    Login logic is unchanged — no special cases for seeded users."""
    env_content = (
        "FREE_SUPERUSER_EMAIL=logintest@example.com\n"
        "FREE_SUPERUSER_PASSWORD=LoginPass1!\n"
        "FREE_SUPERUSER_ORG_NAME=Login Org\n"
        "PAID_SUPERUSER_EMAIL=logintest-paid@example.com\n"
        "PAID_SUPERUSER_PASSWORD=LoginPaidPass1!\n"
        "PAID_SUPERUSER_ORG_NAME=Login Paid Org\n"
        "PAID_SUPERUSER_PLAN=pro_monthly\n"
    )
    tmp = _make_env_file(env_content)
    try:
        await seed_on_startup(db_session, env_path=tmp)

        # Free user login
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "logintest@example.com", "password": "LoginPass1!"},
        )
        assert r.status_code == 200, f"Free user login failed: {r.text}"
        data = r.json()
        assert "access_token" in data
        assert data["access_token"]

        # Paid user login
        r2 = await client.post(
            "/api/v1/auth/login",
            json={"email": "logintest-paid@example.com", "password": "LoginPaidPass1!"},
        )
        assert r2.status_code == 200, f"Paid user login failed: {r2.text}"
        assert r2.json()["access_token"]
    finally:
        tmp.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_seeded_user_wrong_password_rejected(client, db_session):
    """Standard auth flow: wrong password returns 401/400, not a bypass."""
    env_content = (
        "FREE_SUPERUSER_EMAIL=wrongpw@example.com\n"
        "FREE_SUPERUSER_PASSWORD=CorrectPass1!\n"
        "FREE_SUPERUSER_ORG_NAME=Wrong PW Org\n"
        "PAID_SUPERUSER_EMAIL=wrongpw-paid@example.com\n"
        "PAID_SUPERUSER_PASSWORD=CorrectPaidPass1!\n"
        "PAID_SUPERUSER_ORG_NAME=Wrong PW Paid Org\n"
        "PAID_SUPERUSER_PLAN=pro_monthly\n"
    )
    tmp = _make_env_file(env_content)
    try:
        await seed_on_startup(db_session, env_path=tmp)
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw@example.com", "password": "WrongPassword!"},
        )
        assert r.status_code in (400, 401)
    finally:
        tmp.unlink(missing_ok=True)


# ── seed_superuser unit tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_seed_creates_user(db_session):
    result = await seed_superuser(
        db_session,
        email="free@seed.test",
        password="LocalPass1!",
        full_name="Free Seed",
        org_name="Free Seed Org",
        plan="free",
    )
    assert result["email"] == "free@seed.test"
    assert result["user_status"] == "created"

    row = await db_session.execute(select(User).where(User.email == "free@seed.test"))
    user = row.scalar_one()
    assert user.is_active is True
    assert user.is_verified is True
    assert user.is_superuser is True


@pytest.mark.asyncio
async def test_seed_password_is_hashed_not_plaintext(db_session):
    plain = "SuperSecret999!"
    await seed_superuser(
        db_session,
        email="hashed@seed.test",
        password=plain,
        full_name="Hash Test",
        org_name="Hash Org",
        plan="free",
    )
    row = await db_session.execute(select(User).where(User.email == "hashed@seed.test"))
    user = row.scalar_one()
    assert user.password_hash != plain
    assert verify_password(plain, user.password_hash) is True


@pytest.mark.asyncio
async def test_seed_result_does_not_contain_password(db_session):
    plain = "ShouldNotAppear!"
    result = await seed_superuser(
        db_session,
        email="nopw@seed.test",
        password=plain,
        full_name="No PW",
        org_name="No PW Org",
        plan="free",
    )
    assert plain not in str(result)


@pytest.mark.asyncio
async def test_seed_creates_owner_membership(db_session):
    await seed_superuser(
        db_session,
        email="member@seed.test",
        password="MemberPass1!",
        full_name="Member Test",
        org_name="Member Org",
        plan="free",
    )
    user_row = await db_session.execute(select(User).where(User.email == "member@seed.test"))
    user = user_row.scalar_one()
    member_row = await db_session.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    )
    member = member_row.scalar_one()
    assert member.role == "owner"


@pytest.mark.asyncio
async def test_seed_free_user_gets_free_plan(db_session):
    await seed_superuser(
        db_session,
        email="freeplan@seed.test",
        password="FreePass1!",
        full_name="Free Plan",
        org_name="Free Plan Org",
        plan="free",
    )
    org_row = await db_session.execute(
        select(Organization).where(Organization.name == "Free Plan Org")
    )
    org = org_row.scalar_one()
    sub_row = await db_session.execute(
        select(Subscription).where(Subscription.organization_id == org.id)
    )
    sub = sub_row.scalar_one()
    assert sub.plan == "free"
    assert sub.status == "active"


@pytest.mark.asyncio
async def test_seed_paid_user_gets_pro_plan(db_session):
    await seed_superuser(
        db_session,
        email="proplan@seed.test",
        password="ProPass1!",
        full_name="Pro Plan",
        org_name="Pro Plan Org",
        plan="pro_monthly",
    )
    org_row = await db_session.execute(
        select(Organization).where(Organization.name == "Pro Plan Org")
    )
    org = org_row.scalar_one()
    sub_row = await db_session.execute(
        select(Subscription).where(Subscription.organization_id == org.id)
    )
    sub = sub_row.scalar_one()
    assert sub.plan == "pro_monthly"
    assert sub.status == "active"


@pytest.mark.asyncio
async def test_seed_is_idempotent_no_duplicates(db_session):
    kwargs = dict(
        email="idem@seed.test",
        password="IdemPass1!",
        full_name="Idem User",
        org_name="Idem Org",
        plan="free",
    )
    r1 = await seed_superuser(db_session, **kwargs)
    r2 = await seed_superuser(db_session, **kwargs)

    assert r1["user_status"] == "created"
    assert r2["user_status"] == "updated"

    users = await db_session.execute(select(User).where(User.email == "idem@seed.test"))
    assert len(users.scalars().all()) == 1

    orgs = await db_session.execute(select(Organization).where(Organization.name == "Idem Org"))
    assert len(orgs.scalars().all()) == 1


@pytest.mark.asyncio
async def test_seed_idempotent_subscription_no_duplicates(db_session):
    kwargs = dict(
        email="subdup@seed.test",
        password="SubPass1!",
        full_name="Sub Dup",
        org_name="Sub Dup Org",
        plan="pro_monthly",
    )
    await seed_superuser(db_session, **kwargs)
    await seed_superuser(db_session, **kwargs)

    org_row = await db_session.execute(
        select(Organization).where(Organization.name == "Sub Dup Org")
    )
    org = org_row.scalar_one()
    subs = await db_session.execute(
        select(Subscription).where(Subscription.organization_id == org.id)
    )
    assert len(subs.scalars().all()) == 1


# ── gitignore check ────────────────────────────────────────────────────────

def test_gitignore_covers_local_superusers_env():
    gitignore = Path(__file__).parent.parent.parent.parent / ".gitignore"
    assert gitignore.exists(), ".gitignore not found at repo root"
    content = gitignore.read_text(encoding="utf-8")
    assert ".local-superusers.env" in content
