# Design Override — Dashboard (`/dashboard`)

> Overrides `design-system/MASTER.md` for the dashboard page only.

## Purpose

Home base for authenticated users. A jumping-off point to all active features. Fast to scan and navigate. Not a data dashboard — no metrics, no charts in current scope.

## Layout

Top nav → page heading → feature quick-links grid → quick-action strip

```
[Nav]
[h1: Dashboard] [subtitle: Welcome, email]
[Feature Grid — 2 or 3 columns, active features only]
[Quick Links strip — 4 links: Shops, Listings, Pricing, Billing]
```

## Feature Grid

Show only working features. Never show disabled/greyed-out cards for future features.

Current active features:
- Etsy Shops (`/shops`)
- Listings (`/listings`)
- Bulk Edit (`/bulk-edit`)
- Media Editor (`/media`)
- Variation Editor (`/variations`)
- Pricing (`/pricing`)
- Billing (`/billing`)

Card style: interactive card from MASTER.md (hover:border-indigo-300). No emoji icons — use SVG (Heroicons).

## What to Remove

- All `href: null` cards (disabled roadmap items)
- "Sprint 13 — AI Tools" card
- "Magic Revert — Sprint 9" card (revert is integrated into bulk-edit, not a separate page)
- "API Endpoints" debug section at bottom
- Emoji icons on all cards

## Typography

- Page heading: `text-2xl font-bold text-gray-900`
- Subtitle: `text-gray-500 mt-1 text-sm`
- Card heading: `font-semibold text-gray-800`
- Card subtext: `text-sm text-gray-500`

## Icons

Replace emoji with Heroicons SVG (outline, 20px):
- Shops: `LinkIcon`
- Listings: `ViewColumnsIcon` or `TableCellsIcon`
- Bulk Edit: `PencilSquareIcon`
- Media: `PhotoIcon`
- Variations: `AdjustmentsHorizontalIcon`
- Pricing: `CreditCardIcon`
- Billing: `BanknotesIcon`

## Anti-patterns for this page

- No disabled roadmap cards
- No API endpoint lists
- No sprint labels
- No debug panels
- No emoji icons
- No metric cards (no "X listings synced" counters unless live data)
