# Owner Runbook — Rate Limit (429) Handling

**Audience:** the shop owner, understanding what happens when a Bulk Edit apply, Magic Revert, or
Variation write hits Etsy's rate limit, and what to do about it.

## How the guard works (already built, PR #102)

Two separate mechanisms, working together:

1. **Per-shop write pacing** (`sleep_before_etsy_write()`) — before *every* write call to a given
   shop, the backend waits at least `ETSY_BULK_WRITE_DELAY_MS` (currently **1100ms**) since the last
   write to that same shop. This is what keeps a fast loop over many listings from outrunning Etsy's
   limit in the first place.
2. **Per-call retry with backoff** (`_request_with_retry()`) — if a single write call still gets a
   `429` despite the pacing gate, it's retried automatically up to `ETSY_RETRY_MAX_ATTEMPTS`
   (currently **3**) times, honoring Etsy's `Retry-After` header when present, with jitter otherwise.

Both apply transparently to Bulk Edit apply, Magic Revert, and Variation apply — none of them needed
separate rate-limit code, since they all route through the same shared write primitives
(`patch_etsy_listing`, `apply_single_listing_price_quantity`, `etsy_variation_write.py`'s functions).

## What you'll actually see

- **Normal case:** nothing — the pacing gate means most batches never hit a 429 at all. You won't
  see any indication the guard even ran.
- **A single call gets 429, retry succeeds:** also invisible to you — the item still shows
  `success` in the result card, just took a bit longer.
- **A call gets 429 on every retry (all 3 attempts exhausted):** that item shows `failed`, with a
  message like *"Etsy returned HTTP 429: Exceeded per second rate limit. Retried 3/3 times; try again
  later."* — this is the one case that surfaces to you directly.

## What to do if you see a residual 429 failure

1. **Don't immediately retry the exact same batch** — if Etsy's limit is currently saturated (e.g.
   from a very large or very fast batch, or another process hitting the same shop), retrying
   instantly just repeats the same failure.
2. **Wait a minute or two**, then retry only the failed item(s) — not the whole batch, since the
   successful items already wrote and don't need to be touched again.
3. **If it keeps happening on small batches** (a handful of listings, not hundreds) — that's not
   expected behavior at the current pacing rate; report it rather than continuing to retry, since it
   may indicate the pacing gate isn't engaging correctly for some reason.
4. **For a genuinely large batch** (dozens+ listings) — some residual 429s are more plausible even
   with the guard; the safe move is smaller batches (the size progression in
   `OWNER_BULK_EDIT_RUNBOOK.md`: one listing, then a handful, then larger) rather than one huge batch
   on the first live test of anything new.

## Reading the diagnostics safely

The failure message you see is already sanitized — no token, no `Authorization` header, no raw Etsy
response body. If you ever see something in an error message that looks like it could be a
credential or an internal header value, stop and report it as a bug (it would mean the sanitization
itself has a gap) rather than sharing it further.

## Related

- `OWNER_BULK_EDIT_RUNBOOK.md` — general safe-testing procedure, batch-size progression.
- `MAGIC_REVERT_RUNBOOK.md` — the same guard applies to revert writes.
- `DECISIONS.md` (2026-08-28 entry) — the architectural reasoning for why pacing and retry are two
  separate mechanisms, and why pacing is scoped only to write entry points, not general reads.
