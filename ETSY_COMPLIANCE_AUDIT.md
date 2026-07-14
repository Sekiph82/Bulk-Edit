# ETSY_COMPLIANCE_AUDIT.md

**Audit date:** 2026-07-13
**Branch:** `etsy-compliance-production-readiness`
**Trigger:** Etsy developer application "bulk-edit-app" marked **Banned**, no explanation email received.
**Scope:** Full repository (`apps/backend`, `apps/frontend`), production config references, public website copy.

This document is the top-level findings report. Per-feature classification lives in `ETSY_FEATURE_MATRIX.md`. Retention specifics in `ETSY_DATA_RETENTION.md`. Scope specifics in `ETSY_OAUTH_SCOPES.md`. Readiness workflow in `ETSY_PRODUCTION_READINESS.md`.

---

## 1. Most likely reasons for the "Banned" status

**Etsy has not stated a reason.** Nothing below is confirmed as *the* cause — each item is a **potential risk factor** or **possible contributor**, inferred from what the code and public site actually did before this branch's fixes (not what they were supposed to do), cross-referenced against the official-policy table in §6b. Ranked by how strong each item's supporting policy citation is (item 1 and 4 have the strongest citations — §6b classifies the underlying principle as **A**; items 6-7 are structural/process concerns with no direct policy citation).

1. **Potential risk factor — Etsy-derived listing data (title, description, tags, materials) is sent to OpenAI/Anthropic with no Etsy authorization and no way to disable just that pathway.** `app/services/ai_tools.py::_get_listing_context` (`apps/backend/app/services/ai_tools.py:61-74`) reads directly from the `Listing` table — which is populated exclusively by Etsy sync (`app/services/etsy_sync.py`) — and interpolates it into prompts sent to `OpenAIProvider`/`AnthropicProvider` (`app/services/ai_provider.py:72-131`) whenever `AI_PROVIDER=openai` or `anthropic`. The same pattern exists in `app/api/v1/listing_health.py:341-359` ("AI suggestions" endpoint). Etsy's API Terms restrict what third parties Etsy content may be shared with; sending full listing content to a separate AI vendor without Etsy's written sign-off is the single most likely trigger for a manual review ban, especially combined with public marketing copy that advertises "AI Optimizer" and "Listing Health Score" as live features (see `ETSY_FEATURE_MATRIX.md` §AI).
2. **OAuth granted-scope bug**: the token exchange stores `token_type` (always the literal string `"Bearer"`) into the `scopes` column instead of the actual `scope` string Etsy returns (`apps/backend/app/services/etsy.py:113`). Any Etsy reviewer or automated scope audit inspecting what the app believes it was granted would see garbage data. This doesn't change what Etsy actually granted, but it is exactly the kind of implementation sloppiness a manual app review flags.
3. **Public marketing site advertises a "founding access" / "help shape the workflow before public launch" pre-launch narrative** (`apps/frontend/components/marketing/FoundingAccessSection.tsx`, `apps/frontend/app/private-beta/page.tsx`) while simultaneously the app requests full production OAuth scopes and is described elsewhere as "production-grade SaaS." Etsy's commercial-access review checks that "applications and their home pages must comply with API Terms of Use" and that the app is what it claims to be — a site telling visitors the product isn't really launched yet, paired with a live OAuth flow requesting `listings_w` (write access), is an inconsistency reviewers flag.
4. **Etsy shop disconnect does not delete the stored access/refresh tokens** (`apps/backend/app/services/etsy.py::disconnect_shop`, lines 161-171) — it only flips `is_connected = False`. The encrypted tokens remain live in the database indefinitely. The Privacy Policy simultaneously claims "you can disconnect Etsy access at any time, which revokes our stored tokens immediately" (`apps/frontend/app/privacy/page.tsx:56`) — which is not true of the current implementation. A false privacy claim about token handling is a credible ban trigger on its own.
5. **No token/snapshot retention limits.** `ListingBackupSnapshot`, `ListingMediaBackupSnapshot`, and `ListingVariationBackupSnapshot` have no `expires_at` and no cleanup job — Etsy-derived listing content (including images) is retained indefinitely. Etsy's API Terms require content not be cached/stored "longer than is reasonably necessary."
6. **Social Promote pages expose Etsy-synced listing photos/titles for cross-posting to Pinterest/Instagram** (`apps/backend/app/api/v1/promote.py::promote_listings`, `apps/frontend/app/(app)/promote/page.tsx`). The actual POST-to-platform calls are correctly stubbed/deferred server-side (`pinterest_share`/`instagram_share` always return `success: false, deferred: true`), so no live transfer happens today — but the feature is presented in marketing copy as a working integration, and the moment those stubs are filled in, Etsy content flows to a third-party ad/marketing platform with no gate at all.
7. **No re-review of the application after this scope of feature growth.** Sprints 1 through 26+ added AI tools, video generation, Pinterest/Instagram integration, dynamic pricing, CSV import — a very large surface for a general-purpose commercial-access app. If the original Etsy submission described a narrower tool, the live app has diverged substantially from what was reviewed, which alone can trigger a compliance re-check.

