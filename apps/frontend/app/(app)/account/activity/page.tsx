"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  getAccessToken, ApiError, getApplyJobHistory, getAuditTrail, exportAuditTrailCSV,
  type ApplyJobHistoryItem, type FieldAuditLog, type AuditTrailFilters,
} from "@/lib/api";
import { jobStateLabel, jobStateBadgeClass } from "@/lib/jobStates";
import AccountPlaceholder from "@/components/account/AccountPlaceholder";

type ActivityRow = {
  key: string;
  type: "Bulk Edit Apply" | "Magic Revert";
  date: string | null;
  status: string;
  summary: string;
  applyJobId: string;
};

function toRows(items: ApplyJobHistoryItem[]): ActivityRow[] {
  const rows: ActivityRow[] = [];
  for (const item of items) {
    rows.push({
      key: `apply-${item.id}`,
      type: "Bulk Edit Apply",
      date: item.created_at,
      status: item.canonical_state ?? item.status,
      summary: `${item.success_count} success / ${item.failure_count} failed / ${item.skipped_count} skipped`,
      applyJobId: item.id,
    });
    if (item.revert_job_id && item.revert_status) {
      rows.push({
        key: `revert-${item.revert_job_id}`,
        type: "Magic Revert",
        date: item.finished_at ?? item.created_at,
        status: item.revert_status,
        summary: `Reverted apply job from ${new Date(item.created_at).toLocaleDateString()}`,
        applyJobId: item.id,
      });
    }
  }
  return rows.sort((a, b) => new Date(b.date ?? 0).getTime() - new Date(a.date ?? 0).getTime());
}

// ---- Audit Trail value rendering ----

function renderAuditValue(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "object") {
    try {
      return JSON.stringify(v);
    } catch {
      return String(v);
    }
  }
  return String(v);
}

function truncateText(s: string, max = 50): string {
  return s.length > max ? `${s.slice(0, max)}…` : s;
}

function AuditValueCell({ value }: { value: unknown }) {
  const full = renderAuditValue(value);
  if (full === "—") return <span className="text-gray-300">—</span>;
  return (
    <span title={full} className="cursor-help">
      {truncateText(full)}
    </span>
  );
}

const RESULT_STATUS_BADGE: Record<string, string> = {
  success: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  skipped: "bg-gray-100 text-gray-500",
};

function ResultStatusBadge({ status }: { status: string | null }) {
  if (!status) return <span className="text-gray-300">—</span>;
  return (
    <span className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-medium ${RESULT_STATUS_BADGE[status] ?? "bg-gray-100 text-gray-500"}`}>
      {status}
    </span>
  );
}

function RevertStatusBadge({ status }: { status: string | null }) {
  if (!status) return <span className="text-gray-300">Not reverted</span>;
  return (
    <span className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-medium ${jobStateBadgeClass(status)}`}>
      {jobStateLabel(status)}
    </span>
  );
}

function CopyableId({ id }: { id: string | null }) {
  const [copied, setCopied] = useState(false);
  if (!id) return <span className="text-gray-300">—</span>;
  return (
    <button
      type="button"
      title={id}
      onClick={() => {
        navigator.clipboard?.writeText(id).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1200);
        }).catch(() => {});
      }}
      className="font-mono text-[11px] text-gray-500 hover:text-indigo-600 hover:underline"
    >
      {copied ? "Copied!" : `${id.slice(0, 8)}…`}
    </button>
  );
}

const AUDIT_PER_PAGE = 25;

// A <input type="date"> value is a bare "YYYY-MM-DD" string with no
// timezone. `new Date("2026-08-31")` parses that as UTC midnight, which
// silently makes date_to mean "the very start of the selected day" instead
// of its end -- excluding nearly every record from the day the user
// actually picked. Parsing the parts and constructing a *local*-timezone
// Date instead means the boundaries follow the day as the user's own
// browser/clock understands it, in both directions.
function localDayStartISO(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  return new Date(y, m - 1, d, 0, 0, 0, 0).toISOString();
}

