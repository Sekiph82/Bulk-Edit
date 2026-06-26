"use client";

import { useState, useRef, useCallback } from "react";
import {
  importCSV,
  listCSVJobs,
  getCSVPreview,
  convertCSVJob,
  exportCSV,
  downloadCSVTemplate,
  type CSVJob,
  type CSVRow,
  type CSVPreviewPage,
  type CSVImportSummary,
  ApiError,
} from "@/lib/api";

type TabId = "export" | "import" | "jobs";

export default function CSVPage() {
  const [tab, setTab] = useState<TabId>("import");

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-1">CSV Import / Export</h1>
      <p className="text-sm text-gray-500 mb-6">
        Export listings, import changes as a draft — nothing publishes to Etsy until you approve in Bulk Edit.
      </p>

      <div className="flex gap-2 mb-6 border-b border-gray-200">
        {(["import", "export", "jobs"] as TabId[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
              tab === t
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t === "jobs" ? "Job History" : t}
          </button>
        ))}
      </div>

      {tab === "import" && <ImportTab />}
      {tab === "export" && <ExportTab />}
      {tab === "jobs" && <JobsTab />}
    </div>
  );
}

// ── Export Tab ────────────────────────────────────────────────────────────────

function ExportTab() {
  const [state, setState] = useState<string>("");

  const handleExport = () => {
    const url = exportCSV(undefined, state || undefined);
    const a = document.createElement("a");
    a.href = url;
    a.download = "listings.csv";
    a.click();
  };

  const handleTemplate = () => {
    window.open(downloadCSVTemplate(), "_blank");
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h2 className="font-semibold mb-3">Export Listings</h2>
        <p className="text-sm text-gray-500 mb-4">
          Download all your listings as a CSV file. Edit the file and re-import to bulk update.
        </p>
        <div className="flex gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Filter by state</label>
            <select
              value={state}
              onChange={(e) => setState(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1.5"
            >
              <option value="">All states</option>
              <option value="active">Active</option>
              <option value="draft">Draft</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <button
            onClick={handleExport}
            className="bg-blue-600 text-white text-sm px-4 py-1.5 rounded hover:bg-blue-700"
          >
            Download CSV
          </button>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h2 className="font-semibold mb-2">Download Template</h2>
        <p className="text-sm text-gray-500 mb-4">
          Start with an empty template that has all the correct column headers.
        </p>
        <button
          onClick={handleTemplate}
          className="text-sm border border-gray-300 px-4 py-1.5 rounded hover:bg-gray-50"
        >
          Download Template
        </button>
      </div>
    </div>
  );
}

// ── Import Tab ────────────────────────────────────────────────────────────────

function ImportTab() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [summary, setSummary] = useState<CSVImportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<CSVPreviewPage | null>(null);
  const [previewPage, setPreviewPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [converting, setConverting] = useState(false);
  const [convertResult, setConvertResult] = useState<{ session_id: string; message: string } | null>(null);
  const [ignoreInvalid, setIgnoreInvalid] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    setSummary(null);
    setPreview(null);
    setConvertResult(null);
    try {
      const result = await importCSV(file);
      setSummary(result);
      await loadPreview(result.job_id, 1, "");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const loadPreview = useCallback(async (jobId: string, page: number, status: string) => {
    try {
      const p = await getCSVPreview(jobId, { page, per_page: 50, status: status || undefined });
      setPreview(p);
      setPreviewPage(page);
    } catch {
      // preview load failure is non-fatal
    }
  }, []);

  const handleConvert = async () => {
    if (!summary) return;
    setConverting(true);
    setError(null);
    try {
      const r = await convertCSVJob(summary.job_id, ignoreInvalid);
      setConvertResult({ session_id: r.bulk_edit_session_id, message: r.message });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Conversion failed.");
    } finally {
      setConverting(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Upload area */}
      <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <p className="text-sm text-gray-500 mb-3">
          Upload a CSV file exported from this tool or using the template.
        </p>
        <button
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className="bg-blue-600 text-white text-sm px-5 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {uploading ? "Uploading…" : "Choose CSV File"}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleUpload}
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Summary */}
      {summary && (
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="font-semibold mb-3">Import Summary</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <Stat label="Total rows" value={summary.row_count} />
            <Stat label="Valid" value={summary.valid_row_count} color="green" />
            <Stat label="Invalid" value={summary.invalid_row_count} color={summary.invalid_row_count > 0 ? "red" : undefined} />
            <Stat label="Unchanged" value={summary.unchanged_row_count} color="gray" />
          </div>
          {summary.ignored_columns.length > 0 && (
            <p className="text-xs text-gray-500 mb-3">
              Ignored columns: {summary.ignored_columns.join(", ")}
            </p>
          )}
          <p className="text-sm text-gray-600 mb-4">{summary.message}</p>

          {!convertResult && (
            <div className="flex items-center gap-3">
              <button
                onClick={handleConvert}
                disabled={converting}
                className="bg-green-600 text-white text-sm px-4 py-1.5 rounded hover:bg-green-700 disabled:opacity-50"
              >
                {converting ? "Converting…" : "Convert to Bulk Edit"}
              </button>
              {summary.invalid_row_count > 0 && (
                <label className="flex items-center gap-1.5 text-sm text-gray-600">
                  <input
                    type="checkbox"
                    checked={ignoreInvalid}
                    onChange={(e) => setIgnoreInvalid(e.target.checked)}
                  />
                  Skip invalid rows
                </label>
              )}
            </div>
          )}

          {convertResult && (
            <div className="bg-green-50 border border-green-200 rounded p-3 text-sm text-green-800">
              <p className="font-medium mb-1">Bulk edit session created!</p>
              <p className="mb-2">{convertResult.message}</p>
              <a
                href="/bulk-edit"
                className="text-blue-600 underline"
              >
                Go to Bulk Edit to review and apply →
              </a>
            </div>
          )}
        </div>
      )}

      {/* Preview table */}
      {preview && (
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold">Row Preview ({preview.total} rows)</h2>
            <div className="flex items-center gap-2">
              <select
                value={statusFilter}
                onChange={(e) => {
                  const s = e.target.value;
                  setStatusFilter(s);
                  if (summary) loadPreview(summary.job_id, 1, s);
                }}
                className="text-xs border border-gray-300 rounded px-2 py-1"
              >
                <option value="">All statuses</option>
                <option value="valid">Valid</option>
                <option value="invalid">Invalid</option>
                <option value="unchanged">Unchanged</option>
                <option value="warning">Warning</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 pr-3 font-medium text-gray-600">Row</th>
                  <th className="text-left py-2 pr-3 font-medium text-gray-600">Status</th>
                  <th className="text-left py-2 pr-3 font-medium text-gray-600">Listing</th>
                  <th className="text-left py-2 font-medium text-gray-600">Issues / Changes</th>
                </tr>
              </thead>
              <tbody>
                {preview.items.map((row) => (
                  <PreviewRow key={row.id} row={row} />
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
            <button
              disabled={previewPage <= 1}
              onClick={() => summary && loadPreview(summary.job_id, previewPage - 1, statusFilter)}
              className="text-xs px-3 py-1 border border-gray-300 rounded disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-xs text-gray-500">
              Page {preview.page} of {Math.ceil(preview.total / preview.per_page) || 1}
            </span>
            <button
              disabled={previewPage >= Math.ceil(preview.total / preview.per_page)}
              onClick={() => summary && loadPreview(summary.job_id, previewPage + 1, statusFilter)}
              className="text-xs px-3 py-1 border border-gray-300 rounded disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function PreviewRow({ row }: { row: CSVRow }) {
  const statusColors: Record<string, string> = {
    valid: "bg-green-100 text-green-800",
    invalid: "bg-red-100 text-red-800",
    unchanged: "bg-gray-100 text-gray-600",
    warning: "bg-yellow-100 text-yellow-800",
  };
  const color = statusColors[row.status] ?? "bg-gray-100 text-gray-600";
  const errors = row.validation_errors ?? [];
  const warnings = row.validation_warnings ?? [];
  const diffKeys = row.diff ? Object.keys(row.diff) : [];

  return (
    <tr className="border-b border-gray-50 hover:bg-gray-50">
      <td className="py-2 pr-3 text-gray-500">{row.row_number}</td>
      <td className="py-2 pr-3">
        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${color}`}>{row.status}</span>
      </td>
      <td className="py-2 pr-3 text-gray-700">{row.listing_title ?? row.etsy_listing_id ?? row.listing_id ?? "—"}</td>
      <td className="py-2 text-gray-600">
        {errors.map((e, i) => (
          <span key={i} className="block text-red-600">{e}</span>
        ))}
        {warnings.map((w, i) => (
          <span key={i} className="block text-yellow-700">{w}</span>
        ))}
        {diffKeys.length > 0 && errors.length === 0 && (
          <span className="text-gray-500">Changes: {diffKeys.join(", ")}</span>
        )}
      </td>
    </tr>
  );
}

// ── Jobs Tab ──────────────────────────────────────────────────────────────────

function JobsTab() {
  const [jobs, setJobs] = useState<CSVJob[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const j = await listCSVJobs("import");
      setJobs(j);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load jobs.");
    } finally {
      setLoading(false);
    }
  };

  if (jobs === null && !loading) {
    return (
      <div className="text-center py-10">
        <button
          onClick={load}
          className="bg-blue-600 text-white text-sm px-5 py-2 rounded hover:bg-blue-700"
        >
          Load Job History
        </button>
      </div>
    );
  }

  if (loading) {
    return <div className="text-sm text-gray-500 py-6 text-center">Loading…</div>;
  }

  if (error) {
    return <div className="text-sm text-red-600 py-4">{error}</div>;
  }

  if (!jobs || jobs.length === 0) {
    return <div className="text-sm text-gray-500 py-6 text-center">No import jobs yet.</div>;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="text-left py-3 px-4 font-medium text-gray-600">File</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">Status</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">Rows</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">Valid</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">Invalid</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">Converted</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">Date</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id} className="border-t border-gray-100 hover:bg-gray-50">
              <td className="py-3 px-4 text-gray-700">{job.filename ?? "—"}</td>
              <td className="py-3 px-4">
                <StatusBadge status={job.status} />
              </td>
              <td className="py-3 px-4 text-gray-700">{job.row_count}</td>
              <td className="py-3 px-4 text-green-700">{job.valid_row_count}</td>
              <td className="py-3 px-4 text-red-700">{job.invalid_row_count}</td>
              <td className="py-3 px-4 text-gray-500 text-xs">
                {job.converted_bulk_edit_session_id ? (
                  <a href="/bulk-edit" className="text-blue-600 underline">View</a>
                ) : "—"}
              </td>
              <td className="py-3 px-4 text-gray-500 text-xs">
                {new Date(job.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Shared components ─────────────────────────────────────────────────────────

function Stat({ label, value, color }: { label: string; value: number; color?: string }) {
  const colors: Record<string, string> = {
    green: "text-green-700",
    red: "text-red-700",
    gray: "text-gray-500",
  };
  return (
    <div className="bg-gray-50 rounded p-3">
      <div className={`text-2xl font-bold ${color ? colors[color] : "text-gray-800"}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    preview_ready: "bg-blue-100 text-blue-800",
    converted: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
    processing: "bg-yellow-100 text-yellow-800",
  };
  const color = colors[status] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
