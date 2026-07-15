# ETSY_FEATURE_MATRIX.md

**Current status (2026-07-15):** All "this branch" corrections below are live in production. Etsy app remains **Banned**; appeal drafted (`ETSY_FINAL_APPEAL_DRAFT.md`), not yet submitted.

Per-feature compliance classification. Classifications: **A** allowed/production-ready · **B** allowed, needs correction (corrected in this branch unless noted) · **C** allowed only with Etsy-derived data isolated · **D** requires Etsy's express written authorization (flagged off by default) · **E** clearly prohibited · **F** incomplete/not production-ready.

---

## OAuth Shop Connection

- **Current behavior:** Etsy OAuth2 Authorization Code + PKCE (S256). `GET /api/v1/etsy/authorize` → Etsy → `GET /api/v1/etsy/callback`.
- **Production-ready:** Yes, code-level. Blocked end-to-end only by Etsy's own app-review/ban status (external).
- **Etsy API-derived data:** Shop id, shop name.
- **Endpoints used:** `POST https://api.etsy.com/v3/public/oauth/token` (code exchange + refresh), `GET https://openapi.etsy.com/v3/application/users/{user_id}/shops`.
- **OAuth scopes required:** `shops_r`, `profile_r`.
- **Data stored:** `EtsyShop` (shop id, name, connected flag), `EtsyToken` (Fernet-encrypted access + refresh token, expiry, scopes).
- **Retention:** Indefinite while connected; **now deleted on disconnect** (this branch — see `ETSY_DATA_RETENTION.md`).
- **External services receiving data:** None.
- **Relevant rule:** Etsy Authentication docs (OAuth2 + PKCE required for member data); API Terms §1 (no plaintext credential storage implied by standard security practice).
- **Required correction:** (1) Fix `scopes` column storing `token_type` instead of granted `scope` — **done, this branch**. (2) Delete tokens + stop related jobs on disconnect — **done, this branch**.
- **Etsy clarification needed:** No.
- **Classification: B → corrected, now A.**

---

## Listing Synchronization

