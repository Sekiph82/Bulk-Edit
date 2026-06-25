# Design System — Bulk-Edit (Master)

> Global Source of Truth. Page-specific overrides live in `design-system/pages/[page].md`.
> When building a specific page, check `design-system/pages/[page].md` first.
> If it exists, its rules override this file. Otherwise, use this file exclusively.

---

## Brand Positioning

Bulk-Edit is a professional SaaS tool for Etsy sellers. The design register is **product**: design serves the task, not the brand. The tool should disappear into the workflow.

Tone: reliable, precise, efficient.
Mood: calm, trustworthy, zero clutter.

---

## Color Palette

Strategy: **Restrained** — one accent, semantic states, neutral surfaces.

| Role | Tailwind | Hex | Usage |
|---|---|---|---|
| Primary | `indigo-600` | `#4F46E5` | Primary buttons, active state, focus rings |
| Primary hover | `indigo-700` | `#4338CA` | Button hover |
| Primary light | `indigo-50` | `#EEF2FF` | Selected row, tag bg |
| Background | `gray-50` | `#F9FAFB` | Page background |
| Surface | white | `#FFFFFF` | Cards, panels, modals |
| Surface alt | `gray-100` | `#F3F4F6` | Sidebar, toolbar, table header |
| Border | `gray-200` | `#E5E7EB` | Card borders, dividers, table rows |
| Text primary | `gray-900` | `#111827` | Body text, headings |
| Text secondary | `gray-500` | `#6B7280` | Labels, metadata |
| Text muted | `gray-400` | `#9CA3AF` | Placeholder, disabled, empty state |
| Success | `green-600` | `#16A34A` | Success badge, active listing |
| Warning | `amber-600` | `#D97706` | Warning badge, draft state |
| Error | `red-600` | `#DC2626` | Error message, failed state |
| Info | `blue-600` | `#2563EB` | Info badge, sync state |

**Never**: gradient text, glassmorphism, colored side-stripe borders, full-saturation accents on inactive states.

---

## Typography Scale

Font family: **Inter** (Google Fonts or system-ui fallback)

```css
font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
```

| Scale | px | Weight | Line Height | Tailwind | Usage |
|---|---|---|---|---|---|
| xs | 12 | 400/500 | 1.5 | `text-xs` | Badges, metadata, helper text |
| sm | 14 | 400/500 | 1.5 | `text-sm` | Table cells, labels, secondary |
| base | 16 | 400 | 1.6 | `text-base` | Body text, form inputs |
| lg | 18 | 600 | 1.4 | `text-lg` | Card headings, subsections |
| xl | 20 | 700 | 1.3 | `text-xl` | Page subheadings |
| 2xl | 24 | 700 | 1.2 | `text-2xl` | Page headings (h1) |
| 3xl | 30 | 800 | 1.1 | `text-3xl` | Hero headings only |

Rules:
- One font family throughout. No display/body pairing.
- No display fonts in buttons, labels, or table cells.
- `text-wrap: balance` on h1–h3.
- Line length: ≤65ch for prose, wider for tables.
- Inter numeric features: `font-feature-settings: "cv02","cv03","cv04","cv11"` where numerals are critical (prices, quantities).

---

## Spacing Scale

Base: 4px. All spacing in multiples of 4.

| Token | px | Tailwind | Usage |
|---|---|---|---|
| 1 | 4 | `space-1` / `p-1` | Micro gaps, icon margins |
| 2 | 8 | `space-2` / `p-2` | Inline gaps |
| 3 | 12 | `space-3` / `p-3` | Form field padding |
| 4 | 16 | `space-4` / `p-4` | Card padding, row height |
| 5 | 20 | `space-5` / `p-5` | Section gaps |
| 6 | 24 | `space-6` / `p-6` | Card-to-card gaps |
| 8 | 32 | `space-8` / `p-8` | Section breaks |
| 10 | 40 | `space-10` | Large section padding |
| 12 | 48 | `space-12` | Hero rhythm |

---

## Card Styles

```css
/* Standard card */
bg-white rounded-xl border border-gray-200 shadow-sm p-5

/* Focused/interactive card */
bg-white rounded-xl border border-gray-200 shadow-sm p-5
hover:border-indigo-300 transition-colors cursor-pointer

/* Active/selected card */
bg-indigo-50 border border-indigo-300 rounded-xl p-5
```

Rules:
- No nested cards.
- No `shadow-lg` on standard content cards.
- No colored side-stripe borders.
- No glassmorphism.

---

## Button Styles

```css
/* Primary */
bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-4 py-2 rounded-lg text-sm
transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300 cursor-pointer

/* Danger */
bg-red-600 hover:bg-red-700 text-white font-medium px-4 py-2 rounded-lg text-sm
transition-colors focus:outline-none focus:ring-2 focus:ring-red-300 cursor-pointer

/* Ghost */
border border-gray-300 text-gray-700 font-medium px-4 py-2 rounded-lg text-sm
hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-200 cursor-pointer

/* Link */
text-indigo-600 text-sm font-medium hover:underline underline-offset-2

/* Disabled modifier (add to any) */
disabled:opacity-50 disabled:cursor-not-allowed
```

Touch targets: minimum 44×44px on all buttons and interactive elements.

---

## Badge Styles

```css
/* Base */
inline-block px-2 py-0.5 rounded text-xs font-medium

/* States */
active / success:    bg-green-100 text-green-700
warning / draft:     bg-yellow-100 text-yellow-700
error / failed:      bg-red-100 text-red-700
info / running:      bg-blue-100 text-blue-700
inactive / default:  bg-gray-100 text-gray-600
preview_ready:       bg-blue-100 text-blue-700
completed_with_errors: bg-orange-100 text-orange-700
```

