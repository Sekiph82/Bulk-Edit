# Design

## Color

Strategy: Restrained. One accent, semantic states, neutral surfaces.

| Token | Value | Usage |
|---|---|---|
| `--color-primary` | `#4F46E5` (indigo-600) | Primary buttons, active nav, links, focus rings |
| `--color-primary-hover` | `#4338CA` (indigo-700) | Button hover state |
| `--color-primary-light` | `#EEF2FF` (indigo-50) | Selected row highlight, tag background |
| `--color-bg` | `#F9FAFB` (gray-50) | Page background |
| `--color-surface` | `#FFFFFF` | Cards, panels, modals |
| `--color-surface-2` | `#F3F4F6` (gray-100) | Sidebar, toolbar, table header |
| `--color-border` | `#E5E7EB` (gray-200) | Card borders, dividers, table rows |
| `--color-text` | `#111827` (gray-900) | Primary body text |
| `--color-text-2` | `#6B7280` (gray-500) | Secondary labels, metadata |
| `--color-text-3` | `#9CA3AF` (gray-400) | Placeholder, disabled, empty state |
| `--color-success` | `#16A34A` (green-600) | Success badges, active state |
| `--color-warning` | `#D97706` (amber-600) | Warning badges, draft state |
| `--color-error` | `#DC2626` (red-600) | Error messages, failed state |
| `--color-info` | `#2563EB` (blue-600) | Info badges, sync state |

Dark mode: not in scope for current sprints. Tokens are structured for future dark mode addition.

## Typography

Font: **Inter** (already web-safe via system-ui fallback; load from Google Fonts when network available).

```css
font-family: 'Inter', system-ui, -apple-system, sans-serif;
```

| Scale | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| `text-xs` | 12px | 400/500 | 1.5 | Table metadata, badges, helper text |
| `text-sm` | 14px | 400/500 | 1.5 | Table cells, form labels, secondary content |
| `text-base` | 16px | 400 | 1.6 | Body text, form inputs |
| `text-lg` | 18px | 600 | 1.4 | Card headings, section titles |
| `text-xl` | 20px | 700 | 1.3 | Page headings (h2) |
| `text-2xl` | 24px | 700 | 1.2 | Page headings (h1) |
| `text-3xl` | 30px | 800 | 1.1 | Hero / marketing headings only |

Rules:
- No display fonts in UI labels, buttons, or data cells.
- Line length capped at 65ch for prose; tables run wider.
- `font-feature-settings: "cv02","cv03","cv04","cv11"` on Inter for better numerals.

## Spacing

Base unit: 4px. All spacing in multiples of 4.

| Token | Value | Usage |
|---|---|---|
| `space-1` | 4px | Micro gaps, icon-to-label |
| `space-2` | 8px | Inline element gaps |
| `space-3` | 12px | Form element internal padding |
| `space-4` | 16px | Card internal padding, row padding |
| `space-5` | 20px | Section gaps, large form spacing |
| `space-6` | 24px | Card-to-card gaps |
| `space-8` | 32px | Section top/bottom padding |
| `space-10` | 40px | Page section breaks |
| `space-12` | 48px | Hero vertical rhythm |

## Components

### Buttons

```
Primary: bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium
         hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-300 transition-colors
Danger:  bg-red-600 text-white ... hover:bg-red-700
Ghost:   border border-gray-300 text-gray-700 ... hover:bg-gray-50
Link:    text-indigo-600 underline-offset-2 hover:underline
```

All buttons: `cursor-pointer`, `transition-colors duration-150`, disabled state with `opacity-50 cursor-not-allowed`.

Touch targets: minimum 44×44px on all interactive elements.

### Cards

```
bg-white rounded-xl border border-gray-200 shadow-sm p-5
```

No nested cards. No shadow-lg on standard cards. No colored side-stripe borders.

### Tables

```
Table wrapper: overflow-x-auto
Table: w-full text-sm border-collapse
TH: text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide
    bg-gray-50 border-b border-gray-200
TD: py-3 px-4 text-gray-700 border-b border-gray-100
TR hover: hover:bg-gray-50 transition-colors
```

### Status Badges

```
active/success: bg-green-100 text-green-700
warning/draft:  bg-yellow-100 text-yellow-700
error/failed:   bg-red-100 text-red-700
inactive/gray:  bg-gray-100 text-gray-600
running/info:   bg-blue-100 text-blue-700
```

Format: `inline-block px-2 py-0.5 rounded text-xs font-medium`

### Form Fields

```
Input: border border-gray-300 rounded-lg px-3 py-2 text-sm w-full
       focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent
Select: same as input
Label: block text-sm font-medium text-gray-700 mb-1
```

All inputs must have an associated label (not placeholder-only).

### Modals

Overlay: `fixed inset-0 bg-black/40 flex items-center justify-center z-50`
Panel: `bg-white rounded-2xl shadow-xl p-8 max-w-md w-full mx-4`

Destructive confirms require typed confirmation string (e.g. "APPLY VARIATIONS").

### Empty States

```
<div class="text-center py-12 text-gray-400">
  <p class="text-sm">No listings found.</p>
  <p class="text-xs mt-1">Sync your shop to get started.</p>
</div>
```

Empty states must teach — include a one-line action hint, not just "nothing here."

### Error/Warning/Success Messages

```
Error:   bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700
Warning: bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 text-sm text-yellow-800
Success: bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-700
Info:    bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-700
```

## Layout

### Top Navigation

`bg-white border-b border-gray-200 px-6 lg:px-8 py-4 flex items-center justify-between`

Contains: Logo (left), primary nav links (center or left), user email + sign-out (right).
No hamburger menus in current scope (desktop-first tool).

### Page Shell

`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8`

Consistent max-width across all pages. No page-specific container widths.

### Grid System

Feature grids: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5`
Two-column layouts: `grid grid-cols-1 lg:grid-cols-3 gap-6`
Full-width tables/panels: no max restriction inside page shell.

## Motion

All transitions: `transition-colors duration-150` or `transition-all duration-200`.
No bounce, no elastic, no spring.
Loading state: `disabled:opacity-50` on buttons, skeleton placeholders for table rows.
No orchestrated page-load sequences.
`prefers-reduced-motion`: all transitions respect it via Tailwind's `motion-reduce:` prefix.

## Navigation Hierarchy

z-index scale:
- 10: sticky table headers
- 20: dropdown menus, popovers
- 30: sticky top nav
- 40: modal backdrop
- 50: modal panel
- 60: toast notifications

## Icons

Use SVG icons only. No emoji as navigation or action icons.
Recommended library: Heroicons (24px outline variant) or Lucide React.
Icon size: `w-5 h-5` for inline actions, `w-4 h-4` for table/badge icons.

## Copywriting Rules

- No sprint numbers in customer-facing UI.
- No API paths visible to users.
- No "coming soon" cards — absent features are simply absent.
- Action labels: imperative verbs. "Sync", "Apply", "Preview", "Revert" — not "Click here to sync."
- Error messages: say what happened + what to do. "Etsy connection not configured. Connect your shop in Settings."
- Empty states: one action hint. "No listings yet. Sync your shop to get started."
- Confirmation modals: describe consequences, not just "are you sure?"
