"""
Local-only demo superuser seed service.

Runs automatically on backend startup if .local-superusers.env exists.
Also runnable via CLI (inside Docker container):
  docker compose exec backend python scripts/seed_local_superusers.py

The seed file is read from .local-superusers.env in the backend root.
Inside Docker that file lives at /app/.local-superusers.env.
On the host machine it lives at apps/backend/.local-superusers.env.
Both resolve to the same path because docker-compose mounts ./apps/backend:/app.

Rules:
- Never print passwords.
- Never log secrets.
- Idempotent: safe to run multiple times.
- seed_on_startup() never crashes the backend.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.security import hash_password
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.subscription import Subscription
from app.models.user import User

_logger = logging.getLogger(__name__)

# Path relative to this file: apps/backend/app/services/local_seed.py
# Goes up 3 levels to reach apps/backend/
_BACKEND_ROOT = Path(__file__).parent.parent.parent
ENV_FILE_PATH = _BACKEND_ROOT / ".local-superusers.env"


class SeedConfigError(Exception):
    pass


def load_seed_config(env_path: Path | None = None) -> dict[str, str]:
    """Load seed config from .local-superusers.env. Raises SeedConfigError if file missing."""
    path = env_path or ENV_FILE_PATH
    if not path.exists():
        example = path.parent / ".local-superusers.env.example"
        raise SeedConfigError(
            f"Seed config not found: {path}\n\n"
            "To set up local demo superusers:\n"
            f"  1. Copy {example} to {path}\n"
            f"  2. Edit {path} with your LOCAL credentials.\n"
            "  3. Re-run this script.\n\n"
            "The real .local-superusers.env is gitignored and never committed."
        )
    config: dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            config[key.strip()] = value.strip()
    return config


def _require(config: dict[str, str], key: str) -> str:
    value = config.get(key, "").strip()
    if not value:
        raise SeedConfigError(f"Missing required key in seed config: {key}")
    return value


async def _upsert_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    is_superuser: bool = False,
) -> tuple[User, bool]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.full_name = full_name
        user.is_active = True
        user.is_verified = True
        user.is_superuser = is_superuser
        user.password_hash = hash_password(password)
        await db.flush()
        return user, False
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
        is_verified=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.flush()
    return user, True


async def _upsert_org(
    db: AsyncSession,
    owner_id: str,
    org_name: str,
) -> tuple[Organization, bool]:
    result = await db.execute(
        select(Organization).where(
            Organization.owner_id == owner_id,
            Organization.name == org_name,
        )
    )
    org = result.scalar_one_or_none()
    if org:
        return org, False
    org = Organization(name=org_name, owner_id=owner_id)
    db.add(org)
    await db.flush()
    return org, True


async def _upsert_member(db: AsyncSession, org_id: str, user_id: str) -> None:
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        )
    )
    if not result.scalar_one_or_none():
        db.add(OrganizationMember(organization_id=org_id, user_id=user_id, role="owner"))
        await db.flush()


async def _upsert_subscription(db: AsyncSession, org_id: str, plan: str) -> None:
    result = await db.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.plan = plan
        sub.status = "active"
    else:
        db.add(Subscription(organization_id=org_id, plan=plan, status="active"))
    await db.flush()


async def seed_superuser(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    org_name: str,
    plan: str,
    is_superuser: bool = True,
) -> dict[str, Any]:
    """
    Create or update one demo user with organization and subscription.
    Pass is_superuser=False for normal customer accounts.
    Idempotent. Returns summary dict — password is never included.
    """
    user, user_created = await _upsert_user(db, email, password, full_name, is_superuser=is_superuser)
    org, org_created = await _upsert_org(db, user.id, org_name)
    await _upsert_member(db, org.id, user.id)
    await _upsert_subscription(db, org.id, plan)
    await db.commit()
    return {
        "email": email,
        "org_name": org_name,
        "plan": plan,
        "user_status": "created" if user_created else "updated",
        "org_status": "created" if org_created else "existing",
    }


async def seed_on_startup(db: AsyncSession, env_path: Path | None = None) -> None:
    """
    Called by the FastAPI lifespan startup hook.
    Seeds local demo users if .local-superusers.env exists.
    Silent when file is absent. Logs a warning on any error — never crashes the backend.
    Login logic is not modified: seeded users log in normally via the standard auth endpoint.
    """
    path = env_path or ENV_FILE_PATH
    if not path.exists():
        _logger.debug("Local superuser seed file not found at %s — skipping.", path)
        return

    try:
        config = load_seed_config(path)

        free_email = _require(config, "FREE_SUPERUSER_EMAIL")
        free_password = _require(config, "FREE_SUPERUSER_PASSWORD")
        free_full_name = config.get("FREE_SUPERUSER_FULL_NAME", "Free Demo Superuser")
        free_org_name = config.get("FREE_SUPERUSER_ORG_NAME", "Free Demo Org")

        paid_email = _require(config, "PAID_SUPERUSER_EMAIL")
        paid_password = _require(config, "PAID_SUPERUSER_PASSWORD")
        paid_full_name = config.get("PAID_SUPERUSER_FULL_NAME", "Paid Demo Superuser")
        paid_org_name = config.get("PAID_SUPERUSER_ORG_NAME", "Paid Demo Org")
        paid_plan = config.get("PAID_SUPERUSER_PLAN", "pro_monthly")

        r1 = await seed_superuser(db, free_email, free_password, free_full_name, free_org_name, "free", is_superuser=False)
        r2 = await seed_superuser(db, paid_email, paid_password, paid_full_name, paid_org_name, paid_plan, is_superuser=True)

        _logger.info(
            "Local superuser seed: %s (%s, %s) | %s (%s, %s)",
            r1["email"], r1["plan"], r1["user_status"],
            r2["email"], r2["plan"], r2["user_status"],
        )
    except Exception as exc:
        _logger.warning("Local superuser seed failed (backend continues normally): %s", exc)


async def run_seed(env_path: Path | None = None) -> list[dict[str, Any]]:
    """
    Load .local-superusers.env, connect to DB, seed both demo users.
    Returns list of result summaries (no passwords).
    Uses DATABASE_URL env var (set by docker-compose or caller).
    """
    config = load_seed_config(env_path)

    free_email = _require(config, "FREE_SUPERUSER_EMAIL")
    free_password = _require(config, "FREE_SUPERUSER_PASSWORD")
    free_full_name = config.get("FREE_SUPERUSER_FULL_NAME", "Free Demo Superuser")
    free_org_name = config.get("FREE_SUPERUSER_ORG_NAME", "Free Demo Org")

    paid_email = _require(config, "PAID_SUPERUSER_EMAIL")
    paid_password = _require(config, "PAID_SUPERUSER_PASSWORD")
    paid_full_name = config.get("PAID_SUPERUSER_FULL_NAME", "Paid Demo Superuser")
    paid_org_name = config.get("PAID_SUPERUSER_ORG_NAME", "Paid Demo Org")
    paid_plan = config.get("PAID_SUPERUSER_PLAN", "pro_monthly")

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://bulkedit:bulkedit_password@localhost:55432/bulkedit",
    )
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    results: list[dict[str, Any]] = []
    async with session_factory() as db:
        results.append(
            await seed_superuser(db, free_email, free_password, free_full_name, free_org_name, "free", is_superuser=False)
        )
        results.append(
            await seed_superuser(db, paid_email, paid_password, paid_full_name, paid_org_name, paid_plan, is_superuser=True)
        )

    await engine.dispose()
    return results
