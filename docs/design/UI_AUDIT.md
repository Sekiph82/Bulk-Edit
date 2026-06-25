# UI Audit — Bulk-Edit Frontend

Audit performed: 2026-06-26
Tools used: Impeccable (audit reference), UI UX Pro Max (design system analysis)
Pages audited: homepage, dashboard, listings, bulk-edit, media, variations

---

## Audit Health Score

| # | Dimension | Score | Key Finding |
|---|---|---|---|
| 1 | Accessibility | 1/4 | No focus rings, form inputs missing labels, no ARIA on interactive elements |
| 2 | Performance | 3/4 | No lazy loading on thumbnails, but no heavy animations — good baseline |
| 3 | Responsive Design | 2/4 | Grid breakpoints exist but table overflow on mobile, no touch target audit |
| 4 | Theming | 1/4 | Hard-coded Tailwind classes throughout, no design tokens, no dark mode support |
| 5 | Anti-Patterns | 1/4 | Sprint labels, API endpoints, emoji icons, disabled card grid, debug panels in customer UI |
| **Total** | | **8/20** | **Poor — major overhaul needed** |

---

## Anti-Patterns Verdict

**FAIL — clear AI slop and developer-first tells throughout.**

Specific tells found:
1. Sprint badge on homepage ("Sprint 1 — Monorepo Skeleton") — developer roadmap visible to end users.
2. API endpoint exposed on homepage (`/api/v1/health`) — debug card masquerading as content.
3. Emoji-heavy feature cards on dashboard (🔗🔄✏️🤖↩️🖼️🎛️) — violates SVG-only icon rule.
4. Disabled greyed-out roadmap cards on dashboard ("Sprint 7", "Sprint 13") — placeholder grid anti-pattern.
5. API endpoint debug panel at bottom of dashboard — raw endpoint list in customer-facing UI.
6. "Auth coming in Sprint 2" copy in homepage — internal roadmap language.

---

## Detailed Findings

### P0 — Blocking

**[P0] Sprint labels and API endpoints visible to users**
- Location: `apps/frontend/app/page.tsx` — lines 21-44
- Category: Anti-Pattern / Product positioning
- Impact: Users see internal developer language. Destroys professional credibility. Customers should never see sprint numbers or API routes.
- Recommendation: Remove the yellow sprint badge entirely. Remove the "Backend API" debug card. Remove "Auth coming in Sprint 2" copy.
- Suggested command: `/impeccable clarify apps/frontend/app/page.tsx`

**[P0] Disabled roadmap cards exposed as customer UI**
- Location: `apps/frontend/app/dashboard/page.tsx` — placeholderFeatures array with `href: null` items
- Category: Anti-Pattern / Product positioning
- Impact: Users see "Sprint 7", "Sprint 13", "AI Tools — Sprint 13" — internal roadmap exposed. Greyed-out cards imply broken features.
- Recommendation: Remove all items with `href: null`. Show only working features. Future features are simply absent, not shown as disabled.
- Suggested command: `/impeccable distill apps/frontend/app/dashboard/page.tsx`

**[P0] API endpoint debug panel in dashboard**
- Location: `apps/frontend/app/dashboard/page.tsx` — lines 132-147 (API Endpoints section)
- Category: Anti-Pattern / Developer tooling in customer UI
- Impact: Renders raw backend URLs to end users. Completely inappropriate for customer-facing UI.
- Recommendation: Remove the entire "API Endpoints" section from the customer dashboard.
- Suggested command: `/impeccable distill apps/frontend/app/dashboard/page.tsx`

### P1 — Major

**[P1] No accessible focus states on buttons**
- Location: All pages — all `<button>` and `<Link>` elements
- Category: Accessibility — WCAG 2.1 AA (SC 2.4.7)
- Impact: Keyboard users cannot track focus. Tab navigation is broken functionally.
- Recommendation: Add `focus:ring-2 focus:ring-indigo-300 focus:outline-none` to all interactive elements. Use `focus-visible:ring-2` to avoid showing focus ring on mouse clicks.
- Suggested command: `/impeccable harden apps/frontend/app`

