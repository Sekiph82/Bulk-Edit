# Product UI Direction — Bulk-Edit

## Positioning

Bulk-Edit is a professional tool for Etsy sellers. The UI must feel like a productivity tool, not a marketplace. Comparable tone: Shopify admin, Linear, Stripe dashboard. Not Etsy's own UI. Not a startup landing page.

## Target User Mental Model

The seller arrives with a task: "I need to add '2026 handmade' to the title of every active listing in my Ceramics section." They expect:

1. A listing grid they can filter and select from.
2. An operation picker that's self-explanatory.
3. A preview showing exactly what will change before anything touches Etsy.
4. A clear apply button with a single confirmation step.
5. A result summary with per-listing pass/fail.
6. The ability to undo.

The UI must serve this flow without detours, modals they didn't ask for, or decorative elements that slow down scanning.

## Register

Product (tool-first). Every surface is in service of a task, not a brand expression.

## Information Hierarchy

### Primary: the listing grid

Listings are the center of gravity. The grid must be:
- Fast to scan (thumbnail, title, price, quantity, state at a glance)
- Easy to filter (by shop, state, tag, price range, variation flag)
- Easy to multi-select (checkbox per row, select-all, select-page)
- Sortable by all visible columns

### Secondary: operation configuration

Operations are contextual. After selection, the user picks what to change and by how much. This should feel like a focused form, not a wizard with five steps.

### Tertiary: preview and apply

Preview is a read-only table. It must not be dismissible without clear intent. Apply requires explicit confirmation for destructive or large-scale operations.

## Page-by-Page Direction

### Homepage (`/`)

Current state: developer placeholder with sprint badge, API endpoint, "Auth coming in Sprint 2."

Direction: Professional marketing landing. Hero with headline + subheadline + single CTA. Brief feature highlights. No sprint labels. No API endpoints. No debug cards.

### Dashboard (`/dashboard`)

Current state: emoji-heavy feature grid, disabled "coming soon" cards, API endpoint debug panel.

Direction: Minimal command center. Active features as clean links. No disabled/greyed-out roadmap cards. No emoji icons. No API debug panel. Maybe a recent activity feed if data is available, or just direct feature links.

### Listings (`/listings`)

Current state: functional data grid. Good foundation.

Direction: Clean up column headers (remove dev-speak). Ensure filter panel is collapsible. Table rows should be clickable. Variation flag should say "Has variations" not a boolean. Price should format as currency.

### Bulk Edit (`/bulk-edit`)

Current state: functional but dense.

Direction: Two-column layout — listing selector left, operation configuration right. Preview below full-width. The modal for confirmation should be single-purpose (not a kitchen sink).

### Media (`/media`)

Current state: functional. Has operation picker, confirm modal.

Direction: Add empty state when no listings found. Replace emoji operation labels with text only. Compact the form fields.

### Variations (`/variations`)

Current state: functional (Sprint 12).

Direction: Same as media — compact, no emoji, clear selector, empty state.

### Shops (`/shops`)

Direction: List of connected shops with sync status. Connect button prominent. Disconnect is secondary (destructive, needs confirm).

### Pricing (`/pricing`)

Direction: Clean plan comparison table. No filler feature lists. Highlight what's included at each tier. CTA to upgrade is clear but not pushy.

### Billing (`/billing`)

Direction: Current plan, next billing date, usage meter, portal/upgrade button. Simple and factual.

## Anti-Patterns Already Present — Fix List

| Location | Issue | Fix |
|---|---|---|
| `app/page.tsx` | "Sprint 1 — Monorepo Skeleton" badge | Remove entirely |
| `app/page.tsx` | "Backend API" card with `/api/v1/health` | Remove entirely |
| `app/page.tsx` | "Auth coming in Sprint 2" | Remove entirely |
| `app/dashboard/page.tsx` | Emoji icons (🔗🔄✏️🤖↩️🖼️🎛️) on feature cards | Replace with text-only or SVG icons |
| `app/dashboard/page.tsx` | "Sprint 7", "Sprint 13", etc. in descriptions | Remove sprint references |
| `app/dashboard/page.tsx` | Disabled/greyed-out cards for unbuilt features | Remove unbuilt feature cards entirely |
| `app/dashboard/page.tsx` | API endpoint debug panel at bottom | Remove from customer-facing UI |
| All pages | No loading states on data fetches | Add skeleton loaders or spinner |
| All pages | Placeholder text visible to users | Remove all placeholder copy |

## Not in Scope for This Prep Task

- Full page redesigns (Productization Sprint)
- Dark mode
- Mobile navigation
- Animation / motion design
- New feature pages

## Next Task After This

**Productization UI Sprint**: Apply the design system to all customer-facing pages. Start with homepage and dashboard. Then listings, bulk edit, media, variations.
