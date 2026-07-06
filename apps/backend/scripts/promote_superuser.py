#!/usr/bin/env python3
"""
Flip is_superuser=true for exactly one EXISTING user. Nothing else.

Safe by construction:
- Only ever sets is_superuser. Never touches password_hash, is_active,
  is_verified, or any other field.
- Does not create a user — refuses if the email doesn't already exist
  (unlike create_admin_user.py, which upserts and would reset a password).
- Reads TARGET_EMAIL/DATABASE_URL from env vars only — never CLI args.
- Refuses to run unless ENVIRONMENT is explicitly one of local/staging/production.
- Refuses to run against ENVIRONMENT=production unless --confirm-production
  is passed explicitly.
- Never prints the password, any token, DATABASE_URL, REDIS_URL, or JWT_SECRET.
- Idempotent: no-ops with a clear message if already is_superuser=true.

Usage (staging example, run inside the running app container via
`doctl apps console <app-id> api`, where DATABASE_URL is already set):
  ENVIRONMENT=staging TARGET_EMAIL=owner@example.com python scripts/promote_superuser.py
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

import importlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.user import User  # noqa: E402

importlib.import_module("app.models")

_ALLOWED_ENVIRONMENTS = {"local", "staging", "production"}


def _fail(message: str) -> None:
    print(f"\n[ERROR] {message}\n", file=sys.stderr)
    sys.exit(1)


async def _promote(db: AsyncSession, email: str) -> str:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        return "not_found"
    if user.is_superuser:
        return "already_superuser"
    user.is_superuser = True
    await db.commit()
    return "promoted"


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

    email = os.environ.get("TARGET_EMAIL", "").strip()
    if not email:
        _fail("TARGET_EMAIL env var is required.")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        _fail("DATABASE_URL env var is required (never printed by this script).")

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        status = await _promote(db, email)

    await engine.dispose()

    if status == "not_found":
        _fail(f"No user found for that email in environment={environment}. Nothing changed.")
    elif status == "already_superuser":
        print(f"\nAlready is_superuser=true for environment={environment}. No change made.\n")
    else:
        print(f"\nPromoted to is_superuser=true for environment={environment}.")
        print("Email and status only — password_hash was never touched.\n")


if __name__ == "__main__":
    asyncio.run(main())
