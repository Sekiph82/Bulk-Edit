# HANDOFF.md — Session Handoff

Purpose: only what the next session needs to resume safely. For full engineering history, see `CHANGELOG_AI.md`. For current production/environment state, see `PROJECT_STATUS.md`. For durable decisions, see `DECISIONS.md`.

## RESUME HERE — 2026-08-27 (ninth same-day update — Etsy OAuth working, issue #80 closed)

**Current state: Etsy OAuth shop connection now works end-to-end in production.** Owner retried live OAuth after the shop-lookup parser fix (`fix/etsy-shop-lookup-single-shop-response` / PR #83, merged `fee6e4c`) deployed. Success — **WearYourStoriesCom** (Etsy shop ID `44263504`) connected, verified read-only via `/etsy/shops` (`is_connected=True`, `last_synced_at=None` — no sync run yet, no writes performed). Issue #80 commented with the full 4-step root-cause chain and **closed as completed**. Full detail: `CHANGELOG_AI.md` + `DECISIONS.md`, entries dated `2026-08-27`.

**Exact next step:** a **controlled, explicitly-approved, read-only** listing sync validation — not started yet, needs its own owner go-ahead before triggering (this is new scope, not a continuation of issue #80). Separately, non-urgent: uvicorn's access log for `GET /etsy/callback` includes the raw `code`/`state` query string in `doctl apps logs` output (distinct from the safe categorized `etsy_oauth_callback_failed` logger, which never does this) — worth a follow-up fix, not yet scheduled.

**Safety constraints still active (unchanged):** never print secrets/tokens; no live Etsy write without explicit owner approval; no real Stripe action; do not disable Private Beta; no DNS/Cloudflare changes; no staging action; do not create a new Etsy developer app; do not submit another Etsy appeal.

**Earlier today (2026-08-27), for context, in order:** (1) Private Beta was blocking sign-in entirely, including masking the OAuth callback's `/shops?...` redirect behind `/private-beta?...` — fixed, `fix/private-beta-allow-signin`, merged `4a232fb`. (2) `/etsy/callback` had zero logging anywhere in its failure path — added 11 safe categories, `fix/etsy-oauth-safe-callback-logging`, merged `34b53c9`. (3) `doctl` auth had expired (`401`) — restored via a local-only script reading the token from `deploy-production.local.env` directly into doctl's config file (never printed, never a CLI arg). (4) Owner retried OAuth; diagnosed as `etsy_oauth_shop_lookup_failed` / 403, provisionally attributed to Personal Use access tier. (5) Shipped defensive `user_id` validation (`fix/etsy-oauth-user-id-validation`, merged `48f5a02`) — didn't fix the 403, closed an unrelated real gap. (6) x-api-key format fix (`fix/etsy-oauth-shop-lookup-x-api-key`, merged `9336c53`) — this was the actual 403 root cause, confirmed by the next retry no longer 403ing. (7) Owner retried again post-deploy: new failure, `etsy_oauth_shop_not_found`; owner confirmed active shop exists. (8) Response-shape parsing bug found and fixed (`fix/etsy-shop-lookup-single-shop-response` / PR #83, merged `fee6e4c`). (9) Owner retried once more: **success** — shop connected, issue #80 closed.

**Previously (2026-07-31), for context:** Etsy issued new developer-app credentials for `bulk-edit-app` (owner received Keystring + Shared Secret directly from Etsy, rate limit 5 QPS / 5000 QPD — matching this project's existing `ETSY_API_REQUESTS_PER_SECOND`/`ETSY_API_DAILY_LIMIT` defaults exactly, no code change needed). Credentials were configured as encrypted `SECRET` env vars on `bulk-edit-prod-api` via `doctl apps update --spec`, and production OAuth URL generation was verified end-to-end against the live API (masked keystring `qvmj...fh33`, callback `https://api.bulkeditapp.com/api/v1/etsy/callback`, scopes `listings_r listings_w shops_r profile_r`, PKCE `S256` present). Live OAuth completion was deliberately NOT performed that session — that still needed explicit owner go-ahead (see `TASKS.md` Owner Action). Full detail: `CHANGELOG_AI.md` entry `2026-07-31`.

**Mid-task bug caught and fixed in the 2026-07-31 session (documented for anyone touching `.ops-local` deploy scripts later):** an initial PowerShell env-patch script used `[regex]::Replace($text, $pattern, $replacement, 1)` intending "replace first match only" — the 4th positional arg to the *static* `Regex.Replace` overload is actually `RegexOptions`, not a match-count limiter, so `1` was silently interpreted as `IgnoreCase` and the patch applied to every `envs:` block in the spec (api service + both jobs), triple-duplicating the new Etsy env entries and leaving the old encrypted values still present too. Caught by re-fetching and grep-counting keys (values redacted) before trusting the deploy; fixed with a YAML-aware Python pass (`.ops-local/fix-etsy-env-duplicates.py`, PyYAML) that deduped to exactly one entry per key in the `api` service and stripped the 6 stray entries each from `migrate`/`retention-cleanup` jobs, then redeployed and re-verified counts. Net effect on production: two consecutive `bulk-edit-prod-api` deploys this session, both `ACTIVE`, final state clean and confirmed. `.ops-local/deploy-etsy-env-to-digitalocean.ps1` still contains the original buggy regex path — **do not trust its "patch existing" branch as-is**; it needs the same fix (or should be replaced by the Python approach) before reuse.

**Previously (2026-07-16), for context:** the Etsy appeal had been **submitted by the owner** and production was LIVE and fully healthy (backend/frontend/DB/Redis confirmed, migration `0025`, Private Beta enabled). Retention cleanup Option A (DO Scheduled Job) had two consecutive successful runs. PR #64 aligned the public website with the submitted appeal. That waiting period is now resolved by the credential issuance above.

**Critical environment facts:**
- Hosting: DigitalOcean App Platform (`bulk-edit-prod-api`, `bulk-edit-prod-web`) + Cloudflare. App IDs: prod-api `2f37fa86-a826-4dc2-b5d3-22f44d85cb1c`, prod-web `fb4415ca-cd2d-4929-a754-08f1893f4d25`.
- **Merging to `main` triggers an immediate production rebuild for BOTH apps** (`deploy_on_push: true`, no path filter) — even a docs-only merge redeploys both. Always confirm DB backup + any relevant preflight *before* merging, not after; the merge itself is the deploy trigger.
- Retention job monitoring: `doctl apps list-job-invocations <app-id> --job-name retention-cleanup --format ID,Jobname,Created,Started,Completed,Phase`, then `doctl apps logs <app-id> retention-cleanup --job-invocation <id> --type run`. (`--component` is not a real flag — component name is positional.)
- Checking Alembic revision live without a direct DB connection: the `migrate` PRE_DEPLOY job (`alembic upgrade head`) runs on every deploy — `doctl apps logs <api-app-id> migrate --deployment <deployment-id> --type run` shows "Running upgrade" lines only if something was actually applied. No lines + a repo migration chain topping out at the expected revision = confirmation, without ever opening a credentialed DB connection. (A prior session attempt to install a DB driver for a direct query was correctly blocked by the permission system — don't repeat that; this log-based method is the safer existing path.)
- Backend tests: 982 passed (current authoritative count).

**Current branch/PR state:** `main` is clean and matches `origin/main`. No open feature branches from this session (no code change was needed — env/config only).

**Unresolved work:** engineering side is done for this credential-configuration pass. The only remaining step is an **owner decision**: explicitly approve a live OAuth test (connect one real test Etsy shop, no writes) before anything Etsy-live is exercised further.

**Exact next step:** get owner approval for a live OAuth test per `TASKS.md` → Owner Action, then connect one test shop, confirm token exchange, and re-verify live Etsy reads (writes stay preview-gated as always — see `CLAUDE.md` rule 2). Do not create a new Etsy developer app, do not disable Private Beta, do not enable Etsy-derived external AI processing (`ALLOW_ETSY_DATA_TO_AI`), do not perform any Etsy write, and do not submit another appeal.

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
