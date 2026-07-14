# ETSY_FINAL_APPEAL_DRAFT.md

**STATUS: NOT SUBMITTED.** This is a draft prepared for owner review only. Per explicit instruction, nothing in this file is to be sent to Etsy without the owner's separate, explicit approval. See `ETSY_APPEAL_CHECKLIST.md` for pre-submission steps (verbatim trademark-wording re-check, confirming which inbox a ban reason might have gone to, etc.) that should happen *before* sending this.

Prepared: 2026-07-14, sixth session. Sources: `ETSY_APPEAL_CHECKLIST.md`, `ETSY_SUPPORT_QUESTIONS.md`, `ETSY_COMPLIANCE_AUDIT.md` (especially §6b's citation table), `ETSY_FEATURE_MATRIX.md`, and the current live production state (all compliance fixes from PR #56 are live as of 2026-07-14, merge commit `435a1aa`).

---

## A. Short appeal message (for email / appeal form)

> Subject: Appeal request — app "bulk-edit-app" (client_id `7usvn9q6itlj6306sef64god`), status "Banned"
>
> Hello,
>
> Our application, Bulk Edit App (bulkeditapp.com), was marked "Banned" and we have not received an email or in-console explanation of the specific reason. We would like to understand what triggered this so we can confirm it is fully resolved, and to be transparent about our own process: during our internal review, we identified several areas where our implementation and public documentation could be made clearer and more conservative, and we have already corrected them in production, in case any of them contributed.
>
> Specifically, we found and fixed a bug where our OAuth token storage recorded the token type instead of the granted scope string in one internal display field (this did not affect what scopes were actually granted by Etsy or used by the app). We found that disconnecting a shop was not immediately deleting the shop's stored access and refresh tokens the way our own Privacy Policy said it would, and fixed that so disconnection now deletes tokens immediately and pauses any scheduled jobs tied to that shop. We reviewed our handling of Etsy-derived content and set a conservative 30-day maximum retention window (configurable, not hardcoded) on backup snapshots and CSV export jobs, with an automated daily cleanup job now running in production. We also reviewed every feature in the app to confirm it uses only the documented Etsy Open API v3 endpoints — no scraping, no legacy or undocumented endpoints, and no browser automation against etsy.com anywhere in our codebase.
>
> One area we specifically want your guidance on: the app includes an optional feature that can send a seller's own synced listing content (title, description, tags) to a third-party AI provider to generate suggested edits, which the seller must manually review and approve before anything is written back to Etsy — nothing is ever auto-applied. We have disabled this specific Etsy-data-to-AI pathway by default in production (it requires an explicit server-side flag to be turned on, which it currently is not) until we have your written confirmation that it's permitted, and if so, under what conditions.
>
> Our production site is live at bulkeditapp.com, the application itself is at app.bulkeditapp.com, and our OAuth callback is at api.bulkeditapp.com/api/v1/etsy/callback. We currently request only the `listings_r`, `listings_w`, `shops_r`, and `profile_r` scopes. Account creation is currently gated behind a private-beta waitlist while we await your response, so no new sellers are being onboarded in the meantime.
>
> Could you tell us the specific reason our app was banned, so we can confirm it's addressed? We're glad to answer any follow-up questions or provide further detail on any part of our implementation.
>
> Thank you for your time.
>
> — [Owner name], Bulk Edit App

*(Word count: ~380, within the requested 300–500 range.)*

---

## B. Detailed technical appendix

**Architecture:** Next.js 14 (App Router) frontend, FastAPI (Python 3.12) backend, PostgreSQL 16, Redis 7, deployed on DigitalOcean App Platform. All Etsy communication goes through a single backend service (`bulk-edit-prod-api`) using `httpx` against `https://openapi.etsy.com/v3` — no direct frontend-to-Etsy calls, no other network path to Etsy anywhere in the codebase.

**OAuth implementation:** Authorization Code grant with mandatory PKCE (S256), a single-use `state` parameter with expiry, and the app's `x-api-key` header sent alongside the Bearer token on every request, per Etsy's documented Authentication flow. Access and refresh tokens are encrypted at rest (Fernet/AES) before being written to the database — plaintext tokens are never persisted.

**Data freshness and caching:** Synced listing content is treated as stale after 6 hours; other Etsy content (shop info, etc.) after 24 hours. Stale data triggers a re-sync or a freshness warning to the seller before it's relied on for a new write, rather than being silently reused.

**Rate limiting and retries:** Outbound Etsy `GET` requests go through a shared retry/backoff wrapper (`app/services/etsy_http.py`) that respects `429`/`5xx` responses and any `Retry-After` header, with exponential backoff, honoring the documented 10 QPS / 10,000 QPD limits.

**Write safety pipeline:** Every write to Etsy follows the same sequence, with no exceptions in the codebase: seller connects their shop → app generates a preview of the exact before/after change → seller explicitly confirms → a backup snapshot of the pre-write state is taken → the write executes → the action is recorded to an audit log. No code path in this application writes to Etsy without a preceding seller confirmation.

**Foreign-key / data-lifecycle integrity:** During this review we also found and fixed a data-lifecycle bug unrelated to any Etsy policy but relevant to describing our data-deletion behavior accurately: 9 internal tables (shop/listing/token/sync-related) were missing database-level foreign-key constraints on their organization reference, meaning a full account deletion could not previously guarantee those rows were removed. This is now fixed (`ON DELETE CASCADE` constraints added, migration verified against production with zero orphaned rows before and after).

**AI safeguard:** `ALLOW_ETSY_DATA_TO_AI` is a server-side configuration flag, default `false`, enforced in the AI service layer itself (not just the UI) — even if a request reaches the AI-suggestion endpoint, Etsy-derived content is not sent to any AI provider unless this flag is explicitly set to `true`. It is not set in the production environment today. Separately, the AI provider itself is currently configured as `mock` in production, meaning no live call to any external AI provider (OpenAI, Anthropic, or otherwise) is possible right now regardless of the flag.

**No scraping / no unofficial access:** Confirmed by direct code review — every Etsy interaction in the codebase goes through the documented Open API v3 REST surface via the single `httpx`-based client. No headless browser, no HTML parsing of etsy.com, no undocumented endpoints.

---

## C. Updated application description (for the Etsy developer console)

> Bulk Edit App is a seller-authorized listing management utility for Etsy sellers. Using Etsy's official Open API v3 and OAuth2 (PKCE), it lets a seller connect their own shop, synchronize their own listings, prepare bulk changes to titles, descriptions, tags, prices, quantities, variations, photos, and videos, review an exact before-and-after preview of every change, and explicitly confirm before anything is submitted to Etsy. Every write is preceded by a backup snapshot so changes can be reverted. The app also offers CSV import/export and scheduled seller-authorized updates (which only ever create drafts requiring separate manual confirmation — nothing is auto-applied). An optional AI-assisted listing-suggestion feature exists but is currently disabled from accessing any Etsy-derived data pending Etsy's guidance. The app does not process orders, payments, or buyer data, and requests only `listings_r`, `listings_w`, `shops_r`, and `profile_r` scopes.

---

## D. Current production URLs

- Marketing site: `https://bulkeditapp.com` (and `https://www.bulkeditapp.com`)
- Application: `https://app.bulkeditapp.com` (currently gated behind a private-beta notice for new sign-ups — see section K)
- API: `https://api.bulkeditapp.com`
- OAuth callback: `https://api.bulkeditapp.com/api/v1/etsy/callback`

---

## E. Exact OAuth scopes requested

```
listings_r
listings_w
shops_r
profile_r
```

No transaction, buyer-email, financial, or billing scopes are requested anywhere in the codebase.

---

## F. User authorization explanation

A seller initiates the connection from within their own account in the app. The app redirects to Etsy's own OAuth authorization page, where the seller logs in directly with Etsy (this app never sees or stores an Etsy password) and explicitly grants the requested scopes on Etsy's own consent screen. Only after that seller-driven grant does the app receive an authorization code, which it exchanges (server-side, with PKCE) for an access/refresh token pair scoped to that seller's own shop. There is no mechanism in the app for connecting or acting on a shop the authenticated user does not themselves own.

---

## G. Preview and explicit confirmation before writes

No write reaches Etsy without: (1) the seller building or selecting a set of intended changes in the app, (2) the app rendering an exact field-by-field before/after preview of what will change, (3) the seller clicking an explicit confirm action, (4) a backup snapshot of the current state being taken, and only then (5) the write being sent to Etsy. This sequence is enforced in the backend service layer, not just the UI, so there is no code path that can skip the preview/confirmation step.

---

## H. Data-retention explanation

Backup snapshots (pre-write state, for revert) and CSV import/export job records are retained for a maximum of 30 days from creation, after which an automated daily job deletes them. This 30-day figure is this project's own conservative, configurable default (`ETSY_DERIVED_DATA_RETENTION_DAYS`, adjustable without a code change) — we are not asserting that Etsy requires exactly 30 days; Etsy's own API Terms state that accessed content should not be cached or stored longer than reasonably necessary to serve the app's users, without specifying a number, and 30 days is our own conservative interpretation of that principle pending any more specific guidance. Live, current listing data itself is not subject to this 30-day cap — it is kept in sync with Etsy on an ongoing basis (treated as stale after 6 hours) for as long as the seller keeps the shop connected.

---

## I. Disconnect / token-deletion behavior

When a seller disconnects their Etsy shop from within the app, the app immediately deletes the shop's stored access and refresh tokens from the database (not merely marking them inactive), and pauses any scheduled jobs tied to that shop. This was verified via live code review and testing this session; it was previously a discrepancy between the stated Privacy Policy behavior and the actual implementation, and is now corrected and matches what the Privacy Policy states.

---

## J. AI safeguard explanation

The app has an optional AI-assisted listing-suggestion feature. Sending any Etsy-derived listing content (title, description, tags) to a third-party AI provider (OpenAI or Anthropic) for this feature is gated behind a server-side configuration flag, `ALLOW_ETSY_DATA_TO_AI`, defaulting to `false` and enforced at the service layer — not merely hidden in the UI. This flag is not enabled in the production environment as of this appeal. We are not claiming Etsy has explicitly prohibited this kind of AI use; we found no official Etsy documentation addressing it in either direction, and we chose to disable the pathway by default as our own conservative precaution until we have Etsy's explicit written guidance either way (see the question raised in section A / the appeal message).

---

## K. Trademark and independence statement

"Etsy" is a trademark of Etsy, Inc. Bulk Edit App uses Etsy's official API but is not endorsed, sponsored, or certified by Etsy, Inc. This disclosure is displayed on the app's Terms of Service and Privacy Policy pages, and near the shop-connection flow. Bulk Edit App's own branding is presented independently and is not styled to imply any Etsy affiliation.

---

## L. Testing and production-readiness summary

- Backend test suite: 982 tests passing (SQLite for unit-level logic; separately verified against real PostgreSQL for anything touching cascading deletes, foreign-key constraints, or webhook-driven billing state, since SQLite's lax constraint enforcement previously masked two real bugs that were found and fixed this review cycle).
- Frontend: TypeScript compiles clean, lint clean (only pre-existing, non-blocking warnings), production build clean.
- All changes described in this document are live in production as of 2026-07-14 (merge commit `435a1aa`), verified directly against the live site and live API — not merely committed to source control.
- Account registration currently requires explicit acceptance of the Terms of Service and Privacy Policy (enforced server-side, not just in the UI).
- New account sign-ups are currently paused behind a private-beta notice while this appeal is pending, so the live seller-facing surface is not actively growing during Etsy's review.
- We have not tested the Etsy listing-video-upload endpoint live, since doing so requires an active (non-banned) connection — implemented per the documented endpoint shape, pending live verification once access is restored.
- We have not claimed Etsy has approved, endorsed, or confirmed any specific part of this implementation; every claim above about Etsy's own requirements is limited to what is stated in Etsy's own publicly available documentation (see `ETSY_COMPLIANCE_AUDIT.md` §6b for the full source-by-source citation table used to write this document).
