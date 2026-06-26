#!/usr/bin/env python3
"""
Seed local demo superusers into the development database.

Run inside the Docker backend container:
  docker compose exec backend python scripts/seed_local_superusers.py

Or directly on the host (requires apps/backend/.local-superusers.env):
  cd apps/backend
  python scripts/seed_local_superusers.py

The script reads .local-superusers.env from the backend root directory.
Passwords are never printed or logged.
Safe to run multiple times (idempotent).
"""
import asyncio
import sys
from pathlib import Path

# Ensure the backend app package is importable from any working directory
_script_dir = Path(__file__).parent
_backend_root = _script_dir.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

import app.models  # noqa: F401 — register all SQLAlchemy models before use

from app.services.local_seed import SeedConfigError, run_seed  # noqa: E402


def main() -> None:
    try:
        results = asyncio.run(run_seed())
    except SeedConfigError as exc:
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Seed failed: {exc}\n", file=sys.stderr)
        sys.exit(1)

    print("\nLocal superuser seed completed:\n")
    for r in results:
        print(f"  Email     : {r['email']}")
        print(f"  Org       : {r['org_name']}")
        print(f"  Plan      : {r['plan']}")
        print(f"  User      : {r['user_status']}")
        print(f"  Org       : {r['org_status']}")
        print()
    print("Login at http://localhost:3100\n")


if __name__ == "__main__":
    main()
