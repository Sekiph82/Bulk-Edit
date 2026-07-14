# ETSY_PRODUCTION_READINESS.md

Full production workflow audit, items 1-30 as specified. Status legend: **OK** working as-is · **FIXED** corrected in this branch · **BLOCKED** blocked by the suspended Etsy key, mock/unit-tested only · **MANUAL** requires a manual verification pass the owner must run (cannot be safely automated in this session).

1. **Homepage and public pages** — FIXED. Removed founding-access/pre-launch framing (see §"Website corrections" below); rest of the marketing site (features, pricing, FAQ, contact, blog, compare, tools) renders and builds cleanly.
2. **Registration** — FIXED. Added required Terms/Privacy checkbox, enforced both sides.
3. **Terms and Privacy acceptance** — FIXED. See §2 detail below.
4. **Login and logout** — OK. JWT access+refresh, rotation on refresh, revoke-on-logout via DB row. No change needed.
5. **Password reset** — OK. `forgot-password`/`reset-password` flow exists, rate-limited (`RATE_LIMIT_FORGOT_PASSWORD_PER_HOUR`).
6. **Email delivery and verification** — MANUAL. Resend domain verification was an open blocker as of the last session's `HANDOFF.md` (waiting on DNS records from the owner) — this is an infra/DNS action outside this branch's scope; contact-form submissions persist to DB regardless (`contact_submissions` table) so inquiries aren't lost while email is unverified. No email-verification-on-signup step exists — accounts are usable immediately after registration (documented gap, not fixed here — would require a product decision on blocking dashboard access pending verification, out of scope for a compliance-focused branch).
7. **Stripe checkout and subscription management** — OK, previously validated live per `HANDOFF.md` 2026-07-10 entry (live checkout session, zero charges).
8. **Etsy OAuth initiation** — OK code-side; BLOCKED end-to-end by the ban.
9. **OAuth callback** — OK code-side (PKCE, state validation); BLOCKED end-to-end by the ban.
10. **Secure token storage and refresh** — FIXED (scopes bug, now covered by `test_callback_stores_real_granted_scope_not_token_type`) + OK (encryption) + FIXED (auto-refresh on near-expiry, revoked-refresh now surfaces a clean 401 via the existing `SyncError` type instead of an opaque 500 — both paths covered by `test_sync_auto_refreshes_near_expiry_token` / `test_sync_marks_shop_disconnected_on_revoked_refresh` in `tests/test_etsy.py`, added during verification after the initial pass shipped the behavior without regression tests).
11. **Shop synchronization** — OK.
12. **Listing synchronization** — OK.
13. **Listing freshness detection** — FIXED. `last_synced_at` staleness banner added ahead of bulk-edit preview/apply.
14. **Listing selection** — OK (listings grid, filters, multi-select).
15. **Bulk-edit creation** — OK.
16. **Validation** — OK (field-type registry rejects invalid field/operation combos before persisting).
17. **Exact before-and-after preview** — OK (`BulkEditPreviewItem.diff`, before/after data rendered in UI).
18. **Explicit final confirmation** — OK (typed "APPLY"-style confirmation modals across bulk-edit/media/variation/revert flows).
19. **Etsy update submission** — OK code-side; BLOCKED for a real live-shop test.
20. **Partial-failure handling** — OK (`BulkEditApplyResult` per-listing status; `completed_with_errors` state).
21. **Per-listing results** — OK.
22. **Backup snapshot creation** — OK, retention FIXED (30-day cap added).
23. **Revert** — OK, now correctly surfaces "snapshot expired" once retention window passes (see `ETSY_DATA_RETENTION.md`).
24. **Scheduled seller-authorized changes** — OK (never auto-writes to Etsy; drafts only). FIXED: paused automatically on shop disconnect.
25. **Etsy shop disconnect** — FIXED. Now deletes tokens, pauses scheduled jobs referencing the shop.
26. **Token removal** — FIXED (see 25).
27. **Account deletion** — **FIXED, both parts.** (a) DB cascade correctness — verified against real Postgres, not just SQLite. Owner-review validation found the cascade was actually broken two different ways (crashed with a 500 whenever an active refresh token/org membership was present; 9 org-scoped tables including `etsy_shops` and `listings` had no foreign key at all, so "deletion" silently left Etsy-derived data orphaned forever). Both root-caused, fixed (`passive_deletes=True` on 3 relationships; migration `0025` adding the 9 missing FKs), and re-verified end-to-end against a live backend hitting real Postgres. Full detail in `ETSY_DATA_RETENTION.md` §4a. (b) Stripe — **owner decision received and implemented this session: block, don't auto-cancel.** `DELETE /api/v1/auth/me` now runs `assert_account_deletion_billing_safe()` (`app/services/billing.py`) before touching any row. Deletion is allowed only when: no `Subscription` row exists, the org is on the free plan with no `stripe_subscription_id`, or the subscription is `canceled` with its billing period actually over (checked via `current_period_end`, not just the status string — a `cancel_at_period_end=true` subscription that hasn't actually ended yet is still blocked, per the owner's explicit instruction). Every other state — `active`, `trialing`, `past_due`, `unpaid`, `incomplete`, `incomplete_expired`, and any Stripe status this function doesn't explicitly recognize — is blocked by default (fail closed), returning `409` with a stable code (`ACTIVE_SUBSCRIPTION_MUST_BE_CANCELED`, or `BILLING_PORTAL_UNAVAILABLE` for the edge case of a billable-looking subscription with no `stripe_customer_id` on file). No Stripe IDs or internal billing metadata appear in the response. No live Stripe API call is made by this check — it reads only the local `Subscription` row, kept current by verified webhooks. 14 new tests (11 owner-specified scenarios + 3 supporting), plus 2 real-Postgres end-to-end scenarios (blocked with an active subscription, confirmed data untouched; allowed once safely ended, confirmed zero orphans) — see `ETSY_DATA_RETENTION.md` §4b.
28. **Support contact** — OK. `support@bulkeditapp.com` present in footer, Terms, Privacy, contact page; contact form persists to DB (`contact_submissions`) independent of email delivery. MANUAL: actually sending a test message through the live form and confirming inbox delivery needs the owner (requires live SMTP verification, item 6).
29. **Mobile and desktop usability** — MANUAL. Prior sprints (Productization UI, Theme System) addressed this generally, but no fresh device-matrix pass was run in this session — out of scope for a compliance audit; flagged, not re-verified.
30. **Production error handling** — OK. Security headers, rate limiting, Sentry scrubbing, structured error responses all present from prior sprints; not modified here.

