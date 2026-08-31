# Owner Runbook — Media Restore & Video Generator Testing

**Audience:** the shop owner, testing media backup/restore and the Product Video Generator against a real connected Etsy shop or real synced data.
**Claude/Codex never runs a live media replace/delete/restore, never generates then uploads a real video, and never enables `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED`** — every action in this runbook that touches Etsy is owner-initiated only.

## Current state (2026-08-31, M13.04/M13.05)

- `add_image`/`add_video` (Media page, `/media`) are live and enabled — purely additive, nothing existing is ever destroyed.
- `replace_image`/`delete_image`/`replace_video`/`delete_video` are **disabled**, both in the UI (greyed-out dropdown option) and now the backend (`POST /bulk-edit/media/jobs` returns `403` for these operation types). A `ListingMediaBackupSnapshot` is still created before every write that does run, but the disabled operations themselves cannot be triggered at all right now — not through the UI, not through a direct API call.
- A real image-restore path now exists (`restore_images` job type, `POST /bulk-edit/media/backups/{id}/restore`) but is gated behind the same `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED` flag (default `False`) — it will also return `403` until an owner explicitly decides to test it live.
- Video restore does **not** exist — only images can be restored from a backup.
- The Product Video Generator renders real MP4s locally (ffmpeg) and never auto-uploads to Etsy under any circumstance. Uploading a generated video to a listing is a separate, explicit action (Add Video / Replace Video on `/media`), itself gated by the same destructive-actions flag for the replace case.

## Current verified state (2026-08-31, post PR #126 owner visual check)

**UI/copy visual check completed by the owner** (production screenshots of `/media` and `/video-generator`) — this confirms the pages render and every truthfulness claim below actually matches what the UI shows. It does **not** substitute for any of the live tests in Part 1/Part 2 below.

- `/media`: listing selector, Job History ("No media jobs yet" — expected, no live job has run), and the **Backups & Restore** section ("No backups yet," exact copy "Restore infrastructure implemented — disabled until owner-verified against a live listing") all confirmed rendering correctly. Operation dropdown confirmed: Add Image/Add Video available; Replace Image/Delete Image/Replace Video/Delete Video all reading "disabled until restore is owner-verified."
- `/video-generator`: no-auto-upload banner, render form, and empty **Recent Videos** section (correct copy) confirmed rendering correctly. The "Select from a listing's synced photos" flow was exercised end-to-end (a listing's 10 synced photos loaded, thumbnails and URLs populated correctly) with **Generate not clicked**.
- **No live media action performed.** No replace, delete, restore, or upload was run.
- **No live video generation performed.** No render was triggered, no video was created or downloaded.
- `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED` **must remain `False`** until the owner explicitly initiates the Part 1 procedure below — this visual check is not that authorization.

## Part 1 — Media restore (owner-only, requires flag enabled)

This section only applies once you have decided to test the restore path live. Until then, `/media`'s "Backups & Restore" section is read-only — you can see what backups exist and what their restore status is, but clicking Restore will show a clear "disabled" message.

### Before enabling `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED`

1. Confirm you have at least one real `ListingMediaBackupSnapshot` to test against — one is created automatically before any `add_image`/`add_video` write, or ask for a throwaway test write to generate one.
2. Pick a **single, low-stakes listing** for the first test — ideally not your best-selling item.
3. Screenshot the listing's current photos in Etsy Shop Manager, in order, before doing anything.

### Enabling the flag

This is a production environment variable change (`MEDIA_DESTRUCTIVE_ACTIONS_ENABLED=true` on `bulk-edit-prod-api`), not an in-app toggle — ask for it to be set only when you are ready to test immediately, and ask for it to be reverted back to `false` right after the test, whether it succeeds or fails.

### Safe procedure

1. Open `/media`, scroll to **Backups & Restore**.
2. Find the backup for your chosen test listing. Confirm the image count shown matches what you screenshotted.
3. Click **Restore**. This creates a pending `restore_images` job.
4. The job must still be **applied** to actually run (same two-step pattern as every other media job) — do this from the Job History section, "Apply" on that job.
5. Watch the result: `success_count`/`failure_count`/`skipped_count`, and the item-level error message if any.
6. Compare the listing's photos in Etsy Shop Manager against your before-screenshot — order and content should match what the backup had.
7. Send back: the job id, the result counts, and a screenshot of the listing's photos after restore.

### Stop conditions

- If the backup's image count looks wrong (too few/many) before you even click Restore — stop, do not proceed, report it.
- If the restore result shows any `failure_count > 0` — stop, do not retry, capture the item-level error message and report it. A partial failure here means the listing was already deleted-from but the re-upload didn't fully complete — Etsy Shop Manager is the source of truth for the listing's actual current state, not the app's own success claim.
- Never ask for the flag to be left `true` "just in case" — it should be `false` except for the exact window of an active, deliberate test.

## Part 2 — Video Generator review/download/manual-publish (no Etsy write required)

This part never touches Etsy and can be tested any time, with no flag and no risk.

1. Open `/video-generator`, pick "Select from a listing's synced photos," choose a listing.
2. Confirm the selected-photo preview grid shows the right photos in the right order.
3. Choose a template/aspect ratio/duration, click Generate.
4. Wait for the render to complete (status badge updates automatically).
5. **Do not skip this:** click "Download MP4" and actually watch the video before doing anything else with it.
6. Check the **Recent Videos** section — your new render should appear with the correct template, source, photo count, and a working Download link.
7. The app explicitly does **not** upload this video to Etsy for you — publish it manually through Etsy's own listing editor if you're satisfied with it.

### If you also want to test uploading the generated video to a listing (Add Video)

Add Video is **not** gated by `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED` (it's additive — the listing must not already have a video, or it fails cleanly rather than silently replacing one). This can be tested without the flag:

1. On `/media`, choose Add Video, select your completed render from the "Generated" tab.
2. Pick a listing with **no existing video** (Etsy allows exactly one video per listing).
3. Apply, confirm the item-level result, then check the listing in Etsy Shop Manager.

Replace Video (for a listing that already has one) IS gated the same way as the other destructive operations — follow Part 1's procedure for that.

## Evidence to capture, every time

- Before-state screenshot (Etsy Shop Manager) for anything destructive.
- The exact job id and result counts (`success_count`/`failure_count`/`skipped_count`).
- Any item-level `error_message`.
- After-state screenshot (Etsy Shop Manager), compared against the before-state.

## What Claude/Codex will never do here

- Never call a live Etsy media upload/delete/replace endpoint.
- Never call a live Etsy video upload endpoint.
- Never set `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED=true`.
- Never generate a video expecting it to be reviewed as "done" without the owner actually watching it first.
- Never auto-upload a generated video to Etsy, or imply that happened.
- Never mark a destructive-media or video-generation task owner-verified without the owner actually having performed it.