- **Current behavior:** `POST /api/v1/shops/{id}/sync` pulls listings, images, videos, variations/inventory. Inline (HTTP-thread), not backgrounded.
- **Production-ready:** Yes.
- **Etsy API-derived data:** Full listing record (title, description, tags, materials, price, quantity, taxonomy, images, videos, variations, state, timestamps).
- **Endpoints used:** `GET /v3/application/shops/{shop_id}/listings`, `GET /v3/application/listings/{listing_id}/images`, `.../videos`, `.../inventory`.
- **OAuth scopes required:** `listings_r`.
- **Data stored:** `Listing`, `ListingImage`, `ListingVideo`, `ListingVariation` (full `raw_data` JSON retained for field-drift resilience).
- **Retention:** Indefinite while shop connected — mirrors Etsy's own listing state; deleted on shop disconnect (this branch adds cleanup — see `ETSY_DATA_RETENTION.md`).
- **External services receiving data:** None.
- **Relevant rule:** API Terms caching/freshness section — listing content must not be displayed materially older than the Etsy site without indicating staleness.
- **Required correction:** Surface `last_synced_at` staleness warning before bulk-edit preview/apply when sync is older than 6 hours (matches Etsy's own listing-content freshness window) — **added this branch**, see `ETSY_DATA_RETENTION.md` §Freshness.
- **Etsy clarification needed:** No.
- **Classification: B → corrected, now A.**

---

## Bulk Titles / Descriptions / Tags / Price / Quantity / Variations / Photos

- **Current behavior:** Session-based diff engine (`BulkEditSession` → preview → explicit confirm → `PATCH /v3/application/listings/{id}` + `PUT /v3/application/shops/{shop}/listings/{listing}/inventory`). Pre-write snapshot always taken. Magic Revert available.
- **Production-ready:** Yes.
- **Etsy API-derived data:** Full listing field set (as synced).
- **Endpoints used:** `PATCH /v3/application/listings/{listing_id}`, `PUT /v3/application/shops/{shop_id}/listings/{listing_id}/inventory`, image `POST`/`DELETE` under `.../listings/{listing_id}/images`.
- **OAuth scopes required:** `listings_w` (+ `listings_r` for pre-write read).
- **Data stored:** `BulkEditSession`, `BulkEditChange`, `BulkEditPreviewItem`, `BulkEditApplyJob/Result`, `ListingBackupSnapshot`, `AuditLog`.
- **Retention:** Backup snapshots previously indefinite — **now 30-day `expires_at` + scheduled cleanup, this branch.**
- **External services receiving data:** None.
- **Relevant rule:** CLAUDE.md's own 6-step external-write protocol (preview → confirm → snapshot → permission check → plan gate → audit log) — verified implemented in full in `apply_bulk_edit_session()`.
- **Required correction:** Snapshot retention (above).
- **Etsy clarification needed:** No.
- **Classification: A** (write-safety protocol already correct; only retention needed correcting).

---

## Video (Etsy listing video upload via documented endpoint)

- **Current behavior:** `replace_video`/`delete_video` media job operations call `POST`/`DELETE /v3/application/listings/{listing_id}/videos`, reusing an already-rendered local MP4.
- **Production-ready:** Implemented but **never exercised against a live Etsy shop** (per `DECISIONS.md` 2026-06-27 entry — endpoint shape inferred from Etsy's changelog + third-party OSS reference, not confirmed live).
- **Etsy API-derived data:** None sent *to* a third party — this writes Bulk Edit App's own rendered video *to* Etsy, which is core product functionality, not a third-party transfer.
- **OAuth scopes required:** `listings_w`.
- **Required correction:** None code-side. Mark as "requires manual verification against a live shop" in test report — **cannot claim tested until Etsy access restored.**
- **Etsy clarification needed:** No (uses documented-shape endpoint; if the first live call 404s/405s, `EtsyMediaWriteError.not_implemented` already surfaces it safely rather than silently failing).
- **Classification: F → not fully verifiable until the ban is lifted.** Code path kept enabled (per this task's "preserve every feature Etsy permits" rule) but publicly marketed only as "video upload," not guaranteed.

---

## CSV Import / Export

- **Current behavior:** Export full listing set to CSV; import with per-row validation + preview; convert to `BulkEditSession` draft (never writes directly to Etsy).
- **Etsy API-derived data:** Yes (export contains synced listing fields).
- **External services:** None — local file download/upload only.
- **Data stored:** `CSVJob`, `CSVRow` (raw + normalized + diff).
- **Retention:** No `expires_at` currently — **added in this branch's retention pass** (see `ETSY_DATA_RETENTION.md`).
- **Classification: B → corrected.**

---

## Templates / Change History / Time-Limited Rollback (Magic Revert)

- **Current behavior:** `RevertJob`/`RevertResult` restore from `ListingBackupSnapshot`, dual-write (listing PATCH + inventory PUT), local DB updated only after Etsy write success.
- **Etsy API-derived data:** Yes (restores prior synced state).
- **Retention:** Backup snapshots that back an active revert window get the same 30-day `expires_at` policy — see `ETSY_DATA_RETENTION.md` for how revert eligibility interacts with the retention window.
- **Classification: A**, retention correction applied same as bulk-edit snapshots.

---

## Scheduling of Seller-Authorized Updates

- **Current behavior:** `ScheduledJob` supports `etsy_sync` (read-only), `bulk_edit_draft` (creates a **draft** session only, never applies), `dynamic_pricing_preview` (preview only), `csv_export_snapshot` (metadata only). **None of the four job types ever call `etsy_write.py` or auto-apply a change** — confirmed via `DECISIONS.md` Sprint 16 entry and by reading `app/services/scheduled_jobs.py` executor dispatch.
- **Etsy API-derived data:** Yes (sync + draft creation reads listings).
- **Required correction:** On shop disconnect, active `ScheduledJob` rows referencing that shop must be paused — **added this branch** (part of the `disconnect_shop` fix).
- **Classification: A** — genuinely never auto-writes; this is exactly the "seller must still confirm" design Etsy's API Terms and this project's own CLAUDE.md require.

---

## Multiple Shops (within Etsy's permitted access limits)

- **Current behavior:** `EtsyShop` is org-scoped, no artificial cap on shop count in code.
- **Required correction:** None found. If Etsy's commercial-access grant specifies a shop-count or rate-limit ceiling per app, that is an Etsy-side condition, not a code gap — see `ETSY_SUPPORT_QUESTIONS.md`.
- **Classification: A.**

---

## Stripe and Subscriptions

- **Current behavior:** Stripe Checkout + Customer Portal + webhook (signature-verified, idempotent). No Etsy data involved.
- **Classification: A.**

---

## Factual Dashboards / Listing Statuses / Sync Timestamps

- **Current behavior:** Dashboard shows listing counts, shop counts, statuses, `last_synced_at`. Purely factual, no scoring/prediction.
- **Classification: A.**

---

## AI Tools — Title / Description / Tags / Alt Text / SEO Score

- **Current behavior:** `AISession` → `run_ai_session()` builds a prompt from `_get_listing_context()` (title, description, tags, materials, taxonomy_id — **all Etsy-sync-derived**) and calls `OpenAIProvider`/`AnthropicProvider` when `AI_PROVIDER` is set to a live provider. Output requires explicit accept → `convert_to_bulk_edit()` before it ever reaches a bulk-edit session; **never auto-applied or auto-written to Etsy** (verified: `accept_suggestion`/`convert_to_bulk_edit` both require explicit per-suggestion user action).
- **Input source:** 100% Etsy-API-derived (no manual-entry alternative path exists today).
- **OAuth scopes required:** N/A (reads local DB, not Etsy directly).
- **External services receiving data:** OpenAI and/or Anthropic, only when `AI_PROVIDER != mock` and API keys configured. Default `AI_PROVIDER=mock` — **no live send happens out of the box**, but production deployments with real keys configured (which this app has done, per `HANDOFF.md` provider setup) would send Etsy listing content to OpenAI/Anthropic silently, with no user-visible consent step beyond the general Terms of Service.
- **Data stored:** `AISession.input_payload` (stores the **exact** Etsy listing content sent to the AI provider), `AISuggestion`, `AIUsageLog` (metadata only — tokens/status, not raw prompt text, confirmed by reading the model's fields).
- **Relevant rule:** This task's own explicit instruction: "Do not send Etsy API-derived content to OpenAI, Anthropic or another AI provider unless Etsy gives express written authorization." No confirmation of such authorization exists in `DECISIONS.md` or anywhere in the repo.
- **Required correction:** Gate the Etsy-data pathway behind a new server-side flag, default OFF, independent of `AI_PROVIDER` — **done this branch**: `ALLOW_ETSY_DATA_TO_AI` (see `app/core/config.py` and `app/services/ai_tools.py`). When off, `AI_PROVIDER` may still be `openai`/`anthropic` for **manually-entered** content in the future, but the Etsy-sourced listing-context pathway is hard-blocked at the service layer (not just the UI), so it cannot be bypassed by direct API calls, background workers, or crafted requests.
- **Etsy clarification needed: Yes — this is the single most important open question. See `ETSY_SUPPORT_QUESTIONS.md` Q1.**
- **Precise current-state status (verified during owner-review validation, not just described):** Etsy-data AI pathway is disabled by default (`ALLOW_ETSY_DATA_TO_AI=false`). Local non-provider scoring (Listing Health Score) remains fully functional — see its own entry below, unaffected by this flag. **A manual/independent AI pathway (user-typed or independently-supplied content, not pulled from a synced listing) is NOT implemented today** — `_get_listing_context()` is the only input builder that exists, and it is 100% listing-derived. Do not read "AI_PROVIDER may still be used for manually-entered content in the future" (above) as a claim that this exists now — it does not. Building a real manual-input AI mode is out of scope for this compliance branch; it would be new product work, not a compliance fix.
- **Classification: D.**

---

## Listing Health "AI Suggestions" endpoint

- Same finding and same fix as AI Tools above — `POST /listing-health/listings/{id}/ai-suggestions` (`apps/backend/app/api/v1/listing_health.py:295-359`) sends listing title/description/tags to the configured AI provider. Gated behind the same `ALLOW_ETSY_DATA_TO_AI` flag in this branch.
- **Classification: D.**

---

## Listing Health Score (rule-based scoring engine)

- **Current behavior:** `app/services/listing_health.py` computes score 0-100 from local listing fields (title length, tag count, photo count, price, has_video) via **pure Python arithmetic — no external API call of any kind.**
- **Etsy API-derived data:** Yes (title, tags, photos, price — read from local synced `Listing`).
- **External services receiving data:** None.
- **Relevant rule:** This is a "factual dashboard" / deterministic computation over already-synced data the seller already has access to via their own Etsy listing — not analytics sent to a third party, and not (by itself) an AI-generated "recommendation." However, this task's own instructions classify "scoring, prediction, benchmarking and optimization recommendation" features derived from Etsy data as requiring Etsy clarification **regardless of whether the computation is local or AI-based**, because the underlying concern is Etsy's control over derivative analytical products built on their marketplace data, not just data leaving to a third party.
- **Required correction:** Keep the underlying score computation enabled (it is a genuinely local, non-third-party feature and directly useful to sellers) but **remove/hold public marketing claims about it** until Etsy confirms scoring/benchmarking features are permitted — see `ETSY_SUPPORT_QUESTIONS.md` Q2. In-app (post-login) display is preserved as a factual/informational dashboard, consistent with "keep listing count, quantity, price, tag/image counts" being explicitly permitted by this task's own feature list.
- **Etsy clarification needed:** Yes, specifically for the public-marketing claim, not for the private in-app computation.
- **Classification: C** — isolated from any third party already (never was a violation on that axis); the correction is marketing-claim removal, not a code gate.

---

## Profit & Cost Calculator

- **Current behavior:** Deterministic Decimal-precision fee/margin math using Etsy's published fee schedule + user-entered cost data. No AI, no external call (verified — no `openai`/`anthropic` import anywhere in `app/services/profit.py`).
- **Classification: A.**

---

## Pinterest / Instagram "Promote" (Social Sharing)

- **Current behavior:** OAuth connect to Pinterest/Meta directly (not through Etsy). `GET /promote/listings` exposes the seller's own synced listing title/price/primary-image-URL/Etsy-listing-URL so the seller can **pick which of their own listings** to reference in a caption. The actual `POST /pinterest/share` and `POST /instagram/share` calls are **hard-coded to return `success: false, deferred: true`** and never call the Pinterest/Instagram post APIs (confirmed by reading `apps/backend/app/api/v1/promote.py:504-528,676-700` in full — there is no `httpx.post` to a pin/media-publish endpoint anywhere in the file).
- **Etsy API-derived data:** Yes — listing title, price, primary image URL, Etsy listing URL are surfaced in the picker UI.
- **External services receiving data:** Pinterest/Meta receive **OAuth account-connection data only** (username, account id) — no listing content is transmitted today, because the share call is a stub.
- **Data stored:** `SocialConnection` (encrypted platform token), `SocialOAuthState`.
- **Required correction:** Keep the deferred stub in place (do **not** implement live posting) until Etsy confirms cross-posting synced listing content to third-party marketing platforms is permitted. Add an explicit code comment + this doc as the gate, since there was previously no written record of *why* this stays a stub beyond "Meta app review pending." **Done this branch** — comment added, no functional change needed since it was already correctly deferred.
- **Etsy clarification needed:** Yes, before ever implementing the real POST calls — see `ETSY_SUPPORT_QUESTIONS.md` Q3.
- **Classification: C** — Etsy-derived pathway already technically isolated (no live transfer); marketing claims corrected to say "connect your accounts" rather than implying active cross-posting of listings.

---

## Product Video Generator

- **Current behavior:** Accepts `image_urls` (typically Etsy-synced listing photo URLs, though technically any URL) as slideshow input; renders locally via ffmpeg; output stays local until (a) manually downloaded, or (b) explicitly attached to an Etsy listing via the existing media-job "replace video" flow (**writes back to Etsy itself**, not to a third party).
- **Etsy API-derived data:** Yes (source images, when the seller picks their own synced photos).
- **External services receiving data:** None — no Pinterest/Instagram auto-post of generated video found anywhere in the render pipeline.
- **Classification: A** — this is Etsy-photo-to-Etsy-video, not a third-party transfer, and stays fully in the "features that should remain enabled" list (explicitly named: "Videos through documented Etsy endpoints").

---

## Admin / Owner Console

- **Current behavior:** `require_superuser`-gated, no Etsy tokens/secrets in any response (verified by `tests/test_admin_panel.py` assertions).
- **Classification: A.**

---

## Registration / Terms Acceptance

- **Current behavior (before this branch):** No checkbox, no acceptance record at all.
- **Required correction:** Added unchecked required checkbox, backend enforcement, `terms_accepted_at`/`terms_version`/`privacy_version`/`acceptance_source` columns + migration + tests — **done this branch**, see `ETSY_PRODUCTION_READINESS.md` §2.
- **Classification: F → corrected.**
