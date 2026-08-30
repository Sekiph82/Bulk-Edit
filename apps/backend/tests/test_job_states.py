"""M04.03 — canonical apply/revert job state mapping. Pure function, no DB/HTTP."""
from app.core.job_states import canonical_apply_job_state


def test_pending():
    assert canonical_apply_job_state("pending") == "pending"


def test_running():
    assert canonical_apply_job_state("running") == "running"


def test_completed_maps_to_succeeded():
    assert canonical_apply_job_state("completed", success_count=5) == "succeeded"


def test_completed_with_errors_maps_to_partially_failed():
    assert canonical_apply_job_state("completed_with_errors", success_count=2) == "partially_failed"


def test_failed_maps_to_failed_without_rate_limit_signature():
    assert canonical_apply_job_state("failed", success_count=0, error_message="Listing not found.") == "failed"


def test_failed_with_429_signature_maps_to_rate_limited():
    assert canonical_apply_job_state("failed", error_message="HTTP 429: Too Many Requests") == "rate_limited"


def test_failed_with_rate_limit_words_maps_to_rate_limited():
    assert canonical_apply_job_state("failed", error_message="Exceeded per second rate limit") == "rate_limited"


def test_revert_completed_overrides_base_state_to_reverted():
    assert canonical_apply_job_state("completed", success_count=5, revert_status="completed") == "reverted"


def test_revert_failed_overrides_base_state_to_revert_failed():
    assert canonical_apply_job_state("completed", success_count=5, revert_status="failed") == "revert_failed"


def test_revert_completed_with_errors_maps_to_revert_failed():
    assert canonical_apply_job_state("completed", success_count=5, revert_status="completed_with_errors") == "revert_failed"


def test_revert_running_does_not_override_base_state():
    """A revert still in progress isn't "reverted" or "revert_failed" yet -- base apply state applies."""
    assert canonical_apply_job_state("completed", success_count=5, revert_status="running") == "succeeded"


def test_cancelled_is_never_produced():
    """No code path can cancel a running apply job today (TASKS.md M04.03) --
    this function must never claim otherwise."""
    for status in ("pending", "running", "completed", "completed_with_errors", "failed"):
        assert canonical_apply_job_state(status) != "cancelled"


def test_unknown_status_passes_through_rather_than_masking():
    assert canonical_apply_job_state("some_future_status") == "some_future_status"
