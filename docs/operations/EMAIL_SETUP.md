# Email Setup

How to enable real email delivery for password reset and the contact form.
Safe by default: with no configuration, `EMAIL_PROVIDER=disabled` and the
app never attempts to send anything — password reset and contact form
both degrade gracefully instead of crashing.

## Required env vars

| Var | Default | Notes |
|---|---|---|
| `EMAIL_PROVIDER` | `disabled` | Set to `smtp` to enable real delivery |
| `SMTP_HOST` | _(empty)_ | e.g. `smtp.resend.com` |
| `SMTP_PORT` | `587` | Standard TLS submission port |
| `SMTP_USERNAME` | _(empty)_ | Provider-specific; see below |
| `SMTP_PASSWORD` | _(empty)_ | **Secret** — set as an encrypted env var, never in `.env.example` or committed anywhere |
| `SMTP_FROM_EMAIL` | `noreply@bulkeditapp.com` | Must be a domain you control/verified with your provider |
| `SMTP_FROM_NAME` | `Bulk-Edit` | Display name on outgoing mail |
| `SMTP_USE_TLS` | `true` | STARTTLS on connect |
| `SUPPORT_EMAIL` | `support@bulk-edit.com` | Contact form notifications go here |
| `APP_PUBLIC_URL` | `http://localhost:3100` | Used to build the password-reset link (`{APP_PUBLIC_URL}/reset-password?token=...`) — set to `https://staging.bulkeditapp.com` on staging, `https://app.bulkeditapp.com` on production |

## Provider options (all generic-SMTP compatible)

The service (`apps/backend/app/services/email.py`) uses plain `smtplib` —
any provider that speaks SMTP works without code changes.

- **Resend** — `smtp.resend.com:587`, username `resend`, password = API key. Simple, modern, good free tier.
- **Postmark** — `smtp.postmarkapp.com:587`, username/password = server API token (same value for both). Strong deliverability, transactional-focused.
- **SendGrid** — `smtp.sendgrid.net:587`, username `apikey`, password = API key.
- **Mailgun** — `smtp.mailgun.org:587`, username = SMTP credentials from your domain, password = generated SMTP password.
- **Amazon SES** — `email-smtp.<region>.amazonaws.com:587`, username/password = SES SMTP credentials (not your AWS IAM keys — SES has a separate SMTP credential generator).
- **Self-hosted / other SMTP** — any host, port, username/password combination works the same way.

No single provider is hard-coded or required — pick one, set the env vars, done.

## Staging setup

1. Choose a provider (Resend or Postmark are the simplest to get a test domain going quickly).
2. Set these on the staging backend app (DO dashboard → encrypted env vars, same pattern as `JWT_SECRET`/`STRIPE_SECRET_KEY`):
   - `EMAIL_PROVIDER=smtp`
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` (secret), `SMTP_FROM_EMAIL`
   - `APP_PUBLIC_URL=https://staging.bulkeditapp.com`
3. Redeploy (or `doctl apps update --spec .do/app.staging-backend.yaml` if the spec itself changed — see the domain-drop incident note in `PRODUCTION_LAUNCH_FOLLOWUPS.md` for why that command needs care).
4. Test with the steps below.

## Production setup

Same as staging, on the production backend app, with `APP_PUBLIC_URL=https://app.bulkeditapp.com` and a from-address on your verified production sending domain. Do this only when you're ready to actually send real email — until then, leaving `EMAIL_PROVIDER=disabled` (the default) is the safe state.

## Testing forgot password

1. `POST /api/v1/auth/forgot-password` with `{"email": "you@example.com"}` for a real registered account.
2. Response is always the generic "if an account exists..." message — this is intentional (no user-enumeration signal).
3. If `EMAIL_PROVIDER=smtp` and configured correctly, check the inbox for a real email with a `https://.../reset-password?token=...` link.
4. If `EMAIL_PROVIDER=disabled`, no email is sent — check backend logs for `Email not sent (provider disabled/unconfigured)` to confirm the no-op path ran cleanly.
5. Follow the link, submit a new password via `/reset-password`, confirm login works with the new password and fails with the old one.

## Testing the contact form

1. Visit `/contact-us`, submit the form.
2. If email is configured, `SUPPORT_EMAIL` receives a `[Contact] <subject>` message with `Reply-To` set to the submitter's address.
3. If email is disabled, the form clearly shows "Email delivery isn't configured on this environment yet — please email us directly" instead of a fake success message.

## No secrets in repo

`SMTP_PASSWORD` and any provider API key are never placed in `.env.example`, this doc, or committed anywhere — they are set only as encrypted platform env vars (DO dashboard) or in the gitignored local `.env`.