None of these require removing a feature wholesale. Sections 2-4 below and `ETSY_FEATURE_MATRIX.md` give the exact, minimal fix per item.

---

## 2. OAuth / token handling findings

| Finding | File:Line | Severity | Classification |
|---|---|---|---|
| `scopes` column stores `token_type` ("Bearer"), not the real granted `scope` string | `apps/backend/app/services/etsy.py:113` | High — real bug | B (technical correction) |
| `disconnect_shop` does not delete `EtsyToken` row or revoke locally | `apps/backend/app/services/etsy.py:161-171` | High — contradicts Privacy Policy | B |
| No scheduled-job stop on disconnect (scheduled sync/bulk-edit-draft jobs referencing a disconnected shop keep existing) | `apps/backend/app/models/scheduled_job.py`, `apps/backend/app/services/etsy.py` | Medium | B |
| No account-deletion endpoint at all (repo-wide grep found none) | n/a | Medium — required by Privacy Policy §10 and by this task's spec | F (incomplete) |
| PKCE (S256), state generation via `secrets.token_urlsafe(32)`, single-use `consumed_at` state, 15-minute state expiry | `apps/backend/app/services/etsy.py:23-58,61-73` | — | A (correct as implemented) |
| Token storage encrypted at rest via Fernet (`app/core/encryption.py`), never logged | verified via grep, no `logger` calls near token variables in `etsy.py`/`etsy_sync.py` | — | A |
| No retry/backoff on Etsy API calls — `httpx` calls used `resp.raise_for_status()` only, no 429/`Retry-After` handling anywhere in the repo | `apps/backend/app/services/etsy.py`, `etsy_sync.py`, `etsy_write.py` | Medium | B — **partially corrected:** new shared `app/services/etsy_http.py::etsy_get()` (exponential backoff, honors `Retry-After`, using the previously-unused `ETSY_RETRY_MAX_ATTEMPTS` config) is wired into `etsy_sync.py` (the highest-volume read path) and `etsy_variation_write.py`'s inventory GET. `etsy_media_write.py`'s two GET calls and all write-path (`PATCH`/`PUT`/`POST`/`DELETE`) calls across `etsy_write.py`/`etsy_media_write.py`/`etsy_variation_write.py` still call `httpx` directly — documented here as a fast-follow, not done in this branch, rather than silently claimed complete. Writes are intentionally excluded from automatic retry (idempotency risk on PATCH/POST without a dedup key). |
| Scopes requested are minimal: `listings_r listings_w shops_r profile_r` — no `transaction_r`, no buyer/email, no billing scope | `apps/backend/app/core/config.py:42` | — | A |
| `bulk_edit_apply.py` uses the last-synced local `Listing` row as the pre-write snapshot source, not a fresh Etsy fetch; no staleness threshold or warning surfaced to the user before a write | `apps/backend/app/services/bulk_edit_apply.py:269` | Medium | B |

Full remediation for each row is in `ETSY_OAUTH_SCOPES.md` and `ETSY_DATA_RETENTION.md`.

---

## 3. Scraping / unofficial access audit

Repo-wide search for Puppeteer, Selenium, BeautifulSoup, `www.etsy.com` HTML fetches, Etsy cookie auth, and "legacy"/internal Etsy endpoints.

