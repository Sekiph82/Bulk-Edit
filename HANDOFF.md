# HANDOFF.md — Session Handoff

## RESUME HERE — 2026-07-14, sixth session (retention cleanup: Option B → Option A, in progress)

**Where we are:** Fifth session merged PR #56 to production and left one open item: retention cleanup (`scripts/run_retention_cleanup.py`) is deployed inside the backend image but nothing schedules it (Option B). This session's job, per owner instruction: (1) merge the pending docs-only PR #57, (2) add a safe `--dry-run` mode plus tests, (3) wire a real production scheduler using the smallest reliable option compatible with the existing DO App Platform deployment — explicitly no Celery, no Redis queue, no separate worker — (4) verify locally against real Postgres before touching production, (5) open a PR the same disciplined way as before, (6) prepare (but not submit) a final Etsy appeal package.

**Done so far, in order:**
1. **PR #57 merged** (docs-only session log from the previous session) — merge commit `8345de4`. This retriggered both prod apps' auto-deploy (deploy_on_push doesn't path-filter); both reached `ACTIVE`, health/DB/Redis/Private-Beta/migration-0025 all reconfirmed unaffected.
2. **Reviewed the retention-cleanup implementation end-to-end** — confirmed scope is exactly the 4 intended tables (`listing_backup_snapshots`, `listing_media_backup_snapshots`, `listing_variation_backup_snapshots`, `csv_jobs`), filtered by `expires_at < now()`, and that deleting these rows cannot cascade to shops/tokens/listings/users/orgs/active sessions (they're FK children of those, not parents). Confirmed the script already exits non-zero on any unhandled exception (no swallowed errors) and is already idempotent.
3. **Added `--dry-run`** — `count_expired_snapshots()` in `app/services/retention_cleanup.py` (same `WHERE` clause as the delete, sharing one `_RETENTION_MODELS` tuple so the two can't drift), wired into `scripts/run_retention_cleanup.py` via `argparse`. Prints aggregate counts only.
4. **7 new tests** in `tests/test_retention_cleanup.py` — all passing locally against the SQLite test DB (dry-run finds/doesn't-delete/doesn't-modify-unexpired, real cleanup deletes/preserves-unexpired, idempotency, and a subprocess-level non-zero-exit-on-DB-failure test).
5. **Found the DO App Platform job kind is `SCHEDULED`, not `CRON`** — the task brief (and this repo's own prior docs) assumed "CRON job component," but `doctl apps propose` rejected `kind: CRON` outright with a real API error. Probed the correct shape directly against the live `bulk-edit-prod-api` app using `propose` (validates without applying, safe): `kind: SCHEDULED` + `schedule: { cron: "30 3 * * *" }` validates cleanly; there's no `timezone` field (confirmed by testing one — rejected), so DO Scheduled Jobs are UTC-only, which is exactly what was needed.
6. **Built `ops/app-specs/bulk-edit-prod-api.yaml`** — the full current prod-api spec (reused an already-cached copy from earlier in this engagement rather than re-pulling the full spec, per the "avoid unnecessary full-spec pulls" instruction) plus one new `retention-cleanup` job, mirroring the existing `migrate` job's build config exactly (same `github`/`dockerfile_path`/`source_dir`, same two `envs`: `ENVIRONMENT` + `DATABASE_URL`), single instance, smallest size (`apps-s-1vcpu-0.5gb`), no public route or domain. Re-validated the *entire* modified spec against the real prod-api app via `propose` — passed, no errors. The file's `SECRET`-type env vars are DigitalOcean's `EV[...]` encrypted ciphertext placeholders, round-tripped from the original spec unchanged — never decrypted, never re-exposed as plaintext.
7. Created branch `ops/production-retention-cleanup-scheduler` from `main`, docs updated (`WORKERS.md`, `DECISIONS.md`, `TASKS.md`, this file).

**Not yet done (pick up here):** local Postgres verification (4-expired/4-unexpired fixture, dry-run → real run → idempotent re-run), full backend suite re-run, frontend health checks, secret scan, commit in the 3 logical groups the owner specified, push, open the scheduler PR, wait for CI, merge, then run `doctl apps update` to actually register the new job (a brand-new component needs an explicit spec update — pushing to `main` alone only rebuilds components already in the spec, it does not add new ones), then verify DO confirms the job exists, run a production dry-run with the anomaly-threshold check, and only then flip the docs from "Option B" to "Option A" — not before DO actually confirms the job is live. The Etsy appeal draft (`ETSY_FINAL_APPEAL_DRAFT.md`) still needs to be written; not submitted regardless.

**Exact next step:** local Postgres verification, then the full pre-PR verification pass (Task 6 in the owner's spec), then open the PR.

---

## Previous — 2026-07-14, fifth session (Etsy compliance — merged to main and deployed to production)

**Where we are:** Same overall effort, two sessions later. Fourth session opened PR #56 from `etsy-compliance-production-readiness` (6 logical commits). This session's job was to merge it and deploy directly to production — no staging step, per explicit owner instruction — with a long list of hard safety rules (no Etsy/Stripe live writes, no DNS/Cloudflare changes, no disabling Private Beta, fail closed on any CI or orphan-data problem, never print secrets).

**What happened, in order:**
1. **CI blocker found and fixed.** `gh pr checks 56` showed the top-level `CodeQL` check failed (distinct from the two passing `Analyze` sub-jobs). Per the owner's explicit "if any required check is failed, stop, do not merge" instruction, stopped immediately. Investigated via `gh api .../check-runs/.../annotations` and found two real findings: an illegal `raise` of a statically-`Optional` exception in `apps/backend/app/services/etsy_http.py` (both retry-exhaustion raise sites), and an unused import in `apps/backend/scripts/run_retention_cleanup.py`. Fixed both, verified with `py_compile` + targeted tests, then ran the full backend suite twice from scratch (**975/975 passed** both times) before committing. Pushed as a new commit (`6e0a1f0`, not a force-push, not an amend — the branch was already open as a PR). All 6 required checks went green.
2. **Final pre-merge production-safety diff review** (owner's Task 2): read the full `main...etsy-compliance-production-readiness` diff. No secrets (grepped for key/token/password patterns — zero real hits, one changelog mention of the pre-existing real `owner.bulkeditapp.com` domain, not a leak). No staging URLs. No invented legal entity — `LEGAL_ENTITY_NAME` defaults to the product name itself, per an explicit `DECISIONS.md` entry from an earlier session, not a fabricated company. Verified live-pricing source (`apps/frontend/lib/pricingPlans.ts`, untouched by this PR but re-confirmed correct): Free $0, Basic $19/mo, Pro $49/mo, Basic yearly $15/mo (=$180/yr), Pro yearly $39/mo (=$468/yr) — old $9/$29 pricing confirmed absent. Confirmed AI public-marketing pages were cleanly removed (`FeaturesContent.tsx`, `featurePages.ts`) while the real `ALLOW_ETSY_DATA_TO_AI` server-side gate stays wired in `ai_tools.py` and `listing_health.py`. Confirmed `terms_accepted` is enforced server-side via a Pydantic validator (`schemas/auth.py`), not just a disabled frontend button.
3. **Merged PR #56** into `main` via a normal merge commit (`435a1aa`, no squash, no force-push, auto-merge not used — merged directly after confirming CI green and `mergeStateStatus: CLEAN`). Synced local `main` with a fast-forward pull.
4. **Production DB backup confirmed** before touching anything: `doctl databases backups <prod-db-id>` showed a same-day automated backup (2026-07-14 04:08 UTC) — DO's managed daily backups are active and current; no manual backup trigger was needed.
5. **Production orphan-data preflight** (read-only): wrote a short asyncpg script (not committed to the repo — scratchpad only) checking, for each of the 9 tables that gained an `organization_id` FK in migration 0025, whether any non-null `organization_id` fails to match a real `organizations.id`. **Result: 0 orphan rows across all 9 tables.** Production is a near-empty private-beta dataset, so this was expected but was verified, not assumed.
6. **Production env-var preflight** (names/types/scopes only, values never printed) for both `bulk-edit-prod-api` and `bulk-edit-prod-web`. Notable: neither app has `ALLOW_ETSY_DATA_TO_AI`, `ETSY_DERIVED_DATA_RETENTION_DAYS`, `TERMS_VERSION`/`PRIVACY_VERSION`, or `NEXT_PUBLIC_LEGAL_ENTITY_NAME` set explicitly — all fall back to the safe code-level defaults (AI gate closed, 30-day retention, blank legal entity → "Bulk Edit App"). `AI_PROVIDER=mock` in production — no live AI provider is even wired up right now.
7. **Rollback baseline captured** before deploying: prod-api's pre-merge `ACTIVE` deployment was `d8acd5a4-fa07-4927-ad3d-41599634663c` (main@`9dfa89e`); prod-web's was `38cb833e-c19a-4af6-b45a-08e231dc5242` (same commit). **Important operational note:** both DO apps have `deploy_on_push: true` — the moment the merge commit landed on `main`, both apps started auto-deploying on their own, before any manual "deploy" step was taken. This wasn't a rule violation only because the backup confirmation (step 4) and orphan preflight (step 5) had already both completed and passed *before* the merge happened. **For any future production merge on this repo, treat the merge itself as the deploy trigger — do the backup/orphan checks before merging, not after.**
8. **Monitored the auto-triggered deploys to completion.** prod-api's `migrate` `PRE_DEPLOY` job (kind: `PRE_DEPLOY`, `alembic upgrade head`) ran and reported `SUCCESS` as part of the deploy; both apps reached `ACTIVE` within about 4 minutes.
9. **Verified production state, all read-only / non-destructive:**
   - `alembic_version` on the live DB = `0025`; all 9 `fk_*_organization_id` constraints present with `confdeltype='c'` (`ON DELETE CASCADE`).
   - `api.bulkeditapp.com/api/v1/health`, `/health/ready` (DB connected), `/health/redis` (Redis connected) all `200`/`ok`.
   - `DELETE /api/v1/auth/me` unauthenticated → `403` (auth gate live, no real deletion attempted).
   - Registration endpoint's email validator rejected a test address before reaching `terms_accepted` — confirmed the server-side terms-acceptance enforcement via source diff instead of a live write, to avoid creating a real production account.
   - Live pricing verified by fetching the actual deployed Next.js route chunk (`/_next/static/chunks/app/pricing/page-*.js`, since the price strings are client-rendered and not present in the static-HTML `curl` output) — confirmed `$0/month`, `$15/month`, `$19/month`, `$39/month`, `$49/month`, `Save 20%` all present; `$9/month`/`$29/month` absent.
   - `/features/ai-listing-optimization` and `/features/listing-health-score` → `404` live, as intended (both remain real in-app features, only the public marketing pages were removed).
   - Private Beta gate fully intact: `app.bulkeditapp.com/`, `/dashboard`, `/login`, `/register` all → `307` to `/private-beta`; the `/private-beta` page itself loads `200` with the updated "temporarily paused... Etsy developer-account verification" copy on both `app.` and root `bulkeditapp.com`.
   - Broad smoke test across marketing + API routes: all `200`/expected-redirect, no `500`s. `/api/v1/auth/login` GET → `405` (expected, POST-only). `openapi.json` → `200`.
   - Chrome extension was not connected this session, so pricing/live-page visual verification was done via direct chunk-fetch instead of a real browser render — functionally equivalent for confirming the deployed content, but a real visual check is still worth doing next time the extension is available.
10. **Cleanup scheduler readiness: Option B.** `run_retention_cleanup.py` ships inside the deployed backend image but there is no `CRON`-kind job in the `bulk-edit-prod-api` app spec — nothing currently calls it on a schedule. Needs either a DO App Platform `CRON` job component or a real Celery beat schedule once a worker exists.

**One process note flagged transparently:** while fetching a full deployment JSON blob to check progress/phase, the response included `EV[1:...]`-format tokens for `SECRET`-type env vars. These are DigitalOcean's own encrypted-ciphertext placeholder format for `type: SECRET` fields (the standard, safe representation returned by the spec/deployment API — not decryptable without DO's own key, and explicitly designed to be safe to include in spec output) — not plaintext secrets. Still, this wasn't necessary for the check being performed; switched to narrower `--format` queries for every check after that.

**Not done / still out of scope:** Etsy appeal still not submitted (`ETSY_APPEAL_CHECKLIST.md`, `ETSY_SUPPORT_QUESTIONS.md`). Retention cleanup still not on a real schedule. No live Etsy OAuth/API test possible while the developer app is banned. No live Stripe checkout/cancellation/refund was performed at any point this session. Staging was not touched.

**Exact next step:** either submit the Etsy appeal now that the compliance fixes are live, or wire up the retention-cleanup scheduling (Option B → Option A). No other blockers remain from this deployment.

---

## Previous — 2026-07-13, third session (Etsy compliance — Stripe account-deletion safety gate)

**Where we are:** Same branch, same day, third session. The second session's validation pass left exactly one open item: a paying user could delete their account while their Stripe subscription stayed active and billing, with no remaining self-service cancel path. The owner reviewed this and gave an explicit decision: **do not auto-cancel Stripe subscriptions on deletion — block deletion instead, until the subscription is safely non-billable.** This session implemented that decision.

**What was built:**
- `app/services/billing.py::assert_account_deletion_billing_safe(org_id, db)` — the single authoritative eligibility check, called from `delete_account()` before any row is touched. Reads only the local `Subscription` row (kept current by verified Stripe webhooks) — no live Stripe API call. Explicit allowlist, fail-closed: safe only when no `Subscription` row exists, the org is free-plan with no `stripe_subscription_id`, or the subscription is `canceled` with `current_period_end` already past. Every other state — `active`, `trialing`, `past_due`, `unpaid`, `incomplete`, `incomplete_expired`, `active` with `cancel_at_period_end=true` (not yet actually ended), and any unrecognized future Stripe status — blocks by default.
- `DELETE /api/v1/auth/me` now returns `409` with a stable code (`ACTIVE_SUBSCRIPTION_MUST_BE_CANCELED` or `BILLING_PORTAL_UNAVAILABLE` for the no-stripe-customer-id edge case) when blocked. No Stripe IDs or billing metadata in the response.
- Minimal "Danger zone" deletion UI added to the existing `/billing` page (`apps/frontend/app/(app)/billing/page.tsx`) — no new page, no settings redesign. Shows the owner's exact required blocked-state copy and a "Manage Subscription" button routed through the existing `/billing/portal` endpoint.
- 14 new backend tests (`tests/test_auth.py`): a table-driven test covering all 11 owner-specified scenarios (no subscription / free plan / active / trialing / past_due / unpaid / incomplete / incomplete_expired / cancel-scheduled-not-ended / canceled-and-ended / unknown-future-status), plus 3 supporting tests (no-portal-access edge case, blocked-leaves-data-untouched, safe-deletion-preserves-existing-cascade).
- 2 real-Postgres end-to-end scenarios (local Docker only, no live Stripe calls): registered a user, inserted an `active` subscription directly, called the live API → `409`, confirmed user/org/subscription all unchanged; then set the subscription to `canceled` with a past `current_period_end`, added a connected Etsy shop, retried → `200`, confirmed zero rows remain anywhere.

**No new migration** — `Subscription` already had every column needed (`plan`, `status`, `stripe_customer_id`, `stripe_subscription_id`, `current_period_end`, `cancel_at_period_end`). Migration head unchanged: `0025`.

**Verification:** Backend **975/975 passed** (971 + 4 new test functions), confirmed via a full independent run. Frontend `tsc`/lint/build re-confirmed clean, 82 routes (no new route — same `/billing` page). Alembic single-head confirmed: `0025`.

**Not done / still out of scope:** not committed, not pushed, no PR, not merged, not deployed. No real Stripe API call was made at any point (checkout, cancellation, or otherwise). Etsy appeal still not sent. Live Etsy OAuth/API still impossible while banned.

**Exact next step:** owner does a final review of the full diff (now spanning all three sessions) and either approves commit/merge or requests changes. No open items remain from the owner's own blocker list — the Stripe question is resolved and implemented.

---

## Previous — 2026-07-13, second session (Etsy compliance — owner-review validation pass)

**Where we are:** Same branch (`etsy-compliance-production-readiness`), same day, second session — the owner asked for a rigorous final validation pass before merge: real PostgreSQL testing (not just SQLite), independent verification of every official Etsy policy citation, a full file-by-file change inventory, hygiene/secret scans, and an explicit decision matrix. No delegation of write access to subagents this session — all code/doc/migration/git work done directly.

**What this pass found and fixed, beyond the first session's work (below):**
- **Two real account-deletion bugs**, found only because this pass tested against real Postgres instead of trusting SQLite:
  1. `DELETE /api/v1/auth/me` crashed with HTTP 500 whenever the deleting user had an active refresh token or org membership (i.e., almost always) — a SQLAlchemy default-relationship-cascade issue (`Organization.members`/`User.memberships`/`User.refresh_tokens` tried to NULL out NOT NULL foreign keys instead of letting Postgres's `ON DELETE CASCADE` handle it). Fixed with `passive_deletes=True` on all three relationships.
  2. **9 tables had no foreign key on `organization_id` at all**, at the database level, pre-dating this branch entirely: `etsy_shops`, `listings`, `cost_profiles`, `listing_costs`, `social_connections`, `social_oauth_states`, `etsy_oauth_states`, `sync_jobs`, `video_renders`. This meant account deletion could never actually remove a seller's connected Etsy shop, tokens, or synced listing content — directly contradicting what this very compliance branch's docs were about to tell Etsy. Fixed with new migration `0025_add_missing_org_fk_constraints.py`.
  - Both bugs reproduced live (actual tracebacks captured from a real running backend against real Postgres), both fixed, both re-verified end-to-end afterward (register → connect shop/listing/snapshot → delete → confirm zero rows remain anywhere in Postgres, not just that the API returned 200). 3 new regression tests added to `tests/test_auth.py`.
- **Real local Postgres migration testing**, all three required scenarios: clean `alembic upgrade head` (single head confirmed: `0025`), upgrade from a pre-existing-data 0022 snapshot to head (verified no data loss, correct backfill, existing users NOT retroactively marked as having accepted terms), and a full downgrade/re-upgrade round trip for all of 0023/0024/0025.
- **Consolidated official Etsy policy citation table** added (`ETSY_COMPLIANCE_AUDIT.md` §6b) — every material policy claim in this branch now has a source URL and an honest classification (explicit Etsy requirement / conservative safeguard / requires clarification), rather than blending "Etsy requires this" with "we chose this conservatively."
- **30-day retention window is now configurable**: `ETSY_DERIVED_DATA_RETENTION_DAYS` (default 30, validated range 1-365) — no new migration needed, pure application-level default.
- Secret scan: no candidates found anywhere in the diff. Hygiene scan: no TODO/FIXME/debug artifacts/hardcoded staging hosts found in added lines.
- **Final authoritative backend count: 971/971 passed** (964 original + 4 from the first pass + 3 new account-deletion tests), confirmed via a full independent from-scratch run. Frontend re-confirmed clean (tsc/build, 82 routes) after the backend model changes.

**One item explicitly NOT fixed, flagged for an owner decision instead of a unilateral business-rule change:** `delete_account()` never touches Stripe. A paying user who deletes their account keeps an active Stripe subscription with no remaining way to self-cancel it. See `ETSY_PRODUCTION_READINESS.md` §27b — needs a product decision (block deletion until canceled? auto-cancel? warn?) before this endpoint is production-safe for paying users.

**Not done / still out of scope:** not committed, not pushed, no PR, not merged, not deployed — same as first session. Etsy appeal still not sent. Live Etsy OAuth/API still impossible while banned.

**Exact next step:** owner reviews this session's additions (`ETSY_COMPLIANCE_AUDIT.md` §6c, `ETSY_DATA_RETENTION.md` §4a, `ETSY_PRODUCTION_READINESS.md` §27) plus the Stripe question above, then either approves commit/merge or requests changes.

---

## Previous — 2026-07-13, first session (Etsy compliance + production readiness audit)

**Where we are:** Etsy developer app "bulk-edit-app" status escalated from "pending review" (2026-07-10) to **Banned**, with no explanation from Etsy. This session ran a full compliance + production-readiness audit and correction pass on branch `etsy-compliance-production-readiness` (branched from `main`, NOT merged, NOT deployed).

**What was produced:**
- 7 audit docs at repo root: `ETSY_COMPLIANCE_AUDIT.md` (top-level findings + most-likely ban reasons), `ETSY_FEATURE_MATRIX.md` (every feature classified A–F), `ETSY_PRODUCTION_READINESS.md` (30-item workflow checklist), `ETSY_DATA_RETENTION.md`, `ETSY_OAUTH_SCOPES.md`, `ETSY_APPEAL_CHECKLIST.md`, `ETSY_SUPPORT_QUESTIONS.md` (draft appeal email + updated app description).
- Real bug fixes: OAuth `scopes` column was storing `token_type` instead of the granted `scope` string (`apps/backend/app/services/etsy.py`); `disconnect_shop` now actually deletes tokens + pauses scheduled jobs (previously only flipped a flag, while the Privacy Policy claimed immediate token deletion); Etsy access-token auto-refresh is now actually wired into the sync path (the working `refresh_etsy_token()` existed but was never called).
- New compliance gate: `ALLOW_ETSY_DATA_TO_AI` (default `false`) hard-blocks sending Etsy-synced listing content to OpenAI/Anthropic at the service layer, independent of `AI_PROVIDER`. This was the #1 most likely ban cause found.
- 30-day retention cap (new `expires_at` columns + migration `0023`) on all backup-snapshot tables and CSV jobs, plus `scripts/run_retention_cleanup.py` for an external scheduler to call (no live worker exists yet).
- Terms/Privacy acceptance checkbox (frontend + backend + `terms_acceptances` table, migration `0024`) and a new self-service `DELETE /api/v1/auth/me` account-deletion endpoint.
- Website: removed "Founding access"/pre-launch marketing language and "Your Etsy control panel" replacement-framing; removed public marketing for Listing Health Score / AI Listing Optimization (both remain live in-app, gated); fixed the Etsy trademark disclaimer placement on `/shops`; removed the invented "Bulk Edit App LLC" default (now `LEGAL_ENTITY_NAME`-driven); fixed the stale `README.md` "Sprint 1" claim.

**Verification run this session:**
- Frontend: `tsc --noEmit` clean, `next lint` 0 errors (only pre-existing warnings), `next build` clean — 82 routes, 0 errors.
- Backend: registering the new required `terms_accepted` field broke registration payloads in 23 test files — delegated that mechanical fix to a subagent, which added `terms_accepted: True` across all 23 files plus 3 new tests (`test_register_fails_without_terms_acceptance`, `test_register_fails_with_terms_false`, `test_register_succeeds_and_records_acceptance`) and reported 964/964 passed. Independent verification (same session) added 4 more regression tests for previously-untested compliance fixes (OAuth scope bug, disconnect token deletion, token auto-refresh) in `tests/test_etsy.py`. Final confirmed count, run independently twice: **968/968 passed**.
- Alembic migrations `0023`/`0024`: syntax-checked (`ast.parse`), not applied against a real Postgres (Docker was not running in this environment) — **requires manual verification**: `docker compose up -d postgres && cd apps/backend && alembic upgrade head`.

**Not done / explicitly out of scope this session:**
- Not merged into `main`, not deployed anywhere. User must review the diff first.
- Etsy appeal email not sent — draft is in `ETSY_SUPPORT_QUESTIONS.md`, owner must send it from whatever account/inbox manages the Etsy developer app.
- Retry/backoff wrapper (`etsy_http.py`) only wired into `etsy_sync.py` + `etsy_variation_write.py`'s inventory GET — `etsy_media_write.py`'s two GET calls and all write-path PATCH/POST/PUT/DELETE calls still call `httpx` directly (documented as a fast-follow in `ETSY_COMPLIANCE_AUDIT.md`, not silently claimed done).
- Account-deletion cascade only tested against SQLite (no FK enforcement) — needs a real Postgres staging pass before trusting it in production.
- Live Etsy OAuth/API testing impossible while banned — everything Etsy-facing is code-verified only.

**Exact next steps:**
1. Confirm the background `pytest -q` run (started this session, may still be running) finished clean — check for a completion notification or re-run `cd apps/backend && python -m pytest -q`.
2. Review the 7 audit docs + full diff on `etsy-compliance-production-readiness`.
3. Decide: merge to `main` now (safe — no live-Etsy behavior depends on the ban being lifted) vs. wait.
4. Send the Etsy appeal (`ETSY_SUPPORT_QUESTIONS.md`), using `ETSY_APPEAL_CHECKLIST.md` first.
5. Once Etsy responds/unbans: run `alembic upgrade head` against real Postgres, re-test OAuth end-to-end, re-test the Etsy video-upload endpoint live (never exercised against a real shop, see `DECISIONS.md` 2026-06-27 entry), verify the account-deletion cascade on a Postgres staging DB.

**Rules still active:** never print secrets/tokens; no Etsy write during any future OAuth test; no real Stripe charge/subscription/refund; do not disable Private Beta until both Etsy and Stripe pass; no DNS/Cloudflare/owner-domain changes; do not deploy without explicit owner go-ahead.

---

## Previous — 2026-07-10 (Final controlled activation — BLOCKED on Etsy app review)

**Where we are:** Production is live (`bulk-edit-prod-api` / `bulk-edit-prod-web`), Stripe Live products/prices/env fully wired (prior session), Etsy/Stripe env vars injected into DO (prior session). This session ran the final controlled-activation checklist before disabling Private Beta.

**Stripe validation — PASSED:**
- Internal test account created: `sekiphayit1982+internal-test@gmail.com` (credentials in gitignored `deploy-production.local.env` under `INTERNAL_TEST_ACCOUNT_EMAIL`/`INTERNAL_TEST_ACCOUNT_PASSWORD`, never printed).
- Hit `/api/v1/billing/checkout` directly with a bearer token (no frontend/Private-Beta bypass code needed — Option B from the task spec). Got a **Live Mode** Checkout Session (`cs_live_...`), Basic Monthly, $19.00 USD confirmed via the Price object, production success/cancel URLs (`FRONTEND_URL=https://app.bulkeditapp.com`). One live Stripe customer created for the test account (`cus_UrMfFr80ISI59r`) — zero charges, zero subscriptions confirmed via Stripe API. All four price mappings (Basic/Pro × Monthly/Yearly) confirmed correct via read-only Price lookups.
- Webhook: signing secret present in DO, code validates signatures correctly — but the Stripe MCP connector has **no webhook-endpoint API access at all** (search returns empty for every resource-name variant tried: `webhook`, `webhook_endpoints`, `notification endpoint`, etc.) — cannot confirm the endpoint/events exist in the Stripe Dashboard from here. Same limitation hit in the prior session.

**Etsy validation — BLOCKED, not started (OAuth callback/token/read-only checks not yet run):**
- Generated the production Etsy OAuth authorization URL via `/api/v1/etsy/authorize` (bearer token from the same test account). Code-level checks passed: production `redirect_uri` (`https://api.bulkeditapp.com/api/v1/etsy/callback`), correct scopes (`listings_r listings_w shops_r profile_r`), PKCE `code_challenge` + `state` present, no staging domain.
- User opened the link → Etsy returned **"The application that is requesting authorization to use your Etsy account is not recognized."**
- Root cause confirmed: **the Etsy Developer app (keystring `7usvn9q6itlj6306sef64god`) is stuck in "pending review" on Etsy's side.** Etsy blocks OAuth completion for apps that haven't cleared review — this is external to our infra. Verified local env file and DO-deployed `ETSY_CLIENT_ID` are byte-identical (sha256 hash compare, no plaintext exposed) — ruled out a sync/typo bug.
- **Nothing further can be done on our end until Etsy approves the app.** This is a pure waiting-on-third-party blocker.

**Private Beta:** still enabled (`NEXT_PUBLIC_PRIVATE_BETA_MODE=true`) — correctly NOT disabled, since the task's own gate requires both Etsy AND Stripe to pass, and Etsy hasn't.

**Exact next steps once Etsy approves the app:**
1. Re-open the same-shape OAuth URL (client_id/scopes/redirect unchanged) or regenerate via `GET /api/v1/etsy/authorize` with the internal test account's bearer token (`POST /api/v1/auth/login` with the saved test creds).
2. User completes Etsy authorization in browser.
3. Verify callback (`GET /api/v1/etsy/callback`) succeeds, tokens stored encrypted (`app.core.encryption.encrypt_token`/`decrypt_token` — already confirmed used in `app/services/etsy.py`), and `GET /api/v1/etsy/shops` (read-only) returns the connected shop.
4. Only after that passes: Task 8 (disable Private Beta on `bulk-edit-prod-web`, trigger rebuild — `NEXT_PUBLIC_PRIVATE_BETA_MODE` is a Next.js `NEXT_PUBLIC_` var, inlined at **build** time in `middleware.ts`, so a plain env update is not enough — needs `doctl apps update --update-sources` or an equivalent rebuild), then Tasks 9-10 (app + marketing smoke tests).

**Rules still active:** never print secrets/tokens; no Etsy write during OAuth test; no real Stripe charge/subscription/refund; do not disable Private Beta until both Etsy and Stripe pass; no DNS/Cloudflare/owner-domain changes.

---

## Previous — 2026-07-05 (Resend domain verification + owner console rebuild)

**Where we are:** Two connected tasks in flight.

**Part A — Resend outbound sending domain verification (BLOCKED on user):**
Staging Resend SMTP is wired up (env vars applied to `bulk-edit-staging-api`), but every real send fails: `550 The bulkeditapp.com domain is not verified`. Stopped and asked the user to paste the exact DNS records from their Resend dashboard (Domain Verification/DKIM + Enable Sending/SPF/return-path + optional DMARC — explicitly NOT inbound/MX, "Enable Receiving" is disabled and must stay disabled). No Cloudflare DNS changes made yet. **Next action once records are provided:** add them to the Cloudflare zone for `bulkeditapp.com` (DNS-only, never proxied), click "Verify DNS Records" in Resend, then retest staging email end-to-end (health, forgot-password known/unknown email, contact form to both `SUPPORT_EMAIL` recipients).

**Part B — Owner console rebuild (code complete, not yet merged):**
Branch `feature/owner-console-subdomain-rebuild` off `staging`. Rebuilt the internal admin/owner structure per user spec:
- New `/owner` route group (`apps/frontend/app/owner/*`): Dashboard, Users, Organizations, Shops, Jobs, Contact Submissions, Emails (documented follow-up, no fake data), Audit Logs, System Health, Feature Flags (read-only), Content (placeholder) — all reusing the existing `require_superuser`-gated `/api/v1/admin/*` endpoints.
- `middleware.ts` rewrites `owner.bulkeditapp.com/*` → `/owner/*` (no new DO app — attaches to the existing frontend app), applies `X-Robots-Tag: noindex`.
- `/admin` is now a thin compat shim: real 404 for unauthenticated/non-superuser, same-origin redirect to `/owner` for confirmed superusers.
- Fixed a real bug found during the audit: the customer dashboard (`(app)/dashboard/page.tsx`) was unconditionally showing an "Admin Panel" card to every logged-in user (not gated by `is_superuser`, unlike the sidebar nav) — removed.
- Backend additions: `contact_submissions` table (migration 0020) — contact form now persists every submission regardless of email delivery outcome, so inquiries aren't lost while the Resend blocker is live; `GET /api/v1/admin/contact-submissions` and `GET /api/v1/admin/feature-flags` (both `require_superuser`-gated).
- Backend: 875/875 tests pass (6 new). Frontend: `tsc --noEmit` clean, `next build` clean (61 routes incl. 11 `/owner/*`), updated `e2e/auth-flow.spec.ts` for the new `/admin` behavior.
- Docs updated: `DECISIONS.md` (2 new entries), `docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md` (§8 email-history persistence follow-up, §9 feature-flags follow-up).

**Not yet done for Part B:** commit + push branch, open PR into `staging`, wait for CI/CodeQL, squash-merge, pull staging. Then (separate, deliberately not bundled into the same DNS action as Part A): attach `owner.bulkeditapp.com` as a custom domain on the existing staging frontend DO app + add the Cloudflare CNAME (DNS-only) — report the exact record before applying, per the user's own B9 instruction. Also still owed: a Cloudflare Access recommendation for `owner.bulkeditapp.com` (restrict to `sekiphayit1982@gmail.com` + explicitly-approved others only — do not create the policy without confirming the exact allow-list).

**Rules still active:** do not touch `main`/production; no new DO app; Cloudflare DNS changes limited to Resend verification records and `owner.bulkeditapp.com` routing only; never print SMTP_PASSWORD/Resend API key; owner console must never appear in sitemap/nav/footer/JSON-LD on the marketing site.

---

## Previous — 2026-07-02 (DigitalOcean + Cloudflare staging)

**Where we are:** Guardrails done; staging deploy scaffolding + automation built; **nothing provisioned yet** (blocked on DO/Cloudflare tokens + paid-resource approval). Production untouched, design-only.

**Branches / PRs:**
- `main` = `11c70da` (protected, unchanged — do NOT touch).
- `staging` = `dac28bb` (protected; PR required, 0 approvals, 5 checks, no force/delete).
- **PR #3 MERGED** → staging (docs: STAGING_PROVISIONING.md + guardrail status).
- **PR #4 OPEN** (`feature/staging-automation` → staging): staging provisioning automation. Not merged. Needs 5 checks green.
- Current local branch: `feature/staging-automation`.

**Tooling state:** `gh` installed + authed (user `Sekiph82`, ADMIN). `doctl` NOT installed (winget lacks it → use `scoop install doctl` or GitHub releases). No DO/Cloudflare tokens yet.

**Guardrails (done, verified):** main+staging rulesets active; secret scanning + push protection + Dependabot alerts/security updates on; Actions read-only. CI + CodeQL green on staging.

**Exact next steps (in order):**
1. Merge PR #4 into staging (after checks green) — user action (or `gh pr merge 4 --squash`).
2. User fills `deploy-staging.local.env` (gitignored): DIGITALOCEAN_ACCESS_TOKEN, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID, CLOUDFLARE_ACCOUNT_ID (+ optional sk_test_/etsy/AI). Run `scripts/prepare-staging-secrets.ps1`.
3. Install `doctl` (`scoop install doctl`).
4. **Approve DO cost** (~$10–40/mo staging) before creating paid resources.
5. Run `scripts/provision-staging.ps1` (I can drive it; pause for price OK before create).
6. DO dashboard: set backend SECRET env vars (values from local file), attach `api-staging` + `staging` custom domains.
7. Cloudflare: SSL Full(strict); Access on `staging.bulkeditapp.com` only (api-staging stays public + strict CORS).
8. Run `scripts/smoke-staging.ps1`. Then → Phase 2 Security Hardening.

**Key files:** `docs/operations/STAGING_AUTOMATION.md` (run guide), `STAGING_PROVISIONING.md` (manual), `.do/app.staging-*.yaml`, `scripts/{prepare-staging-secrets,provision-staging,smoke-staging}.ps1`.

**Rules still active:** no direct push to main/staging (PR only); production design-only; no sk_live_; fresh private ENCRYPTION_KEY (never the public CI key `uOv7…`); secrets never printed/committed.

---

## Last Session

**Date:** 2026-06-30
**Task:** One-click startup reliability fixes — port conflict + demo login seeding — COMPLETE
**Commits:** e7d5111 (port fix), aa93aee (launcher rewrite), 32c0e49 (seed fix)

### Task 1 — Docker port ACL fix
- `docker-compose.yml`: postgres + redis changed from `ports:` to `expose:` (no Windows host binding)
- New `docker-compose.dev-ports.yml` for optional dev host access
- Root cause: Windows Hyper-V/WSL2 dynamic port reservation blocks port 55432

### Task 2 — Windows one-click launcher rewrite
- `start-dev.bat`: 3-line thin wrapper (no logic duplication)
- `setup-and-start.bat`: ASCII-only (U+2500 replaced), Step 5 seed before compose up, Step 7c login verification

### Task 3 — Demo login seed BOM fix
- Root cause: PowerShell 5.1 `Set-Content -Encoding UTF8` prepends BOM, corrupts first key
- `create-seed.ps1`: WriteAllLines + UTF8Encoding($false) — no BOM written
- `local_seed.py`: encoding="utf-8-sig" — strips BOM on read
- New `scripts/windows/verify-demo-logins.ps1`: POST /api/v1/auth/login for both accounts after readiness
- 45/45 tests pass

**Test results:** 45/45 batch+seed tests pass (all pre-existing tests pass too)
**Security:** No secrets staged. .local-superusers.env gitignored.

---

## Previous Last Session

**Date:** 2026-06-29
**Task:** Code Freeze Cleanup — COMPLETE
**Commits:** 670f4c9 (fix: hide setup details and prepare integrations), f38a007 (chore: finalize code freeze cleanup)

**What was built:**

### Sprint 27 — Customer UX + Code Freeze (670f4c9)
- `apps/frontend/app/(app)/video-generator/page.tsx` — removed "Renderer disabled" / VIDEO_RENDERER_ENABLED / apt-get from main page; form + Generate Video button always visible; clicking Generate when disabled/missing-deps opens `VideoUnavailableModal` (friendly copy, superuser admin note only inside modal); always fetches status + templates in parallel; fallback static data if API fails
- `apps/backend/app/api/v1/promote.py` — `ConfigStatus` no longer returns `pinterest_missing_vars` / `instagram_missing_vars` (env var names leaked); only returns `pinterest_configured` / `instagram_configured` booleans
- `docker-compose.yml` — adds `VIDEO_RENDERER_ENABLED`, `FFMPEG_PATH`, `VIDEO_OUTPUT_DIR`, `PINTEREST_CLIENT_ID`, `PINTEREST_CLIENT_SECRET`, `PINTEREST_REDIRECT_URI`, `META_APP_ID`, `META_APP_SECRET`, `INSTAGRAM_REDIRECT_URI` passthrough to backend
- `.env.example` — adds placeholders for all social and video vars with correct local callback URLs
- `apps/backend/scripts/validate_env.py` — adds Video Renderer and Social Integrations check sections (masked output only)
- `apps/backend/tests/test_promote.py` — updated config-status assertions; added `test_promote_config_does_not_expose_var_names`
- `docs/operations/ENVIRONMENT.md` / `docs/operations/PROVIDER_SETUP.md` — added Video Generator, Pinterest, Instagram/Meta sections with setup instructions and callback URL examples

### Code Freeze Cleanup (f38a007)
- `.github/workflows/ci.yml` — CI now installs `requirements-dev.txt` (was `requirements.txt`); fixes test infrastructure — all 30 test files across 3 async patterns now have correct deps in CI
- `Makefile` — `test-backend` installs dev deps in container before pytest
- `docs/operations/LAUNCH_CHECKLIST.md` — added Video Generator, Pinterest, Instagram/Meta checklist items

**Test results (last clean run with full dev deps):**
- 62/62 focused backend tests pass (27 promote + 35 video)
- Previous clean run: 797/797 all backend tests (HANDOFF 2026-06-27)
- TypeScript: 0 errors
- Frontend lint: 0 errors, warnings only (all pre-existing)
- Security scan: no secrets in diff

**Docker:** Docker Desktop was offline during this session. All code changes are volume-mounted — apply on next `docker compose up`. Rebuild needed to pick up docker-compose.yml env passthrough changes.

## Next Task

**Status:** Code freeze ready. No blocking code issues.

**Manual setup still required before production:**
- Real Pinterest app credentials (developers.pinterest.com)
- Real Meta/Instagram app credentials (developers.facebook.com)
- Etsy production credentials
- Stripe live keys
- Email provider (SMTP)
- Storage provider (S3/MinIO) if needed
- `VIDEO_RENDERER_ENABLED=true` if advertising Video Generator

**Next prompt template:**
```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: Code freeze complete as of 2026-06-29. Last commits: 670f4c9, f38a007 on main.
CI fixed to install requirements-dev.txt. Video Generator + Promote customer UX clean.
No env var names in customer UI. All docs updated.

## Previous Session (2026-06-27)

**Date:** 2026-06-27
**Task:** Social Connect and Product Sharing UX — COMPLETE
**Commit:** 13421bd fix: complete social connect and product sharing UX

**What was built:**
- `apps/backend/app/api/v1/promote.py` — popup OAuth callbacks (HTML not redirect), connect-url endpoints, GET /listings (org-isolated), POST /pinterest/share + /instagram/share (deferred, no fake success), config-status now public, disconnect sets revoked/clears token, timezone-naive fix in _consume_state
- `apps/backend/app/models/social_connection.py` — added status, account_name, username, external_account_id, disconnected_at columns; access_token_encrypted now nullable
- `apps/backend/alembic/versions/0018_add_social_connection_account_fields.py` — migration adds 5 columns + alters nullable
- `apps/backend/tests/test_promote.py` — 54 tests (22 new): popup HTML, token exposure, org isolation, deferred share, listings empty state
- `apps/frontend/app/(app)/promote/page.tsx` — popup OAuth (window.open + postMessage), fallback link if blocked, SocialConnectionCard 4 states, PromoteListingCard grid, ShareModal with caption editor + deferred notice + copy/download fallbacks, Toast, product listings section
- **797/797 backend tests passing**
- **Frontend build: 0 errors**
- Docker Desktop was offline during session — migration 0018 will apply on next `docker compose up`

## Next Task

**Sprint 27 suggestion:** Real Etsy sync integration, Celery workers, email integration, or profit page editable cost fields.

**Deferred (documented):**
- Full Pinterest Pin creation (pending Pinterest developer app approval)
- Full Instagram publishing (pending Meta app review for instagram_content_publish)
- Pinterest board selector (requires boards:read API call)
- Etsy listing video upload via API

**Next prompt template:**
```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: Social UX COMPLETE. Popup OAuth for Pinterest/Instagram, product listing cards, share modals, deferred posting. 797/797 tests. Migration 0018 pending Docker restart.

## Previous Session (Sprint 26 polish)

**Date:** 2026-06-27
**Task:** Sprint 26 polish — Etsy Video Spec Compliance + Promote Page Clarity — COMPLETE
**Commit:** (see below)

**What was built:**
- `apps/backend/app/services/video_renderer.py` — ASPECT_RATIO_PRESETS dict (9:16/1:1/4:5/16:9 with width×height), check_ffmpeg(ffmpeg_path=None), render_slideshow_mp4() returns dict {output_path, file_size_bytes, width, height} + uses aspect ratio in vf filter, check_etsy_ready(file_size_bytes, duration_seconds, aspect_ratio, width, height) → (bool, list[str])
- `apps/backend/app/models/video_render.py` — added aspect_ratio, width, height, is_etsy_ready, etsy_issues_json columns; get_etsy_issues() helper
- `apps/backend/alembic/versions/0017_add_video_render_etsy_fields.py` — migration adds 5 new columns to video_renders table
- `apps/backend/app/api/v1/video_generator.py` — NEW schemas: VideoGeneratorStatus (renderer_enabled/available), TemplatesResponse (templates/aspect_ratios/etsy_specs), RenderRequest (aspect_ratio/duration_seconds), RenderStatusResponse (width/height/is_etsy_ready/etsy_issues/download_url); duration validation 5–15s → 400; aspect ratio validation; unimplemented template → 400; file_path/stored_filename NEVER in response; /config-status endpoint
- `apps/backend/app/api/v1/promote.py` — added ConfigStatus schema + GET /config-status endpoint
- `apps/frontend/app/(app)/video-generator/page.tsx` — format selector (9:16 default, 4 options), duration input (min=5, max=15, default=10, helper text), EtsyReadyChecklist component (5 checks: format/duration/size/resolution/aspect), download_url from API response
- `apps/frontend/app/(app)/promote/page.tsx` — state-specific copy blocks for all 4 states × 2 platforms; always-visible Instagram Business/Creator note in not_connected/connected/expired states; fallback copy+download row for non-app_not_configured states; typed toast {text, type}
- `apps/backend/tests/test_video_renderer.py` — NEW: 26 tests (check_ffmpeg, presets, check_etsy_ready boundary/multi-issue, render_slideshow_mp4)
- `apps/backend/tests/test_video_generator.py` — REWRITTEN: 17 tests (auth, status schema, templates, duration/aspect/template validation, file_path not exposed, org isolation)
- 747/747 backend tests pass. TypeScript: 0 errors.

## Next Task

**Sprint 27 suggestion:** Real Etsy sync integration, Celery workers, email integration, or profit page editable cost fields.

**Next prompt template:**
```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: Sprint 26 polish COMPLETE. Etsy video spec compliance (4 aspect ratios, 5-15s validation, 100MB check, etsy_ready checklist) + promote page per-state clarity. 747/747 tests. Migration 0017 applied.

Start Sprint 27: [task name]
[spec here]
```

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 26 follow-up — Real Video Rendering + Social OAuth — COMPLETE
**Commit:** 430eaa6 — feat: enable video rendering and social account connections

**What was built:**
- `apps/backend/Dockerfile` — added `apt-get install -y --no-install-recommends ffmpeg`
- `apps/backend/app/core/config.py` — added FFMPEG_PATH, VIDEO_OUTPUT_DIR, VIDEO_MAX_DURATION_SECONDS, VIDEO_MAX_IMAGES
- `apps/backend/app/services/video_renderer.py` — NEW: `check_ffmpeg()` returns (state, message) with states disabled/dependency_missing/working; `render_slideshow_mp4()` builds ffmpeg concat list, runs subprocess with arg list (never shell=True), 1080×1080 letterbox pad, libx264 fast preset
- `apps/backend/app/models/video_render.py` — NEW: VideoRender model (id, org_id, template_id, status, image_count, duration_seconds, file_size_bytes, file_path [never in API responses], error_message, completed_at)
- `apps/backend/alembic/versions/0015_create_video_render_tables.py` — NEW: video_renders table
- `apps/backend/app/api/v1/video_generator.py` — REWRITTEN: 5 endpoints (GET /status with 3 states, GET /templates, POST /render 202+background task, GET /renders/{id}, GET /renders/{id}/download FileResponse auth+org-isolated)
- `apps/backend/app/services/token_encryption.py` — NOT created; existing `app.core.encryption` (encrypt_token/decrypt_token) reused
- `apps/backend/app/models/social_connection.py` — NEW: SocialConnection (org, platform, access_token_encrypted, token_type, scope, expires_at; unique org+platform)
- `apps/backend/app/models/social_oauth_state.py` — NEW: SocialOAuthState (org, user, platform, state_hash=SHA256(state_value), expires_at, consumed_at)
- `apps/backend/alembic/versions/0016_create_social_tables.py` — NEW: social_connections + social_oauth_states tables
- `apps/backend/app/api/v1/promote.py` — REWRITTEN: 8 endpoints for Pinterest+Instagram (GET /status 4 states, GET /connect-url CSRF state, GET /callback token exchange + redirect, DELETE /disconnect); Fernet-encrypted tokens via app.core.encryption; tokens NEVER in API responses
- `apps/frontend/app/(app)/video-generator/page.tsx` — REWRITTEN: 3-state UI (disabled/dependency_missing/working), template selector, image URL textarea, POST /render, status polling every 2s, download via fetch+blob
- `apps/frontend/app/(app)/promote/page.tsx` — REWRITTEN: per-platform PlatformCard with 4 states, connect/disconnect buttons, OAuth redirect flow, error/success toast from ?connected= ?error= query params, Instagram Business requirement note

**Tests:** 617/617 backend tests pass (all pre-existing). TypeScript: 0 errors. All new module imports verified clean.

## Next Task

**Sprint 27 suggestion:** Real Etsy sync integration — wire the /shops OAuth flow to a live Etsy sandbox shop. Requires ETSY_CLIENT_ID + ETSY_REDIRECT_URI in .env. Or: profit page editable cost fields + persist to backend. Or: listing analytics — surface per-listing views/favs from Etsy API.

**Next prompt template:**
```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: Sprint 26 follow-up COMPLETE. Real video rendering (ffmpeg) + Pinterest/Instagram OAuth account connection flows implemented. 617/617 tests. Commit: 430eaa6.

Start Sprint 27: [task name]
[spec here]
```

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 26 — Growth, Insights, Credits, Media Reorder, Social Promote, Action Queue, Video Generator, Bulk Create — COMPLETE
**Commit:** feat: add insights credits promote action queue video generator and bulk create (Sprint 26)

**What was built:**
- `apps/frontend/lib/sound.ts` — playSuccessSound(), isSoundEnabled(), setSoundEnabled() using /sounds/cha-ching.mp3
- `apps/frontend/components/ui/AppShell.tsx` — SoundToggle in topbar (default off, localStorage key bulk-edit-sound-enabled); new nav items: Insights, Bulk Create, Promote, Video Generator; new icons: InsightsIcon, PromoteIcon, VideoIcon, CreateIcon
- `apps/frontend/app/features/page.tsx` — removed href from Listing Health + Profit (no more "Open →"); added 6 new feature cards; FeatureItem type for TypeScript
- `apps/frontend/app/faq/page.tsx` — 8 new FAQ entries: Insights, Credits, Promote, Video, Bulk Create sections
- `apps/frontend/app/(app)/listing-health/page.tsx` — checkboxes on every row + select-all header + bulk action bar ("Send to Bulk Edit →" with ?listing_ids= URL); individual Bulk Edit links pass listing_id
- `apps/frontend/app/(app)/bulk-edit/page.tsx` — reads ?listing_ids= URL param + banner "X listings pre-selected from Listing Health"
- `apps/frontend/app/(app)/dashboard/page.tsx` — Action Queue widget: fetches /api/v1/action-queue, shows preview_ready jobs across all types
- `apps/frontend/app/(app)/media/page.tsx` — reorder_images, replace_video, delete_video set to implemented: true (no longer "coming soon")
- `apps/frontend/app/(app)/scheduled/page.tsx` — bulk_edit_draft renamed "Apply Approved Bulk Edit Draft"; job payload JSON hidden under <details> Advanced
- `apps/frontend/app/(app)/insights/page.tsx` — date range picker + metrics grid + empty state note
- `apps/frontend/app/(app)/promote/page.tsx` — Pinterest + Instagram not-configured safe states; safety notice; config-driven
- `apps/frontend/app/(app)/video-generator/page.tsx` — "renderer not configured" safe state; safety notice
- `apps/frontend/app/(app)/bulk-create/page.tsx` — folder upload UI + draft editor; "not_configured" safe state; safety notice
- `apps/backend/app/api/v1/action_queue.py` — GET /action-queue; queries variation, media, csv, pricing jobs with status preview_ready
- `apps/backend/app/api/v1/insights.py` — GET /insights/summary with date_from/date_to query params
- `apps/backend/app/api/v1/promote.py` — GET /promote/config-status (pinterest_configured, instagram_configured)
- `apps/backend/app/api/v1/video_generator.py` — GET /video-generator/status (renderer_enabled from VIDEO_RENDERER_ENABLED config)
- `apps/backend/app/api/v1/usage.py` — GET /usage/summary (ai_credits, bulk_edits stub)
- `apps/backend/app/api/v1/bulk_create.py` — GET /bulk-create/status, POST /bulk-create/drafts (both return not_configured)
- `apps/backend/app/core/config.py` — Etsy rate limit vars, PINTEREST_*/META_*/INSTAGRAM_* social vars, VIDEO_RENDERER_ENABLED
- `apps/frontend/e2e/new-pages.spec.ts` — 4 smoke tests for insights, promote, video-generator, bulk-create

**Tests:** 24 new backend tests pass. 28 frontend routes build clean. Pre-existing Fernet test failures unrelated to Sprint 26 (confirmed pre-existing).

## Next Task

**Sprint 27 suggestion:** Real Etsy sync integration — wire the /shops OAuth flow to a live Etsy sandbox shop. Requires ETSY_CLIENT_ID + ETSY_REDIRECT_URI in .env. Or: profit page editable cost fields + persist to backend. Or: listing analytics — surface per-listing views/favs from Etsy API.

**Next prompt template:**
```
You are working inside: C:\Users\sekip\Desktop\Bulk-Edit
Start Sprint 26: [task name]
[spec here]
```

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 24 — Listing Health Score + Profit & Cost Calculator — COMPLETE
**Commit:** feat: add listing health score and profit calculator modules (Sprint 24)

**What was built:**
- `app/services/listing_health.py` — rule-based listing health score engine. Score 0-100, grade (excellent/good/needs_work/critical), priority, per-category issues (title, tags, description, media, pricing). Points deducted per rule violation. Informational cost warning (no penalty) stored separately.
- `app/services/profit.py` — Decimal-precision profit calculator. Etsy transaction fee (6.5%), payment fee (3% + $0.25), listing fee ($0.20), optional offsite ads (15%). Returns gross_revenue, net_profit, margin_percent, break_even_price, recommended_min_price, roi_percent.
- `apps/backend/alembic/versions/0014_create_profit_calculator_tables.py` — creates `cost_profiles` + `listing_costs` tables. Migration applied.
- `app/models/cost_profile.py` + `app/models/listing_cost.py` — SQLAlchemy ORM models with Numeric(10,4) for money.
- `app/schemas/listing_health.py` + `app/schemas/profit.py` — Pydantic v2 schemas for all endpoints.
- `app/api/v1/listing_health.py` — 5 endpoints: summary, paginated list (filter by grade/priority/search/sort), detail, AI suggestions (safe no-op when AI_PROVIDER=mock), recalculate.
- `app/api/v1/profit.py` — 7 endpoints: summary, paginated list, detail, upsert listing costs, list/create/update cost profiles.
- `apps/frontend/lib/api.ts` — 13 new API helpers + TypeScript interfaces for both modules.
- `apps/frontend/app/(app)/listing-health/page.tsx` — health score page with summary cards, grade/priority/sort filters, score badges, AI suggestions inline panel (never auto-applied disclaimer).
- `apps/frontend/app/(app)/profit/page.tsx` — profit page with fee rate warning banner, summary cards, profit/loss/missing-costs status badges, inline cost editor per listing.
- `apps/frontend/components/ui/AppShell.tsx` — added Listing Health + Profit nav items after Listings with HeartIcon + DollarIcon.
- `apps/frontend/app/(app)/dashboard/page.tsx` — health + profit summary widgets fetched in parallel.
- `e2e/listing-health.spec.ts` + `e2e/profit.spec.ts` — 4 Playwright tests (2 auth-redirect + 2 seeded).
- `tests/test_listing_health.py` + `tests/test_profit.py` — 52 tests total; all pass.

**Tests:** 673/673 backend tests pass (52 new). Build: 24 routes clean. Migration 0014 applied.

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 23 — Production Deployment Readiness Kit — COMPLETE
**Commit:** chore: add production deployment readiness kit (Sprint 23)

**What was built:**
- `apps/backend/scripts/validate_env.py` — standalone env validator. 20+ checks across Database, Redis, Security, CORS, Stripe, Etsy, AI, Rate Limiting, Observability. Masks all secret values. Hard-fails (exit 1) in production mode for missing/placeholder required vars. Warns in development/staging. CORS wildcard check, weak JWT_SECRET detection, Stripe test key in production warning.
- `scripts/smoke_test_deployment.ps1` — PowerShell smoke test. Checks /health, /health/ready, 11 frontend routes. Exit 0 on all pass. 13/13 passed locally.
- `scripts/smoke_test_deployment.sh` — Bash equivalent for Linux/Mac/CI.
- `docker-compose.prod.example.yml` — reference production compose. Health checks, restart policies, commented Celery worker/beat. No secrets hardcoded. Notes: prefer managed DB + Redis. No .local-superusers.env volume.
- `docs/operations/MIGRATIONS.md` — Alembic commands, migration table (0001-0013), zero-downtime migration notes, post-migration smoke test.
- `docs/operations/BACKUP_AND_ROLLBACK.md` — pg_dump, managed platform options, Redis considerations, Docker image rollback, emergency checklist.
- `docs/operations/STAGING_DEPLOYMENT.md` — staging architecture, env var table, step-by-step deploy procedure, promotion criteria.
- `docs/operations/DNS_SSL.md` — domain structure, DNS records, HSTS, CORS config, OAuth/webhook URLs, common mistake table.
- `docs/operations/PROVIDER_SETUP.md` — Stripe setup (products/keys/webhook), Etsy app (scopes, PKCE), OpenAI/Anthropic, email options, Sentry.
- `docs/operations/LAUNCH_READINESS_REPORT.md` — fill-in launch template with test/infra/security/provider/go-no-go sections.
- `.github/workflows/ci.yml` — added `validate_env.py --env development` step before backend tests. Uses CI env vars, exits 0 (warnings only), so CI doesn't break.

**Tests:** 621/621 backend tests pass. Smoke test 13/13. Routes 19/19. Security headers present frontend + backend.

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 22 — First-Run Onboarding, Non-Superuser Seed, Etsy Connection UX — COMPLETE
**Commit:** feat: add first-run onboarding and customer seed flow (Sprint 22)

**What was built:**
- `apps/backend/app/services/local_seed.py` — `_upsert_user()` now takes `is_superuser: bool = False`; `seed_superuser()` takes `is_superuser: bool = True`; `seed_on_startup()` calls FREE with `is_superuser=False`, PAID with `is_superuser=True`; `run_seed()` updated same way
- `apps/backend/tests/test_seed_local_superusers.py` — 4 new tests: `test_free_user_is_not_superuser`, `test_paid_user_is_superuser`, `test_seed_on_startup_free_user_is_not_superuser`, `test_seed_on_startup_paid_user_is_superuser` (27 total in file, 621 total backend)
- `apps/frontend/components/onboarding/OnboardingChecklist.tsx` — NEW: 4-step checklist (connect shop, sync listings, try bulk edit, explore paid features), progress bar, hides when all complete, dark mode safe via `be-card`, `data-testid="onboarding-checklist"`
- `apps/frontend/app/(app)/dashboard/page.tsx` — fetches `/api/v1/etsy/shops` (shopCount) and `/api/v1/listings?limit=1` (listingCount); shows `OnboardingChecklist` above feature cards when counts loaded
- `apps/frontend/app/(app)/shops/page.tsx` — empty state: added Etsy trademark note + OAuth explanation; button text changed to "Redirecting to Etsy..."
- `apps/frontend/e2e/onboarding.spec.ts` — NEW: 2 always-run tests (unauthenticated dashboard, shops no-crash) + 2 seeded-user tests (checklist visible, trademark note)
- Live seed verification: `test@example.com is_superuser=False` ✓, `test-su@example.com is_superuser=True` ✓

**Tests:** 621/621 backend tests pass. Playwright: 13 passed, 4 skipped. Build: 22 routes, 0 TS errors.

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 21 — Production Monitoring, Redis Rate Limiting, Sentry, Celery Readiness — COMPLETE
**Commit:** chore: add production monitoring redis rate limiting sentry and celery readiness (Sprint 21)

**What was built:**
- `apps/backend/app/core/rate_limit.py` — upgraded to Redis+memory dual backend; IP-only key for login (Pydantic already consumed body); memory fallback on Redis unavailability; `contact_rate_limit` dependency added
- `apps/backend/app/core/config.py` — added RATE_LIMIT_REDIS_URL, RATE_LIMIT_CONTACT_PER_HOUR, SENTRY_DSN, SENTRY_ENVIRONMENT, SENTRY_TRACES_SAMPLE_RATE
- `apps/backend/app/main.py` — `_init_sentry()` + `_scrub_sentry_event()` (scrubs password, tokens, keys); safe no-op when DSN absent
- `apps/backend/requirements.txt` — added `sentry-sdk[fastapi]==2.19.2`
- `apps/backend/app/schemas/admin.py` — AdminSystemHealth upgraded: redis_status, rate_limit_backend, rate_limit_enabled, sentry_configured, worker_status, csp_mode
- `apps/backend/app/services/admin.py` — `_check_redis_health()` probe; `get_system_health()` returns all new fields; never exposes Redis URL
- `apps/frontend/next.config.mjs` — removed `unsafe-eval` in production; added HSTS for production (NODE_ENV=production); sha256 hash documented as comment
- `apps/backend/tests/test_rate_limiting.py` — 9 tests (up from 3)
- `apps/backend/tests/test_security_headers.py` — 10 tests (up from 3); system-health monitoring field tests, no-Redis-URL, no-Sentry-DSN, worker_status
- `docs/operations/MONITORING.md` — NEW: health endpoints, Sentry, rate limits, Stripe, Etsy, scheduled jobs, Redis, admin checks, daily checklist
- `docs/operations/RUNBOOK.md` — NEW: 14 incident scenarios + rollback + secret rotation procedures
- `docs/operations/WORKERS.md` — NEW: current inline scheduler docs + future Celery architecture
- `.github/workflows/e2e.yml` — NEW: manual workflow_dispatch for Playwright E2E with artifact upload

**Tests:** 609/609 backend tests pass. Build: 22 routes, 0 errors.

## Previous Last Session

**Date:** 2026-06-27
**Task:** Sprint 20 — Launch QA, CI/CD, E2E, Rate Limiting, CSP — COMPLETE
**Commit:** chore: add launch qa ci e2e rate limiting and security headers (Sprint 20)

**What was built:**
- `.github/workflows/ci.yml` — GitHub Actions CI: backend tests + postgres:16 + redis:7 services, Alembic migration, pytest; frontend lint+build; docker-compose config validate
- `apps/frontend/playwright.config.ts` — Playwright config targeting localhost:3100
- `apps/frontend/e2e/public-pages.spec.ts` — 7 tests: 5 marketing pages + 2 auth pages
- `apps/frontend/e2e/theme.spec.ts` — 3 tests: anti-flash script, light mode, dark mode
- `apps/frontend/e2e/auth-flow.spec.ts` — 1 test (dashboard loads) + 2 seeded-user tests (skipped without `PLAYWRIGHT_RUN_SEEDED_TESTS=1`)
- `apps/backend/app/core/rate_limit.py` — in-memory rate limiter; login 10/min, register 5/min per IP; disabled by default (`RATE_LIMIT_ENABLED=false`)
- `apps/backend/app/core/security_headers.py` — `SecurityHeadersMiddleware` adding 4 headers to all API responses
- `apps/backend/app/main.py` — imports + registers SecurityHeadersMiddleware
- `apps/backend/app/core/config.py` — added RATE_LIMIT_ENABLED, RATE_LIMIT_BACKEND, RATE_LIMIT_LOGIN_PER_MINUTE, RATE_LIMIT_REGISTER_PER_MINUTE
- `apps/backend/app/api/v1/auth.py` — added `Depends(login_rate_limit)` / `Depends(register_rate_limit)` to login + register
- `apps/frontend/next.config.mjs` — CSP + X-Content-Type-Options + X-Frame-Options + Referrer-Policy + Permissions-Policy + X-DNS-Prefetch-Control on all routes
- `apps/frontend/components/ui/AppShell.tsx` — `data-testid="admin-nav-link"` on Admin link
- `apps/frontend/app/(app)/admin/page.tsx` — `data-testid="admin-access-denied"` + `data-testid="admin-dashboard"`
- `apps/backend/tests/test_rate_limiting.py` — 3 tests
- `apps/backend/tests/test_security_headers.py` — 3 tests
- `docs/operations/LAUNCH_CHECKLIST.md` — NEW: 10-section production launch checklist
- TASKS.md, PROJECT_STATUS.md, HANDOFF.md, CHANGELOG_AI.md, DECISIONS.md, SECURITY.md updated

**Tests:** 595/595 backend tests pass. Playwright: 11 passed, 2 skipped. Build: 22 routes, 0 errors.

## Next Task

**Sprint 24** — Options: (1) CSP nonce hardening via Next.js middleware (remove unsafe-inline), (2) Celery task workers (real background jobs), (3) Email delivery integration (contact form + billing notifications), (4) Etsy token auto-refresh. Choose from TASKS.md backlog.

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: Sprint 23 COMPLETE. Production deployment readiness kit shipped: validate_env.py, smoke_test_deployment scripts, docker-compose.prod.example.yml, 6 ops docs (MIGRATIONS, BACKUP_AND_ROLLBACK, STAGING_DEPLOYMENT, DNS_SSL, PROVIDER_SETUP, LAUNCH_READINESS_REPORT), CI validate_env step. 621/621 backend tests. 19/19 routes.

Start Sprint 24 per TASKS.md backlog.
```

## Next Prompt (legacy Sprint 21 — DONE)

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: Sprint 20 COMPLETE. CI/CD live, Playwright E2E added, rate limiting + security headers active. 595/595 tests. 22 routes. 0 errors.

Start Sprint 21: CSP nonce hardening, Celery production workers, monitoring, post-launch ops.
```

## Previous Last Session

**What was built:**
- `apps/backend/app/schemas/admin.py` — added `AdminBillingSummary`, `AdminStripeSummary`, `AdminProductUsage`, `AdminSystemHealth` schemas
- `apps/backend/app/services/admin.py` — added `get_billing_summary`, `get_stripe_summary`, `get_product_usage`, `get_system_health` service functions + `BillingEvent` import
- `apps/backend/app/api/v1/admin.py` — added 5 new endpoints: `GET /admin/billing-summary`, `/stripe-summary`, `/product-usage`, `/system-health`, `/audit-log`; all require superuser
- `apps/frontend/components/ui/AppShell.tsx` — Admin nav item now hidden from non-superusers; reads `is_superuser` from `/me` response
- `apps/frontend/lib/api.ts` — added `AdminUsageSummary`, `AdminBillingSummary`, `AdminStripeSummary`, `AdminProductUsage`, `AdminSystemHealth` types + 6 new API helpers
- `apps/frontend/app/(app)/admin/page.tsx` — full rewrite as 6-tab business dashboard (Overview, Users, Billing, Etsy, Usage, System)
- `apps/backend/tests/test_admin_dashboard.py` — 17 new tests: auth gates, response shape, MRR field name safety, is_superuser in /me

**Tests:** 17/17 new tests pass. 59/59 total admin tests pass. Build: 20 routes, 0 errors. TypeScript: 0 errors.

## Next Task

**Sprint 20** — CI/CD pipeline, production Docker, rate limiting, CSP headers, Playwright E2E tests.

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: Sprint 19 COMPLETE. Admin business dashboard live. 20 routes, 0 TS errors.

Start Sprint 20 per TASKS.md.
```

## Previous Last Session

**What was built:**
- `apps/frontend/app/globals.css` — `.be-btn-primary`, `.be-btn-secondary`, `.be-card`, `.be-contact-card`, `.be-faq-item`, `.be-faq-trigger`, `.be-hero-bg`, `.be-section-accent`, `.be-icon-ring`, `.be-step`. Gradient buttons, hover-lift cards, reduced-motion guard.
- `apps/frontend/components/marketing/MarketingNav.tsx` — sticky nav with active link highlighting, mobile-safe, links to /features /faq /contact-us /pricing.
- `apps/frontend/components/marketing/MarketingFooter.tsx` — 4-col footer, legal Etsy disclaimer.
- `apps/frontend/app/features/page.tsx` — 11-feature grid, 6-step workflow, safety checklist, CTA, animated listing preview visual.
- `apps/frontend/app/faq/page.tsx` — animated accordion, 6 categories (General, Etsy Connection, Safety, Billing, AI Tools, CSV & Dynamic Pricing), 17 Q&As.
- `apps/frontend/app/contact-us/page.tsx` — 4 contact cards, demo form with success state, FAQ cross-link.
- `apps/frontend/app/page.tsx` — replaced inline nav with MarketingNav, added MarketingFooter, motion FadeUp animations, feature tease section.
- `apps/frontend/app/pricing/page.tsx` — added MarketingNav + MarketingFooter, removed inline logo.
- Build: 22 routes, 0 errors. 521/521 backend tests pass.

## Previous Last Session

**What was built:**
- `app/schemas/admin.py` — 16 Pydantic schemas. No password_hash, no Etsy tokens, no Stripe secret keys, no raw billing event payload.
- `app/services/admin.py` — `_paginate()` generic helper + 14 list functions + 4 safe action functions (disable/enable user, pause/resume job).
- `app/api/v1/admin.py` — 20 endpoints all gated on `require_superuser` from deps.py. Prefix: `/api/v1/admin`.
- Router registered in `app/api/v1/router.py`.
- `tests/test_admin_panel.py` — 42 tests: auth gates, 403 for non-superuser, no secrets in responses, pagination, user disable/enable, job pause/resume, not-found handling.
- `apps/frontend/lib/api.ts` — admin types + 11 API helpers appended at end.
- `apps/frontend/app/admin/page.tsx` — admin UI: 8 overview cards, 6 section tabs (users, orgs, subs, shops, scheduled jobs, events), paginated tables, inline disable/enable and pause/resume actions, 403 handled cleanly.
- Dashboard card added: "Admin Panel" → /admin.
- 521/521 tests pass. Build clean.

**Security verified:**
- All endpoints → 403 without superuser role
- No password_hash in any user response
- No Etsy access_token/refresh_token in any shop response
- No stripe_subscription_id or stripe_price_id in any subscription response
- No destructive delete operations
- Cannot disable own account (400)

**Root Cause:**
1. Sprint migrations 0008-0012 originally used `postgresql.UUID`/`sa.UUID` for FK columns while parent tables (`organizations`, `users`, `listings`, etc.) have `VARCHAR(36)` IDs (from migration 0001+). PostgreSQL rejects FK constraints across incompatible types.
2. All parent-table ORM models (`organization.py`, `user.py`, `listing.py`, and 21 others) declared columns as `Uuid(as_uuid=False)`. With asyncpg, this generates `$1::UUID` bind type in SQL. PostgreSQL rejects `VARCHAR = UUID` comparisons.
3. `bcrypt==5.0.0` (unpinned transitive dep) broke `passlib==1.7.4` — `__about__.__version__` removed, causing seed hash failure.

**Fixes:**
- Migrations 0008-0012: already fixed to use `sa.String(36)` (were in unstaged changes)
- **ALL 43 model files**: replaced `Uuid(as_uuid=False)` → `String(36)`, removed `Uuid` imports (bulk PowerShell replace across 24 files)
- `requirements.txt`: pinned `bcrypt==4.0.1` (last compatible with passlib 1.7.4)

**Verified:**
- `alembic upgrade head` from clean DB: all 12 migrations pass, no FK errors
- Backend health: HTTP 200 `{"status":"ok","service":"bulk-edit-api"}`
- Frontend: HTTP 200, valid HTML
- Local superuser seed: `test@example.com (free, created) | test-su@example.com (pro_monthly, created)` — no errors
- Login: both users return `access_token`; wrong password → 401
- `.local-superusers.env` gitignored, not staged
- **438/438 tests pass on host**

## Previous Session — Sprint 16

**Date:** 2026-06-26
**Task:** Fix local superuser workflow — seed on backend startup — COMPLETE
**Commit:** `23e1520` — `chore: seed local superusers on backend startup`
**Completed:**
- `app/main.py` — FastAPI lifespan hook calls `seed_on_startup` on startup
- `app/services/local_seed.py` — `seed_on_startup(db, env_path=None)` async fn: silent if file absent, logs warning on error, never crashes backend
- `start-dev.bat` + `start-dev-clean.bat` — removed Y/N seed prompt and `seed_local_superusers.py` invocation entirely
- `tests/test_seed_local_superusers.py` — rewritten: 23 tests including startup hook tests and login endpoint tests (fixed `.test` TLD rejection — changed to `@example.com`)
- `tests/test_windows_batch_readiness.py` — replaced `test_start_dev_bat_has_seed_prompt` with `test_start_dev_bat_no_seed_prompt` (seed strings must be ABSENT)
- 431/431 full suite passes

**How seeding works now:**
1. Backend starts → FastAPI lifespan fires `seed_on_startup`
2. If `.local-superusers.env` absent → silent, backend continues normally
3. If present → creates/updates free + paid superusers in DB (idempotent)
4. Users log in normally via unchanged `/api/v1/auth/login` endpoint
5. No Y/N prompt. No bat file involvement. No login bypass.

## Previous Session

**Date:** 2026-06-26
**Task:** Local Dev Reliability — Superuser Seed + Startup Readiness — COMPLETE
**Commit:** `d0fc2c8` — `chore: add local superusers and startup readiness checks`
**Completed:** `.gitignore` updated. `.local-superusers.env.example` created. `local_seed.py` service (async, idempotent, no password output). `scripts/seed_local_superusers.py` thin CLI wrapper. All 4 .bat files updated: run compose -d, poll backend health (8100/api/v1/health) + frontend (3100) via PowerShell Invoke-WebRequest before opening browser. 431/431 full suite.

## Previous Session

**Date:** 2026-06-26
**Sprint:** Sprint 15 — Dynamic Pricing — COMPLETE
**Commit:** `3286787` — `feat: add dynamic pricing workflow (Sprint 15)`
**Completed:** DynamicPricingJob + DynamicPricingRecommendation models (alembic 0012). `dynamic_pricing_jobs_used` on UsageCounter. Pro plan gate (`can_use_dynamic_pricing`, 100 jobs/month). Full calculation engine: percentage_adjustment, fixed_amount_adjustment, set_price, reference_price. Safety guardrails: margin floor (Decimal math), price floor, price cap, rounding (ending_99/95/nearest_50/nearest_100). accept/reject/accept-all/convert endpoints. Convert creates BulkEditSession draft + scoped BulkEditChange (`target_listing_ids=[listing_id]`) — NEVER writes to Etsy. 50 tests. `/pricing-rules` page (listing selector, rule builder, guardrails, preview table with per-row accept/reject, convert modal with "CONVERT PRICES" confirmation). Dashboard DP card. 403/403 full suite passing. Build: 16 routes, zero errors.

## Current State

**Backend (`apps/backend/`):**

**Local Seed Service (`app/services/local_seed.py`):**
- `seed_on_startup(db, env_path=None)` — async startup hook. Reads `.local-superusers.env`, upserts free + paid superuser. Silent if file missing. Warning log on error. Never raises.
- `seed_superuser(db, email, password, full_name, org_name, plan)` — idempotent upsert: user + org + member + subscription. Returns summary dict (no password). status = "created" or "updated".
- `load_seed_config(path)` — parses KEY=value env file, raises `SeedConfigError` if file missing
- `_require(config, key)` — raises `SeedConfigError` if key absent
- `run_seed(env_path)` — CLI fn for manual use via `scripts/seed_local_superusers.py`

**ENV_FILE_PATH:** resolves to `apps/backend/.local-superusers.env` on host, `/app/.local-superusers.env` inside Docker (volume mount `./apps/backend:/app`)

**Sprint 14 additions (CSV Import / Export):**
- `app/models/csv_job.py` — CSVJob model (status machine: processing → preview_ready → converted/failed)
- `app/models/csv_row.py` — CSVRow model (per-row: listing_id, etsy_listing_id, raw_data, normalized_data, diff, status, errors, warnings)
- `app/models/bulk_edit_change.py` — added `target_listing_ids` JSON nullable column
- `alembic/versions/0011_create_csv_import_export_tables.py` — migration
- `app/schemas/csv_tools.py` — 6 schemas
- `app/services/csv_tools.py` — full service: export, template, parse, validate, import job, preview, convert to BulkEditSession
- `app/api/v1/csv_tools.py` — 6 REST endpoints under /api/v1/csv
- `app/services/bulk_edit.py` — preview engine updated: `if targets is None or lid in targets: apply_change()`
- `tests/test_csv_tools.py` — 49 tests

**Sprint 15 additions (Dynamic Pricing):**
- `app/models/dynamic_pricing_job.py` — DynamicPricingJob model
- `app/models/dynamic_pricing_recommendation.py` — DynamicPricingRecommendation model
- `app/models/usage_counter.py` — added `dynamic_pricing_jobs_used`
- `app/core/plans.py` — added `dynamic_pricing_jobs_per_month`
- `alembic/versions/0012_create_dynamic_pricing_tables.py` — migration
- `app/schemas/dynamic_pricing.py` — 6 schemas
- `app/services/dynamic_pricing.py` — full engine
- `app/api/v1/dynamic_pricing.py` — 10 REST endpoints
- `tests/test_dynamic_pricing.py` — 50 tests

**Frontend (`apps/frontend/`):**
- `app/pricing-rules/page.tsx` — Dynamic Pricing 3-step page
- `app/csv/page.tsx` — CSV 3-tab page
- `lib/api.ts` — all types + helpers for DP and CSV
- `app/dashboard/page.tsx` — DP + CSV cards

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Dev Startup Scripts

| File | Who | What |
|---|---|---|
| `setup-and-start.bat` | Friend / reviewer | Installs Git + Docker if missing, clones repo, starts app, opens browser |
| `setup-and-start-clean.bat` | Friend / reviewer | Same + destroys DB volumes (requires YES) |
| `start-dev.bat` | Developer | Stops old containers, rebuilds, polls readiness, opens browser, streams logs |
| `start-dev-clean.bat` | Developer | Same + destroys DB volumes (requires YES) |

**ASCII-only scripts.** Docker Desktop auto-start via `docker info` poll (5s, 180s max). Project isolation: `docker compose -p bulk-edit`.

## Safety Gates Active

- Seeded users authenticate via unchanged `/api/v1/auth/login` — no bypass
- `.local-superusers.env` gitignored — never committed
- `seed_on_startup` swallows all exceptions — bad env file never crashes backend
- No passwords logged or printed

## Next Task

**Sprint 18: Tests, Deployment, Security Hardening, Polish**

CI/CD pipeline, production Docker config, OWASP security audit, >80% backend test coverage, accessibility.

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Current state: 521/521 tests passing. Sprints 1-17 all COMPLETE.

Start Sprint 18 per TASKS.md.
```

## Known Issues

- Etsy access token auto-refresh not implemented. Logs warning but uses token.
- `fetch_listing_videos` is best-effort — returns empty list on 404/405.
- Sync runs inline in HTTP thread. Celery background task deferred to Sprint 16.
- Frontend npm not installed — run `npm install` inside `apps/frontend` or `docker compose up`.
- Video upload/delete NOT supported — Etsy requires direct file upload. Stubs return 501.
- Image reorder NOT supported — Etsy has no atomic reorder endpoint.
- Variation revert NOT implemented — backup snapshots created; revert deferred.
- AuditLog model uses `extra_data` in Python, stored as `metadata` column in DB.
- `anyio==4.6.2` in requirements-dev.txt is yanked — works fine.

## Push Status

Last pushed: `23e1520` — chore: seed local superusers on backend startup
Branch: main
