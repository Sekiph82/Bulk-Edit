# Owner Runbook — Safe Magic Revert Testing

**Audience:** the shop owner, running a live Magic Revert against a real connected Etsy shop.
**Claude/Codex never clicks Revert** — this is always a real Etsy write and must be owner-initiated.

## What Magic Revert actually does

Restores a listing's title/description/tags/materials/etc. (via a PATCH) and, where the snapshot
includes it, price/quantity (via a fetch-patch-put on the inventory endpoint) back to the values
captured in the backup snapshot taken immediately before the original Bulk Edit apply wrote to that
listing. It does **not** revert media (photos/video) or variation-level changes — those are separate,
currently-unimplemented revert paths (see `TASKS.md` M13.04, M15.04).

## Two ways to revert

1. **Right after an apply** — the Bulk Edit completion screen still shows the immediate in-flight
   Magic Revert button for the job you just ran.
2. **From history** — `/magic-revert` lists every past apply job for your org, not just the most
   recent one. Each row shows whether it's currently revertible and why not if it isn't.

## Reading the History page

| `can_revert` / label | Meaning |
|---|---|
| "Revert available" (green) | Job completed, has ≥1 successful item, no existing revert, and your plan allows Magic Revert. Clicking Revert will actually attempt a write. |
| "Already reverted" | A revert job already ran for this apply job (successfully or partially) — clicking Revert again returns `409`, it does not create a second attempt. |
| "Revert in progress" | A revert is currently running for this job — wait for it to finish before doing anything else with it. |
| "No successful items to revert" | The original apply had zero successes (all failed/skipped) — there's nothing to restore. |
| "Apply job did not complete" | The original apply itself failed or is still running — not eligible. |
| "Magic Revert is not available on your current plan" | The M08.07 plan gate — expected on Free, should never appear on Pro or a comp-granted account (if it does on Pro, that's a bug, report it). |

Expand a row ("View details") to see the item-level apply results before deciding to revert.

## Safe procedure

1. Pick a job you *want* reverted — ideally the same single-listing test job from
   `OWNER_BULK_EDIT_RUNBOOK.md`.
2. Click **Revert** on that row. A confirmation modal appears stating exactly how many listings will
   be restored and that this writes back to Etsy.
3. Confirm. A blocking overlay appears ("Reverting Etsy listings…") — leave the tab open until it
   clears, same as Apply.
4. Check the result: `success_count`/`failure_count`/`skipped_count`.
5. Confirm in Etsy Shop Manager that the listing(s) actually returned to their pre-apply state — the
   app's own success claim is not itself the evidence.

## When to stop

- If the confirmation modal's stated listing count doesn't match what you expect — stop, don't
  confirm, investigate first.
- If a revert's result shows `failure_count > 0` — check the item-level detail (expand the row) for
  the safe failure reason before retrying anything. A partial failure means text fields may have
  reverted while price/quantity didn't (or vice versa) — Etsy Shop Manager is the source of truth for
  what state the listing is actually in, not the local app record, until the next sync.
- Never attempt to "force" a revert that's blocked — every block reason maps to a real backend rule
  (see the table above); working around it client-side isn't possible and isn't the fix if the
  reason seems wrong (report it instead).

## What each error means

| You see | It means |
|---|---|
| `404` "Apply job not found" | Wrong org, wrong id, or the job genuinely doesn't exist — this also fires (correctly, by design) if you try to revert another org's job by guessing an id; it never confirms whether that id exists elsewhere. |
| `400` "must be completed... to revert" | Job status isn't `completed`/`completed_with_errors` yet. |
| `400` "no successfully changed items" | Zero-success guard — nothing to revert. |
| `409` "already has a revert job" | Duplicate-revert guard — see the "Already reverted" row state above. |
| `403` "not available on your current plan" | Plan gate — see the table above. |
| `429` during the revert write itself | Same rate-limit guard as Apply — see `RATE_LIMIT_RUNBOOK.md`. |

## Evidence to capture

Same as `OWNER_BULK_EDIT_RUNBOOK.md`: the app's result card, the Etsy Shop Manager before/after, and
the item-level detail if anything failed. Save into the dated log folder if part of a formal
verification round.
