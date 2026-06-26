"""
Tests for the local superuser seed service.
Tests service functions directly against the in-memory SQLite test DB.
Does NOT test run_seed() (which creates its own engine) to keep tests fast and isolated.
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
    seed_superuser,
)


# ── load_seed_config tests ─────────────────────────────────────────────────

def test_load_seed_config_missing_file_raises():
    with pytest.raises(SeedConfigError) as exc_info:
        load_seed_config(Path("/nonexistent/path/.local-superusers.env"))
    msg = str(exc_info.value)
    assert "not found" in msg.lower() or "seed config" in msg.lower()
    # Instructions should mention the example file
    assert ".env.example" in msg or "example" in msg.lower()


def test_load_seed_config_missing_file_mentions_copy_instructions():
    with pytest.raises(SeedConfigError) as exc_info:
        load_seed_config(Path("/nonexistent/.local-superusers.env"))
    msg = str(exc_info.value)
    assert "copy" in msg.lower() or "Copy" in msg


def test_load_seed_config_parses_example_style_env():
    content = (
        "FREE_SUPERUSER_EMAIL=free@example.com\n"
        "FREE_SUPERUSER_PASSWORD=Secret123!\n"
        "FREE_SUPERUSER_FULL_NAME=Free User\n"
        "# A comment line\n"
        "\n"
        "PAID_SUPERUSER_EMAIL=paid@example.com\n"
        "PAID_SUPERUSER_PASSWORD=PaidSecret!\n"
        "PAID_SUPERUSER_PLAN=pro_monthly\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(content)
        tmp_path = Path(f.name)
    try:
        config = load_seed_config(tmp_path)
        assert config["FREE_SUPERUSER_EMAIL"] == "free@example.com"
        assert config["FREE_SUPERUSER_PASSWORD"] == "Secret123!"
        assert config["FREE_SUPERUSER_FULL_NAME"] == "Free User"
        assert config["PAID_SUPERUSER_EMAIL"] == "paid@example.com"
        assert config["PAID_SUPERUSER_PLAN"] == "pro_monthly"
        # Comments and blank lines are skipped
        assert "#" not in config
    finally:
        tmp_path.unlink(missing_ok=True)


def test_load_seed_config_skips_blank_and_comment_lines():
    content = "# header\n\nKEY=value\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(content)
        tmp_path = Path(f.name)
    try:
        config = load_seed_config(tmp_path)
        assert config == {"KEY": "value"}
    finally:
        tmp_path.unlink(missing_ok=True)


def test_require_raises_on_missing_key():
    with pytest.raises(SeedConfigError):
        _require({}, "MISSING_KEY")


def test_require_returns_value():
    assert _require({"K": "v"}, "K") == "v"


# ── seed_superuser tests ───────────────────────────────────────────────────

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
    result_str = str(result)
    assert plain not in result_str


@pytest.mark.asyncio
async def test_seed_creates_organization(db_session):
    await seed_superuser(
        db_session,
        email="orgtest@seed.test",
        password="OrgPass1!",
        full_name="Org Test",
        org_name="My Seed Org",
        plan="free",
    )
    row = await db_session.execute(select(Organization).where(Organization.name == "My Seed Org"))
    org = row.scalar_one()
    assert org.name == "My Seed Org"


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
    assert ".local-superusers.env" in content, (
        "apps/backend/.local-superusers.env is not covered by .gitignore"
    )
