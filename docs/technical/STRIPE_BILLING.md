# Stripe Billing Integration

## Sprint 3 Implementation Status: COMPLETE

## Products and Prices

Created in Stripe Dashboard and configured via environment variables:

| Plan | ENV var | Stripe type |
|---|---|---|
| Basic Monthly | `STRIPE_PRICE_BASIC_MONTHLY` | Recurring, monthly |
| Pro Monthly | `STRIPE_PRICE_PRO_MONTHLY` | Recurring, monthly |
| Basic Yearly | `STRIPE_PRICE_BASIC_YEARLY` | Recurring, yearly |
| Pro Yearly | `STRIPE_PRICE_PRO_YEARLY` | Recurring, yearly |

---

## Plan Limits

Defined in `app/core/plans.py` — `PLAN_LIMITS` dict:

| Feature | Free | Basic | Pro |
|---|---|---|---|
| max_shops | 1 | 3 | 10 |
| max_listings | 25 | 1,000 | 10,000 |
| bulk_edits_per_month | 10 | 250 | 5,000 |
| ai_credits_per_month | 5 | 250 | 2,000 |
| media_assets | 25 | 1,000 | 10,000 |
| can_bulk_edit_photos | ✗ | ✓ | ✓ |
| can_bulk_edit_variations | ✗ | ✗ | ✓ |
| can_use_magic_revert | ✗ | ✓ | ✓ |
| can_use_dynamic_pricing | ✗ | ✗ | ✓ |
| can_schedule_jobs | ✗ | ✓ | ✓ |

Yearly plans share the same limits as their monthly counterparts.

---

## Checkout Flow

1. Frontend calls `POST /api/v1/billing/checkout` with `{ "plan": "pro_monthly" }`
2. Backend checks:
   - Plan is not "free" (400)
   - Stripe is configured: `STRIPE_SECRET_KEY` starts with `sk_test_` or `sk_live_` (503)
   - Price ID is not placeholder (503)
3. Backend creates/reuses Stripe Customer for org
4. Backend creates Stripe Checkout Session:
   - `mode: 'subscription'`
   - `customer: existing_customer_id`
   - `metadata: { organization_id: org.id, plan: plan }`
   - `success_url: http://localhost:3100/billing?success=true`
   - `cancel_url: http://localhost:3100/pricing?canceled=true`
5. Returns `{ "checkout_url": "..." }`
6. Frontend redirects to Stripe Checkout
7. User completes payment
8. Stripe fires `checkout.session.completed` webhook
9. Backend syncs subscription status

---

## Webhook Events Handled

| Event | Action |
|---|---|
| `checkout.session.completed` | Set plan, status=active, store stripe_customer_id + subscription_id |
| `customer.subscription.created` | Sync status, period dates, price_id |
| `customer.subscription.updated` | Sync status, period dates, cancel_at_period_end |
| `customer.subscription.deleted` | Set plan=free, status=canceled |
| `invoice.payment_failed` | Set status=past_due |

### Webhook Security

Every webhook request:
1. Must have `Stripe-Signature` header
2. `STRIPE_WEBHOOK_SECRET` must start with `whsec_` (503 otherwise)
3. Verified: `stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)`
4. Invalid signature: return 400
5. Idempotency: duplicate `stripe_event_id` silently ignored

### Local Webhook Testing

```bash
stripe listen --forward-to http://localhost:8100/api/v1/billing/webhook
# Copy the signing secret (whsec_...) to STRIPE_WEBHOOK_SECRET
```

---

## Customer Portal

```
POST /api/v1/billing/portal → { "portal_url": "..." }
```

Requires:
1. Stripe configured (503 otherwise)
2. Org must have `stripe_customer_id` — set after first paid checkout (400 otherwise)
3. User redirected to Stripe-hosted portal to manage subscription

---

## Feature Gate

`app/services/billing.py`:
```python
can_use_feature(subscription, "can_use_magic_revert")  # → bool
check_usage_limit(org_id, "bulk_edits_used", db)       # → bool (within limit)
increment_usage(org_id, "bulk_edits_used", db)          # increments UsageCounter
```

Feature gate FastAPI dependency:
```python
# app/core/deps.py
get_current_org_id  # resolves org_id from user's membership
```

---

## Subscription Status Values

| Status | Meaning |
|---|---|
| `free` | No Stripe subscription, free plan |
| `active` | Paying and in good standing |
| `trialing` | In trial period |
| `past_due` | Payment failed, grace period |
| `canceled` | Canceled, access ends at current_period_end |
| `incomplete` | Checkout incomplete |
| `unpaid` | Multiple payment failures |

---

## Usage Counters

Tracked in `usage_counters` table, scoped by `organization_id` + `period_key` (YYYY-MM):
- `bulk_edits_used`
- `ai_credits_used`
- `listings_synced`
- `media_assets_used`

GET `/api/v1/billing/usage` returns current period usage + plan limits.

---

## Configuration Required

Set in `.env`:
```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC_MONTHLY=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_BASIC_YEARLY=price_...
STRIPE_PRICE_PRO_YEARLY=price_...
```

Without valid keys, checkout/portal return 503 with `"Stripe is not configured."` / `"Stripe webhook is not configured."`.

---

## Known Limitations

- `stripe.Webhook.construct_event` is synchronous and blocks the event loop. Fix with `anyio.to_thread.run_sync` in Sprint 18.
- No invoice listing endpoint yet (Sprint future).
- No trial period configuration yet.
