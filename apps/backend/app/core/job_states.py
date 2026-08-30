"""
Canonical apply/revert job state-machine presentation (M04.03).

DB `status` columns on BulkEditApplyJob/RevertJob use free-text values that
predate this mapping (`pending`, `running`, `completed`, `completed_with_errors`,
`failed`) and are NOT renamed here — historical job rows already exist in
production and renaming them would be a destructive migration for zero real
benefit (Option B from the task spec: backward-compatible canonical
presentation state, not a DB normalization migration).

`canonical_apply_job_state()` maps the existing DB status (plus optional
revert-linkage and a best-effort rate-limit signal) onto the target 9-state
vocabulary for API/UI presentation only:

    pending, running, succeeded, partially_failed, failed,
    rate_limited, cancelled, reverted, revert_failed

`cancelled` is part of the vocabulary but UNREACHABLE today — this app has
no code path that can cancel a running apply job (no cancel endpoint, no
`is_cancelled` flag, no architecture for safely stopping an in-flight Etsy
write loop mid-item). This function never returns it. Per this task's
explicit instruction, cancellation is documented as unsupported (TASKS.md
M04.03) rather than invented here.

`rate_limited` detection is a lightweight, best-effort text match on the
job's stored error message — the same "pattern-match the message" approach
already used by the frontend's `FAILURE_REASON_CATEGORY` (bulk-edit/page.tsx)
for item-level failures, since no structured failure-category column exists
on BulkEditApplyResult/BulkEditApplyJob today.
"""
from __future__ import annotations

_RATE_LIMIT_SIGNATURE = ("429", "rate limit", "rate_limited", "too many requests")


def _looks_rate_limited(error_message: str | None) -> bool:
    if not error_message:
        return False
    lowered = error_message.lower()
    return any(sig in lowered for sig in _RATE_LIMIT_SIGNATURE)


def canonical_apply_job_state(
    status: str,
    success_count: int = 0,
    error_message: str | None = None,
    revert_status: str | None = None,
) -> str:
    """Map a BulkEditApplyJob's raw DB status (+ optional revert linkage) to
    the canonical presentation state.

    `revert_status` is the *latest* RevertJob.status for this apply job, if
    one exists (None if never reverted) — the same value already computed by
    `bulk_edit_revert.get_revert_eligibility_map()`, so callers with access
    to that map should pass it through rather than leaving this at its
    default (which yields a base apply-only state).
    """
    if revert_status == "completed":
        return "reverted"
    if revert_status in ("completed_with_errors", "failed"):
        return "revert_failed"

    if status == "pending":
        return "pending"
    if status == "running":
        return "running"
    if status == "completed":
        return "succeeded"
    if status == "completed_with_errors":
        return "partially_failed"
    if status == "failed":
        return "rate_limited" if _looks_rate_limited(error_message) else "failed"
    return status  # unknown/future status value — pass through rather than mask it
