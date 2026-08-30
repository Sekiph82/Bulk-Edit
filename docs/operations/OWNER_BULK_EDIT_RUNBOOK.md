# Owner Runbook — Safe Bulk Edit Testing

**Audience:** the shop owner (`sekiphayit1982@gmail.com`), running a live test against a real
connected Etsy shop. **Claude/Codex never performs any step in this runbook** — every write here
is a real Etsy API call and must be owner-initiated by clicking the actual button in the app.

## Before you start

- Confirm which shop is connected: Account → Connected Shops.
- Pick **one** low-stakes listing for the first test of anything new — not your best seller, not
  something with active orders.
- Have Etsy Shop Manager open in a second tab so you can compare before/after directly, not just
  trust the app's own result card.

## Safe single-listing test procedure

1. Go to `/bulk-edit`, select **exactly one** listing.
2. Make **one** field change (e.g. append a word to the title, or nudge the price by a small,
   reversible amount).
3. Click **Preview** — read the before/after diff. If anything looks wrong, stop here; nothing has
   been written yet.
4. Click **Apply**. A blocking overlay appears ("Writing changes to Etsy…") — leave the tab open
   until it clears. Don't click Apply again while it's showing (it's guarded against double-submit,
   but there's no reason to test that guard on purpose).
5. Check the result card: `success_count`/`failure_count`/`skipped_count`. For a single listing you
   expect `1/0/0`.
6. Switch to the Etsy Shop Manager tab, refresh, and confirm the field actually changed there —
   the app's own "success" claim is not itself the evidence.
7. Only after a single listing succeeds and is visually confirmed on Etsy, consider a small batch
   (3–5 listings), then larger.

## How to capture evidence

- Screenshot the app's result card (with counts visible).
- Screenshot the same listing(s) in Etsy Shop Manager, before and after.
- If anything failed, screenshot the failure reason shown in the app (never a raw Etsy error dump —
  if you see something that looks like a token, a header, or a stack trace, stop and report it as a
  bug rather than continuing).
- Save these into the dated log folder (`bulkeditapp logs/` or wherever the current session's
  evidence is being collected) if this is part of a formal verification round.

## When to stop

Stop immediately and do not retry if you see:
- A `403` mentioning a plan/upgrade message that doesn't match your actual plan (Billing page should
  agree with what Bulk Edit enforces — if they disagree, that's the exact bug class PR #104 fixed;
  report it, don't work around it).
- A `429` you weren't expecting on a single-listing test (the rate-limit guard should make this rare
  at low volume — see `RATE_LIMIT_RUNBOOK.md`).
- Any field changing on Etsy that you did **not** select in the app.
- The result card showing `success_count` higher than the number of listings you selected.

## How to revert

- From the Bulk Edit completion screen: click "View job details →" or "Open Magic Revert History →".
- From `/magic-revert`: find the job, click **Revert**, confirm in the modal. See
  `MAGIC_REVERT_RUNBOOK.md` for the full revert procedure and what each blocked-reason means.
- Revert only works once per apply job (a second attempt returns "already reverted," not a silent
  no-op) and only reverts items that actually succeeded in the original apply — skipped/failed items
  were never written, so there's nothing to revert for them.

## What not to click

- Don't click **Apply** more than once per intended change, even if the overlay seems slow — it's
  guarded, but a second click before the first click registers can still confuse your own mental
  model of what you tested.
- Don't click **Revert** on a job you're not sure about "just to see what happens" — it's a real
  Etsy write, not a preview.
- Don't disconnect/reconnect the Etsy shop mid-test — that's a separate, unrelated action that will
  make it harder to tell what actually caused any observed behavior.

## What errors mean

| You see | It means |
|---|---|
| `400` with a field-specific message | Etsy rejected the payload shape or a value — read the message, it's sanitized but specific. |
| `402` / "Upgrade your plan" | The usage/plan gate blocked you — check Account → Plan & Billing shows the same plan the error references. |
| `403` "not available on your current plan" (Magic Revert) | The effective-plan gate (M08.07) — expected on Free, unexpected on Pro/comp-Pro (report if unexpected). |
| `409` "already has a revert job" | Someone already reverted this apply job — check `/magic-revert` for the existing revert's result. |
| `429` | Etsy rate limit — see `RATE_LIMIT_RUNBOOK.md`. |
| `503` "Etsy integration is not configured" | Server-side config issue, not something you can fix by retrying — report it. |

## 429 handling

See `RATE_LIMIT_RUNBOOK.md` for the full explanation of the retry/backoff/pacing guard and what a
residual 429 (one that survives all retries) looks like in the UI.

---

## Safety checklist — read this before *every* live test below, not just the first one

- **Owner only.** Claude/Codex must never click Apply, Preview-then-Apply, or Revert. These steps
  are yours to run by hand, every time — a prior session's approval does not carry forward.
- **This is real production Etsy write risk.** Every Apply here changes real, live listing data on
  a real connected shop. There is no sandbox mode.
- **Preview first, always.** Never skip the Preview step, even on a batch you've run before.
- **Screenshot before AND after** — the app's result card, and the same listing(s) in Etsy Shop
  Manager. "The app said success" is not evidence on its own.
- **Confirm the revert, don't just trust it.** After clicking Revert, re-check Etsy Shop Manager the
  same way you checked the apply.
- **Stop on any failure.** If any item in a batch fails or behaves unexpectedly, stop — do not
  retry, do not continue to a larger batch, and do not proceed to a different field type until the
  failure is understood. Report it instead of working around it.
- **Never run a live variation apply unless you explicitly accept there is no one-click revert for
  it** (`TASKS.md` M15.04) — a variation write today can only be undone by manually re-editing the
  listing back on Etsy yourself, not by this app's Magic Revert.

## 3-listing small-batch test (price or title) — not yet owner-run

1. In `/listings`, pick 3 low-stakes listings (same guidance as the single-listing test above).
2. Go to `/bulk-edit`, select those 3, choose **one** field (price nudge or a reversible title
   suffix), Preview, read all 3 rows of the diff.
3. Apply. Expect `success_count: 3, failure_count: 0, skipped_count: 0`. Screenshot the result card.
4. Check all 3 listings on Etsy Shop Manager, not just one — a partial success (e.g. `2/1/0`) with
   only one screenshot checked is not a passed test.
5. Revert the job from `/magic-revert`, re-check all 3 listings restored correctly.
6. Record the result (pass/partial/fail, exact counts) in `TASKS.md` M04.04 and this session's log.

## 10-listing batch test (price or title) — not yet owner-run

Same procedure as the 3-listing test, scaled to 10 listings. This is meant to catch rate-limiting
or pacing issues that a 1-3 listing test is too small to surface — watch specifically for any `429`
in the result card even though the guard (`RATE_LIMIT_RUNBOOK.md`) should keep them rare. Record the
exact counts and whether any `429` occurred, retried, and succeeded vs. exhausted its retries.

## Non-price field batch test — not yet owner-run

Pick a **reversible** non-price field — appending/removing a short suffix on the title, or adding/
removing a single tag, are good choices specifically because they're trivially reversible even
without Magic Revert if something goes wrong. Run this at 3-listing scale first, same procedure as
above. The goal is to confirm batch-scale writes work correctly for a field other than price (which
has already been extensively tested) before broader beta relies on it.
