# Design Override — Media Editor (`/media`)

> Overrides `design-system/MASTER.md` for the media page only.

## Purpose

Bulk edit listing images. Add, replace, or delete images across multiple listings. Same safety chain as bulk edit.

## Layout

Same 3-panel pattern as bulk edit (listing selector left, operation config right, preview/results below).

## Specific for Media

Operation picker: show only implemented operations prominently.
- Add Image (implemented)
- Replace Image at rank (implemented)
- Delete Image at rank (implemented)

Deferred operations (do not show in current build):
- Reorder Images
- Replace Video
- Delete Video

If shown, mark them clearly as "Not available" — do not grey them out silently.

## Form Fields (conditional on operation)

**Add Image**: Image URL (text input), Rank (number, optional), Alt Text (text, optional)
**Replace Image**: Image URL (text input), Rank to replace (number, required)
**Delete Image**: Image URL or Rank to delete (either works)

## Backup Warning

Prominent info banner above apply button:
"A backup snapshot is created automatically before any change. You can view backups after applying."

Not a modal — inline info message (blue `bg-blue-50` style).
