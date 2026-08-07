# HANDOFF.md — Session Handoff

Purpose: only what the next session needs to resume safely. For full engineering history, see `CHANGELOG_AI.md`. For current production/environment state, see `PROJECT_STATUS.md`. For durable decisions, see `DECISIONS.md`.

## RESUME HERE — 2026-08-07

**Current state:** Etsy lifted the ban and granted Personal Use access for `bulk-edit-app`. First live OAuth attempt was made (read-only test, per owner instruction) — **blocked by Etsy, not our code or config.** Etsy returned "The requested redirect URL is not permitted" on its own consent page, before any redirect back to our backend. Root cause: `https://api.bulkeditapp.com/api/v1/etsy/callback` is very likely not yet in the app's registered Redirect URI allowlist in the Etsy Developer Console (plausible leftover from the ban/review period, when this could never have been set up live). Confirmed this is not a config-sync bug: the `redirect_uri` embedded in the generated authorize URL decodes to exactly `https://api.bulkeditapp.com/api/v1/etsy/callback`, matching both `ETSY_REDIRECT_URI` in production and the callback route in code (`apps/backend/app/api/v1/etsy.py`). **No production env change was made** — nothing on our side was proven wrong, so per `CLAUDE.md` rule "do not change production env unless a read-only test proves the current config is wrong," nothing was touched.

**Owner action needed before retry:** log into https://www.etsy.com/developers/your-apps → `bulk-edit-app` → add `https://api.bulkeditapp.com/api/v1/etsy/callback` to the Redirect URI(s) field exactly (no trailing slash) → save.

**Everything else from the 2026-07-31 credential-configuration session still holds:** credentials configured as encrypted `SECRET` env vars on `bulk-edit-prod-api`, production OAuth URL generation verified end-to-end (masked keystring `qvmj...fh33`, callback/scopes/PKCE all correct — this part was re-confirmed working again this session, multiple times, right up to the point Etsy rejected the redirect). Private Beta remains enabled; no Etsy writes, no listing/media changes, no Stripe/DNS/Cloudflare/staging action, no production env change. Full detail: `CHANGELOG_AI.md` entry `2026-08-07`.

**Mid-task bug caught and fixed this session (documented for anyone touching `.ops-local` deploy scripts later):** an initial PowerShell env-patch script used `[regex]::Replace($text, $pattern, $replacement, 1)` intending "replace first match only" — the 4th positional arg to the *static* `Regex.Replace` overload is actually `RegexOptions`, not a match-count limiter, so `1` was silently interpreted as `IgnoreCase` and the patch applied to every `envs:` block in the spec (api service + both jobs), triple-duplicating the new Etsy env entries and leaving the old encrypted values still present too. Caught by re-fetching and grep-counting keys (values redacted) before trusting the deploy; fixed with a YAML-aware Python pass (`.ops-local/fix-etsy-env-duplicates.py`, PyYAML) that deduped to exactly one entry per key in the `api` service and stripped the 6 stray entries each from `migrate`/`retention-cleanup` jobs, then redeployed and re-verified counts. Net effect on production: two consecutive `bulk-edit-prod-api` deploys this session, both `ACTIVE`, final state clean and confirmed. `.ops-local/deploy-etsy-env-to-digitalocean.ps1` still contains the original buggy regex path — **do not trust its "patch existing" branch as-is**; it needs the same fix (or should be replaced by the Python approach) before reuse.

**Previously (2026-07-31), for context:** Etsy issued new developer-app credentials for `bulk-edit-app` (Keystring + Shared Secret, rate limit 5 QPS / 5000 QPD, matching existing code defaults exactly). Configured as encrypted `SECRET` env vars via `doctl apps update --spec`; production OAuth URL generation verified. Live OAuth completion deliberately not performed that session — see `CHANGELOG_AI.md` entry `2026-07-31` for full detail (including a mid-session PowerShell regex bug caught and fixed before it could corrupt the deploy).

**Before that (2026-07-16), for context:** the Etsy appeal had been **submitted by the owner** and production was LIVE and fully healthy (backend/frontend/DB/Redis confirmed, migration `0025`, Private Beta enabled). Retention cleanup Option A (DO Scheduled Job) had two consecutive successful runs. PR #64 aligned the public website with the submitted appeal. That waiting period is now resolved by the credential issuance above.

