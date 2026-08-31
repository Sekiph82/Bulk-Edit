"use client";

import { Fragment, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  getAccessToken, ApiError,
  getApplyJobHistory, getApplyJobDetail, revertApplyJob, getRevertJob,
  type ApplyJobHistoryItem, type ApplyResult, type RevertResult,
} from "@/lib/api";
import { jobStateLabel, jobStateBadgeClass } from "@/lib/jobStates";

const RESULT_STATUS_BADGE: Record<string, string> = {
  success: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  skipped: "bg-gray-100 text-gray-500",
  pending: "bg-gray-100 text-gray-500",
  // M06.03: listing changed since the original apply — revert refused for
  // this item, not attempted. See error_message (rendered below) for the
  // exact "changed after apply" warning.
  conflict: "bg-amber-100 text-amber-800",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${jobStateBadgeClass(status)}`}>
      {jobStateLabel(status)}
    </span>
  );
}

function fmt(dt: string | null): string {
  return dt ? new Date(dt).toLocaleString() : "—";
}

function revertLabel(item: ApplyJobHistoryItem): string {
  if (item.can_revert) return "Revert available";
  if (item.revert_status === "running") return "Revert in progress";
  if (item.revert_status === "completed" || item.revert_status === "completed_with_errors") return "Already reverted";
  return item.revert_blocked_reason ?? "Not reversible";
}

function ResultsTable({ title, results }: { title: string; results: { id: string; etsy_listing_id: string; status: string; error_message: string | null }[] }) {
  if (results.length === 0) return null;
  return (
    <div className="mb-3 last:mb-0">
      <h4 className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 mb-1">{title}</h4>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-gray-400">
            <th className="text-left font-medium py-1">Etsy listing</th>
            <th className="text-left font-medium py-1">Status</th>
            <th className="text-left font-medium py-1">Detail</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {results.map((r) => (
            <tr key={r.id}>
              <td className="py-1.5 pr-3">#{r.etsy_listing_id}</td>
              <td className="py-1.5 pr-3">
                <span className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-medium ${RESULT_STATUS_BADGE[r.status] ?? "bg-gray-100 text-gray-500"}`}>
                  {r.status}
                </span>
              </td>
              <td className="py-1.5 text-gray-500">{r.error_message ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function JobDetail({ jobId, revertJobId }: { jobId: string; revertJobId: string | null }) {
  const [results, setResults] = useState<ApplyResult[] | null>(null);
  const [revertResults, setRevertResults] = useState<RevertResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getApplyJobDetail(jobId)
      .then((d) => setResults(d.results))
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load job details."));
    if (revertJobId) {
      getRevertJob(revertJobId)
        .then((d) => setRevertResults(d.results))
        .catch(() => setRevertResults([])); // non-fatal — apply results still show
    } else {
      setRevertResults(null);
    }
  }, [jobId, revertJobId]);

  if (error) return <p className="text-xs text-red-600 px-4 py-3">{error}</p>;
  if (!results) return <p className="text-xs text-gray-400 px-4 py-3">Loading item results…</p>;
  if (results.length === 0 && (!revertResults || revertResults.length === 0)) {
    return <p className="text-xs text-gray-400 px-4 py-3">No item results recorded.</p>;
  }

  return (
    <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
      <ResultsTable
        title={revertJobId ? "Apply results" : "Item results"}
        results={results.map((r) => ({ id: r.id, etsy_listing_id: r.etsy_listing_id, status: r.status, error_message: r.error_message }))}
      />
      {revertJobId && revertResults && (
        <ResultsTable
          title="Revert results"
          results={revertResults.map((r) => ({ id: r.id, etsy_listing_id: r.etsy_listing_id, status: r.status, error_message: r.error_message }))}
        />
      )}
    </div>
  );
}

