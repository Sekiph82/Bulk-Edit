# ETSY_APPEAL_CHECKLIST.md

Use this before submitting an appeal for the "Banned" `bulk-edit-app` application.

## Before appealing

- [ ] Manually re-read `https://www.etsy.com/legal/api/` and `https://www.etsy.com/legal/trademarks/` in a browser (this session's fetcher was blocked with HTTP 403 — quotes used in the audit docs are best-effort from search snippets, not a verbatim re-read). Confirm the exact required trademark statement wording and the exact caching/freshness numbers before citing them back to Etsy.
- [ ] Confirm whether Etsy sent a ban reason to a different email/inbox than expected (developer account email vs. shop owner email vs. spam folder) — re-check before assuming no reason was given.
- [ ] Log in to the Etsy Developer Console and check the app's current status page for any listed reason, review notes, or required-action banner beyond "Banned."
- [ ] Confirm this branch's changes are merged/deployed to production *before* appealing — Etsy reviewers may re-check the live app and live site, not just the code.

## Fixes to point to in the appeal (this branch)

- [ ] OAuth granted-scope storage bug fixed (was storing token_type, not scope) — `ETSY_OAUTH_SCOPES.md`.
- [ ] Etsy-derived listing content is no longer sent to any AI provider by default — new `ALLOW_ETSY_DATA_TO_AI` flag, off unless explicitly authorized — `ETSY_FEATURE_MATRIX.md` §AI Tools.
- [ ] Shop disconnect now deletes stored tokens immediately (Privacy Policy claim is now true) — `ETSY_DATA_RETENTION.md` §3.
- [ ] Snapshot/backup data capped at 30-day retention with scheduled cleanup — `ETSY_DATA_RETENTION.md` §2.
- [ ] Public site no longer describes the product as pre-launch/founding-access while requesting production write scopes — see Website corrections in the final report.
- [ ] Full required trademark disclaimer added near the Connect Etsy Shop button (was previously abbreviated) — `ETSY_COMPLIANCE_AUDIT.md` §4.
- [ ] Registration now requires explicit Terms/Privacy acceptance, recorded with version + timestamp.
- [ ] No scraping, no unofficial/legacy Etsy API access, no browser automation against etsy.com anywhere in the codebase (positively confirmed, not just absence of evidence) — `ETSY_COMPLIANCE_AUDIT.md` §3.
- [ ] OAuth scopes requested are minimal (`listings_r listings_w shops_r profile_r`) — no transaction, buyer-email, or billing scopes requested.

## What NOT to claim in the appeal

- [ ] Do not claim the Etsy video-upload endpoint has been tested live — it has not (blocked by the ban itself). Say "implemented per documented endpoint shape, pending live verification."
- [ ] Do not claim account deletion has been tested end-to-end in production — it is unit-tested only in this session.
- [ ] Do not claim email delivery/verification is fully operational if the Resend domain-verification blocker from `HANDOFF.md` (2026-07-05 entry) is still open — check current state before saying so.
- [ ] Do not claim Listing Health Score / AI-powered marketing features are "Etsy-approved" — they are described accurately as pending Etsy clarification, with the Etsy-data AI pathway disabled by default.

## Draft submission checklist

- [ ] Use the draft message in `ETSY_SUPPORT_QUESTIONS.md` (or a shortened version) as the appeal body — do not write a new one from scratch that might omit the specific, concrete fixes above.
- [ ] Attach or link nothing that requires Etsy to create an account/log in — keep any evidence (screenshots, doc links) accessible without auth if possible.
- [ ] Ask explicitly and specifically what the ban reason was, even if it isn't answered — a documented ask matters for any future dispute.
- [ ] Do not create a new Etsy developer application while this one is under appeal — per this task's explicit instruction and because most marketplaces flag "create a new app to dodge a ban" as an aggravating factor.
