"""Tests for the public contact form endpoint. EMAIL_PROVIDER stays
'disabled' in tests (default) — no real email is ever sent from this file.
"""
import pytest

CONTACT_URL = "/api/v1/contact"

VALID_PAYLOAD = {
    "name": "Jane Seller",
    "email": "jane@example.com",
    "subject": "Billing question",
    "message": "How do I upgrade my plan?",
}


@pytest.mark.anyio
async def test_contact_valid_request_email_disabled(client):
    """With EMAIL_PROVIDER=disabled (test default), the endpoint must not
    crash and must clearly report delivery is not configured."""
    r = await client.post(CONTACT_URL, json=VALID_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["delivered"] is False
    assert "not configured" in data["message"].lower() or "email us directly" in data["message"].lower()


@pytest.mark.anyio
async def test_contact_invalid_email_rejected(client):
    r = await client.post(CONTACT_URL, json={**VALID_PAYLOAD, "email": "not-an-email"})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_contact_missing_name_rejected(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "name"}
    r = await client.post(CONTACT_URL, json=payload)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_contact_missing_message_rejected(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "message"}
    r = await client.post(CONTACT_URL, json=payload)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_contact_blank_message_rejected(client):
    r = await client.post(CONTACT_URL, json={**VALID_PAYLOAD, "message": "   "})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_contact_oversized_message_rejected(client):
    r = await client.post(CONTACT_URL, json={**VALID_PAYLOAD, "message": "x" * 5001})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_contact_no_auth_required(client):
    """Contact form is public — must work with zero Authorization header."""
    r = await client.post(CONTACT_URL, json=VALID_PAYLOAD)
    assert r.status_code != 401
    assert r.status_code != 403
