# Design Override — Variation Editor (`/variations`)

> Overrides `design-system/MASTER.md` for the variations page only.

## Purpose

Bulk edit variation-level attributes (price, quantity, SKU, availability) across listings that have variations. The listing selector must only show listings with `has_variations: true`.

## Layout

Same 3-panel pattern as bulk edit (listing selector left, operation config right, preview/results below).

## Listing Selector

Filter: only `has_variations: true` listings. If no variation listings found, show empty state:
"No listings with variations found. Sync your shop or check that your listings have variations enabled on Etsy."

## Operation Picker

8 operations in a `<select>`. Labels must be human-readable (no snake_case):

| Code | Display Label |
|---|---|
| `set_variation_price` | Set Price |
| `adjust_variation_price_percent` | Adjust Price by % |
| `adjust_variation_price_fixed` | Adjust Price by Amount |
| `set_variation_quantity` | Set Quantity |
| `adjust_variation_quantity_fixed` | Adjust Quantity by Amount |
| `set_variation_sku` | Set SKU |
| `replace_variation_sku_text` | Find & Replace in SKU |
| `set_variation_availability` | Set Availability |

## Selector Fields

Optional. Shown below operation fields.
Label: "Target specific variation only (optional)"
- Property name (e.g. Size)
- Value name (e.g. Large)
- Helper text: "Leave blank to apply to ALL variations in each listing"

## Preview Table

Before/After columns show variation-level data, not listing-level:
- Property: Value (e.g. Size: Large)
- Price (formatted as currency)
- Quantity
- SKU

## Safety Note

Same backup warning as media page:
"A backup snapshot is created before each Etsy write. Changes can be reviewed in the backups tab."