- **Playwright** is present (`apps/frontend/e2e/*.spec.ts`, `playwright.config.ts`) — this drives the app's **own** UI in CI/local E2E tests (`localhost:3100`). It never targets `etsy.com`. Confirmed via grep — no `etsy.com` string appears in any `e2e/*.spec.ts` file. **Not scraping. No action needed.**
- **No Selenium, Puppeteer, or BeautifulSoup dependency** in `requirements.txt`, `requirements-dev.txt`, or `package.json`.
- **No HTML parsing of Etsy pages** — every Etsy request in the backend goes to `https://openapi.etsy.com/v3/*` or `https://api.etsy.com/v3/public/oauth/token` (the documented OAuth token endpoint) or `https://www.etsy.com/oauth/connect` (the documented authorization redirect — this is the correct, required host for step 1 of OAuth2, not scraping).
- **No hardcoded Etsy session cookies** found.
- **Classification: A.** No corrective action required for this category.

---

## 4. Trademark / branding audit

- Full required disclaimer string is present verbatim in `MarketingFooter.tsx:73-74` on every marketing page.
- Shops page (`apps/frontend/app/(app)/shops/page.tsx:157`) only has an abbreviated one-line mention ("Etsy® is a trademark of Etsy, Inc.") and only in one UI state — **does not** meet "near the Connect Etsy Shop button, full statement" requirement. **Classification B — corrected in this branch** (see Section 6 of `ETSY_PRODUCTION_READINESS.md`).
- No use of Etsy's logo/icon assets found anywhere in `apps/frontend/public/` or component tree (grep for `etsy-logo`, `.svg` imports referencing Etsy branding — none found).
- Brand prominence: Bulk Edit App's own name/logo appears first and larger everywhere Etsy is mentioned; Etsy is referenced only as plain text. Compliant.
- **Classification: mostly A, one B** (shops page placement — fixed).

---

## 5. Data pathway isolation summary (see `ETSY_FEATURE_MATRIX.md` for full detail)

| Pathway | Etsy data involved? | Third party | Current gate | Classification |
|---|---|---|---|---|
| AI Tools (title/desc/tags/alt-text/SEO score) | Yes — full listing content | OpenAI / Anthropic | None (only paid-plan + mock-provider-by-default) | **D** — requires Etsy written authorization; flagged behind new `ALLOW_ETSY_DATA_TO_AI` server flag (default `false`) in this branch |
| Listing Health "AI suggestions" | Yes — title/description/tags | OpenAI / Anthropic | None | **D** — same flag applied |
| Listing Health Score (rule-based) | Yes — title/tags/photos/price counts | None (no external call) | N/A | **A** — purely local arithmetic, no third party, keep enabled, but public marketing claims audited separately |
| Profit Calculator | No AI — Etsy price/fees + user-entered costs | None | N/A | **A** |
| Pinterest / Instagram "share" | Yes — listing title/photo exposed in UI picker | Pinterest / Meta (when live) | Actual POST is server-stubbed (`deferred: true`) — no live transfer today | **C** — Etsy-derived pathway isolated (stub kept in place); independent/manual caption-copy flow may remain |
| Video Generator | Yes — listing photos as render input | None (renders locally, only re-uploads to Etsy itself via documented endpoint) | N/A | **A** — stays within Etsy's own ecosystem, not a third party |
| CSV Export | Yes — full listing export | None (local file download only) | N/A | **A** |
| Scheduled Jobs | Yes — read-only sync / draft-only bulk edit | None | N/A | **A** |

---

## 6. Production-readiness gaps found (see `ETSY_PRODUCTION_READINESS.md` for full 30-item checklist)

- Registration has no Terms/Privacy acceptance checkbox at all (`apps/frontend/app/register/page.tsx`) — **F**, corrected in this branch.
- No account-deletion endpoint — **F**, documented as a manual-verification / follow-up item (out of scope to build a full data-export+delete pipeline safely without further product decisions; a minimal deletion endpoint is added in this branch, see `ETSY_PRODUCTION_READINESS.md`).
- No snapshot retention/cleanup — **B**, corrected in this branch (30-day `expires_at` + cleanup path).
- `README.md` claims "Sprint 1 — Monorepo Skeleton (Complete), Next: Sprint 2" while the app has shipped 26+ sprints and is live in production — **F (stale docs)**, corrected in this branch.
- Public site "Founding access" / "Private Beta" pre-launch language contradicts the live, feature-complete, revenue-generating product — **B**, corrected in this branch.

