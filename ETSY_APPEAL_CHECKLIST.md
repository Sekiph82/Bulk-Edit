# ETSY_APPEAL_CHECKLIST.md

**Status (2026-07-16): appeal SUBMITTED by owner.** All engineering fixes referenced by the original version of this checklist are complete and live in production — see `ETSY_FINAL_APPEAL_DRAFT.md` §B for the full, current, itemized list. The pre-submission sections below are kept as a historical record of what was confirmed before sending; see "Post-submission checklist" below for what's active now. Retention scheduler is Option A, second consecutive successful run 2026-07-16 — see `ETSY_DATA_RETENTION.md` §2.

## Post-submission checklist (current)

- [ ] **Wait for Etsy's response.** Do not follow up or re-send unless a reasonable amount of time has passed with no response at all — check with the owner before any follow-up contact.
- [ ] **Do not submit a duplicate appeal.** One submission is in; sending another (or opening a new developer app) reads as an aggravating factor to most marketplaces' trust & safety teams.
- [ ] **Record the case/ticket number** here and in `ETSY_FINAL_APPEAL_DRAFT.md`'s submission-status header as soon as it's known (Etsy may or may not provide one).
- [ ] **Respond only to Etsy's specific questions** if/when they reply — don't volunteer new claims or re-open closed items; re-verify current production state (this repo's `PROJECT_STATUS.md`) before answering anything time-sensitive.
- [ ] **Do not enable `ALLOW_ETSY_DATA_TO_AI`** or any other Etsy-clarification-gated behavior until Etsy's response explicitly covers it.

---

## Historical: before appealing (owner-side manual actions — this repo cannot verify these were individually performed; the appeal has been submitted regardless, so treat this list as reference, not a confirmed record)

- [ ] Manually re-read `https://www.etsy.com/legal/api/` and `https://www.etsy.com/legal/trademarks/` in a browser (automated fetches are blocked with HTTP 403 — quotes used in the audit docs are best-effort from search snippets, not a verbatim re-read). Confirm the exact required trademark statement wording before citing it back to Etsy.
- [ ] Confirm whether Etsy sent a ban reason to a different email/inbox than expected (developer account email vs. shop owner email vs. spam folder) — re-check before assuming no reason was given.
- [ ] Log in to the Etsy Developer Console and check the app's current status page for any listed reason, review notes, or required-action banner beyond "Banned."
- [ ] Confirm the client_id (`7usvn9q6itlj6306sef64god`) and OAuth callback URL still match what's registered in the Etsy developer console.

## Historical: what the drafted appeal was written not to claim (verified against the draft text itself, not against what was actually sent)

- The draft in `ETSY_FINAL_APPEAL_DRAFT.md` does not claim the Etsy video-upload endpoint has been tested live — it says "implemented per documented endpoint shape, pending live verification."
- The draft does not claim account deletion has been tested end-to-end in production.
- The draft does not claim email delivery/verification is fully operational.
- The draft does not claim Listing Health Score / AI-assisted marketing features are "Etsy-approved" — it describes them as pending Etsy clarification, with the Etsy-data AI pathway disabled by default.

## Historical: draft submission checklist (reference — reflects the draft as prepared, not independently confirmed against what was actually sent)

- `ETSY_FINAL_APPEAL_DRAFT.md` §A was prepared as the appeal body.
- The draft attaches/links nothing that requires Etsy to create an account/log in.
- The draft explicitly asks what the ban reason was.
- No new Etsy developer application was created by this project while this one is under appeal.