function localDayEndISO(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  return new Date(y, m - 1, d, 23, 59, 59, 999).toISOString();
}

// "Conflict" is deliberately not a quick filter here: AuditLog.revert_status
// is set from the *revert job's* overall status (see
// bulk_edit_apply.py::_field_audit_trail_query()'s docstring), not from the
// per-listing RevertResult.status a specific conflict actually lives on --
// a row's revert_status cannot truthfully answer "was THIS field's revert a
// conflict." Faking it here would silently mislead. Deferred to a future
// sprint that joins to RevertResult -- see DECISIONS.md/TASKS.md M06.03.
type QuickFilterKey = "failed" | "reverted" | "not_reverted" | "price" | "title";

const QUICK_FILTERS: { key: QuickFilterKey; label: string; filters: Partial<AuditTrailFilters> }[] = [
  { key: "failed", label: "Failed", filters: { result_status: "failed" } },
  { key: "reverted", label: "Reverted", filters: { revert_status: "completed" } },
  { key: "not_reverted", label: "Not reverted", filters: { revert_status: "not_reverted" } },
  { key: "price", label: "Price", filters: { field_name: "price_amount" } },
  { key: "title", label: "Title", filters: { field_name: "title" } },
];

function AuditTrailSection() {
  const [items, setItems] = useState<FieldAuditLog[] | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [applyJobId, setApplyJobId] = useState("");
  const [listingId, setListingId] = useState("");
  const [fieldName, setFieldName] = useState("");
  const [resultStatus, setResultStatus] = useState("");
  const [revertStatus, setRevertStatus] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [activeQuickFilter, setActiveQuickFilter] = useState<QuickFilterKey | null>(null);

  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const filters: AuditTrailFilters = {
    apply_job_id: applyJobId || undefined,
    listing_id: listingId || undefined,
    field_name: fieldName || undefined,
    result_status: resultStatus || undefined,
    revert_status: revertStatus || undefined,
    date_from: dateFrom ? localDayStartISO(dateFrom) : undefined,
    date_to: dateTo ? localDayEndISO(dateTo) : undefined,
  };
  const hasActiveFilters = Object.values(filters).some((v) => v !== undefined);

  const load = useCallback((p: number) => {
    setLoading(true);
    setError(null);
    getAuditTrail(filters, { page: p, per_page: AUDIT_PER_PAGE })
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
        setPage(res.page);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load audit trail."))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [applyJobId, listingId, fieldName, resultStatus, revertStatus, dateFrom, dateTo]);

  useEffect(() => {
    load(1);
  }, [load]);

  function applyQuickFilter(qf: (typeof QUICK_FILTERS)[number]) {
    if (activeQuickFilter === qf.key) {
      // toggle off
      setActiveQuickFilter(null);
      setResultStatus("");
      setRevertStatus("");
      setFieldName("");
      return;
    }
    setActiveQuickFilter(qf.key);
    setResultStatus(qf.filters.result_status ?? "");
    setRevertStatus(qf.filters.revert_status ?? "");
    setFieldName(qf.filters.field_name ?? "");
  }

  function clearFilters() {
    setApplyJobId(""); setListingId(""); setFieldName("");
    setResultStatus(""); setRevertStatus(""); setDateFrom(""); setDateTo("");
    setActiveQuickFilter(null);
  }

  async function handleExport() {
    setExporting(true);
    setExportError(null);
    try {
      await exportAuditTrailCSV(filters);
    } catch (e) {
      setExportError(e instanceof ApiError ? e.message : "Export failed.");
    } finally {
      setExporting(false);
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / AUDIT_PER_PAGE));

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">Write Audit Trail</h2>
          <p className="text-xs text-gray-500 mt-0.5">Every field Bulk Edit has written or attempted to write, per listing.</p>
        </div>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="border border-gray-300 text-gray-700 text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-gray-50 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {exporting ? "Exporting…" : "Export CSV"}
        </button>
      </div>

      {exportError && <p className="text-xs text-red-600">{exportError}</p>}

      {/* Quick filters */}
      <div className="flex flex-wrap gap-1.5">
        {QUICK_FILTERS.map((qf) => (
          <button
            key={qf.key}
            onClick={() => applyQuickFilter(qf)}
            className={`px-2.5 py-1 rounded-full text-[11px] font-medium border ${
              activeQuickFilter === qf.key
                ? "bg-indigo-600 border-indigo-600 text-white"
                : "border-gray-300 text-gray-600 hover:bg-gray-50"
            }`}
          >
            {qf.label}
          </button>
        ))}
        {hasActiveFilters && (
          <button onClick={clearFilters} className="px-2.5 py-1 rounded-full text-[11px] font-medium text-gray-400 hover:text-gray-600">
            Clear filters
          </button>
        )}
      </div>

      {/* Filter inputs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        <input
          type="text" placeholder="Apply job ID" value={applyJobId}
          onChange={(e) => { setApplyJobId(e.target.value); setActiveQuickFilter(null); }}
          className="border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
        <input
          type="text" placeholder="Listing ID" value={listingId}
          onChange={(e) => { setListingId(e.target.value); setActiveQuickFilter(null); }}
          className="border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
        <input
          type="text" placeholder="Field name" value={fieldName}
          onChange={(e) => { setFieldName(e.target.value); setActiveQuickFilter(null); }}
          className="border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
        <select
          value={resultStatus}
          onChange={(e) => { setResultStatus(e.target.value); setActiveQuickFilter(null); }}
          className="border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-300"
        >
          <option value="">Any result</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="skipped">Skipped</option>
        </select>
        <input
          type="date" value={dateFrom} title="From date — includes the entire selected day"
          onChange={(e) => setDateFrom(e.target.value)}
          className="border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
        <input
          type="date" value={dateTo} title="To date — includes the entire selected day"
          onChange={(e) => setDateTo(e.target.value)}
          className="border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-8">
          <div className="w-6 h-6 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : !items || items.length === 0 ? (
        <p className="text-sm text-gray-400 py-4">
          {hasActiveFilters ? "No audit records match these filters." : "No write audit records yet."}
        </p>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="border-b border-gray-100">
                <tr className="text-left text-gray-400">
                  <th className="py-2 pr-3 font-medium">Date</th>
                  <th className="py-2 pr-3 font-medium">Listing</th>
                  <th className="py-2 pr-3 font-medium">Field</th>
                  <th className="py-2 pr-3 font-medium">Op</th>
                  <th className="py-2 pr-3 font-medium">Before</th>
                  <th className="py-2 pr-3 font-medium">After</th>
                  <th className="py-2 pr-3 font-medium">Result</th>
                  <th className="py-2 pr-3 font-medium">Revert</th>
                  <th className="py-2 pr-3 font-medium">Apply job</th>
                  <th className="py-2 font-medium">Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {items.map((row) => (
                  <tr key={row.id} className="text-gray-700">
                    <td className="py-2 pr-3 whitespace-nowrap text-gray-500">{new Date(row.created_at).toLocaleString()}</td>
                    <td className="py-2 pr-3 max-w-[160px]">
                      {row.extra_data?.etsy_listing_id ? (
                        <span title={row.listing_title ?? undefined} className="block truncate">
                          {row.listing_title ? `${row.listing_title} ` : ""}
                          <span className="text-gray-400">#{row.extra_data.etsy_listing_id}</span>
                        </span>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="py-2 pr-3 font-medium">{row.field_name ?? "—"}</td>
                    <td className="py-2 pr-3 text-gray-500">{row.extra_data?.operation ?? "—"}</td>
                    <td className="py-2 pr-3 max-w-[140px] truncate"><AuditValueCell value={row.extra_data?.before} /></td>
                    <td className="py-2 pr-3 max-w-[140px] truncate"><AuditValueCell value={row.extra_data?.after} /></td>
                    <td className="py-2 pr-3"><ResultStatusBadge status={row.result_status} /></td>
                    <td className="py-2 pr-3"><RevertStatusBadge status={row.revert_status} /></td>
                    <td className="py-2 pr-3"><CopyableId id={row.apply_job_id} /></td>
                    <td className="py-2 max-w-[280px] truncate text-gray-500" title={row.extra_data?.error_message ?? row.message ?? undefined}>
                      {row.extra_data?.error_message ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between pt-1">
            <p className="text-[11px] text-gray-400">
              Showing {(page - 1) * AUDIT_PER_PAGE + 1}–{Math.min(page * AUDIT_PER_PAGE, total)} of {total}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => load(page - 1)}
                disabled={page <= 1}
                className="text-xs font-medium text-indigo-600 hover:underline disabled:text-gray-300 disabled:no-underline disabled:cursor-not-allowed"
              >
                ← Prev
              </button>
              <span className="text-[11px] text-gray-400">Page {page} of {totalPages}</span>
              <button
                onClick={() => load(page + 1)}
                disabled={page >= totalPages}
                className="text-xs font-medium text-indigo-600 hover:underline disabled:text-gray-300 disabled:no-underline disabled:cursor-not-allowed"
              >
                Next →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function AccountActivityPage() {
  const router = useRouter();
  const [rows, setRows] = useState<ActivityRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    getApplyJobHistory({ per_page: 50 })
      .then((page) => setRows(toRows(page.items)))
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) { router.push("/login"); return; }
        setError(e instanceof ApiError ? e.message : "Failed to load activity.");
      });
  }, []);

  return (
    <div className="space-y-5">
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-900">Recent Activity</h2>
          <Link href="/magic-revert" className="text-xs font-medium text-indigo-600 hover:underline">Open Magic Revert →</Link>
        </div>

        {error ? (
          <p className="text-sm text-red-600">{error}</p>
        ) : rows === null ? (
          <div className="flex justify-center py-8">
            <div className="w-6 h-6 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : rows.length === 0 ? (
          <p className="text-sm text-gray-400">No activity yet. Run a Bulk Edit apply to see it here.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-100">
                <tr>
                  <th className="text-left py-2 pr-3 font-medium text-gray-500 text-xs">Date</th>
                  <th className="text-left py-2 pr-3 font-medium text-gray-500 text-xs">Type</th>
                  <th className="text-left py-2 pr-3 font-medium text-gray-500 text-xs">Status</th>
                  <th className="text-left py-2 pr-3 font-medium text-gray-500 text-xs">Summary</th>
                  <th className="text-left py-2 font-medium text-gray-500 text-xs">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {rows.map((row) => (
                  <tr key={row.key}>
                    <td className="py-2 pr-3 text-xs text-gray-600">{row.date ? new Date(row.date).toLocaleString() : "—"}</td>
                    <td className="py-2 pr-3 text-xs text-gray-700">{row.type}</td>
                    <td className="py-2 pr-3">
                      <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium ${jobStateBadgeClass(row.status)}`}>
                        {jobStateLabel(row.status)}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-xs text-gray-500">{row.summary}</td>
                    <td className="py-2">
                      <Link href="/magic-revert" className="text-xs font-medium text-indigo-600 hover:underline">
                        {row.type === "Magic Revert" ? "View Details" : "Open Magic Revert"}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <AuditTrailSection />

      <AccountPlaceholder
        title="More activity types coming soon"
        description="Account events like Etsy shop connected/disconnected, plan changes, AI usage, and media jobs aren't tracked here yet."
      />
    </div>
  );
}
