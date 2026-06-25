# User Flows

---

## Flow 1: New User Onboarding

```
Landing Page
  → Sign Up (email + password)
  → Email verification
  → Dashboard (empty state)
  → "Connect your Etsy shop" CTA
  → Etsy OAuth flow
  → Shop connected
  → "Sync your listings" CTA
  → Sync starts (background job)
  → Listings grid populated
  → Onboarding complete
```

**Error states:**
- Email already registered → show login link
- Etsy OAuth denied → show retry with instructions
- Sync fails → show error, retry button

---

## Flow 2: Bulk Edit Titles

```
Listings Grid
  → Select listings (multi-select checkboxes)
  → Click "Bulk Edit" → "Titles"
  → Bulk Edit Panel opens
  → Choose edit mode:
      - Find & Replace
      - Prepend text
      - Append text
      - Set all to value
  → Enter edit value
  → Click "Preview"
  → Preview modal: before/after diff per listing
  → Review changes, override individual listings if needed
  → Click "Apply to Etsy"
  → Confirmation dialog (warning: this writes to Etsy)
  → User confirms
  → Background job runs
  → Progress indicator
  → Success: show results (N updated, M failed)
  → Listings grid refreshes
```

**Error states:**
- Etsy API error on individual listing → mark failed, continue others
- Rate limit hit → pause and retry automatically
- Subscription limit reached → show upgrade modal

---

## Flow 3: Magic Revert

```
Any page → "Revert History" in sidebar
  → List of bulk edit sessions (date, listings affected)
  → Select session to revert
  → Choose: full revert or selective revert
  → If selective: choose specific listings and/or fields
  → Preview revert (before = snapshot, after = current)
  → Confirm revert
  → Background job: writes snapshot values back to Etsy
  → Success: listing values restored
```

---

## Flow 4: AI Title Optimizer

```
Listings Grid
  → Select listings
  → Click "AI Tools" → "Optimize Titles"
  → AI panel opens
  → Optional: add context (keywords, style notes)
  → Click "Generate"
  → Spinner (API call to AI provider)
  → AI output displayed: suggested title per listing
  → User reviews suggestions
  → Per-listing: accept / edit / reject
  → Click "Apply Selected"
  → Enters normal Bulk Edit Preview flow (Flow 2 from Preview step)
```

---

## Flow 5: Subscribe to Pro

```
Any gated feature → "Upgrade to Pro" modal
  → User clicks "Upgrade"
  → Choose: Monthly or Yearly
  → Stripe Checkout opens
  → User completes payment
  → Stripe webhook → backend syncs subscription
  → User redirected to app
  → Feature now accessible
  → Welcome email sent
```

---

## Flow 6: CSV Import

```
Sidebar → "CSV Import/Export" → "Import"
  → Upload CSV file
  → Validation runs (format, required fields)
  → If errors: show row-by-row error list
  → If valid: show import preview (diff per listing)
  → User reviews changes
  → Click "Apply Import"
  → Enters normal Bulk Edit confirmation flow
```

---

## Flow 7: Connect Additional Shop

```
Settings → "Shops" → "Add Shop"
  → Etsy OAuth flow (new shop)
  → Shop connected
  → Sync starts
  → All listings grids now include new shop
  → Filter bar: filter by shop
```
