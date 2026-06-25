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

## Anti-patterns for this page

- No hero metric cards
- No gradient hero background
- No animation on page load
- No testimonials, social proof, or feature grids in MVP
- No pricing section on the homepage (use `/pricing`)
