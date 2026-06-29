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

---

## Video Generator (ffmpeg)

### How it works

The Video Generator converts listing photos into short MP4 slideshow videos. It requires ffmpeg on the backend server. Videos are never auto-uploaded to Etsy — the seller downloads and uploads manually.

### Setup

The backend Dockerfile installs ffmpeg automatically (`apt-get install ffmpeg`). To enable the feature:

1. Set `VIDEO_RENDERER_ENABLED=true` in your `.env` (or deployment environment).
2. Optionally set `FFMPEG_PATH` if ffmpeg is not on the system PATH.
3. Optionally set `VIDEO_OUTPUT_DIR` to override where MP4 files are stored (default: `/tmp/video_renders`).

```
VIDEO_RENDERER_ENABLED=true
FFMPEG_PATH=
VIDEO_OUTPUT_DIR=
```

### Customer behavior when disabled

- The Video Generator page is fully visible with all controls.
- When the customer clicks Generate Video and the renderer is disabled, a friendly modal explains the feature is not yet available.
- No environment variable names or setup instructions are shown to customers.

### Status check

```bash
GET /api/v1/video-generator/status
```

Returns `renderer_enabled` and `renderer_available`. If `renderer_enabled=true` but `renderer_available=false`, ffmpeg is not found in the container — rebuild or install ffmpeg.

---

## Pinterest Integration

### Prerequisites

- A Pinterest developer account at [developers.pinterest.com](https://developers.pinterest.com)
- An approved Pinterest app (sandbox available for development)

### Setup Checklist

- [ ] Create a Pinterest app at developers.pinterest.com
- [ ] Set the OAuth redirect URI in your Pinterest app to:
  - Local: `http://localhost:8100/api/v1/promote/pinterest/callback`
  - Production: `https://api.bulk-edit.com/api/v1/promote/pinterest/callback`
- [ ] Copy the App ID → `PINTEREST_CLIENT_ID=...`
- [ ] Copy the App Secret → `PINTEREST_CLIENT_SECRET=...`
- [ ] Set `PINTEREST_REDIRECT_URI` to match what you registered above
- [ ] Add scopes: `boards:read`, `pins:read`, `pins:write`, `user_accounts:read`

```
PINTEREST_CLIENT_ID=your_app_id
PINTEREST_CLIENT_SECRET=your_app_secret
PINTEREST_REDIRECT_URI=http://localhost:8100/api/v1/promote/pinterest/callback
```

### Customer behavior when not configured

- The Pinterest card on /promote shows "Connect" normally.
- When the customer clicks Connect and the app is not configured, a friendly modal explains Pinterest integration is not yet available.
- No environment variable names are shown to customers.

### Status check

```bash
GET /api/v1/promote/config-status
```

Returns `pinterest_configured: true` when all three vars are set. Never returns secret values.

---

## Instagram / Meta Integration

### Prerequisites

- A Meta developer account at [developers.facebook.com](https://developers.facebook.com)
- A Meta app with Instagram Basic Display or Instagram Graph API product
- Instagram publishing requires a **Business** or **Creator** account connected to a Facebook Page

### Setup Checklist

- [ ] Create a Meta app at developers.facebook.com
- [ ] Add Instagram Graph API product to your app
- [ ] Set the OAuth redirect URI in your Meta app to:
  - Local: `http://localhost:8100/api/v1/promote/instagram/callback`
  - Production: `https://api.bulk-edit.com/api/v1/promote/instagram/callback`
- [ ] Copy the App ID → `META_APP_ID=...`
- [ ] Copy the App Secret → `META_APP_SECRET=...`
- [ ] Set `INSTAGRAM_REDIRECT_URI` to match above
- [ ] Request `instagram_basic` and `instagram_content_publish` permissions (requires Meta app review for publish)

```
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
INSTAGRAM_REDIRECT_URI=http://localhost:8100/api/v1/promote/instagram/callback
```

### Customer behavior when not configured

- The Instagram card on /promote shows "Connect" normally.
- When the customer clicks Connect and the app is not configured, a friendly modal explains Instagram integration is not yet available.
- No environment variable names are shown to customers.

### Status check

```bash
GET /api/v1/promote/config-status
```

Returns `instagram_configured: true` when all three Meta vars are set. Never returns secret values.
