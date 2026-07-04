#!/usr/bin/env python3
"""
Create or update exactly one owner/operator admin (superuser) account.

Safe by construction:
- Reads email/password from env vars only — never accepts them as CLI args
  (avoids shell history / process-list exposure).
- Refuses to run unless ENVIRONMENT is explicitly one of local/staging/production.
- Refuses to run against ENVIRONMENT=production unless --confirm-production
  is passed explicitly.
- Never prints the password, any token, DATABASE_URL, REDIS_URL, or JWT_SECRET.
- Idempotent: upserts by email, does not create duplicate users.
- Does not create an organization/subscription — this is an operator account,
  not a customer account. Admin API access is gated purely on is_superuser.

Usage (staging example):
  ENVIRONMENT=staging \
  DATABASE_URL=postgresql+asyncpg://... \
  ADMIN_EMAIL=owner@example.com \
  ADMIN_PASSWORD='a-strong-password' \
  python scripts/create_admin_user.py

Production requires the extra flag:
  ENVIRONMENT=production ... python scripts/create_admin_user.py --confirm-production

See docs/operations/ADMIN_USER_CREATION.md for the full walkthrough.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

_backend_root = Path(__file__).parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

import app.models  # noqa: F401 — register all SQLAlchemy models before use
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password  # noqa: E402
from app.models.user import User  # noqa: E402

_ALLOWED_ENVIRONMENTS = {"local", "staging", "production"}


def _fail(message: str) -> None:
    print(f"\n[ERROR] {message}\n", file=sys.stderr)
    sys.exit(1)


async def _upsert_admin(db: AsyncSession, email: str, password: str, full_name: str) -> str:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.password_hash = hash_password(password)
        user.full_name = full_name or user.full_name
        user.is_active = True
        user.is_verified = True
        user.is_superuser = True
        await db.commit()
        return "updated"
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    db.add(user)
    await db.commit()
    return "created"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm-production",
        action="store_true",
        help="Required in addition to ENVIRONMENT=production to actually run.",
    )
    args = parser.parse_args()

    environment = os.environ.get("ENVIRONMENT", "").strip().lower()
    if environment not in _ALLOWED_ENVIRONMENTS:
        _fail(
            "ENVIRONMENT must be explicitly set to one of "
            f"{sorted(_ALLOWED_ENVIRONMENTS)} (got: {environment or '<unset>'})."
        )

    if environment == "production" and not args.confirm_production:
        _fail(
            "Refusing to run against ENVIRONMENT=production without --confirm-production. "
            "This is a deliberate safety gate — re-run with the flag only if you are certain."
        )

    email = os.environ.get("ADMIN_EMAIL", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    full_name = os.environ.get("ADMIN_FULL_NAME", "Admin").strip()

    if not email:
        _fail("ADMIN_EMAIL env var is required.")
    if not password or len(password) < 12:
        _fail("ADMIN_PASSWORD env var is required and must be at least 12 characters.")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        _fail("DATABASE_URL env var is required (never printed by this script).")

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        status = await _upsert_admin(db, email, password, full_name)

    await engine.dispose()

    print(f"\nAdmin user {status} for environment={environment}.")
    print("Email and status only — password/DATABASE_URL are never printed.\n")


if __name__ == "__main__":
    asyncio.run(main())
