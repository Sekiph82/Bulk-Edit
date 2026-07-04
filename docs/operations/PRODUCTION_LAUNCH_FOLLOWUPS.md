# Production Launch Follow-Ups

Deliberately **not** built in the `feature/production-blockers-seo-landing-admin`
PR — each is either too large for a safe single PR, needs a provider/secret
decision only the product owner can make, or both. This document is the
tracked plan for each.

---

## -1. Bulk Create Listings — backend is a complete stub

A follow-up claim audit (`feature/video-creation-shop-insights-and-claim-fixes`)
found `apps/backend/app/api/v1/bulk_create.py` always returns
`status: "not_configured"` from both `/status` and `/drafts` regardless of
input — there is no real draft-creation logic behind it at all. It has been
**removed from all public marketing copy** (homepage, `/features`, `/faq`)
per product decision — not shown as "coming soon" either, just not
mentioned publicly until it's real. The internal `/bulk-create` app page
already honestly shows a "not configured" state to logged-in users, so no
change was needed there. Building the real feature (actual draft
persistence + Etsy listing creation via the existing preview/confirm
pattern used elsewhere) is unscoped future work.

---

## 0. Favicon / Open Graph image assets

**Attempted and reverted in this PR:** a code-generated favicon (`app/icon.tsx`)
and OG image (`app/opengraph-image.tsx`) using Next's built-in `next/og`
`ImageResponse` — this avoids committing binary asset files, but it broke
`next build` on this Windows dev machine:

```
TypeError: Invalid URL
    at new URL (node:internal/url:819:25)
    at fileURLToPath (node:internal/url:1604:12)
    at .../node_modules/next/dist/compiled/@vercel/og/index.node.js:18988:32
```

This is a known `@vercel/og` issue resolving its bundled default font via a
`file://` URL built from a Windows path. Since a broken production build is
worse than a missing favicon, both files were removed and `layout.tsx`'s
`icons` metadata was reverted.

**Follow-up options:**
1. Retry the same `ImageResponse` approach from a Linux/macOS dev machine or
   directly in CI (the bug is Windows-path-specific — DO's build runner is
   Linux, so this may just work there; verify with a scratch build before
   trusting it in production).
2. Or skip code-generation entirely and add a real designed `icon.png` /
   `apple-icon.png` / `opengraph-image.png` binary asset (small, reasonable
   file size — this task's "avoid large binaries" guidance is about not
   bloating the repo with heavy files, not about avoiding small icons).

---

## 1. Password reset / transactional email (pre-public-launch blocker)

**Current state:** no forgot-password flow, no SMTP/email-sending capability
anywhere in the backend. `app.services.auth` only has register/login/refresh/logout.

**Scope to build:**
- Provider choice: Resend, Postmark, or SES (matches existing `SMTP_*` env
  var naming already referenced in `.do/app.production-backend.yaml` comments).
- Email service abstraction: `app/services/email.py` — a thin `send_email()`
  wrapper so the provider can be swapped without touching call sites.
- New table: `password_reset_tokens` (user_id, token_hash, expires_at, used_at) —
  same pattern as the existing `social_oauth_states` state-hash table.
- `POST /api/v1/auth/forgot-password` — issues a token, emails a reset link,
  always returns 200 regardless of whether the email exists (no user enumeration).
- `POST /api/v1/auth/reset-password` — validates token + expiry, sets new
  password hash, invalidates the token.
- Frontend: `/forgot-password` and `/reset-password` pages.
- Audit log entry on both request and completion.
- Rate limiting on both endpoints (reuse `app/core/rate_limit.py` pattern).

**Risk if deferred:** real users who forget their password have no
self-service recovery — support burden, or account lockout. Treat as a
**pre-public-launch blocker**, not a nice-to-have.

---

## 2. Email/waitlist capture

**Current state:** the `/contact-us` demo form is 100% client-side —
`setTimeout(() => setFormState("sent"), 800)` in `ContactContent.tsx`. It
does not submit anywhere. No backend contact/waitlist endpoint exists.

**Scope to build:** requires the email service abstraction from item 1 (or a
lightweight `contact_submissions` table if you want unconfirmed-email capture
without an email service yet). Do not wire the existing form to "success" UI
without an endpoint behind it — that would create the exact "collect emails
into nowhere" problem this task explicitly rules out.

**Recommendation:** build this alongside item 1, since both need transactional
email or at least a persisted-submission table.

---

## 3. Admin panel — deeper roadmap

**Current state (already solid):** `/admin` frontend page + 20
`require_superuser`-gated backend endpoints (`/api/v1/admin/*`) covering
users, organizations, subscriptions, shops, sync jobs, usage, billing,
Stripe summary, product usage, system health, and audit log. It is a
**separate route with its own tab-based UI** (Overview/Users/Billing/Etsy/Usage/System)
— it does not reuse any customer dashboard component, and it 403s cleanly
for non-superusers. This already satisfies "not a customer dashboard."

