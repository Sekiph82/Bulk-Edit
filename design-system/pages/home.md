# Design Override — Home Page (`/`)

> Overrides `design-system/MASTER.md` for the homepage only.

## Purpose

First impression for unauthenticated visitors. Marketing surface — but minimal. Not a full brand landing page. A clean, confident entry point that communicates what the product is and gets the user to sign up or log in.

## Register

Brand-adjacent (marketing landing) — but restrained. No scroll-driven sections, no hero animations, no testimonials in current scope.

## Layout

Single centered column. Max width: `max-w-2xl`. Vertically centered on the viewport.

```
Logo / Brand name
Headline (one sentence, max 10 words)
Subheadline (one sentence, max 20 words)
CTA button (Get Started / Go to Dashboard)
Optional: 3 brief feature bullets (text only)
Sign in link (for returning users)
```

## Typography

- Headline: `text-3xl font-extrabold text-gray-900` — one sentence only
- Subheadline: `text-lg text-gray-500 mt-3` — value proposition, not a paragraph
- CTA: primary button style from MASTER.md

## What to Remove

- Yellow sprint badge ("Sprint 1 — Monorepo Skeleton") — remove entirely
- "Backend API" debug card — remove entirely
- "Auth coming in Sprint 2" copy — remove entirely
- Any `<code>` blocks with API endpoints

## What to Keep

- Simple headline
- Single CTA to dashboard
- Clean minimal layout

## Colors

Same as MASTER.md. No accent background on homepage body.

## Layout — Current (Post-Animation Sprint)

Desktop: Two-column grid (`lg:grid-cols-2`). Left: headline + CTAs + trust strip. Right: `AnimatedProductDemo` component.
Mobile: Stacked, demo below hero text.

## AnimatedProductDemo

Mock browser shell showing the Bulk-Edit workflow in 5 animated phases:
1. Listing grid idle
2. 3 rows selected
3. Edit panel slides in from right (append title, add tag, +10% price)
4. Preview panel appears (before/after, amber highlight)
5. Safety strip appears (Backup snapshot, Magic Revert, Apply safely button)

Component: `apps/frontend/components/AnimatedProductDemo.tsx`
Library: `motion` v12 (`"motion/react"`)
Reduced motion: if `prefers-reduced-motion`, skip to phase 4 (static final state).
All content is mock/static — no API calls.

## Trust Strip

4-item grid below CTAs: Preview every change / Backup snapshots / Magic Revert / Built for Etsy sellers

## Workflow Strip

Below hero section, full-width white bar: Connect → Sync → Edit → Preview → Apply → Revert

## Anti-patterns for this page

- No hero metric cards
- No gradient hero background
- No testimonials, social proof, or feature grids in MVP
- No pricing section on the homepage (use `/pricing`)
- Do not animate app UI pages — animation is homepage-only via AnimatedProductDemo
