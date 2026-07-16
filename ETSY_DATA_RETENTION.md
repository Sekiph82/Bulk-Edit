# ETSY_DATA_RETENTION.md

Governs caching, freshness, and retention of Etsy-derived data. Etsy's API Terms of Use require that cached Etsy content not be displayed materially stale and not be retained "longer than is reasonably necessary to provide service to your Application's users." (Section quoted via search-engine excerpt of `https://www.etsy.com/legal/api/` — direct fetch blocked, see `ETSY_COMPLIANCE_AUDIT.md` §7 sourcing note; owner should confirm exact wording directly before appealing.)

## 1. Freshness — `last_synced_at`

- Every `Listing` row carries `last_synced_at`, set by `etsy_sync.py` on every successful sync.
- **New in this branch:** the bulk-edit preview response and the frontend preview screen surface a staleness warning when `last_synced_at` is more than **6 hours** old (matches the listing-content freshness window cited in the audit). The warning does not block preview generation, but it is shown before the user reaches the final confirmation step, and a "Re-sync now" action is offered.
- Sensitive writes (bulk-edit apply, revert, media apply, variation apply) still read from the local `Listing`/`ListingVariation` row as the snapshot source (unchanged from prior behavior) — this is a deliberate design tradeoff already documented in `DECISIONS.md` (fetch-patch-put pattern only exists for the variation inventory tree, which is always fetched fresh from Etsy at write time; scalar fields use the last-synced local copy). The staleness banner is the mitigation, not a forced re-sync on every write, to avoid turning every bulk apply into a full re-sync (rate-limit and latency risk).

## 2. Snapshot retention — 30-day default, configurable

Applies to: `ListingBackupSnapshot`, `ListingMediaBackupSnapshot`, `ListingVariationBackupSnapshot`, `CSVJob`.

**Official basis, verified against actual Etsy sources (not inferred) — see `ETSY_COMPLIANCE_AUDIT.md` §6b for the full citation table:** Etsy's API Terms state cached Etsy content must not be stored "longer than is reasonably necessary to provide service to your Application's users." **This is real and explicit (classification A). The specific number 30 is NOT — Etsy's text does not give a day count.** Classification for the current implementation:

| Question | Answer |
|---|---|
| Does Etsy explicitly require a 30-day limit for backup snapshots? | No — no day count found in any official source reviewed. |
| Does Etsy explicitly require a 30-day limit for rollback history? | No — same as above; snapshots and revert history are the same tables here. |
| Does Etsy explicitly require a 30-day limit for CSV exports? | No — CSV exports aren't addressed by name in any official source found. |
| Does Etsy require *some* bound on Etsy-derived data generally? | Yes (A) — the "reasonably necessary" principle applies to all of the above. |
| **Overall classification of the current 30-day implementation** | **Conservative but reasonable (not "explicitly required," not "overly broad" either — 30 days is a defensible reading of "reasonably necessary" for data whose entire purpose is a time-bounded revert window).** |

- **Before this branch:** no `expires_at` column, no cleanup job. Snapshots (including full listing content and image/video references) were retained indefinitely — this was the actual policy gap, not the specific number chosen to replace it.
- **This branch adds:**
  - `expires_at` column on all three snapshot tables plus `CSVJob`, computed at insert time via `_default_expiry()` in `app/models/listing_backup_snapshot.py` (migration `0023_add_snapshot_retention.py`).
  - **Now configurable:** `settings.ETSY_DERIVED_DATA_RETENTION_DAYS` (env var, default `30`, validated range 1-365) — added during owner-review validation so the number can be tightened or loosened without a code change if Etsy gives explicit guidance later. No new migration was needed for this — it's a pure application-level default, the column type/structure is unchanged.
  - `app/services/retention_cleanup.py::delete_expired_snapshots()` — deletes snapshot rows where `expires_at < now()`. **Verified against a real local Postgres database, not just read**: inserted one snapshot with a future `expires_at` and one with a past `expires_at`, ran the script twice — first run correctly deleted 0 rows (nothing expired yet), second run (after adding a genuinely-expired row) deleted exactly that one row and left the non-expired row untouched.
  - **Production scheduling: live (Option A), not manual.** `scripts/run_retention_cleanup.py --dry-run` supports a safe count-only preview; the real run is invoked automatically by a DigitalOcean App Platform `SCHEDULED` job (`retention-cleanup`, `cron: "30 3 * * *"`, i.e. 03:30 UTC daily — no separate Celery worker, per the explicit no-new-worker instruction; see `DECISIONS.md` "[OPS] Retention scheduling uses a DO App Platform `SCHEDULED` job, not Celery"). **First real execution confirmed:** 2026-07-15, 03:31:29–03:31:31 UTC, clean `COMMIT`, 0 rows deleted across all four tables (expected — private-beta dataset has little aged data yet), no errors. **Second consecutive successful run confirmed:** 2026-07-16, invocation `ad207ee4-f05c-4038-b244-6e54bf9fd13a`, created 03:31:12 UTC, started 03:31:30 UTC, completed 03:31:33 UTC, phase `SUCCEEDED`. Monitoring: `doctl apps list-job-invocations <app-id> --job-name retention-cleanup --format ID,Jobname,Created,Started,Completed,Phase`, then `doctl apps logs <app-id> retention-cleanup --job-invocation <id> --type run` (see `docs/operations/WORKERS.md`).
