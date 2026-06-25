# Stripe Billing Integration

## Products and Prices

Created in Stripe Dashboard and configured via environment variables:

| Plan | ENV var | Stripe type |
|---|---|---|
| Pro Monthly | `STRIPE_PRICE_PRO_MONTHLY` | Recurring, monthly |
| Pro Yearly | `STRIPE_PRICE_PRO_YEARLY` | Recurring, yearly |

---

## Checkout Flow

1. Frontend calls `POST /billing/checkout` with `{ plan: 'pro_monthly' }`
2. Backend creates Stripe Checkout Session:
   - `mode: 'subscription'`
   - `price_id: env.STRIPE_PRICE_PRO_MONTHLY`
   - `customer_email: user.email`
   - `metadata: { organization_id: org.id }`
   - `success_url: /billing/success`
   - `cancel_url: /billing/cancel`
3. Backend returns `{ checkout_url }`
4. Frontend redirects to Stripe Checkout
5. User completes payment
6. Stripe fires `checkout.session.completed` webhook
7. Backend syncs subscription status

---

## Webhook Events Handled

| Event | Action |
|---|---|
| `checkout.session.completed` | Create/update subscription, set status=active |
| `customer.subscription.updated` | Sync plan and status |
| `customer.subscription.deleted` | Set status=canceled |
| `invoice.payment_succeeded` | Log payment, extend period_end |
| `invoice.payment_failed` | Set status=past_due, email user |

### Webhook Security

Every webhook request must:
1. Have `Stripe-Signature` header
2. Be verified: `stripe.webhooks.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)`
3. If verification fails: return 400, log attempt

---

## Customer Portal

For subscription management (cancel, change plan, view invoices):
1. Backend creates Stripe Customer Portal session
2. `POST /billing/portal` → returns `{ portal_url }`
3. Frontend redirects to Stripe portal
4. User manages subscription on Stripe's hosted page

---

## Feature Gate Implementation

```python
# Middleware pseudocode
def require_pro(organization_id):
    sub = db.query(Subscription).filter_by(organization_id=organization_id).first()
    if sub.plan == 'free' or sub.status != 'active':
        raise HTTPException(403, "SUBSCRIPTION_REQUIRED")
```

Applied as FastAPI dependency injection on protected routes.

---

## Subscription Status in DB

`subscriptions.status` values:
- `active` — paying and in good standing
- `trialing` — in trial period
- `past_due` — payment failed, grace period
- `canceled` — canceled, access ends at `current_period_end`
- `free` — no Stripe subscription (free plan)

Free plan rows have `stripe_subscription_id = null`.

---

## Usage Limits Enforcement

Usage counters tracked in Redis per organization per calendar month:
- `org:{org_id}:bulk_edits:{YYYY-MM}` — bulk edit count
- `org:{org_id}:ai_uses:{YYYY-MM}` — AI tool use count

Reset automatically on month rollover.

---

## Blockers

If `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` are not set, billing cannot be tested live. Use Stripe's test mode keys and `stripe listen --forward-to localhost:8000/api/v1/billing/webhook` for local webhook testing.