**Critical environment facts:**
- Hosting: DigitalOcean App Platform (`bulk-edit-prod-api`, `bulk-edit-prod-web`) + Cloudflare. App IDs: prod-api `2f37fa86-a826-4dc2-b5d3-22f44d85cb1c`, prod-web `fb4415ca-cd2d-4929-a754-08f1893f4d25`.
- **Merging to `main` triggers an immediate production rebuild for BOTH apps** (`deploy_on_push: true`, no path filter) — even a docs-only merge redeploys both. Always confirm DB backup + any relevant preflight *before* merging, not after; the merge itself is the deploy trigger.
- Retention job monitoring: `doctl apps list-job-invocations <app-id> --job-name retention-cleanup --format ID,Jobname,Created,Started,Completed,Phase`, then `doctl apps logs <app-id> retention-cleanup --job-invocation <id> --type run`. (`--component` is not a real flag — component name is positional.)
- Checking Alembic revision live without a direct DB connection: the `migrate` PRE_DEPLOY job (`alembic upgrade head`) runs on every deploy — `doctl apps logs <api-app-id> migrate --deployment <deployment-id> --type run` shows "Running upgrade" lines only if something was actually applied. No lines + a repo migration chain topping out at the expected revision = confirmation, without ever opening a credentialed DB connection. (A prior session attempt to install a DB driver for a direct query was correctly blocked by the permission system — don't repeat that; this log-based method is the safer existing path.)
- Backend tests: 982 passed (current authoritative count).

**Current branch/PR state:** `main` is clean and matches `origin/main` at session start (`b82b00c`). This session's docs-only update will land via a `docs/` branch + PR per this task's own instructions (see below) — no application code changed.

**Unresolved work:** blocked on the owner registering the callback URL in the Etsy Developer Console (see above). Everything else in the read-only OAuth verification task (Tasks 6-10 of that task's numbering: callback verification, token storage check, read-only shop/listing fetch, refresh-path check) is still pending — none of it could be reached because Etsy rejected the redirect before our backend was ever called.

**Exact next step:** once the owner confirms the redirect URI is registered in Etsy's console, generate a fresh production OAuth URL (`.ops-local/get-prod-oauth-url-for-handoff.py` — reads test-account credentials from `deploy-production.local.env` in-memory, never prints them, prints only the full authorize URL for hand-off), have the owner complete login/approval for the owner-controlled test Etsy shop, then resume from verifying the callback reached the backend, state validated, token exchange succeeded, shop connected, and do the read-only shop/listing fetch. Do not create a new Etsy developer app, do not disable Private Beta, do not enable Etsy-derived external AI processing (`ALLOW_ETSY_DATA_TO_AI`), do not perform any Etsy write, and do not submit another appeal.

**Safety constraints still active:** never print secrets/tokens or DigitalOcean's `EV[...]` encrypted placeholders; no live Etsy write; no real Stripe charge/subscription/refund without explicit instruction; do not disable Private Beta without explicit instruction; no DNS/Cloudflare/owner-domain changes without explicit instruction; do not deploy without explicit go-ahead beyond normal PR-merge flow; do not submit another Etsy appeal or contact Etsy again unless the owner explicitly decides to; do not perform live OAuth completion without explicit per-session owner approval even though credentials are now configured.

---

## Known Issues (carried forward, still accurate)

- Etsy access-token auto-refresh: implemented and wired into the sync path (fixed during the 2026-07-13 compliance pass — earlier notes calling this "not implemented" are stale).
- `fetch_listing_videos` is best-effort — returns empty list on 404/405.
- Image reorder has no live Etsy endpoint — delete-then-reupload is the only workaround and was deliberately not implemented (real risk window on a live listing) — see `DECISIONS.md`.
- `AuditLog` model uses `extra_data` in Python, stored as `metadata` column in DB (SQLAlchemy reserves `metadata`).
- `anyio==4.6.2` in `requirements-dev.txt` is yanked upstream but works fine — upgrade when 4.7.0 is stable.
- Frontend `node_modules` may be absent on a fresh checkout — run `npm install` inside `apps/frontend` or `docker compose up`.

## Local Development

- `start-dev.bat` / `start-dev-clean.bat` — Windows one-click dev startup (see `README.md` for full instructions).
- Ports: frontend 3100, backend 8100, Postgres 55432, Redis 56379.
- Windows note: host-port binding to 55432 can hit a Hyper-V/WSL2 dynamic-port reservation conflict — see `docker-compose.dev-ports.yml` and `DECISIONS.md` for the workaround (already applied in `docker-compose.yml` via `expose:` instead of `ports:` for postgres/redis).
