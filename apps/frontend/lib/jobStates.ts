// Canonical apply/revert job state presentation (M04.03) — shared friendly
// labels + badge colors for Bulk Edit, Magic Revert, and Account Activity.
// DB status stays completed/completed_with_errors/failed/etc underneath
// (see apps/backend/app/core/job_states.py); `canonical_state` is what the
// API returns for apply jobs. RevertJob has no canonical_state field of its
// own (its status vocabulary — pending/running/completed/
// completed_with_errors/failed — is already small and unambiguous), so the
// same label/badge maps cover both by including the raw values too.
export const JOB_STATE_LABELS: Record<string, string> = {
  pending: "Pending",
  running: "Running",
  succeeded: "Succeeded",
  partially_failed: "Partially failed",
  failed: "Failed",
  rate_limited: "Rate limited",
  cancelled: "Cancelled",
  reverted: "Reverted",
  revert_failed: "Revert failed",
  // Raw DB values, for anywhere that only has the raw status (e.g. RevertJob)
  completed: "Completed",
  completed_with_errors: "Completed with errors",
};

export function jobStateLabel(state: string): string {
  return JOB_STATE_LABELS[state] ?? state.replace(/_/g, " ");
}

export const JOB_STATE_BADGE_CLASS: Record<string, string> = {
  succeeded: "bg-green-100 text-green-700",
  completed: "bg-green-100 text-green-700",
  partially_failed: "bg-orange-100 text-orange-700",
  completed_with_errors: "bg-orange-100 text-orange-700",
  failed: "bg-red-100 text-red-700",
  rate_limited: "bg-orange-100 text-orange-700",
  running: "bg-blue-100 text-blue-700",
  pending: "bg-gray-100 text-gray-600",
  reverted: "bg-purple-100 text-purple-700",
  revert_failed: "bg-red-100 text-red-700",
  cancelled: "bg-gray-100 text-gray-500",
};

export function jobStateBadgeClass(state: string): string {
  return JOB_STATE_BADGE_CLASS[state] ?? "bg-gray-100 text-gray-600";
}
