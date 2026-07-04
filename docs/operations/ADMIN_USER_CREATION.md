# Admin (Superuser) User Creation

How to create the first owner/operator admin account for staging or
production. This is separate from customer accounts — an admin account has
`is_superuser=True` and gets access to `/admin` and the `/api/v1/admin/*`
backend endpoints, gated by `require_superuser`.

## Script

`apps/backend/scripts/create_admin_user.py`

Safety properties:
- Reads `ADMIN_EMAIL` / `ADMIN_PASSWORD` from env vars only (never CLI args).
- Refuses to run unless `ENVIRONMENT` is explicitly `local`, `staging`, or `production`.
- Refuses to run against `ENVIRONMENT=production` unless `--confirm-production` is also passed.
- Never prints the password, `DATABASE_URL`, `REDIS_URL`, or `JWT_SECRET`.
- Idempotent — upserts by email, safe to re-run.
- Creates only the `User` row with `is_superuser=True`. Does not create an
  organization or subscription — admin API access is gated purely on
  `is_superuser`, not org membership.

## Staging example

Run this from a machine/shell that has the staging `DATABASE_URL` available
(never commit or print it):

```bash
ENVIRONMENT=staging \
DATABASE_URL="<staging DATABASE_URL>" \
ADMIN_EMAIL="owner@example.com" \
ADMIN_PASSWORD="<strong password, 12+ chars>" \
python scripts/create_admin_user.py
```

## Production example

Identical, plus the explicit confirmation flag:

```bash
ENVIRONMENT=production \
DATABASE_URL="<production DATABASE_URL>" \
ADMIN_EMAIL="owner@example.com" \
ADMIN_PASSWORD="<strong password, 12+ chars>" \
python scripts/create_admin_user.py --confirm-production
```

## Where to run it from

The script needs network access to the target Postgres instance. On
DigitalOcean App Platform, the simplest safe option today is an interactive
`doctl apps console <app-id> <component>` session into the running backend
(which already has `DATABASE_URL` in its environment) — run the script there
rather than exporting the raw connection string to a local shell.

## Not done in this PR

This script only covers *creating* an admin. It does not add:
- A web UI for promoting an existing user to admin (would need its own
  superuser-only endpoint + audit logging — deliberately out of scope here).
- Removing/demoting an admin (use direct DB access or extend the script).
