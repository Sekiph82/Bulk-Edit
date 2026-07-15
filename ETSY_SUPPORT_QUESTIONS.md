# ETSY_SUPPORT_QUESTIONS.md

**Status:** superseded as the appeal draft — use `ETSY_FINAL_APPEAL_DRAFT.md` for the actual message to send. **This file is kept anyway**, unmodified, because its Q1/Q2/Q3 numbering is cited by name in 5 production code comments as the pending-clarification pointer for real runtime gates: `apps/backend/app/core/config.py` (`ALLOW_ETSY_DATA_TO_AI`), `apps/backend/app/services/ai_tools.py`, `apps/backend/app/api/v1/listing_health.py`, `apps/frontend/lib/featurePages.ts`, `apps/frontend/components/marketing/EtsySeoSection.tsx`. Deleting or renumbering this file would break those references; updating the comments themselves is a code change, out of scope for a docs-only cleanup. If those comments are ever touched in a future code change, point them at `ETSY_FINAL_APPEAL_DRAFT.md` §F instead and retire this file then.

## Draft message to Etsy (developer@etsy.com, and/or the app-review contact if the ban notice provides one)

> Subject: Appeal + compliance questions — app "bulk-edit-app" (client_id 7usvn9q6itlj6306sef64god), status "Banned"
>
> Hello,
>
> Our application "bulk-edit-app" was recently marked "Banned" without an explanation email reaching us. We'd like to understand the specific reason so we can confirm it's resolved, and we've also proactively completed a full compliance audit and fixed several issues we found ourselves in case they contributed. Details below.
>
> **1. Could you tell us the specific reason our app was banned?** We have not received any notification explaining the decision.
>
> **2. AI processing of Etsy listing data:** Our app includes an optional AI-assisted listing-optimization feature (title/description/tag suggestions) that, when enabled, sends synced listing content (title, description, tags) to OpenAI or Anthropic to generate suggestions the seller must manually review and approve before anything is applied — nothing is auto-applied or auto-written to Etsy. We have disabled this Etsy-data pathway by default (behind a server-side flag, off unless explicitly authorized) pending your guidance. **Is sending Etsy listing content to a third-party AI provider for this kind of seller-facing suggestion feature permitted under the API Terms, and if so, are there conditions (e.g., data-handling requirements, required disclosures) we need to meet?**
>
> **3. Local scoring/analytics features:** We also compute a "Listing Health Score" — a deterministic, purely local calculation from the listing's own title length, tag count, photo count, and price (no external API call, no AI, no data leaves our servers) — shown only to the shop's own owner as a private in-app dashboard. **Does this kind of local, non-AI, seller-facing-only scoring feature require separate authorization, or is it treated the same as any other factual dashboard (listing count, price, status)?**
>
> **4. Cross-posting to Pinterest/Instagram:** We have a Pinterest/Instagram account-connection feature. We deliberately have not implemented the actual "post to Pinterest/Instagram" API call yet — it is fully stubbed and returns a "not yet available" response — specifically because we were unsure whether cross-posting synced Etsy listing content (title, photo) to a third-party marketing platform requires your authorization. **Can you confirm whether this would be permitted, and under what conditions, before we implement it live?**
>
> **5. Commercial access re-confirmation:** Our application has grown substantially since our original submission (bulk editing, AI tools, CSV import/export, dynamic pricing, scheduling, media/video tools). **Should we resubmit for a fresh commercial-access review given this scope, or is our existing grant still current?**
>
> We've corrected a real bug in our own code where we were storing the OAuth token type instead of the actual granted scope string (display-only issue, did not affect what was actually granted) and fixed our shop-disconnect flow so stored tokens are deleted immediately rather than only being marked inactive. We're also capping backup-snapshot retention at 30 days going forward.
>
> We'd appreciate any specific findings from your review so we can address them directly rather than guessing. Thank you.
>
> — [Owner name], Bulk Edit App (bulkeditapp.com)

## Updated Etsy application description (for the developer console, once appeal is resolved)

> Bulk Edit App is a seller-authorized listing management utility for Etsy sellers. Using Etsy's official Open API v3 and OAuth2 (PKCE), it lets a seller connect their own shop, synchronize their own listings, prepare bulk changes to titles, descriptions, tags, prices, quantities, variations, photos, and videos, review an exact before-and-after preview of every change, and explicitly confirm before anything is submitted to Etsy. Every write is preceded by a backup snapshot so changes can be reverted. The app also offers CSV import/export, scheduled seller-authorized updates (which only ever create drafts requiring separate manual confirmation — nothing is auto-applied), and optional AI-assisted listing-suggestion tools (suggestions only, always seller-reviewed, and the Etsy-data pathway to third-party AI providers is disabled unless Etsy has authorized it). The app does not process orders, payments, or buyer data, and requests only `listings_r`, `listings_w`, `shops_r`, and `profile_r` scopes.

## Open questions to track (not yet answered by Etsy)

1. Is Etsy-listing-content → third-party AI (OpenAI/Anthropic) permitted, and under what conditions? — blocks re-enabling `ALLOW_ETSY_DATA_TO_AI`.
2. Does the local, non-AI Listing Health Score require separate authorization or public-marketing restrictions?
3. Is cross-posting synced listing content to Pinterest/Instagram permitted? — blocks implementing the currently-stubbed share endpoints.
4. Does the app's current feature scope require a fresh commercial-access resubmission?
5. What was the actual ban reason? (asked directly; track the answer here once received)
