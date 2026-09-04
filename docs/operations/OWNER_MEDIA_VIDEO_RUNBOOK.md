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
3. Choose a template/aspect ratio/duration.
4. **Read the pre-generation safety panel** above the Generate button — it states generation creates a local MP4 only, does not upload to Etsy, makes no Etsy listing changes, and that Upload to Etsy is not enabled yet. Screenshot it.
5. Click **Generate Video** → a lightweight confirm modal appears ("Generate local MP4? … It will not upload to Etsy"). Confirm the copy, then click Generate.
6. Wait for the render to complete (status badge updates automatically).
7. Confirm the **result screen** — the completed-render card shows "Your video was generated," the render details grid (render id, created, status, template, source, aspect ratio, duration, photo count), the Etsy-ready checklist, the **result-state owner checklist** (video generated / review / download / upload gated-not-enabled / no Etsy upload occurred), and the review warning. Screenshot it.
8. **Do not skip this:** click "Download to your computer" and actually watch the downloaded MP4 before doing anything else with it. Expected: the browser saves `product_video_<id>.mp4`.
9. Confirm the **Upload to Etsy** button is present but disabled — clicking it opens a modal saying upload is coming after owner-approved live testing, directs you to download + upload via Etsy's editor, and confirms nothing is sent to Etsy. Screenshot the gate modal.
10. Check the **Recent Videos** section — your new render should appear with the correct template, source, photo count, a working Download link, and the same gated Upload to Etsy affordance. Failed renders show a clear error and no download/upload actions.
11. The app explicitly does **not** upload this video to Etsy for you — publish it manually through Etsy's own listing editor if you're satisfied with it.

**Evidence to capture:** safety-panel screenshot, confirm-modal screenshot, result-screen screenshot, the downloaded MP4 filename, gate-modal screenshot.

**Stop conditions:** render stuck in rendering far beyond expected, a failed render with an unclear error, any UI text implying the video was uploaded/published to Etsy, or the Upload to Etsy button being clickable/enabled → stop and report; none of these should happen. No Etsy upload occurs at any step of Part 2.

### Part 2b — In-app preview + branding options owner check (M13.05B, no upload)

Added 2026-09-03. Still never touches Etsy.

**In-app video player:**
1. On a completed render's result card, an embedded video player appears — play it. The video plays inside the browser (it is fetched locally, never from Etsy).
2. Confirm the **result checklist** updates: "Review the video" checks once you play; "Download to your computer" checks once you click Download.
3. In **Recent Videos**, click **Preview** on a completed row — the same player opens in a modal (it does not start a second render). Close it.
4. Expected fallback: if a file is missing, the card shows "Preview unavailable. Download the video to review it." — not a crash.

**Branding options (preview-only this release):**
5. Open the **Branding options** card. Confirm it clearly reads "preview-only in this release — not yet rendered into the MP4, never uploaded to Etsy," and "Branding overlay rendering is coming soon."
6. Enter a logo URL (a small logo preview appears), headline, slogan, outro, CTA; pick logo position, text placement, brand color. Confirm the character counters cap input (60/80/80/30) and the branding summary reflects your choices.
7. Confirm nothing about branding uploads or publishes anything — it is form-state only in this release.

**Evidence to capture:** in-app player screenshot (mid-play), checklist showing Review + Download checked, Recent Videos Preview modal screenshot, Branding options card screenshot.

**Stop conditions:** any branding UI implying it will upload/publish to Etsy, any player attempt to reach Etsy, or the Upload button becoming enabled → stop and report. No Etsy upload at any step.

### Part 2c — PR #131 remediation recheck (M13.05C, no upload)

Added 2026-09-04, after PR #130's owner check found the in-app player didn't play and dashboard onboarding regressed.

