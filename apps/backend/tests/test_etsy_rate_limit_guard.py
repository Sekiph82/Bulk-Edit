"""
Sprint: Etsy rate-limit guard/backoff for Bulk Edit writes.

Unit tests for the shared retry/backoff/pacing primitives in
app.services.etsy_http. No Etsy API call is made anywhere in this file —
all httpx clients/requests are mocked or faked in-process.

All sleep/time functions are injected (sleep_fn/now_fn/jitter_fn) so no test
here ever performs a real asyncio.sleep — see conftest.py's
_reset_etsy_write_pacing_state for why that matters process-wide too.
"""
import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.etsy_http import (
    classify_etsy_write_status,
    compute_backoff_delay,
    parse_retry_after_seconds,
    sleep_before_etsy_write,
)


# ── parse_retry_after_seconds ──────────────────────────────────────────────

def test_parse_retry_after_seconds_numeric():
    assert parse_retry_after_seconds("3") == 3.0


def test_parse_retry_after_seconds_float_string():
    assert parse_retry_after_seconds("1.5") == 1.5


def test_parse_retry_after_seconds_missing():
    assert parse_retry_after_seconds(None) is None


def test_parse_retry_after_seconds_empty_string():
    assert parse_retry_after_seconds("") is None


def test_parse_retry_after_seconds_http_date_unsupported():
    # HTTP-date form is explicitly not parsed — Etsy has only been observed
    # sending delay-seconds, so this must return None, not raise or guess.
    assert parse_retry_after_seconds("Wed, 21 Oct 2026 07:28:00 GMT") is None


def test_parse_retry_after_seconds_negative_rejected():
    assert parse_retry_after_seconds("-5") is None


# ── compute_backoff_delay ──────────────────────────────────────────────────

def test_compute_backoff_delay_uses_retry_after_verbatim_no_jitter():
    assert compute_backoff_delay(1, retry_after_seconds=7.0, jitter_fn=lambda: 999.0) == 7.0


def test_compute_backoff_delay_first_attempt_default_base():
    assert compute_backoff_delay(1, None, jitter_fn=lambda: 1.0) == 2.0


def test_compute_backoff_delay_second_attempt_doubles():
    assert compute_backoff_delay(2, None, jitter_fn=lambda: 1.0) == 4.0


def test_compute_backoff_delay_applies_jitter():
    assert compute_backoff_delay(1, None, jitter_fn=lambda: 0.5) == 1.0


def test_compute_backoff_delay_negative_retry_after_floored_to_zero():
    assert compute_backoff_delay(1, retry_after_seconds=-1.0) == 0.0


# ── classify_etsy_write_status ─────────────────────────────────────────────

@pytest.mark.parametrize("status,expected", [
    (429, "rate_limited"),
    (400, "validation_rejected"),
    (401, "access_denied"),
    (403, "access_denied"),
    (404, "not_found"),
    (500, "server_error"),
    (503, "server_error"),
    (200, "unknown"),
])
def test_classify_etsy_write_status(status, expected):
    assert classify_etsy_write_status(status) == expected


# ── _request_with_retry via etsy_get/etsy_patch/etsy_put ───────────────────

def _resp(status_code: int, headers: dict | None = None) -> MagicMock:
    r = MagicMock(spec=httpx.Response)
    r.status_code = status_code
    r.headers = headers or {}
    return r


async def _retry(client, method: str, sleep_fn):
    # etsy_get/etsy_patch/etsy_put are thin wrappers with no sleep injection
    # point (production always uses real asyncio.sleep) — the shared retry
    # core they all delegate to (_request_with_retry) is the documented test
    # seam, exactly like sleep_before_etsy_write's own sleep_fn/now_fn params.
    from app.services.etsy_http import _request_with_retry
    make_request = getattr(client, method)
    return await _request_with_retry(lambda: make_request("http://x"), "test", sleep_fn=sleep_fn)


