"""Unit tests for the email service abstraction. Never triggers a real
send — EMAIL_PROVIDER defaults to 'disabled', and the smtp-mode branch is
tested only against a stubbed smtplib.SMTP so no network call ever happens.
"""
from unittest.mock import MagicMock, patch

from app.services.email import (
    send_email,
    send_password_reset_email,
    send_contact_notification_email,
    _parse_recipient_list,
)
from app.core.config import settings


def test_send_email_disabled_by_default_returns_clear_result():
    assert settings.EMAIL_PROVIDER == "disabled"
    result = send_email("someone@example.com", "Subject", "Body")
    assert result.sent is False
    assert result.reason == "disabled"


def test_send_email_disabled_never_raises():
    # Must not raise even with a weird recipient — disabled mode short-circuits
    # before any SMTP interaction, so nothing can throw.
    result = send_email("", "", "")
    assert result.sent is False


def test_send_password_reset_email_disabled_returns_not_sent():
    result = send_password_reset_email("user@example.com", "https://example.com/reset-password?token=abc")
    assert result.sent is False
    assert result.reason == "disabled"


def test_send_contact_notification_email_disabled_returns_not_sent():
    result = send_contact_notification_email("Name", "user@example.com", "Subject", "Message body")
    assert result.sent is False
    assert result.reason == "disabled"


def test_send_email_smtp_mode_uses_smtplib_and_never_logs_password(caplog):
    with patch.object(settings, "EMAIL_PROVIDER", "smtp"), \
         patch.object(settings, "SMTP_HOST", "smtp.test.local"), \
         patch.object(settings, "SMTP_FROM_EMAIL", "noreply@test.local"), \
         patch.object(settings, "SMTP_USERNAME", "testuser"), \
         patch.object(settings, "SMTP_PASSWORD", "super-secret-password-value"), \
         patch("smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        result = send_email("someone@example.com", "Test Subject", "Test body")

        assert result.sent is True
        assert result.reason == "sent"
        mock_server.login.assert_called_once_with("testuser", "super-secret-password-value")
        mock_server.send_message.assert_called_once()

    # The secret password must never appear in any log record.
    for record in caplog.records:
        assert "super-secret-password-value" not in record.getMessage()


def test_send_email_smtp_error_handled_gracefully():
    with patch.object(settings, "EMAIL_PROVIDER", "smtp"), \
         patch.object(settings, "SMTP_HOST", "smtp.test.local"), \
         patch.object(settings, "SMTP_FROM_EMAIL", "noreply@test.local"), \
         patch("smtplib.SMTP", side_effect=ConnectionError("boom")):
        result = send_email("someone@example.com", "Subject", "Body")
        assert result.sent is False
        assert result.reason == "error"


# ── Multiple support-recipient tests ──────────────────────────────────────

def test_parse_recipient_list_splits_trims_and_drops_empty():
    raw = "a@example.com, b@example.com ,, , c@example.com,"
    assert _parse_recipient_list(raw) == ["a@example.com", "b@example.com", "c@example.com"]


def test_parse_recipient_list_drops_entries_without_at_sign():
    raw = "a@example.com, not-an-email, b@example.com"
    assert _parse_recipient_list(raw) == ["a@example.com", "b@example.com"]


def test_parse_recipient_list_single_entry():
    assert _parse_recipient_list("only@example.com") == ["only@example.com"]


def test_parse_recipient_list_all_empty_returns_empty_list():
    assert _parse_recipient_list(" , , ") == []


def test_send_contact_notification_email_reaches_all_support_recipients(caplog):
    with patch.object(settings, "EMAIL_PROVIDER", "smtp"), \
         patch.object(settings, "SMTP_HOST", "smtp.test.local"), \
         patch.object(settings, "SMTP_FROM_EMAIL", "noreply@test.local"), \
         patch.object(settings, "SUPPORT_EMAIL", "support1@example.com, support2@example.com"), \
         patch("smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        result = send_contact_notification_email("Jane", "jane@customer.com", "Billing", "Help please")

        assert result.sent is True
        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["To"] == "support1@example.com, support2@example.com"

    # Full recipient addresses must never appear in logs — only a count.
    for record in caplog.records:
        msg = record.getMessage()
        assert "support1@example.com" not in msg
        assert "support2@example.com" not in msg
    assert any("2 recipients" in r.getMessage() for r in caplog.records)


def test_send_contact_notification_email_ignores_empty_comma_entries():
    with patch.object(settings, "EMAIL_PROVIDER", "smtp"), \
         patch.object(settings, "SMTP_HOST", "smtp.test.local"), \
         patch.object(settings, "SMTP_FROM_EMAIL", "noreply@test.local"), \
         patch.object(settings, "SUPPORT_EMAIL", "support1@example.com, , support2@example.com,"), \
         patch("smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        result = send_contact_notification_email("Jane", "jane@customer.com", "Billing", "Help please")

        assert result.sent is True
        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["To"] == "support1@example.com, support2@example.com"


def test_send_password_reset_email_remains_single_recipient_only():
    """Password reset must never fan out to multiple recipients, even if
    SUPPORT_EMAIL happens to be a comma-separated list elsewhere."""
    with patch.object(settings, "EMAIL_PROVIDER", "smtp"), \
         patch.object(settings, "SMTP_HOST", "smtp.test.local"), \
         patch.object(settings, "SMTP_FROM_EMAIL", "noreply@test.local"), \
         patch.object(settings, "SUPPORT_EMAIL", "support1@example.com, support2@example.com"), \
         patch("smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        result = send_password_reset_email("user@example.com", "https://example.com/reset-password?token=abc")

        assert result.sent is True
        sent_msg = mock_server.send_message.call_args[0][0]
        # Exactly the one target address — never expanded, never comma-joined.
        assert sent_msg["To"] == "user@example.com"
