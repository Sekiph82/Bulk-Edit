# Product

## Register

product

## Users

Etsy sellers — from solo craft makers with 20 listings to growing shops with 500+ listings. They use Bulk-Edit inside their daily seller workflow: after syncing their shop, they want to update prices across a product line, fix a misspelled tag on hundreds of items, or refresh descriptions before a seasonal sale. They are not developers. They are efficient, time-constrained, and have real money on the line.

Secondary users: multi-shop operators, print-on-demand sellers, digital product sellers, marketplace-first creators who treat Etsy as their primary storefront.

Job to be done: Update many listings quickly and safely without building a spreadsheet, without breaking anything on Etsy, and with confidence that mistakes can be undone.

## Product Purpose

Bulk-Edit is a professional SaaS tool that lets Etsy sellers bulk edit listings at scale — titles, prices, tags, descriptions, variations, photos, and more — with preview before write, automatic backup snapshots, and Magic Revert to undo any change. It is the tool Etsy's own dashboard should be but isn't: fast, safe, organized, and built for volume.

Success: a seller can touch 200 listings in 5 minutes, preview every change before it goes live, and sleep at night knowing they can revert.

## Brand Personality

Reliable. Precise. Efficient.

The brand is the tool that professionals trust. Not exciting — dependable. Not flashy — clear. The experience should feel like a well-organized desk: nothing wasted, everything findable, zero clutter.

## Anti-references

- Etsy's own seller dashboard: cluttered, slow, no bulk operations.
- Generic "AI-powered SaaS" UIs with purple-to-blue gradients, hero metrics cards, and testimonial carousels.
- Overly playful marketplace UIs (Airbnb-style cards, emoji-heavy, soft rounded everything).
- Developer-first UIs that expose API routes, sprint labels, or backend debug info to regular users.
- Placeholder card grids with "Coming Soon" or "Sprint X" text visible to customers.

Specific aesthetics to avoid:
- Purple/indigo gradient hero backgrounds
- Glassmorphism cards
- Emoji used as navigation icons
- Roadmap language in the customer UI ("Sprint 7", "/api/v1/health", "Backend API")
- Nested cards inside cards
- Giant disabled feature grids

## Design Principles

1. **Safety is visible.** Every write to Etsy shows a preview first. Backup and revert are never hidden. The user should feel in control, never anxious.
2. **Data density earns its keep.** Tables are the right UI for listings. Use them. Don't card-ify everything. Dense is fine when the data warrants it.
3. **Zero roadmap language in the UI.** Sprint numbers, API paths, "coming in Sprint X" — none of this reaches users. Features are either present or absent; in-progress features are invisible.
4. **Familiar beats inventive.** Sellers use Shopify, Stripe, and Notion. They expect top nav, data tables, status badges, confirmation modals. Don't reinvent these.
5. **One task, one screen.** Each page serves one primary workflow. No feature collisions, no multi-purpose dashboards that try to do everything.

## Accessibility & Inclusion

Target: WCAG 2.1 AA minimum.
- All text must meet 4.5:1 contrast ratio on its background.
- All interactive elements must have visible focus states.
- Forms must have labels (not placeholder-only inputs).
- Destructive actions must have explicit confirmation (not just hover state).
- prefers-reduced-motion must be respected on all transitions.
- No color as sole indicator of state (use text labels + icons alongside color).