async def test_etsy_get_retries_429_then_succeeds():
    responses = [_resp(429, {"Retry-After": "0"}), _resp(200)]
    client = MagicMock()
    client.get = AsyncMock(side_effect=responses)
    sleep_fn = AsyncMock()

    resp = await _retry(client, "get", sleep_fn)
    assert resp.status_code == 200
    assert client.get.call_count == 2
    sleep_fn.assert_awaited_once()


async def test_retry_stops_after_success_no_further_calls():
    client = MagicMock()
    client.get = AsyncMock(return_value=_resp(200))
    sleep_fn = AsyncMock()
    resp = await _retry(client, "get", sleep_fn)
    assert resp.status_code == 200
    assert client.get.call_count == 1
    sleep_fn.assert_not_awaited()


async def test_retry_exhaustion_returns_final_429_without_raising(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ETSY_RETRY_MAX_ATTEMPTS", 3)
    client = MagicMock()
    client.put = AsyncMock(return_value=_resp(429, {"Retry-After": "0"}))
    sleep_fn = AsyncMock()
    resp = await _retry(client, "put", sleep_fn)
    assert resp.status_code == 429
    assert client.put.call_count == 3
    assert sleep_fn.await_count == 2  # between attempt 1→2 and 2→3, not after the final attempt


async def test_non_retryable_400_returns_immediately_no_retry():
    client = MagicMock()
    client.patch = AsyncMock(return_value=_resp(400))
    sleep_fn = AsyncMock()
    resp = await _retry(client, "patch", sleep_fn)
    assert resp.status_code == 400
    assert client.patch.call_count == 1
    sleep_fn.assert_not_awaited()


# ── sleep_before_etsy_write pacing ──────────────────────────────────────────

async def test_sleep_before_etsy_write_no_wait_on_first_call():
    sleep_fn = AsyncMock()
    now_fn = MagicMock(return_value=100.0)
    waited = await sleep_before_etsy_write(
        "shop_a", min_interval_seconds=1.1, sleep_fn=sleep_fn, now_fn=now_fn,
    )
    assert waited == 0.0
    sleep_fn.assert_not_awaited()


async def test_sleep_before_etsy_write_paces_second_call_same_shop():
    sleep_fn = AsyncMock()
    now_values = iter([100.0, 100.2, 100.2])  # first call, second call, post-sleep re-read
    now_fn = MagicMock(side_effect=lambda: next(now_values))

    await sleep_before_etsy_write("shop_b", min_interval_seconds=1.1, sleep_fn=sleep_fn, now_fn=now_fn)
    waited = await sleep_before_etsy_write("shop_b", min_interval_seconds=1.1, sleep_fn=sleep_fn, now_fn=now_fn)

    assert waited == pytest.approx(0.9)
    sleep_fn.assert_awaited_once_with(pytest.approx(0.9))


async def test_sleep_before_etsy_write_independent_per_shop():
    sleep_fn = AsyncMock()
    now_fn = MagicMock(return_value=200.0)

    await sleep_before_etsy_write("shop_c", min_interval_seconds=1.1, sleep_fn=sleep_fn, now_fn=now_fn)
    waited = await sleep_before_etsy_write("shop_d", min_interval_seconds=1.1, sleep_fn=sleep_fn, now_fn=now_fn)

    assert waited == 0.0  # different shop key, no cross-shop throttling
    sleep_fn.assert_not_awaited()


async def test_sleep_before_etsy_write_no_wait_once_interval_elapsed():
    sleep_fn = AsyncMock()
    now_values = iter([100.0, 102.0])
    now_fn = MagicMock(side_effect=lambda: next(now_values))

    await sleep_before_etsy_write("shop_e", min_interval_seconds=1.1, sleep_fn=sleep_fn, now_fn=now_fn)
    waited = await sleep_before_etsy_write("shop_e", min_interval_seconds=1.1, sleep_fn=sleep_fn, now_fn=now_fn)

    assert waited == 0.0
    sleep_fn.assert_not_awaited()