---

## §2 — Terms/Privacy acceptance detail

**Before this branch:** `apps/frontend/app/register/page.tsx` had no checkbox; backend `POST /api/v1/auth/register` accepted registration with no acceptance record of any kind.

**This branch adds:**

- Frontend: unchecked, required checkbox — *"I agree to the Terms of Service and acknowledge the Privacy Policy."* — linking to `/terms` and `/privacy`. Submit button stays enabled but the backend rejects the request if unchecked (frontend also blocks submission client-side as a UX nicety, matching the "enforce in both frontend and backend" instruction).
- Backend: `RegisterRequest` schema requires `terms_accepted: bool = True` (Pydantic literal-true style validation — `False` or missing is a 422). On success, writes to a new `terms_acceptances` table: `user_id`, `terms_accepted_at`, `terms_version`, `privacy_version`, `acceptance_source` (`"web_registration"`).
- Migration: `0024_create_terms_acceptances.py`.
- Tests: `test_auth.py` gains `test_register_fails_without_terms_acceptance`, `test_register_fails_with_terms_false`, `test_register_succeeds_and_records_acceptance`.
- `TERMS_VERSION` / `PRIVACY_VERSION` are config-driven constants (`app/core/config.py`) bumped whenever the Terms/Privacy page content materially changes, so historical acceptances stay attributable to the version the user actually saw.

---

## §3 — Etsy API Terms developer warranty disclaimer

Added to `apps/frontend/app/terms/page.tsx` as new §15, "Etsy API developer disclaimer," stating, in substance: Bulk Edit App represents that its use of the Etsy Open API v3 complies with Etsy's API Terms of Use as in effect at the time of use, that it will promptly remove or correct any feature found to violate those terms upon notice from Etsy, and that Etsy makes no warranty of any kind regarding the Etsy API or Bulk Edit App's use of it, and is not a party to the agreement between the seller and Bulk Edit App. This is **not** a substitute for Etsy's own required legal template if Etsy provides one in an appeal response — flagged for the owner to compare against Etsy's actual required wording once/if Etsy responds (see `ETSY_APPEAL_CHECKLIST.md`).

---

## §4 — Legal entity configuration

`apps/backend/app/core/config.py` gains: `LEGAL_ENTITY_NAME`, `LEGAL_ENTITY_ADDRESS`, `LEGAL_ENTITY_COUNTRY`, `LEGAL_CONTACT_EMAIL` (all optional strings, no invented defaults). Frontend footer copyright line now reads `© 2026 {LEGAL_ENTITY_NAME or "Bulk Edit App"}` — since no explicit owner confirmation of "Bulk Edit App LLC" registration exists anywhere in `DECISIONS.md` or config, the safe default per this task's own instruction ("Do not invent missing values... Otherwise use © 2026 Bulk Edit App") is applied: **the footer now shows "© 2026 Bulk Edit App" unless `LEGAL_ENTITY_NAME` is explicitly set in the environment.** If "Bulk Edit App LLC" is in fact a real registered entity, set `LEGAL_ENTITY_NAME=Bulk Edit App LLC` in production env and it will display exactly as before — no functionality is lost, only the unconfirmed default is removed.
