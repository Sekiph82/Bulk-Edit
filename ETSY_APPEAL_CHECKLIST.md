# ETSY_APPEAL_CHECKLIST.md

**Status (2026-07-15):** all engineering fixes referenced by the original version of this checklist are complete and live in production — see `ETSY_FINAL_APPEAL_DRAFT.md` §B for the full, current, itemized list (it supersedes the old "Fixes to point to" section that used to live here). This file now holds only what's left: pre-submission owner actions. Retention scheduler is Option A, first run succeeded 2026-07-15 — see `ETSY_DATA_RETENTION.md` §2.

Use this before submitting the appeal for the "Banned" `bulk-edit-app` application.

## Before appealing (owner actions — none of these can be automated)

- [ ] Manually re-read `https://www.etsy.com/legal/api/` and `https://www.etsy.com/legal/trademarks/` in a browser (automated fetches are blocked with HTTP 403 — quotes used in the audit docs are best-effort from search snippets, not a verbatim re-read). Confirm the exact required trademark statement wording before citing it back to Etsy.
- [ ] Confirm whether Etsy sent a ban reason to a different email/inbox than expected (developer account email vs. shop owner email vs. spam folder) — re-check before assuming no reason was given.
- [ ] Log in to the Etsy Developer Console and check the app's current status page for any listed reason, review notes, or required-action banner beyond "Banned."
- [ ] Confirm the client_id (`7usvn9q6itlj6306sef64god`) and OAuth callback URL still match what's registered in the Etsy developer console.

## What NOT to claim in the appeal

- [ ] Do not claim the Etsy video-upload endpoint has been tested live — it has not (blocked by the ban itself). Say "implemented per documented endpoint shape, pending live verification."
- [ ] Do not claim account deletion has been tested end-to-end in production — it is unit-tested only in this session.
- [ ] Do not claim email delivery/verification is fully operational if the Resend domain-verification blocker from `HANDOFF.md` (2026-07-05 entry) is still open — check current state before saying so.
- [ ] Do not claim Listing Health Score / AI-powered marketing features are "Etsy-approved" — they are described accurately as pending Etsy clarification, with the Etsy-data AI pathway disabled by default.

## Draft submission checklist

- [ ] Use `ETSY_FINAL_APPEAL_DRAFT.md` §A as the appeal body (§G there is this checklist's newer, more complete twin — work through both) — do not write a new one from scratch that might omit the specific, concrete fixes it documents.
- [ ] Attach or link nothing that requires Etsy to create an account/log in — keep any evidence (screenshots, doc links) accessible without auth if possible.
- [ ] Ask explicitly and specifically what the ban reason was, even if it isn't answered — a documented ask matters for any future dispute.
- [ ] Do not create a new Etsy developer application while this one is under appeal — per this task's explicit instruction and because most marketplaces flag "create a new app to dodge a ban" as an aggravating factor.