export default function MagicRevertPage() {
  const router = useRouter();
  const [items, setItems] = useState<ApplyJobHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [revertableOnly, setRevertableOnly] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const [confirmJob, setConfirmJob] = useState<ApplyJobHistoryItem | null>(null);
  const [reverting, setReverting] = useState(false);
  const [revertMsg, setRevertMsg] = useState<string | null>(null);
  const [revertErr, setRevertErr] = useState<string | null>(null);
  const revertInFlightRef = useRef(false);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    load();
  }, [statusFilter]);

  function load() {
    setLoading(true);
    setError(null);
    getApplyJobHistory({ per_page: 50, status: statusFilter || undefined })
      .then((page) => setItems(page.items))
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) { router.push("/login"); return; }
        setError(e instanceof ApiError ? e.message : "Failed to load apply job history.");
      })
      .finally(() => setLoading(false));
  }

  async function handleRevertConfirmed() {
    if (!confirmJob) return;
    if (revertInFlightRef.current) return;
    revertInFlightRef.current = true;
    const job = confirmJob;
    setConfirmJob(null);
    setReverting(true);
    setRevertErr(null);
    setRevertMsg(null);
    try {
      const revertJob = await revertApplyJob(job.id);
      setRevertMsg(`Revert ${revertJob.status} — ${revertJob.success_count} restored, ${revertJob.failure_count} failed, ${revertJob.skipped_count} skipped.`);
      load();
    } catch (e) {
      setRevertErr(e instanceof ApiError ? e.message : "Revert failed.");
    } finally {
      setReverting(false);
      revertInFlightRef.current = false;
    }
  }

  const filtered = revertableOnly ? items.filter((i) => i.can_revert) : items;

  return (
    <main className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Magic Revert</h1>
        <p className="text-sm text-gray-500 mt-1">Review recent Bulk Edit apply jobs and revert eligible jobs.</p>
      </div>

      {revertMsg && (
        <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-700">{revertMsg}</div>
      )}
      {revertErr && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">{revertErr}</div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
        >
          <option value="">All statuses</option>
          <option value="completed">Completed</option>
          <option value="completed_with_errors">Completed with errors</option>
          <option value="failed">Failed</option>
        </select>
        <label className="flex items-center gap-1.5 text-sm text-gray-600">
          <input type="checkbox" checked={revertableOnly} onChange={(e) => setRevertableOnly(e.target.checked)} className="rounded" />
          Revertable only
        </label>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">{error}</div>
      ) : filtered.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-10 text-center">
          <p className="text-gray-500 text-sm mb-3">No apply jobs yet.</p>
          <Link href="/bulk-edit" className="text-indigo-600 font-medium text-sm hover:underline">Go to Bulk Edit →</Link>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Items</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Revert</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((item) => (
                <Fragment key={item.id}>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-700 text-xs">{fmt(item.created_at)}</td>
                    <td className="px-4 py-3"><StatusBadge status={item.canonical_state ?? item.status} /></td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      {item.success_count} success / {item.failure_count} failed / {item.skipped_count} skipped
                    </td>
                    <td className="px-4 py-3 text-xs">
                      <span className={item.can_revert ? "text-green-700 font-medium" : "text-gray-400"}>
                        {revertLabel(item)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                          className="text-xs font-medium text-indigo-600 hover:underline"
                        >
                          {expandedId === item.id ? "Hide details" : "View details"}
                        </button>
                        <button
                          onClick={() => setConfirmJob(item)}
                          disabled={!item.can_revert || reverting}
                          className="text-xs font-medium text-red-600 hover:underline disabled:text-gray-300 disabled:no-underline disabled:cursor-not-allowed"
                          title={item.can_revert ? "" : revertLabel(item)}
                        >
                          Revert
                        </button>
                      </div>
                    </td>
                  </tr>
                  {expandedId === item.id && (
                    <tr>
                      <td colSpan={5} className="p-0">
                        <JobDetail jobId={item.id} revertJobId={item.revert_job_id} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Blocking overlay while a revert is in flight — same standard as Bulk Edit (UX-01A) */}
      {reverting && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[70]" role="status" aria-live="polite">
          <div className="bg-white rounded-2xl shadow-xl px-8 py-7 max-w-sm w-full mx-4 text-center">
            <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
            <p className="text-base font-semibold text-gray-900 mb-1">Reverting Etsy listings…</p>
            <p className="text-sm text-gray-600">Please keep this page open. Bulk Edit is restoring backup snapshots safely.</p>
          </div>
        </div>
      )}

      {/* Confirmation modal */}
      {confirmJob && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Confirm Magic Revert</h3>
            <p className="text-sm text-gray-600 mb-4">
              This will restore <strong>{confirmJob.success_count}</strong> listing(s) on Etsy to their pre-apply
              state using backup snapshots. This writes back to Etsy and cannot be undone. Keep this page open
              until it finishes.
            </p>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setConfirmJob(null)} className="border border-gray-300 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-50">
                Cancel
              </button>
              <button onClick={handleRevertConfirmed} className="bg-red-600 hover:bg-red-700 text-white text-sm font-medium px-5 py-2 rounded-lg">
                Yes, Revert Etsy Listings
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center gap-4 pt-2">
        <Link href="/bulk-edit" className="text-sm font-medium text-indigo-600 hover:underline">Go to Bulk Edit →</Link>
        <Link href="/account/activity" className="text-sm font-medium text-indigo-600 hover:underline">View Activity &amp; Audit →</Link>
      </div>
    </main>
  );
}
