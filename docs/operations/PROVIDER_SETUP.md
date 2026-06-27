# Provider Setup Guide

## Stripe

### Prerequisites

- A Stripe account (stripe.com)
- Your domain verified and SSL active
- Backend deployed and accessible at `https://api.bulk-edit.com`

### Setup Checklist

**Products and Prices:**

- [ ] In Stripe Dashboard → Products, create:
  - **Bulk-Edit Basic (Monthly)** — set `STRIPE_PRICE_BASIC_MONTHLY=price_...`
  - **Bulk-Edit Pro (Monthly)** — set `STRIPE_PRICE_PRO_MONTHLY=price_...`
  - **Bulk-Edit Basic (Yearly)** — set `STRIPE_PRICE_BASIC_YEARLY=price_...`
  - **Bulk-Edit Pro (Yearly)** — set `STRIPE_PRICE_PRO_YEARLY=price_...`

**API Keys:**

- [ ] Switch Stripe Dashboard to **Live mode**
- [ ] Developers → API keys → copy Secret key → `STRIPE_SECRET_KEY=sk_live_...`

**Webhook:**

- [ ] Developers → Webhooks → Add endpoint
  - URL: `https://api.bulk-edit.com/api/v1/billing/webhook`
  - Events to send:
    - `checkout.session.completed`
    - `customer.subscription.created`
    - `customer.subscription.updated`
    - `customer.subscription.deleted`
    - `invoice.payment_succeeded`
    - `invoice.payment_failed`
- [ ] Copy Signing secret → `STRIPE_WEBHOOK_SECRET=whsec_...`

**Staging Setup (parallel):**

- [ ] Create separate webhook endpoint for staging at `https://api-staging.bulk-edit.com/api/v1/billing/webhook`
- [ ] Use Stripe **Test mode** for staging (key starts with `sk_test_`)

### Testing Stripe

```bash
# Test a checkout session (staging)
curl -X POST https://api-staging.bulk-edit.com/api/v1/billing/checkout \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"plan":"pro_monthly"}'
```

Test cards (use in Stripe test mode):

| Card | Behavior |
|---|---|
| `4242 4242 4242 4242` | Success |
| `4000 0000 0000 9995` | Declined |
| `4000 0025 0000 3155` | 3D Secure required |

Verify webhooks: Stripe Dashboard → Webhooks → your endpoint → Send test event.

---

## Etsy

### Prerequisites

- An Etsy seller account
- Your production domain active with SSL
- Backend deployed

### Setup Checklist

- [ ] Go to [etsy.com/developers](https://www.etsy.com/developers) → Create app (for production)
- [ ] App settings:
  - Name: Bulk-Edit (or your SaaS product name)
  - Redirect URIs: `https://bulk-edit.com/etsy/callback`
- [ ] Copy **Keystring** → `ETSY_CLIENT_ID=...`
- [ ] Note the app's **Shared Secret** if needed (Etsy v3 uses PKCE — client secret may not be required for public clients)
- [ ] Set `ETSY_REDIRECT_URI=https://bulk-edit.com/etsy/callback`
- [ ] Set `ETSY_SCOPES=listings_r listings_w shops_r profile_r`

**Staging app (separate):**

- [ ] Create a separate Etsy app for staging
- [ ] Redirect URI: `https://staging.bulk-edit.com/etsy/callback`
- [ ] Use staging ETSY_CLIENT_ID and ETSY_REDIRECT_URI

### API Rate Limits

Etsy API v3 allows approximately 5 requests/second per OAuth token.

Bulk operations are rate-limited in the app (one listing write per API call). For large batches, the built-in safety gates ensure no runaway API usage.

### Testing Etsy

1. Connect a shop via the `/shops` page
2. Trigger a listing sync
3. Run a bulk edit preview (does not write to Etsy)
4. Confirm the Safe Write Flow before applying:
   - Preview → User confirmation → Backup snapshot → Etsy write → Audit log

---

## AI Provider

### OpenAI

- [ ] Create account at [platform.openai.com](https://platform.openai.com)
- [ ] API Keys → Create secret key → `OPENAI_API_KEY=sk-...`
- [ ] Set `AI_PROVIDER=openai`
- [ ] Set `OPENAI_MODEL=gpt-4o-mini` (cost-efficient) or `gpt-4o` (highest quality)
- [ ] Set a monthly spend limit in OpenAI dashboard (Usage → Limits)
- [ ] Set `AI_REQUEST_TIMEOUT_SECONDS=30`

### Anthropic

- [ ] Create account at [console.anthropic.com](https://console.anthropic.com)
- [ ] API Keys → Create key → `ANTHROPIC_API_KEY=sk-ant-...`
- [ ] Set `AI_PROVIDER=anthropic`
- [ ] Set `ANTHROPIC_MODEL=claude-sonnet-4-6`
- [ ] Set a monthly budget in Anthropic console

### Mock Provider (Development / CI)

Set `AI_PROVIDER=mock` to disable real AI calls. All AI endpoints return static placeholder responses. No API cost. Used in CI automatically.

### Cost Monitoring

- OpenAI: set monthly spend limit in dashboard → Settings → Limits
- Anthropic: set budget alert in console
- Alert at 80% of monthly budget to avoid unexpected overage
- The app gates AI use behind paid plan subscription (free plan has 0 AI credits)

---

## Email / Contact Form

The contact form at `/contact-us` is currently a **demo form** (submits locally, no email delivery).

To activate real email delivery, integrate one of these providers:

| Provider | Free Tier | Notes |
|---|---|---|
| [Resend](https://resend.com) | 3,000/month | Developer-friendly, excellent DX |
| [SendGrid](https://sendgrid.com) | 100/day | Industry standard |
| [AWS SES](https://aws.amazon.com/ses/) | 62,000/month (from EC2) | Cheapest at scale, domain verification required |
| [Postmark](https://postmarkapp.com) | 100/month | Focused on transactional email |

Required environment variables (once implemented):

```
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=re_...
CONTACT_FROM_EMAIL=noreply@bulk-edit.com
CONTACT_TO_EMAIL=support@bulk-edit.com
```

---

## Sentry (Error Monitoring)

- [ ] Create account at [sentry.io](https://sentry.io)
- [ ] Create a new project → Python → FastAPI
- [ ] Copy DSN → `SENTRY_DSN=https://...@sentry.io/...`
- [ ] Set `SENTRY_ENVIRONMENT=production` (or `staging`)
- [ ] Set `SENTRY_TRACES_SAMPLE_RATE=0.05` (5% performance traces — adjust based on traffic)

Sentry integration in the backend:
- Auto-captures unhandled exceptions
- Scrubs secrets before sending (password, tokens, API keys, authorization headers)
- No-op if `SENTRY_DSN` is empty or missing

Verify after deploy: trigger a test error (hit a non-existent endpoint) and confirm it appears in the Sentry dashboard.