**[P1] Form inputs without associated labels**
- Location: `apps/frontend/app/bulk-edit/page.tsx`, `apps/frontend/app/listings/page.tsx`, `apps/frontend/app/media/page.tsx`
- Category: Accessibility — WCAG 2.1 AA (SC 1.3.1)
- Impact: Screen readers cannot identify form inputs. Sellers with assistive tech cannot use the app.
- Recommendation: Every `<input>` and `<select>` must have an explicit `<label>` with `htmlFor` matching the input's `id`. Placeholder text is not a substitute.
- Suggested command: `/impeccable harden`

**[P1] Emoji icons in navigation and UI actions**
- Location: `apps/frontend/app/dashboard/page.tsx` — all feature card icons
- Category: Anti-Pattern — emoji-as-icons
- Impact: Emojis render inconsistently across OS and fonts. Not keyboard-accessible. Violates professional design standards.
- Recommendation: Replace all emoji icons with Heroicons SVG (outline, 20px). Each feature card should have a consistent SVG icon.
- Suggested command: `/impeccable colorize apps/frontend/app/dashboard/page.tsx`

**[P1] No loading states on async data fetches**
- Location: All pages with `useEffect` + API calls
- Category: Performance / UX
- Impact: Tables flash empty before data loads. Users may think content is missing. No feedback during long syncs.
- Recommendation: Add skeleton loader rows for tables. Disable action buttons while loading. Show spinner or progress indicator during sync operations.
- Suggested command: `/impeccable harden`

**[P1] Inconsistent typography — missing type scale**
- Location: All pages
- Category: Theming
- Impact: Heading sizes, weights, and line heights vary across pages. No consistent visual hierarchy.
- Recommendation: Establish Inter as base font. Apply consistent h1/h2/h3 scale from DESIGN.md. Ensure all page headings use the same style.
- Suggested command: `/impeccable typeset apps/frontend/app`

### P2 — Minor

**[P2] Table cells overflow on mobile**
- Location: `apps/frontend/app/listings/page.tsx` — listing table
- Category: Responsive Design
- Impact: Horizontal scroll required on viewports under 768px. Long titles wrap poorly.
- Recommendation: Add `overflow-x-auto` wrapper (already present on some pages). Add `max-w-xs truncate` on title cells. Consider hiding low-priority columns on mobile.
- Suggested command: `/impeccable adapt apps/frontend/app/listings/page.tsx`

**[P2] Image thumbnails without lazy loading**
- Location: `apps/frontend/app/listings/page.tsx`
- Category: Performance
- Impact: On a shop with 200+ listings, all thumbnails load immediately. Unnecessary network load.
- Recommendation: Add `loading="lazy"` to all `<img>` tags. Convert to `next/image` with `priority={false}`.
- Suggested command: `/impeccable optimize apps/frontend/app/listings/page.tsx`

**[P2] Touch targets under 44px**
- Location: Dashboard feature cards, navigation links, table action buttons
- Category: Responsive / Accessibility
- Impact: Hard to tap on mobile or touchscreen. Violates minimum tap target size.
- Recommendation: Ensure all clickable elements have minimum 44×44px bounding box. Use padding to increase touch area on small icons.
- Suggested command: `/impeccable adapt`

**[P2] No empty states**
- Location: All pages with data tables when no data is present
- Category: UX — onboarding
- Impact: Empty tables with no guidance leave new users confused. No direction on what to do next.
- Recommendation: Add empty state to listings table, job history lists, results tables. Include a one-line action hint.
- Suggested command: `/impeccable onboard`

**[P2] Colors hard-coded throughout — no design tokens**
- Location: Every frontend file
- Category: Theming
- Impact: Cannot apply theme changes systematically. No dark mode support possible. Color values scattered and inconsistent.
- Recommendation: Extract color values into CSS custom properties or Tailwind config `extend.colors`. Reference tokens instead of raw hex or color names.
- Suggested command: `/impeccable extract`