**What's a real limitation:** it's one 700+ line client component file.
Follow-up roadmap (not done now — refactor risk vs. benefit doesn't justify
touching working, gated code in this PR):

1. Split into route-based sections: `/admin/users`, `/admin/organizations`,
   `/admin/billing`, `/admin/system`, `/admin/audit`, `/admin/jobs`.
2. User and organization detail pages (drill-down from list rows).
3. Search/filters: email search, plan/status filters, audit log date range.
4. CSV export for users/subscriptions.
5. Charts: MRR trend, daily signups, active users, AI usage, sync failures.
6. Admin actions: plan change/comp, Stripe-integrated refund workflow,
   manual sync trigger, admin-triggered password reset email (depends on
   item 1), user impersonation — **only** if built with mandatory audit
   logging from day one.
7. Monitoring/alerts: sync failure spikes, payment failures, health anomalies.

---

## 4. Blog / programmatic SEO

**Current state:** no blog engine, no MDX pipeline, no `/blog` route.

**Roadmap (content-first, not scaffold-first — thin SEO pages are worse than
no pages):**
1. `/blog` — MDX-based content system (e.g. `next-mdx-remote` or Contentlayer).
2. First articles once the content system exists:
   - How to Bulk Edit Etsy Listings
   - Etsy SEO Title & Tag Optimization Checklist
   - Bulk Edit vs Vela vs eRank comparison (neutral, factual — see homepage
     positioning section for the tone to match)
   - Etsy Listing Health Mistakes
   - Etsy Fee / Profit Calculation Guide
3. Feature landing pages once each has enough real, accurate content:
   `/features/bulk-tag-editor`, `/features/etsy-csv-import`,
   `/features/ai-title-generator`, `/features/photo-bulk-editing`.
4. Free tools (real, working, not lead-gen shells):
   `/tools/etsy-fee-calculator`, `/tools/etsy-title-checker`,
   `/tools/etsy-tag-generator`.

**Explicit non-goal:** do not generate any of the above as thin/placeholder
pages purely for SEO surface area — build them only when there's real,
useful content behind each URL.

---

## 5. Analytics

**Current state:** no analytics integration anywhere in the frontend.

**Recommendation:** Plausible or PostHog — both have straightforward
Next.js App Router patterns and (for Plausible especially) minimal cookie
footprint. Decision on which provider, and any account/project setup, is a
product-owner call, not something to hard-code here.

**Env placeholders to add when a provider is chosen** (`.env.local.example`):
```
NEXT_PUBLIC_ANALYTICS_PROVIDER=       # "plausible" | "posthog" | ""
NEXT_PUBLIC_PLAUSIBLE_DOMAIN=         # only if provider=plausible
NEXT_PUBLIC_POSTHOG_KEY=              # only if provider=posthog
NEXT_PUBLIC_POSTHOG_HOST=             # only if provider=posthog
```

**Cookie/privacy note:** Plausible is cookie-free by default. PostHog uses
cookies/localStorage for session identity by default — if chosen, the
Privacy Policy (`/privacy`) should be updated to mention it explicitly
before enabling in production.

---

## 6. README / GitHub hygiene

**README demo credentials:** already correctly scoped — the `test@example.com`
/ `test-su@example.com` table lives under "Local Setup" → "Windows one-click
setup," clearly local-dev-only, not ambiguous with production. No change
needed.

**GitHub repo metadata** (description, website URL, topics) cannot be changed
from code in this repo and was not changed via the GitHub API per this task's
rules. Manual steps for the repo owner:
- Settings → repo description: short one-liner matching the README's first line.
- Settings → website: `https://bulkeditapp.com` (once live).
- Settings → topics: `etsy`, `saas`, `bulk-edit`, `nextjs`, `fastapi`.

---

## 7. CSP `unsafe-inline` hardening

**Current state:** `next.config.mjs` already documents *why* `unsafe-inline`
(and `unsafe-eval` in dev) are present — Next.js App Router injects inline
scripts that a strict CSP would need a nonce-per-request to allow instead.

**Follow-up (not done now — real risk of breaking every page if rushed):**
Next.js middleware-based nonce injection: generate a per-request nonce in
`middleware.ts`, attach it via response headers, and thread it through to
the CSP header and any inline `<script>` tags (including the anti-flash
theme script in `layout.tsx` and the JSON-LD scripts added in this PR).
This removes `unsafe-inline` from `script-src` entirely. Budget this as its
own PR with full page-by-page verification — do not attempt as a drive-by
change alongside other work.
