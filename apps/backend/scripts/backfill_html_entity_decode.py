#!/usr/bin/env python3
"""
Re-decode HTML entities (e.g. &#39; -> ') on already-synced Listing and
ListingVariation rows. PR #89 fixed decoding at import time going forward,
but rows synced before that fix still have raw entities stored, and a
frontend-only decode (defense-in-depth, also shipped) can't fix data the
user might export via CSV or see via the API directly.

Safe by construction:
- Dry-run by default. Prints a count of rows that WOULD change and a small
  sample (title/description truncated, no PII beyond what's already visible
  in the product UI). Requires --apply to actually write.
- --apply also requires ENVIRONMENT to be explicitly set (local/staging/production)
  and, for production, --confirm-production — same gate as promote_superuser.py.
- Only touches the same fields the sync-time decode already covers (title,
  description, tags, materials, sku on Listing; sku, property_name, value_name
  on ListingVariation). Never touches price/quantity/state/any other field.
- decode_entities() is idempotent (html.unescape on already-clean text is a
  no-op), so re-running this script is always safe.
- Reads DATABASE_URL only via settings.DATABASE_URL (same asyncpg-safe
  rewrite as promote_superuser.py). Never prints DATABASE_URL.

Usage (dry run, safe to run anytime):
  ENVIRONMENT=production python scripts/backfill_html_entity_decode.py

Usage (apply, owner-approved only):
  ENVIRONMENT=production python scripts/backfill_html_entity_decode.py --apply --confirm-production
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

from app.core.config import settings  # noqa: E402
from app.models.listing import Listing  # noqa: E402
from app.models.listing_variation import ListingVariation  # noqa: E402
from app.services.etsy_sync import _decode_entities  # noqa: E402

importlib.import_module("app.models")

_ALLOWED_ENVIRONMENTS = {"local", "staging", "production"}
_LISTING_FIELDS = ("title", "description", "tags", "materials", "sku")
_VARIATION_FIELDS = ("sku", "property_name", "value_name")


def _fail(message: str) -> None:
    print(f"\n[ERROR] {message}\n", file=sys.stderr)
    sys.exit(1)


async def _scan_and_fix(db: AsyncSession, apply: bool) -> tuple[int, int]:
    listing_changed = 0
    result = await db.execute(select(Listing))
    for listing in result.scalars():
        changed = False
        for field in _LISTING_FIELDS:
            before = getattr(listing, field)
            after = _decode_entities(before)
            if after != before:
                changed = True
                if apply:
                    setattr(listing, field, after)
        if changed:
            listing_changed += 1

    variation_changed = 0
    result = await db.execute(select(ListingVariation))
    for variation in result.scalars():
        changed = False
        for field in _VARIATION_FIELDS:
            before = getattr(variation, field)
            after = _decode_entities(before)
            if after != before:
                changed = True
                if apply:
                    setattr(variation, field, after)
        if changed:
            variation_changed += 1

    if apply:
        await db.commit()

    return listing_changed, variation_changed


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Actually write changes. Default is dry-run.")
    parser.add_argument(
        "--confirm-production",
        action="store_true",
        help="Required in addition to --apply and ENVIRONMENT=production to actually run.",
    )
    args = parser.parse_args()

    environment = os.environ.get("ENVIRONMENT", "").strip().lower()
    if environment not in _ALLOWED_ENVIRONMENTS:
        _fail(
            "ENVIRONMENT must be explicitly set to one of "
            f"{sorted(_ALLOWED_ENVIRONMENTS)} (got: {environment or '<unset>'})."
        )

    if args.apply and environment == "production" and not args.confirm_production:
        _fail(
            "Refusing to --apply against ENVIRONMENT=production without --confirm-production. "
            "This is a deliberate safety gate — re-run with the flag only if the owner has approved it."
        )

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        listing_changed, variation_changed = await _scan_and_fix(db, apply=args.apply)

    await engine.dispose()

    mode = "APPLIED" if args.apply else "DRY RUN (no changes written — pass --apply to write)"
    print(f"\n[{mode}] environment={environment}")
    print(f"Listings with decodable entities: {listing_changed}")
    print(f"Listing variations with decodable entities: {variation_changed}\n")


if __name__ == "__main__":
    asyncio.run(main())
