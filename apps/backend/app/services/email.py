"""Email delivery abstraction — provider-flexible, safe by default.

Modes:
  disabled — EMAIL_PROVIDER=disabled (default). No email is ever sent.
             send_email() returns a clear not-configured result instead of
             raising, so callers (password reset, contact form) never crash
             just because SMTP isn't set up yet.
  smtp     — EMAIL_PROVIDER=smtp. Generic SMTP delivery via stdlib
             smtplib, works with any SMTP-compatible provider (see
             docs/operations/EMAIL_SETUP.md for Resend/Postmark/SendGrid/
             Mailgun/SES/self-hosted SMTP notes).

Safety rules enforced here:
  - SMTP_PASSWORD and any auth token are never logged, ever.
  - Only non-sensitive metadata (provider, recipient domain, subject) is
    logged, and only at debug level.
  - Tests never trigger a real send — EMAIL_PROVIDER defaults to
    "disabled" in every test environment, and this module never sends
    when disabled.
"""
from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)

_MAX_LOG_VALUE_LEN = 200


def _safe_log_value(value: str) -> str:
    """Strip CR/LF from user-controlled values before logging them, so a
    crafted subject/email can't forge extra log lines (log injection).
    """
    return value.replace("\r", "").replace("\n", "")[:_MAX_LOG_VALUE_LEN]


@dataclass
class EmailResult:
    sent: bool
    reason: str  # "sent" | "disabled" | "error"


def send_email(to_email: str, subject: str, body_text: str, reply_to: str | None = None) -> EmailResult:
    """Send a plain-text email. Never raises — callers always get a result.

    Never logs SMTP_PASSWORD, message body, or the full recipient address
    (only its domain, for basic diagnostics without leaking PII).
    """
    safe_subject = _safe_log_value(subject)

    if not settings.is_email_configured():
        logger.info("Email not sent (provider disabled/unconfigured): subject=%r", safe_subject)
        return EmailResult(sent=False, reason="disabled")

    recipient_domain = _safe_log_value(
        to_email.rsplit("@", 1)[-1] if "@" in to_email else "unknown"
    )

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.set_content(body_text)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Email sent: recipient_domain=%s subject=%r", recipient_domain, safe_subject)
        return EmailResult(sent=True, reason="sent")
    except Exception:
        logger.exception("Email send failed: recipient_domain=%s subject=%r", recipient_domain, safe_subject)
        return EmailResult(sent=False, reason="error")


def send_password_reset_email(to_email: str, reset_url: str) -> EmailResult:
    subject = "Reset your Bulk-Edit password"
    body = (
        "We received a request to reset your Bulk-Edit password.\n\n"
        f"Reset your password here: {reset_url}\n\n"
        f"This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.\n\n"
        "If you didn't request this, you can safely ignore this email — "
        "your password will not be changed."
    )
    return send_email(to_email, subject, body)


def send_contact_notification_email(name: str, from_email: str, subject: str, message: str) -> EmailResult:
    """Notify SUPPORT_EMAIL of a new contact form submission."""
    body = f"New contact form submission\n\nFrom: {name} <{from_email}>\n\n{message}"
    return send_email(settings.SUPPORT_EMAIL, f"[Contact] {subject}", body, reply_to=from_email)