> **Browser preview vs. download are two different tests — check both.** Download success does NOT prove the in-app player works. Two separate real bugs were found and fixed here:
> 1. **CSP `media-src` gap** (PR #132): `<video>` blob: URLs were blocked; fixed with `media-src 'self' blob:`.
> 2. **Full-range pixel format** (PR #134, the actual player blocker): the generated MP4 was `yuvj420p` (full-range), which browsers refuse to decode in `<video>` though Windows plays it. Fixed by forcing limited-range `yuv420p` in the render.
>
> **The pixel-format fix only applies to NEW renders.** To recheck: **hard-refresh**, **generate a new video**, then (a) press play in the result-card player, (b) press play in the Recent Videos Preview modal, (c) download and open the file, (d) confirm the "Preview could not load" fallback does NOT appear. If a *new* render still fails, the on-screen **"Reason:"** line (media error code / fetch status) names the exact cause — screenshot it.

**Dashboard onboarding:**
1. Open `/dashboard`. If the "Get started" card still shows, confirm **"Try bulk edit" is checked** and it reads **3/3** (the card auto-hides once all three are done, which is also correct). This now uses durable all-time evidence (any past successful bulk edit, even reverted ones), not the monthly usage counter — so it must not regress after a new billing month.

**In-app player (must now play):**
2. Open a completed render's result card → the embedded player should **load and actually play** the video in the browser (not a black box).
3. Confirm "Review the video" checks **only after** you press play.
4. Recent Videos → **Preview** → the modal player should load and play the same video.
5. If a player ever shows "Preview could not load," Download still works and the MP4 still plays locally — report it, but it should not happen for a healthy render.

**Branding text render:**
6. In Branding options, note it now says text branding **will be rendered into the MP4**, logo is **preview-only**.
7. Enter a headline/slogan/CTA/outro, Generate, then preview the new MP4 in the player → confirm the **text actually appears burned into the video**.
8. The result card's "Branding" line should read "✓ Text branding rendered into this MP4" (or, if the server has no font, a truthful "not rendered" — report that case). Logo shows "preview-only, not rendered."

**Evidence to capture:** dashboard 3/3 screenshot, player mid-play screenshot, branded-video preview screenshot, result-card branding-status screenshot.

**Stop conditions:** player still not playing after this deploy, dashboard still 2/3 with a real prior bulk edit, branding text claimed rendered but not visible in the MP4, or any Upload-to-Etsy enablement → stop and report. No Etsy upload at any step.

## Part 3 — Owner-only video upload test plan (future, owner-approved live write)

**Status: NOT yet enabled.** The Video Generator's "Upload to Etsy" button is a disabled placeholder. This plan is the procedure to follow *if and when* the owner decides to build/enable a live generated-video upload path. Claude/Codex must never run any step of this — it is owner-initiated only.

**Prerequisites**
- A dedicated **sacrificial test listing** — never a high-value or best-selling listing on the first run.
- The listing's current media state known and backed up (screenshot Etsy Shop Manager before anything).
- A generated test video already produced and **downloaded first** (Part 2), reviewed and confirmed correct.

**Procedure (owner)**
1. Screenshot the listing's current video/media state in Etsy Shop Manager (before-state).
2. Choose **Download to your computer** first — always have the file locally before any upload attempt.
3. Only if explicitly approving a live write: proceed to the upload path (currently `/media` → Add Video for a listing with no existing video; Replace Video remains gated by `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED` and needs the Part 1 flag procedure).
4. Screenshot the upload confirmation modal before confirming.
5. Confirm, then capture the item-level result (job id, success/failure/skipped counts, any `error_message`).
6. Screenshot the result screen, then screenshot the listing in Etsy Shop Manager (after-state) and compare.

**Revert / restore limitations**
- Etsy allows exactly one video per listing. **Video restore does not exist** — the backup only stores an Etsy CDN URL, not a re-uploadable local file. If you replace or delete a video you cannot self-recover through the app; you must re-upload manually.
- Because of this, prefer **Add Video** (additive, to a listing with no video) over Replace Video for any first live test.

**Stop conditions**
- Any unexpected error, wrong listing, or wrong count → stop, do not retry blindly, capture evidence.
- Never test on a high-value listing first.
- Never enable a live upload path or `MEDIA_DESTRUCTIVE_ACTIONS_ENABLED` unless you are actively running this plan and ready to accept a live Etsy write.

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
