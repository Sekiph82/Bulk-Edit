# ETSY_FINAL_APPEAL_DRAFT.md

# Submission status

**Submitted by owner, on/around 2026-07-16.** Exact submission timestamp and case/ticket number not yet recorded in this repo — record them here (or in `PROJECT_STATUS.md`/`ETSY_APPEAL_CHECKLIST.md`) as soon as available.

**Do not submit another appeal or contact Etsy again** unless Etsy explicitly asks for more information or the owner explicitly decides to. The body below (sections A–G) is kept as the submitted copy, unmodified, for reference — see `ETSY_APPEAL_CHECKLIST.md` for the post-submission checklist (what to do while awaiting Etsy's response).

---

Prepared: 2026-07-14, seventh session (final review pass). Sources: `ETSY_APPEAL_CHECKLIST.md`, `ETSY_SUPPORT_QUESTIONS.md`, `ETSY_COMPLIANCE_AUDIT.md` (especially §6b's citation table), `ETSY_FEATURE_MATRIX.md`, `ETSY_PRODUCTION_READINESS.md`, `ETSY_DATA_RETENTION.md`, the current live production state (verified this session: backend/frontend healthy, migration `0025`, Private Beta enabled, retention-cleanup `SCHEDULED` job configured), and the current live public website.

---

## A. Short appeal message (for email / appeal form)

> Subject: Appeal request — app "bulk-edit-app" (client_id `7usvn9q6itlj6306sef64god`), status "Banned"
>
> Hello,
>
> Our application, Bulk Edit App (bulkeditapp.com), was marked "Banned," and we have not received an email or in-console explanation of the reason. We would like to understand what triggered this so we can confirm it is resolved. In the meantime, during an internal review, we identified several areas where our implementation and public documentation could be made clearer and more conservative, and we have implemented and deployed those changes.
>
> Specifically: we corrected an internal bug where OAuth token storage recorded the token type instead of the granted scope string in one display field (this did not affect what Etsy actually granted or what the app used). We fixed shop disconnection so it now immediately deletes the shop's stored access and refresh tokens and pauses any scheduled jobs tied to that shop, matching our Privacy Policy. We set a conservative, configurable 30-day maximum retention window on backup snapshots and CSV export records, enforced by an automated daily cleanup job now running in production. We reviewed every feature to confirm the app uses only the documented Etsy Open API v3 endpoints, with no scraping and no undocumented access anywhere in our codebase. We also removed public marketing language that described the product as pre-launch while it was actually live, and removed public marketing pages for two features (AI-assisted suggestions and a local listing-health score) pending the clarification below — both remain available in-app to sellers, but we are not marketing them publicly until we understand your position.
>
> One area we would specifically like your guidance on: the app includes an optional feature that can send a seller's own synced listing content to a third-party AI provider to generate suggested edits, which the seller must review and approve before anything reaches Etsy — nothing is auto-applied. We have disabled this Etsy-data pathway by default in production pending your written confirmation that it's permitted, and under what conditions.
>
> Our production site is live at bulkeditapp.com, the application at app.bulkeditapp.com, and our callback at api.bulkeditapp.com/api/v1/etsy/callback, requesting only `listings_r`, `listings_w`, `shops_r`, and `profile_r`. New account creation is currently paused behind a private-beta gate while we await your response, and our backend and frontend are healthy and operating normally. We have not been able to test live Etsy OAuth or any live write since the ban took effect, so several of the changes above are verified in our own code and database, not yet against a live Etsy connection.
>
> Could you tell us the specific reason our app was banned, so we can confirm it's addressed? We respectfully request reconsideration and would appreciate any clarification you can offer.
>
> Thank you for your time.
>
> — [Owner name], Bulk Edit App

*(Word count: ~430, within the requested 300–500 range.)*

---

## B. Detailed technical appendix

**1. Application purpose.** Bulk Edit App is a seller-authorized listing management utility for Etsy sellers: bulk editing of titles, descriptions, tags, prices, quantities, variations, photos, and videos, with CSV import/export, scheduled updates, and cost/profit tooling. It does not process orders, payments, or buyer data.

**2. Production URLs.** Marketing site `https://bulkeditapp.com` (and `www.bulkeditapp.com`); application `https://app.bulkeditapp.com`; API `https://api.bulkeditapp.com`; OAuth callback `https://api.bulkeditapp.com/api/v1/etsy/callback`.

**3. OAuth flow.** Authorization Code grant with mandatory PKCE (S256), a single-use `state` parameter with expiry, and the app's `x-api-key` header sent alongside the Bearer token on every request, per Etsy's documented Authentication flow.

**4. Requested scopes and justification.** `listings_r`, `listings_w` (read and write the seller's own listings — the core bulk-edit function), `shops_r` (read the seller's own shop metadata), `profile_r` (read the seller's own profile for account display). No transaction, buyer-email, financial, or billing scopes are requested anywhere in the codebase.

**5. Seller authorization.** A seller initiates the connection from their own account. The app redirects to Etsy's own OAuth page, where the seller logs in directly with Etsy (this app never sees or stores an Etsy password) and grants the requested scopes on Etsy's own consent screen. There is no mechanism for connecting or acting on a shop the authenticated user does not themselves own.

**6. Listing synchronization.** Listing content is synced from Etsy and treated as stale after 6 hours; other shop content after 24 hours. Stale data triggers a re-sync or a freshness warning before it is relied on for a new write, rather than being silently reused.

**7. Bulk-edit workflow.** A seller selects listings and builds a set of intended changes (field edits, tag operations, price/quantity rules, variation changes, media updates) either through the UI or a CSV import.

**8. Preview and explicit confirmation.** Before anything reaches Etsy, the app renders an exact field-by-field before/after preview of every change. The seller must explicitly confirm. This is enforced in the backend service layer, not just the UI — there is no code path that skips the preview/confirmation step.

**9. Etsy write behavior.** The full sequence, with no exceptions in the codebase: preview generated → seller confirms → backup snapshot of pre-write state taken → write executes → action recorded to an audit log.

**10. Data storage.** Synced listing/shop data, encrypted OAuth tokens, backup snapshots (for revert), and CSV job records are stored in PostgreSQL. Tokens are encrypted at rest (Fernet/AES); plaintext tokens are never persisted.

**11. Retention.** Backup snapshots and CSV job records are retained for a maximum of 30 days from creation (`ETSY_DERIVED_DATA_RETENTION_DAYS`, configurable without a code change), after which an automated daily job deletes them. This is this project's own conservative interpretation of Etsy's API Terms language that accessed content should not be stored "longer than reasonably necessary" — Etsy's terms do not specify a number of days, and we are not asserting they require exactly 30. Live listing data itself is not subject to this cap; it stays in sync for as long as the seller keeps the shop connected. This is not a paper policy: an automated daily job (DigitalOcean App Platform Scheduled Job, 03:30 UTC) is active in production and completed its first real scheduled execution on 2026-07-15 (03:31:29–03:31:31 UTC) with a clean run — all four retention tables checked (`listing_backup_snapshots`, `listing_media_backup_snapshots`, `listing_variation_backup_snapshots`, `csv_jobs`), 0 rows required deletion (consistent with this being a private-beta dataset with little aged data yet), no errors.

**12. Disconnect behavior.** Disconnecting a shop immediately deletes its stored access and refresh tokens from the database (not merely marking them inactive) and pauses any scheduled jobs tied to that shop.

**13. Token security.** OAuth access and refresh tokens are encrypted at rest before being written to the database. They are never logged, never returned in any API response body, and never exposed to the frontend.

**14. AI safeguard.** Sending Etsy-derived listing content (title, description, tags) to a third-party AI provider (OpenAI or Anthropic) for the optional suggestion feature is gated behind a server-side flag, `ALLOW_ETSY_DATA_TO_AI`, defaulting to `false` and enforced at the service layer — not merely hidden in the UI. This flag is not enabled in production today. Separately, the configured AI provider itself is currently `mock` in production, meaning no live call to any external AI provider is possible right now regardless of the flag. We are not asserting Etsy has prohibited this kind of AI use — we found no official Etsy documentation addressing it either way, and disabled the pathway as our own conservative precaution pending guidance (see section F, question 1).

**15. Social integration status.** A Pinterest/Instagram account-connection feature exists, but the actual "post to Pinterest/Instagram" API call is deliberately not implemented — it is fully stubbed and returns a "not yet available" response — specifically because we were unsure whether republishing synced Etsy listing content to a third-party marketing platform requires authorization (see section F, question 4).

**16. No scraping.** Confirmed by direct code review: every Etsy interaction goes through the documented Open API v3 REST surface via a single `httpx`-based client. No headless browser, no HTML parsing of etsy.com, no undocumented endpoints, anywhere in the codebase.

**17. Trademark and independence.** "Etsy" is a trademark of Etsy, Inc. Bulk Edit App uses Etsy's official API but is not endorsed, sponsored, or certified by Etsy, Inc. This is disclosed on the Terms of Service and Privacy Policy pages, and near the shop-connection flow. The live disclaimer text reads: *"The term 'Etsy' is a trademark of Etsy, Inc. This application uses the Etsy API but is not endorsed or certified by Etsy, Inc."* — this matches the phrasing found on Etsy's own Open API v3 developer documentation verbatim. A second, slightly different phrasing appears in search-indexed excerpts of Etsy's API Terms of Use page itself ("This Application uses Etsy's API, but is not endorsed or certified by Etsy," without the trailing ", Inc.") — the two official Etsy sources do not exactly match each other, and our live text matches one of them exactly. Direct automated re-fetch of `www.etsy.com/legal/trademarks/` and `www.etsy.com/legal/api/` returns HTTP 403 to this tooling (bot-blocked, not a content issue), so a manual, in-browser re-check of both pages immediately before submission is still recommended (see `ETSY_APPEAL_CHECKLIST.md` item 1) — but no production change has been made this session, since the discrepancy is between two of Etsy's own pages, not a case where our text clearly fails to match either one.

**18. Public website corrections.** The site previously described the product with pre-launch/"founding access" framing while it was already live and requesting production write scopes — this language has been removed. Public marketing pages for "AI Listing Optimization" and "Listing Health Score" have also been removed (both features remain live and available in-app to authenticated sellers; only the public marketing pages were removed, pending the AI clarification in section F).

**19. Testing and production validation.** Backend test suite: 982 tests passing. Anything touching cascading deletes, foreign-key constraints, or webhook-driven billing state was additionally verified against real PostgreSQL (not just the SQLite unit-test suite), since SQLite's lax constraint enforcement previously masked two real bugs that were found and fixed during this review. Frontend: TypeScript compiles clean, lint clean (only pre-existing, non-blocking warnings), production build clean. All changes described in this document are live in production as of 2026-07-14 (merge commit `435a1aa` and subsequent), verified directly against the live site and live API this session — backend health, database connectivity, and Redis connectivity all confirmed healthy, not merely committed to source control.

**20. Current limitations.** Etsy developer access remains blocked by the ban itself, so live OAuth cannot currently be completed, and no live Etsy write has been re-tested since the ban took effect — everything above describing Etsy-facing behavior (except what predates the ban) is verified in code and against our own database, not against a live Etsy connection. The Etsy listing-video-upload endpoint specifically has not been tested live, for the same reason. New account sign-ups remain paused behind a private-beta gate while this appeal is pending, so the live seller-facing surface is not actively growing during Etsy's review.

---

## C. Updated application description (for the Etsy developer console)

> Bulk Edit App is a seller-authorized listing management utility for Etsy sellers. Using Etsy's official Open API v3 and OAuth2 (PKCE), it lets a seller connect their own shop, synchronize their own listings, prepare bulk changes to titles, descriptions, tags, prices, quantities, variations, photos, and videos, review an exact before-and-after preview of every change, and explicitly confirm before anything is submitted to Etsy. Every write is preceded by a backup snapshot so changes can be reverted. The app also offers CSV import/export and scheduled seller-authorized updates (which only ever create drafts requiring separate manual confirmation — nothing is auto-applied). An optional AI-assisted listing-suggestion feature exists but is currently disabled from accessing any Etsy-derived data pending Etsy's guidance. The app does not process orders, payments, or buyer data, and requests only `listings_r`, `listings_w`, `shops_r`, and `profile_r` scopes.

---

## D. Production URLs

- Marketing site: `https://bulkeditapp.com` (and `https://www.bulkeditapp.com`)
- Application: `https://app.bulkeditapp.com` (currently gated behind a private-beta notice for new sign-ups)
- API: `https://api.bulkeditapp.com`
- OAuth callback: `https://api.bulkeditapp.com/api/v1/etsy/callback`

---

## E. OAuth scopes

```
listings_r
listings_w
shops_r
profile_r
```

Verified directly against `apps/backend/app/core/config.py` (`ETSY_SCOPES`) this session — exact match, no production environment override. No transaction, buyer-email, financial, or billing scopes are requested anywhere in the codebase.

---

## F. Requested Etsy clarifications

1. May Etsy-derived listing content be processed by a third-party AI provider with seller consent?
2. What retention duration does Etsy consider reasonable for rollback snapshots and CSV exports?
3. Are seller-authorized scheduled listing updates permitted under the granted OAuth scopes?
4. May seller-selected Etsy listing content be republished to Pinterest or Instagram through the app?
5. Are Listing Health Score and factual listing analytics acceptable if no external AI provider receives Etsy-derived content?

---

## G. Pre-submission checklist

- [ ] Confirm the exact appeal destination (developer@etsy.com, or the specific contact/form named in the ban notice, if any).
- [ ] Confirm which account/inbox owns the Etsy developer account, and send from (or to) that address.
- [ ] Confirm the app's client_id (`7usvn9q6itlj6306sef64god`) is still current before including it.
- [ ] Confirm the OAuth callback URL (`https://api.bulkeditapp.com/api/v1/etsy/callback`) matches what's registered in the Etsy developer console.
- [ ] Confirm the production website (`https://bulkeditapp.com`) is live and reachable at send time.
- [ ] Manually re-read `https://www.etsy.com/legal/trademarks/` and `https://www.etsy.com/legal/api/` in a browser to re-verify the exact current trademark disclaimer wording (see section B.17 — this tooling's automated fetch is blocked; a human browser check has not yet happened).
- [ ] Confirm the requested scopes (`listings_r listings_w shops_r profile_r`) still match the developer console's granted scopes.
- [ ] Confirm Private Beta is still enabled on `app.bulkeditapp.com` at send time.
- [ ] Attach or link nothing that requires Etsy to create an account or log in; keep any evidence accessible without auth if possible. Screenshots only if Etsy's appeal channel explicitly allows attachments.
- [ ] Do not include any secret value (API keys, tokens, database credentials, or internal deployment identifiers) anywhere in the submitted message — re-scan the final text immediately before sending.
- [ ] Do not create a new Etsy developer application while this one is under appeal.