### P3 — Polish

**[P3] Confirm modals use basic string comparison only**
- Location: All apply confirm modals (bulk-edit, media, variations)
- Category: UX
- Impact: "Type APPLY to confirm" is a reasonable gate but the styling can be improved (character counter, clearer instruction).
- Recommendation: Add `aria-describedby` connecting instruction text to the input. Show character match progress.

**[P3] Breadcrumb navigation inconsistent**
- Location: Some pages have breadcrumb (media, variations), others don't (listings, bulk-edit)
- Category: Navigation consistency
- Recommendation: Apply consistent "BrandName / Section Name" breadcrumb pattern to all authenticated pages.

**[P3] Status badges inconsistent between pages**
- Location: `media/page.tsx` vs `variations/page.tsx` — same StatusBadge component defined twice
- Category: Code/design consistency
- Recommendation: Extract `StatusBadge` to a shared component in `apps/frontend/components/StatusBadge.tsx`. Single source of truth for all badge styles.

---

## Patterns and Systemic Issues

1. **No design tokens**: Every page uses Tailwind's utility classes directly with specific color names (e.g. `bg-indigo-600`, `text-gray-700`). A change to the brand color requires touching every file. Should be extracted to Tailwind config theme extension.

2. **Duplicated components**: `StatusBadge` defined identically in `media/page.tsx` and `variations/page.tsx`. Each new feature adds its own copy. Needs a shared component library.

3. **Developer-mode content in customer pages**: Sprint labels, API endpoints, and debug panels appear in customer-facing routes. This is the most critical issue — it makes the product look unfinished.

4. **No shared layout component**: Each page defines its own nav bar. The same logout/email logic is replicated 3+ times. Should be a shared `<AppNav>` or `<AuthedLayout>` component.

5. **Emoji icon system-wide**: Using emojis as navigation icons is a fast-path during development but unacceptable in a product. Every emoji must become an SVG icon before launch.

---

## Positive Findings

- **Functional safety chain is excellent.** Preview-before-apply, backup snapshots, confirm modal — the data safety model is well-implemented. The UI reflects this correctly with visible confirmation steps.
- **Listing grid is data-dense and useful.** Column visibility toggles, filter panel, sort — the core data table is functional and appropriate.
- **Status badge vocabulary is consistent in naming.** `active/inactive/draft/expired/running/completed/failed` is a clear semantic set. Just needs to be extracted to a shared component.
- **Async error handling exists.** Pages catch `ApiError` and display error messages. Not perfect but better than silent failures.
- **Confirm modals for destructive actions.** APPLY MEDIA, APPLY VARIATIONS typed confirmation — correct pattern.

---

## Recommended Actions (Priority Order)

1. **[P0] `/impeccable distill apps/frontend/app/page.tsx`** — Remove sprint badge, API debug card, internal roadmap copy
2. **[P0] `/impeccable distill apps/frontend/app/dashboard/page.tsx`** — Remove disabled roadmap cards, API debug panel
3. **[P1] `/impeccable harden apps/frontend/app`** — Add focus states, form labels, loading states
4. **[P1] `/impeccable typeset apps/frontend/app`** — Apply consistent Inter type scale
5. **[P1] Extract SVG icons** — Replace all emoji with Heroicons SVG before any visual redesign
6. **[P2] `/impeccable adapt apps/frontend/app/listings/page.tsx`** — Mobile overflow + touch targets
7. **[P2] `/impeccable optimize apps/frontend/app/listings/page.tsx`** — Add lazy loading to thumbnails
8. **[P2] `/impeccable onboard apps/frontend/app`** — Add empty states across all data tables
9. **[P3] Extract shared components** — `StatusBadge`, `AppNav`, `AppLayout`
10. **[P3] `/impeccable polish apps/frontend/app`** — Final quality pass

Re-run `/impeccable audit` after fixes to see score improve.
