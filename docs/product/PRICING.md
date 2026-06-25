# Pricing

## Tiers

### Free
- Price: $0/month forever
- No credit card required
- Listings synced: 25
- Bulk edits/month: 10
- AI tool uses/month: 5
- Magic Revert: No
- CSV import/export: No
- Scheduled jobs: No
- Dynamic pricing: No
- Media library: No
- Shops: 1

### Pro Monthly
- Price: $19/month
- Listings synced: Unlimited
- Bulk edits/month: Unlimited
- AI tool uses/month: 500
- Magic Revert: Yes (30 days)
- CSV import/export: Yes
- Scheduled jobs: Yes
- Dynamic pricing: Yes
- Media library: Yes
- Shops: Unlimited

### Pro Yearly
- Price: $159/year (~$13.25/month, 30% off)
- All Pro Monthly features
- AI tool uses/month: Unlimited
- Priority support: Yes

---

## Stripe Configuration

| Plan | Stripe Price ID ENV |
|---|---|
| Pro Monthly | `STRIPE_PRICE_PRO_MONTHLY` |
| Pro Yearly | `STRIPE_PRICE_PRO_YEARLY` |

> Basic tiers (BASIC_MONTHLY, BASIC_YEARLY) reserved for future intermediate tier.

---

## Feature Gate Rules

Feature gate checks are enforced at the API layer via middleware, not just the frontend.

| Gate | Condition |
|---|---|
| `require_pro` | `subscription.plan IN ('pro_monthly', 'pro_yearly') AND subscription.status = 'active'` |
| `require_free_or_pro` | Any authenticated user |
| `listing_limit` | `count(listings) <= 25` for Free plan |
| `bulk_edit_limit` | `bulk_edits_this_month <= 10` for Free plan |
| `ai_limit` | `ai_uses_this_month <= 5` for Free, `<= 500` for Pro Monthly |

---

## Upgrade Flow

1. User hits a feature gate → shown upgrade modal
2. User clicks "Upgrade to Pro"
3. Stripe Checkout opens
4. On success, Stripe webhook fires `checkout.session.completed`
5. Backend syncs subscription status
6. User is redirected back to the app with Pro access

---

## Cancellation Flow

1. User opens Billing page
2. Clicks "Manage Subscription"
3. Stripe Customer Portal opens
4. User cancels
5. Stripe fires `customer.subscription.deleted`
6. Backend sets `subscription.status = 'canceled'`
7. User retains Pro access until period end, then reverts to Free

---

## Pricing Rationale

- $19/month aligns with Vela ($10–19/month range) while offering more AI features
- Yearly discount at 30% reduces churn
- Free tier with real value drives organic growth and reduces conversion friction
- No per-seat pricing at v1 — simplifies billing logic
