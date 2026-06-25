# Design Override — Bulk Edit (`/bulk-edit`)

> Overrides `design-system/MASTER.md` for the bulk edit page only.

## Purpose

Primary bulk editing workflow. Users select listings, configure field changes, preview all changes, and apply to Etsy. Safety is the #1 design concern — the flow must make it impossible to apply without seeing a preview.

## Layout

```
[Nav]
[Page heading: Bulk Edit]
[Two-column: Listing selector (left 1/3) | Operation config (right 2/3)]
[Preview table — full width, below columns]
[Apply button — bottom of preview, only visible after preview generated]
[Results panel — below apply, after job completes]
[Job history — collapsible, bottom]
```

## Listing Selector

Left panel. Compact, scrollable.
- Search input at top
- Checkbox per listing
- Thumbnail + title (2 lines max)
- Selected count shown below list

## Operation Configuration

Right panel. Focuses user's attention on one operation at a time.

Fields visible depend on field type:
- text fields: `Set to`, `Append`, `Prepend`, `Find & Replace`
- number fields: `Set to`, `Add`, `Subtract`, `Multiply by %`
- array fields (tags, materials): `Add item`, `Remove item`, `Replace item`
- bool fields: `Set to true/false`

## Preview Table

Full-width below operation config. Shows per-listing before/after diff.
- Status badge per row (valid/warning/invalid)
- Before value (truncated)
- After value (highlighted change)
- Validation message if warning/invalid

## Apply Flow

1. User clicks "Preview Changes" → preview table appears
2. User reviews — invalid rows are highlighted red
3. If any invalid: "Cannot apply" message shown, apply button hidden
4. If all valid or warning only: "Apply Changes" button appears
5. Click → confirm modal with "Type APPLY to confirm"
6. Apply executes → results table replaces preview table

## Session Management

Session status badge in page heading area. Sessions are preserved between page loads (visible in job history).
