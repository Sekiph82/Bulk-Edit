# Design Override — Listings (`/listings`)

> Overrides `design-system/MASTER.md` for the listings page only.

## Purpose

Primary data view. Sellers spend the most time here selecting listings for bulk operations. The grid must be fast, filterable, and easy to multi-select.

## Layout

```
[Nav]
[Toolbar: Search | Shop filter | State tabs | Sort | Column toggle | Sync button]
[Filter panel — collapsible, shows: price range, quantity, tags, has_variations]
[Listings table — full width]
[Pagination]
[Listing detail drawer — right side, opens on row click]
```

## Data Density

High. Tables with 8+ visible columns. Use compact row style (`py-2 px-4`).

## Table Columns (priority order)

1. Checkbox (select)
2. Thumbnail (48×48px, `loading="lazy"`, next/image)
3. Title (primary content, truncate at max-w-xs on small screens)
4. State (badge)
5. Price (formatted: `$XX.XX`, not raw cents)
6. Quantity
7. Has Variations (text: "Yes" / "—", not boolean)
8. Last Synced (relative date)

## Specific Copy Fixes

| Current | Fix |
|---|---|
| "Variations" column showing `true`/`false` | "Has Variations" column showing "Yes" / "—" |
| "price_amount" column header | "Price" |
| "last_synced_at" column header | "Last Synced" |
| "etsy_updated_at" column header | "Etsy Updated" |

## Filter Panel

Collapsible sidebar or top panel. Collapsed by default on mobile.
Fields: Price range (min/max), Quantity (min/max), Tags (text input), Has Variations (toggle), Section.

## Performance

- All thumbnails: `loading="lazy"` + `next/image`
- Pagination: 50 per page default, controls at bottom
- Table: `overflow-x-auto` wrapper, sticky checkbox column on mobile

## Saved Views

Feature is present. UI for saved views: a `<select>` or pill strip at top of filter panel. Not in toolbar to avoid clutter.