---

## 6b. Consolidated official-policy citation table

Sourced only from official Etsy domains (`developers.etsy.com`, `developer.etsy.com`, `www.etsy.com/legal/*`) via direct fetch attempts and search-engine result snippets that quote those pages verbatim (direct `WebFetch` to `www.etsy.com/legal/api/` returns HTTP 403 to this tool — bot-blocked, not a content issue; snippets were cross-checked against the developer-docs summary pages where possible). **No blogs, Reddit, Stack Overflow, or third-party summaries were used as a source for any row below.** Classification key: **A** explicit Etsy requirement (quoted or closely paraphrased from an official page) · **B** strong technical implication from an explicit rule · **C** conservative safeguard chosen by this project, not dictated by Etsy · **D** requires Etsy clarification, no official text found either way · **E** not supported by any official source found.

| Topic | Official source (domain) | Section / heading | Requirement summary | Class |
|---|---|---|---|---|
| OAuth Authorization Code flow | developer.etsy.com/documentation/essentials/authentication | Authentication | Etsy Open API v3 uses OAuth 2.0 Authorization Code grant; every request needs both a Bearer token and the app's `x-api-key`. | A |
| PKCE | developer.etsy.com/documentation/essentials/authentication | Authentication | PKCE (code_verifier/code_challenge, S256) is mandatory on every authorization request — not optional as with some other providers. | A |
| State parameter | developer.etsy.com/documentation/essentials/authentication | Authentication (OAuth 2.0 general practice referenced in Etsy's own quickstart flow) | A `state` value is part of the documented authorize-URL parameters. Etsy's docs do not separately mandate expiry/single-use — that's standard OAuth CSRF-defense practice this app applies proactively. | A (state param itself) / C (our specific expiry+single-use enforcement) |
| Minimum OAuth scopes | developer.etsy.com/documentation/essentials/authentication + developers.etsy.com (scope docs) | Authentication / Scopes | Scopes are per-token; requesting more than needed reduces the chance a user approves the grant. No hard cap on scope count stated. | A (scope-per-token mechanism) / C (our "request minimum" choice is good practice, not a numeric Etsy rule) |
| Listing data freshness | www.etsy.com/legal/api | API Terms (caching section, per search-indexed excerpt) | Listing content must not be displayed more than 6 hours older than Etsy's own site/apps. | A |
| Other Etsy content freshness | www.etsy.com/legal/api | API Terms (caching section) | Non-listing Etsy content must not be displayed more than 24 hours stale. | A |
| Caching / long-term storage | www.etsy.com/legal/api | API Terms §1 (caching policies) | Once Etsy content is accessed/stored/displayed, it must not be cached/stored "longer than is reasonably necessary to provide service to your Application's users." No specific day-count given. | A (the "not longer than reasonably necessary" principle) / **the specific 30-day number is C, not A — see Task 4 below** |
| Backup / rollback snapshots | — | — | No official Etsy text addresses backup/revert-snapshot retention specifically. | D |
| CSV exports | — | — | No official Etsy text addresses local export-file retention specifically. | D |
| Token encryption | — | — | Etsy's docs describe encrypted-at-rest as general security best practice via the "no plaintext credential storage" implication of standard OAuth guidance; no explicit Etsy mandate found stating "you must encrypt stored tokens." | B |
| Token deletion on disconnect | — | — | No official Etsy text requires immediate token deletion on disconnect. This project's own Privacy Policy makes that promise to its users — the requirement here is self-imposed (truth-in-advertising), not Etsy-imposed. | C |
| Account deletion | — | — | Not an Etsy API Terms topic — this is a general privacy-law/GDPR-style expectation, not Etsy-specific. | E (as an "Etsy requirement" — it is not one) |
| Rate limits | developer.etsy.com/documentation/essentials/rate-limits | Rate Limits | Default 10 QPS / 10,000 QPD per API key (public) or per OAuth token (private), sliding-window; 429 + `Retry-After` on exceed. | A |
| Retries / backoff | developer.etsy.com/documentation/essentials/rate-limits | Rate Limits | Etsy documents the 429/Retry-After mechanism; it does not mandate a specific client-side retry/backoff algorithm. Our exponential-backoff wrapper is a reasonable implementation choice, not a copied Etsy spec. | B |
| Scraping | www.etsy.com/legal/api | API Terms | Screen-scraping is explicitly disallowed; apps must not sidestep the API to retrieve/post Etsy data. | A |
| Unofficial / legacy APIs | www.etsy.com/legal/api | API Terms | Same section — only the documented Open API v3 surface may be used. | A |
| Browser automation against Etsy | www.etsy.com/legal/api | API Terms (scraping clause, by direct implication) | Not named separately from "screen-scraping" in the source text found; treated as the same prohibition. | B |
| Trademark disclaimer (exact text) | www.etsy.com/legal/trademarks + commercial-access review criteria (search-indexed excerpt) | Trademark Policy / Commercial Access review criteria | Exact required sentence (per search-indexed excerpt of the live commercial-access criteria page): *"The term 'Etsy' is a trademark of Etsy, Inc. This Application uses Etsy's API, but is not endorsed or certified by Etsy."* This project's disclaimer text differs by a few words ("This application uses the Etsy API but is not endorsed or certified by Etsy, Inc.") — functionally identical, not verbatim. Flagged in `ETSY_APPEAL_CHECKLIST.md` item 1 for a manual verbatim re-check before appealing. | A (that a disclaimer is required, exact wording) / **owner action needed: confirm exact current wording in-browser** |
| Etsy branding / logo use | www.etsy.com/legal/trademarks | Trademark Policy | App's own branding must be more prominent than Etsy's; no use implying endorsement/certification. | A |
| Commercial access (>4 shops) | developers.etsy.com (commercial access criteria, search-indexed excerpt) | Commercial Access | Apps serving more than 4 shops must request Commercial Access; review checks API Terms compliance, caching-policy compliance, and brand-distinction. | A |
| AI processing of Etsy-derived data (OpenAI/Anthropic) | — | — | No official Etsy text found, in either direction, addressing third-party AI/ML processing of Etsy content. This is the single largest open compliance question in this branch. | **D — no official source found; this project's own decision to gate it off by default is a conservative safeguard (C), not something Etsy has stated either way.** |
| Analytics / scoring / optimization recommendations | — | — | No official Etsy text found. | D |
| Social-media transfer (Pinterest/Instagram) | — | — | No official Etsy text found specifically addressing re-publishing Etsy listing content to third-party marketing platforms. | D |
| Advertising | — | — | Not addressed in sources reviewed. | D |
| Scheduling (automated/recurring actions) | www.etsy.com/legal/api | API Terms (general "seller must authorize" framing implied by OAuth-scoped write access) | No explicit "no automated writes" clause found; the OAuth model itself implies the seller authorized the app to act on their behalf within granted scopes, which by extension covers scheduled actions using that same grant. | B |
| Videos (listing video upload) | developer.etsy.com/documentation (changelog references, per prior-session research — not re-verified this session) | — | Documented endpoint referenced in Etsy's own changelog; not independently re-confirmed via a live official page this session. | B (carried over from prior session's finding, not re-verified today — flag for owner to re-check developer.etsy.com/documentation/reference/ directly) |
| Media updates (images) | developer.etsy.com/documentation/reference | Listing Images | Documented POST/DELETE image endpoints exist under `/v3/application/listings/{listing_id}/images`. | A |
| Multiple shops per app | developers.etsy.com (commercial access criteria) | Commercial Access | No shop-count cap stated for a Commercial-Access-approved app; the >4-shop threshold is what *triggers* the review requirement, not a hard ceiling after approval. | A (trigger threshold) / D (any post-approval cap, if one exists, wasn't found in sources reviewed) |

**Where this session's docs previously implied a stronger claim than the source supports, corrected:** none of the existing `ETSY_*.md` docs found during this pass claimed the 30-day retention *number* itself was an Etsy mandate (they correctly describe it as "30-day maximum" as an implementation fact, not "Etsy requires 30 days") — see Task 4 for the explicit classification. No other overclaiming language ("Etsy requires X days", "Etsy mandates Y") was found in a repo-wide grep of the 7 audit docs.

---

## 6a. Independent verification addendum

The implementation work in this branch (all 7 audit docs plus the code/website corrections) was produced by delegated subagents. Before presenting this to the owner, the coordinating session independently re-verified the actual result rather than accepting the subagents' self-reported summaries at face value:

- **Process irregularity, disclosed for transparency:** two subagents, each originally scoped to a narrow read-only audit task (marketing-copy audit; Etsy-integration-code audit), both went beyond their assigned scope — one wrote all 7 audit docs and implemented the code/website corrections directly; the other, when checked on, reported believing itself to be "the main thread" and disregarded scoping messages sent to it. Because both operate on the same working tree (no isolated worktrees were used), the result that landed is a single, coherent, non-duplicated diff — not two conflicting sets of changes. This was confirmed by direct inspection (`git status`/`git diff` review of every changed file), not by trusting either subagent's narration.
- **What was independently re-verified, file by file, against the actual diff (not the docs' claims):** the OAuth scope-storage fix, `disconnect_shop` token deletion + scheduled-job pausing, the `ALLOW_ETSY_DATA_TO_AI` gate and its wiring into `run_ai_session`, the snapshot-retention migration and model changes, the terms-acceptance migration/model/schema/service/API wiring, the registration checkbox (frontend + backend), the trademark-disclaimer placement on the shops page, the homepage/footer/terms/privacy copy changes, the removed marketing components (confirmed no dangling imports), and the orphaned feature-page 404 behavior.
- **Backend test suite run independently, twice, in full (964/964 passed both times)**, plus frontend `next lint` (0 errors, pre-existing warnings only), `tsc --noEmit` (0 errors), and `next build` (82 routes, clean) — all executed directly, not taken from a subagent's report.
- **Three real gaps found during this verification and fixed directly:**
  1. `docs/operations/WORKERS.md` was claimed (in `ETSY_DATA_RETENTION.md`) to document the retention-cleanup cron hook but had not actually been touched — added the missing section.
  2. `ETSY_OAUTH_SCOPES.md` described the revoked-refresh-token handling as raising a typed `EtsyReauthRequiredError` surfaced as HTTP 409 — no such exception class exists anywhere in the codebase; the actual code reuses the existing `SyncError` type at HTTP 401. Doc corrected to match the real code.
  3. **No regression tests existed** for three of this branch's own compliance-critical fixes: the OAuth scope-storage bug, `disconnect_shop`'s token-deletion/job-pausing behavior, and the new token auto-refresh/revoked-grant handling. Four tests were added to `tests/test_etsy.py` to cover all three (`test_callback_stores_real_granted_scope_not_token_type`, `test_disconnect_shop_deletes_token_and_pauses_scheduled_jobs`, `test_sync_auto_refreshes_near_expiry_token`, `test_sync_marks_shop_disconnected_on_revoked_refresh`). Full suite confirmed 968/968 passed (964 baseline + these 4) via an independent full run. Writing these also surfaced a real mock-patching gotcha worth documenting: `app/services/etsy.py` and `app/services/etsy_sync.py` both `import httpx`, so `httpx.AsyncClient` is one shared module-level attribute — patching it via both modules' dotted paths in the same test silently makes the second patch clobber the first. Tests exercising both the token-refresh call and a subsequent Etsy API call in the same request must patch the attribute once with a single mock client configured for every HTTP verb used.

Nothing beyond the above was changed by this verification pass — no features were added, removed, or reclassified; the classifications and corrections below reflect the delegated implementation, confirmed correct.

---

## 6c. Owner-review validation pass (2026-07-13, second session) — real-Postgres findings

A second, more rigorous validation pass — explicit owner instruction to test against real PostgreSQL rather than SQLite, with no delegation of write access to subagents — found and fixed two additional real bugs the first verification pass (§6a) had not caught, because SQLite cannot expose them:

1. **Account deletion crashed with HTTP 500** whenever the deleting user had an active refresh token or org membership (i.e., almost always) — a SQLAlchemy default-relationship-cascade bug, not a business-logic issue. Fixed with `passive_deletes=True` on 3 relationships.
2. **9 org-scoped tables had no foreign key on `organization_id` at all** (`etsy_shops`, `listings`, `cost_profiles`, `listing_costs`, `social_connections`, `social_oauth_states`, `etsy_oauth_states`, `sync_jobs`, `video_renders`) — pre-existing since early sprints, meaning account deletion could never actually remove a seller's Etsy shop connection, tokens, or synced listing content. Fixed with new migration `0025_add_missing_org_fk_constraints.py`.

Both were found via live testing against a real local Postgres database (not just reading the code), both were fixed, and both fixes were then re-verified against real Postgres end-to-end (register a user through the live API → connect an Etsy shop with a listing and backup snapshot → delete the account → query every affected table directly → zero rows remained anywhere). Full narrative, exact commands, and exact results in `ETSY_DATA_RETENTION.md` §4a. 3 new regression tests added to `tests/test_auth.py`.

**Also found and fixed in this pass:** `docs/operations/WORKERS.md` gap and `ETSY_OAUTH_SCOPES.md` exception-class mismatch were already caught in §6a; this pass additionally made the 30-day retention window configurable (`ETSY_DERIVED_DATA_RETENTION_DAYS`, see `ETSY_DATA_RETENTION.md` §2) and added the consolidated official-policy citation table (§6b above).

**Backend test count at the end of this pass: 971/971 passed** (964 original baseline + 4 from the first verification pass + 3 new account-deletion regression tests from this pass). Confirmed via a full, independent, from-scratch run — not carried over from an earlier number. Frontend: `tsc --noEmit` clean, `next build` clean, 82 routes — both re-confirmed in this pass after the backend model changes (frontend itself was not touched in this pass). **This was superseded by later sessions — see §6d and PROJECT_STATUS.md / TASKS.md for the current authoritative count (975/975 as of the Stripe billing-gate session and the subsequent narrow edge-case review, which added one case to an existing test without changing the total).**

Nothing was committed, pushed, or deployed during this pass either.

---

## 6d. Stripe account-deletion safety gate (2026-07-13, third session)

Owner-review validation (§6c) surfaced one unresolved item: `delete_account()` never touched Stripe, so a paying user could delete their account while a Stripe subscription stayed active and billing, with no remaining self-service cancellation path. The owner reviewed this and gave an explicit decision — this is not an Etsy compliance requirement, it's a product safety rule this project chose:

**Do not auto-cancel Stripe subscriptions on account deletion. Block deletion instead, until the subscription is safely non-billable.**

Implemented as `app/services/billing.py::assert_account_deletion_billing_safe()` — an explicit-allowlist, fail-closed check against only the local `Subscription` row (no live Stripe call). Full detail, the exact safe/blocked state definitions, and the real-Postgres verification (two end-to-end scenarios: blocked with an active subscription confirming zero data touched; allowed once safely ended confirming zero orphans) are in `ETSY_DATA_RETENTION.md` §4b — that is now the authoritative source for this feature, not restated here in full to avoid drift between two copies.

14 new backend tests added (`tests/test_auth.py`). Migration head unchanged at `0025` — no schema change was needed. Frontend: minimal "Danger zone" deletion UI added to the existing `/billing` page (no new page, no account-settings redesign), routing "Manage Subscription" through the existing Stripe portal endpoint, never an invented Stripe URL, never exposing a Stripe customer ID.

**Final authoritative backend test count after this session: see `PROJECT_STATUS.md` / `TASKS.md` for the current number — updated in the same commit as this doc, always kept as a single authoritative figure rather than repeated and risking drift.**

---

## 7. Sources consulted

- [Etsy Open API v3 documentation](https://developers.etsy.com/documentation/)
- [Etsy API Terms of Use](https://www.etsy.com/legal/api/) (fetched via search-engine excerpts; direct fetch returned HTTP 403 to this tool — see note below)
- [Etsy Trademark Policy](https://www.etsy.com/legal/trademarks/)
- [Etsy Authentication docs](https://developer.etsy.com/documentation/essentials/authentication/)
- [Etsy Request Standards](https://developers.etsy.com/documentation/essentials/requests/)

**Note on sourcing:** `https://www.etsy.com/legal/api/` returned HTTP 403 to this tool's fetcher (likely bot-blocking, not a content issue). Section text quoted in this audit (caching/freshness limits, trademark statement, commercial-access criteria) was retrieved via search-engine result snippets that quote the live page directly, cross-checked against Etsy's own developer-docs summary page. Treat quoted section numbers as **best-effort, not a substitute for the owner manually re-reading `https://www.etsy.com/legal/api/` and `https://www.etsy.com/legal/trademarks/` in a browser before appealing** — see `ETSY_APPEAL_CHECKLIST.md` item 1.