---

## Table Styles

```css
/* Wrapper */
overflow-x-auto

/* Table */
w-full text-sm

/* Header row */
border-b border-gray-200

/* TH */
text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide bg-gray-50

/* TD */
py-3 px-4 text-gray-700 border-b border-gray-100

/* Row hover */
hover:bg-gray-50 transition-colors

/* Sortable column header */
cursor-pointer hover:text-gray-700 select-none
```

---

## Modal Styles

```css
/* Backdrop */
fixed inset-0 bg-black/40 flex items-center justify-center z-50

/* Panel */
bg-white rounded-2xl shadow-xl p-8 max-w-md w-full mx-4

/* Title */
text-lg font-bold text-gray-900 mb-2

/* Body */
text-sm text-gray-600 mb-4

/* Button row */
flex gap-3 mt-6
```

Destructive actions require typed confirmation string. Non-destructive confirmations may use button-only confirm.

---

## Empty State Style

```html
<div class="text-center py-12">
  <p class="text-sm text-gray-500">No listings found.</p>
  <p class="text-xs text-gray-400 mt-1">Sync your shop to get started.</p>
</div>
```

Rules:
- Always include an action hint (what to do next).
- Do not use "nothing here" without direction.
- No illustrations required in current scope.

---

## Error / Warning / Success Messages

```css
/* Error */
bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700

/* Warning */
bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 text-sm text-yellow-800

/* Success */
bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-700

/* Info */
bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-700
```

All must be dismissible or auto-expire after 5 seconds for success/info.

---

## Sidebar / Topbar Rules

### Top Navigation

```css
bg-white border-b border-gray-200 px-6 lg:px-8 py-4 flex items-center justify-between sticky top-0 z-30
```

Contents:
- Left: Logo (`text-xl font-extrabold text-gray-900`, links to `/dashboard`)
- Center (optional): primary nav links for authenticated users
- Right: user email (text-sm text-gray-600), sign-out link

No sidebar in current scope. Future: collapsible sidebar with icon-only collapsed state.

### Breadcrumb

```css
/* Breadcrumb separator */
<span class="text-gray-300 mx-2">/</span>

/* Current page */
<span class="text-sm font-medium text-gray-600">Page Name</span>
```

---

## Form Field Rules

```css
/* Input */
border border-gray-300 rounded-lg px-3 py-2 text-sm w-full
focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent

/* Label */
block text-sm font-medium text-gray-700 mb-1

/* Helper text */
text-xs text-gray-500 mt-1

/* Error state */
border-red-300 focus:ring-red-300
```

**Required**: Every `<input>` and `<select>` must have an associated `<label>`. No placeholder-only labels.

---

## Data Density Rules

Tables are appropriate for listings data. Do not card-ify tabular data.

- 200+ items: paginate (50 per page default, 200 max)
- Column visibility: user-configurable on listing grid
- Mobile: horizontal scroll is acceptable for data-dense tables; hide lowest-priority columns at sm breakpoint
- Row height: `py-3` for standard density, `py-2` for compact (job history, preview items)

---

## Responsive Behavior

| Breakpoint | Behavior |
|---|---|
| `sm` (640px+) | 2-column grids, table column visibility unchanged |
| `md` (768px+) | Full nav visible, filter panel visible |
| `lg` (1024px+) | 3-column grids, side-by-side layouts unlock |
| `xl` (1280px+) | Full density, max-w-7xl container |

Page shell: `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`

---

## Copywriting Rules

| Anti-pattern | Fix |
|---|---|
| "Sprint 7 ✓" | Remove entirely — features are present or absent |
| "Sprint 13 — AI Tools" | Remove — unbuilt features are invisible |
| "/api/v1/health" in UI | Remove — no API endpoints in customer UI |
| "Backend API" section | Remove — internal debug panel |
| "Auth coming in Sprint 2" | Remove — no roadmap in customer UI |
| "Monorepo Skeleton" | Remove — internal architecture jargon |
| Emoji as icons | Replace with SVG (Heroicons outline) |
| "Nothing here" | "No listings yet. Sync your shop to get started." |
| "coming soon" cards | Remove card entirely — absent features are invisible |

Action labels: imperative verbs (Sync, Preview, Apply, Revert, Connect).
Error messages: what happened + what to do.

---

## Z-Index Scale

```css
/* Sticky table headers */   z-index: 10
/* Dropdown menus */         z-index: 20
/* Sticky top nav */         z-index: 30
/* Modal backdrop */         z-index: 40
/* Modal panel */            z-index: 50
/* Toast notifications */    z-index: 60
```

Never use arbitrary values (999, 9999).

---

## Icons

Library: **Heroicons** (outline, 20px) or **Lucide React**.
Size: `w-5 h-5` inline actions, `w-4 h-4` in badges/table cells.
No emoji as icons. No raster icons. SVG only.

---

## Absolute Bans

- Side-stripe borders on cards (no `border-l-4` colored accents)
- Gradient text (`background-clip: text`)
- Glassmorphism cards
- Hero metric card template (big number + small label + gradient)
- Identical card grids (same icon+heading+text repeated)
- Tiny uppercase tracked eyebrow on every section
- Numbered section markers as default scaffolding (01/02/03)
- Sprint numbers in customer-facing UI
- API endpoints in customer-facing UI
- Emoji as navigation or action icons
- Nested cards inside cards
- Disabled "coming soon" roadmap cards
- Raw API endpoint lists
- Developer debug panels