- **Real finding from Postgres testing, not present in the original implementation write-up:** migration `0023`'s backfill for *pre-existing* rows computes `expires_at = migration-run-time + 30 days`, not `original created_at + 30 days`. Verified directly: two test rows with `created_at` 40 and 70 days in the past both received the identical `expires_at` (migration-run-time + 30 days) after upgrading — confirmed by inspecting the actual timestamps in a real Postgres database, not by re-reading the migration source. Practical effect: any snapshot that already existed when this migration runs in production gets a *fresh* 30-day window starting from the deploy date, not its true age. This is not a data-loss or correctness bug (nothing breaks, nothing is deleted early) — it means pre-existing data is retained *somewhat longer* than the nominal 30-day-from-creation policy implies, one time, at migration deploy. Every row created after the migration gets an accurate `created_at`-relative 30-day window via the ORM's `default=_default_expiry` callable. Not fixed in this branch (fixing it would mean computing per-row `created_at + N days` in the migration's `UPDATE` statement instead of a single constant — a reasonable follow-up, not a merge blocker, since it only ever makes retention *more* conservative, never less).
- **Effect on Magic Revert:** reverting an apply job after its backup snapshot has expired now returns a clear 410-style error ("backup snapshot no longer available — revert window has closed") instead of a silent failure. This is a genuine product tradeoff (permanent revert vs. bounded retention) — documented here rather than hidden.

## 3. Token retention — deleted on disconnect

- **Before this branch:** `disconnect_shop()` only set `is_connected = False`; `EtsyToken` row (encrypted access + refresh token) remained in the database indefinitely.
- **This branch:** `disconnect_shop()` now deletes the `EtsyToken` row for the shop, and pauses (`status = "paused"`) any `ScheduledJob` rows referencing that shop. This makes the Privacy Policy's existing claim ("disconnecting revokes our stored tokens immediately") **true** rather than aspirational.
- Etsy itself does not expose a documented v3 token-revocation endpoint for third-party apps to call (per current public docs); "revoke" here means deleting our locally stored copy so it can no longer be used, which is the correct and complete action available to us.

## 4. Account deletion

- **Before this branch:** no account-deletion endpoint existed anywhere in the API surface (confirmed by repo-wide grep).
- **This branch adds:** `DELETE /api/v1/auth/me` (self-service, requires re-authentication via password confirmation in the request body) — deletes the requesting user's `User` row and, if they are the sole owner of an `Organization`, cascades to delete every org-scoped table.

### §4a. Two real bugs found via real-Postgres testing during owner-review validation, both fixed and re-verified

Unit tests against SQLite (which does not enforce `ON DELETE CASCADE` by default, and where the missing-FK bug below is invisible) reported this endpoint as working. It was not. Running it against a real local PostgreSQL database — actual `docker compose` Postgres, real migrations, a registered user with a connected Etsy shop and an active refresh token — surfaced two distinct bugs:

**Bug 1 — deletion crashed with HTTP 500 whenever the user had any active refresh token or org membership loaded.** Root cause: `Organization.members`, `User.memberships`, and `User.refresh_tokens` were declared as plain SQLAlchemy `relationship()`s with no `cascade` and no `passive_deletes` setting. SQLAlchemy's default behavior on `session.delete(parent)` is to try to *disassociate* any loaded children by setting their foreign key to `NULL` — even though the DB-level FK is `ondelete="CASCADE"` and the column is `NOT NULL`, so the attempt itself violates a NOT NULL constraint and crashes. Real error, reproduced exactly: `IntegrityError: null value in column "organization_id" of relation "organization_members" violates not-null constraint`, then (after fixing that) the identical pattern on `refresh_tokens.user_id`. **Fixed** by adding `passive_deletes=True` to all three relationships (`app/models/organization.py`, `app/models/user.py`) — this tells SQLAlchemy to step back and let PostgreSQL's own `ON DELETE CASCADE` do the work, which is what the code's own comments already (incorrectly) assumed was happening.

**Bug 2 — nine tables' `organization_id` column had no foreign key at all, at the database level, at any point before this pass:** `etsy_shops`, `listings`, `cost_profiles`, `listing_costs`, `social_connections`, `social_oauth_states`, `etsy_oauth_states`, `sync_jobs`, `video_renders`. These were plain `String(36)` columns with no `ForeignKey(...)` declaration in the ORM and no constraint in the actual database schema — meaning deleting an Organization could never cascade to them by any mechanism, ORM or DB. This is not new to this branch; it predates it (`etsy_shops` traces back to Sprint 4/migration 0003). This compliance branch's own account-deletion feature was the first thing in the app's history to actually depend on this cascade working, which is how it surfaced. Practical effect: before this fix, "deleting" an account left the seller's connected Etsy shop, encrypted tokens, synced listing content, and social connections permanently orphaned in the database — the exact opposite of what `ETSY_APPEAL_CHECKLIST.md` was about to tell Etsy this feature does. **Fixed**: added `ForeignKey("organizations.id", ondelete="CASCADE")` to all 9 columns (in each model file) plus new migration `0025_add_missing_org_fk_constraints.py`.

**Verification, not assertion — full method:**
1. Started local Docker Postgres, created an isolated `test_deletion` database, ran `alembic upgrade head` for real.
2. Registered a real user through the live API, inserted a connected `EtsyShop` + `EtsyToken` + `Listing` directly, called `DELETE /api/v1/auth/me` through the live API → got the actual 500, captured the actual traceback.
3. Fixed Bug 1, restarted the container, retried → got a *different* 500 (the `refresh_tokens` variant of the same bug) → confirmed the fix needed to cover both `User` relationships, not just `Organization`'s.
4. Fixed both `User` relationships, retried → 200, but found the orphaned `etsy_shops`/`etsy_tokens`/`listings` rows still present → this led directly to finding Bug 2.
5. Wrote migration `0025`. **First attempt to apply it against the still-orphaned `test_deletion` database correctly failed** with a foreign key violation naming the exact orphaned row — proving the migration's safety behavior (it refuses to silently succeed on bad data) before ever proving its happy path.
6. Cleaned up the orphan, re-applied `0025` successfully, then ran a **complete fresh end-to-end test** on a brand-new database: registered a user, inserted rows into all 9 previously-unprotected tables plus a backup snapshot, logged in again (to create a second refresh token, reproducing Bug 1's exact trigger condition), called `DELETE /api/v1/auth/me` → **200**, then queried every one of the 9 tables plus `organizations`/`organization_members`/`users`/`refresh_tokens` directly in Postgres → **zero rows remained anywhere, zero orphans**.
7. Added 3 regression tests to `tests/test_auth.py` (`test_delete_account_wrong_password_rejected`, `test_delete_account_succeeds_with_active_refresh_token_and_membership`, `test_delete_account_cascades_etsy_shop_and_listing`) reproducing the exact trigger conditions — the second test alone would have caught Bug 1 (an active refresh token present at delete time); the third documents, honestly, that SQLite cannot verify Bug 2's fix (no `PRAGMA foreign_keys=ON` anywhere in this suite, confirmed by grep) and that this class of bug requires Postgres to catch, which is exactly why it existed undetected until now.

### §4b. Stripe subscription safety gate (owner decision received and implemented, 2026-07-13 third session)

**This is a product safety rule this project chose, not an Etsy requirement or a Stripe requirement.** The owner explicitly decided: do NOT auto-cancel a Stripe subscription as part of account deletion. Instead, block deletion outright while a subscription is still active or billable, so a user is never left with an unresolved, un-cancelable subscription.

**What this project does NOT claim:**
- It does not claim Stripe customer or subscription records are deleted by this app — they are not, ever. They remain in Stripe, governed entirely by Stripe's own data retention and compliance behavior, independent of this application.
- It does not claim subscription cancellation is automatic — it is never triggered by this app. The seller must cancel through the Stripe customer portal (linked from the app) before account deletion becomes available.
- It does not claim `cancel_at_period_end=true` means the subscription has ended — Stripe keeps billing and providing access until `current_period_end` actually passes, so deletion stays blocked until then.

**What this project's local database does:** deletes the local `Subscription` row (and every other local, org-scoped row) only once the billing state is confirmed safe — never before.

**Implementation:** `app/services/billing.py::assert_account_deletion_billing_safe(org_id, db)` — called from `delete_account()` before any row is touched, using only the local `Subscription` row (kept current by verified Stripe webhooks — see §1 above and `process_webhook_event`), never a live Stripe API call.

Explicitly safe (deletion allowed) — only these three shapes, nothing inferred:
1. No `Subscription` row exists for the organization at all.
2. `plan == "free"` and `stripe_subscription_id` is empty.
3. `status == "canceled"` and `current_period_end` is absent or already in the past (Stripe only sends `customer.subscription.deleted`, which sets `status="canceled"`, once a subscription has actually ended — not when cancellation is merely scheduled — so this reflects a true end-of-billing signal; the `current_period_end` check is an additional guard against stale local data).

Everything else blocks by default (fail closed) — explicitly including `active`, `trialing`, `past_due`, `unpaid`, `incomplete`, `incomplete_expired`, `active` with `cancel_at_period_end=true` (still active until the period ends), and any Stripe status string this function doesn't recognize. `HTTP 409`, code `ACTIVE_SUBSCRIPTION_MUST_BE_CANCELED`. A separate edge case — a billable-looking subscription state with no `stripe_customer_id` on file (so there's no portal to send the user to) — returns a distinct code, `BILLING_PORTAL_UNAVAILABLE`, and the frontend shows a contact-support message instead of a cancel-your-subscription message. Neither response includes a Stripe customer ID, subscription ID, or any other internal billing metadata.

**Frontend:** `/billing` page (`apps/frontend/app/(app)/billing/page.tsx`) — a "Danger zone" section with password-confirmed deletion. On a blocked response, shows the exact required message and a "Manage Subscription" button that routes through the existing `POST /api/v1/billing/portal` endpoint (never an invented Stripe URL).

**Verified against real Postgres, not just SQLite:** registered a user, inserted an `active` Stripe-managed subscription directly, called `DELETE /api/v1/auth/me` through a live backend → `409`, confirmed user/org/subscription rows all unchanged afterward. Then updated the same subscription to `canceled` with a past `current_period_end`, added a connected Etsy shop, retried → `200`, confirmed zero rows remain in `users`/`organizations`/`subscriptions`/`etsy_shops`/`organization_members`. 14 new backend tests (11 owner-specified scenarios table-driven in one test, plus 3 supporting tests for the portal-unavailable edge case, untouched-data-on-block, and the safe-cascade-still-works case).

**Migration status:** no new migration was required — `Subscription` already had every column this check needs (`plan`, `status`, `stripe_customer_id`, `stripe_subscription_id`, `current_period_end`, `cancel_at_period_end`). Migration head remains `0025`, unchanged by this feature.

## 5. What is never retained

- Etsy passwords: never seen, never stored (OAuth-only, confirmed in `etsy.py` — no password field anywhere near Etsy code).
- Plaintext Etsy tokens: never stored; always Fernet-encrypted via `app/core/encryption.py` before persisting.
- Etsy tokens or listing content in logs: no `logger.*`/`print` call anywhere in `etsy.py`, `etsy_sync.py`, `etsy_write.py`, `etsy_media_write.py`, `etsy_variation_write.py` references a token or full listing body (verified by grep — the only logging in these files is generic exception-type logging, e.g. `logger.warning("Etsy sync failed: %s", type(exc).__name__)` style, no payload interpolation).
- Buyer/transaction/financial data beyond what bulk-edit needs: none requested (scopes exclude `transaction_r`; see `ETSY_OAUTH_SCOPES.md`).

## 6. Privacy Policy update required

`apps/frontend/app/privacy/page.tsx` §10 ("Data retention") is updated in this branch to state the exact retention periods above (30-day snapshot cap, immediate token deletion on disconnect, account-deletion self-service) instead of the previous vague "as needed" language.
