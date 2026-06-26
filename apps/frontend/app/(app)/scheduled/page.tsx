"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ScheduledJob,
  ScheduledJobRun,
  createScheduledJob,
  disableScheduledJob,
  getAllRuns,
  listScheduledJobs,
  pauseScheduledJob,
  resumeScheduledJob,
  runScheduledJobNow,
  ApiError,
} from "@/lib/api";

const JOB_TYPES = [
  { value: "csv_export_snapshot", label: "CSV Export Snapshot", description: "Export listing data as a metadata snapshot" },
  { value: "bulk_edit_draft", label: "Bulk Edit Draft", description: "Create a draft bulk edit session" },
  { value: "dynamic_pricing_preview", label: "Pricing Preview", description: "Generate dynamic pricing recommendations" },
  { value: "etsy_sync", label: "Etsy Sync", description: "Sync listings from Etsy (read-only)" },
];

const SCHEDULE_TYPES = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "interval", label: "Interval" },
  { value: "one_time", label: "One-time" },
];

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  paused: "bg-yellow-100 text-yellow-700",
  disabled: "bg-gray-100 text-gray-500",
  completed: "bg-blue-100 text-blue-700",
  failed: "bg-red-100 text-red-700",
  success: "bg-green-100 text-green-700",
  running: "bg-indigo-100 text-indigo-700",
  queued: "bg-gray-100 text-gray-500",
};

function fmtDate(s: string | null): string {
  if (!s) return "—";
  return new Date(s).toLocaleString();
}

function buildSchedulePayload(scheduleType: string, form: Record<string, string>): Record<string, unknown> {
  if (scheduleType === "daily") return { time: form.time || "09:00" };
  if (scheduleType === "weekly") return { day_of_week: form.day_of_week || "monday", time: form.time || "09:00" };
  if (scheduleType === "monthly") return { day_of_month: parseInt(form.day_of_month || "1"), time: form.time || "09:00" };
  if (scheduleType === "interval") return { every: parseInt(form.every || "2"), unit: form.unit || "hours" };
  if (scheduleType === "one_time") return { run_at: form.run_at || new Date(Date.now() + 86400000).toISOString() };
  return {};
}

export default function ScheduledPage() {
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [runs, setRuns] = useState<ScheduledJobRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [runningJob, setRunningJob] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState("");

  const [form, setForm] = useState({
    name: "",
    job_type: "csv_export_snapshot",
    schedule_type: "daily",
    timezone: "UTC",
    time: "09:00",
    day_of_week: "monday",
    day_of_month: "1",
    every: "2",
    unit: "hours",
    run_at: "",
    job_payload_json: "{}",
  });

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [j, r] = await Promise.all([listScheduledJobs(), getAllRuns()]);
      setJobs(j);
      setRuns(r);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError("");
    try {
      let job_payload: Record<string, unknown> = {};
      try { job_payload = JSON.parse(form.job_payload_json); } catch { /* ignore */ }
      await createScheduledJob({
        name: form.name,
        job_type: form.job_type,
        schedule_type: form.schedule_type,
        schedule_payload: buildSchedulePayload(form.schedule_type, form),
        job_payload,
        timezone: form.timezone,
      });
      setShowForm(false);
      setForm({ ...form, name: "", job_payload_json: "{}" });
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to create");
    } finally {
      setCreating(false);
    }
  }

  async function handleAction(action: "pause" | "resume" | "disable" | "run", jobId: string) {
    setError("");
    setActionMsg("");
    try {
      if (action === "pause") await pauseScheduledJob(jobId);
      else if (action === "resume") await resumeScheduledJob(jobId);
      else if (action === "disable") await disableScheduledJob(jobId);
      else if (action === "run") {
        setRunningJob(jobId);
        const run = await runScheduledJobNow(jobId);
        setActionMsg(`Run completed: ${run.status}${run.error_message ? ` — ${run.error_message}` : ""}`);
      }
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Action failed");
    } finally {
      setRunningJob(null);
    }
  }

  return (
    <main className="py-10 px-4">
      <div className="max-w-5xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <Link href="/dashboard" className="text-sm text-indigo-600 hover:underline">← Dashboard</Link>
            <h1 className="text-2xl font-bold text-gray-900 mt-1">Scheduled Jobs</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Schedule safe syncs, draft creation, and pricing previews. Nothing publishes to Etsy without your approval.
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 transition-colors"
          >
            {showForm ? "Cancel" : "+ New Job"}
          </button>
        </div>

        {/* Safety banner */}
        <div className="rounded-lg border border-blue-200 bg-blue-50 px-5 py-4 text-sm text-blue-800">
          <strong>Safe by design.</strong> Scheduled jobs never write to Etsy automatically. Syncs are read-only.
          Drafts require manual review and apply. Pricing previews require manual approval. You stay in control.
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm">{error}</div>
        )}
        {actionMsg && (
          <div className="rounded-lg bg-green-50 border border-green-200 text-green-700 px-4 py-3 text-sm">{actionMsg}</div>
        )}

        {/* Create form */}
        {showForm && (
          <form onSubmit={handleCreate} className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
            <h2 className="font-semibold text-gray-900">Create Scheduled Job</h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500 font-medium">Job name</label>
                <input
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  placeholder="My daily sync"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 font-medium">Job type</label>
                <select
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={form.job_type}
                  onChange={e => setForm({ ...form, job_type: e.target.value })}
                >
                  {JOB_TYPES.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  {JOB_TYPES.find(t => t.value === form.job_type)?.description}
                </p>
              </div>
              <div>
                <label className="text-xs text-gray-500 font-medium">Schedule type</label>
                <select
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={form.schedule_type}
                  onChange={e => setForm({ ...form, schedule_type: e.target.value })}
                >
                  {SCHEDULE_TYPES.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 font-medium">Timezone</label>
                <input
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={form.timezone}
                  onChange={e => setForm({ ...form, timezone: e.target.value })}
                  placeholder="UTC"
                />
              </div>
            </div>

            {/* Schedule payload fields */}
            {(form.schedule_type === "daily" || form.schedule_type === "weekly" || form.schedule_type === "monthly") && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-500 font-medium">Time (HH:MM)</label>
                  <input
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={form.time}
                    onChange={e => setForm({ ...form, time: e.target.value })}
                    placeholder="09:00"
                  />
                </div>
                {form.schedule_type === "weekly" && (
                  <div>
                    <label className="text-xs text-gray-500 font-medium">Day of week</label>
                    <select
                      className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                      value={form.day_of_week}
                      onChange={e => setForm({ ...form, day_of_week: e.target.value })}
                    >
                      {["monday","tuesday","wednesday","thursday","friday","saturday","sunday"].map(d => (
                        <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                      ))}
                    </select>
                  </div>
                )}
                {form.schedule_type === "monthly" && (
                  <div>
                    <label className="text-xs text-gray-500 font-medium">Day of month (1–28)</label>
                    <input
                      type="number" min={1} max={28}
                      className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                      value={form.day_of_month}
                      onChange={e => setForm({ ...form, day_of_month: e.target.value })}
                    />
                  </div>
                )}
              </div>
            )}
            {form.schedule_type === "interval" && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-500 font-medium">Every</label>
                  <input
                    type="number" min={1}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={form.every}
                    onChange={e => setForm({ ...form, every: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 font-medium">Unit</label>
                  <select
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={form.unit}
                    onChange={e => setForm({ ...form, unit: e.target.value })}
                  >
                    <option value="minutes">Minutes (min 60)</option>
                    <option value="hours">Hours</option>
                    <option value="days">Days</option>
                  </select>
                </div>
              </div>
            )}
            {form.schedule_type === "one_time" && (
              <div>
                <label className="text-xs text-gray-500 font-medium">Run at (ISO datetime)</label>
                <input
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={form.run_at}
                  onChange={e => setForm({ ...form, run_at: e.target.value })}
                  placeholder="2026-07-01T09:00:00+00:00"
                />
              </div>
            )}

            <div>
              <label className="text-xs text-gray-500 font-medium">Job payload (JSON)</label>
              <textarea
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono"
                rows={4}
                value={form.job_payload_json}
                onChange={e => setForm({ ...form, job_payload_json: e.target.value })}
                placeholder={'{\n  "shop_id": "your-shop-id"\n}'}
              />
              <p className="text-xs text-gray-400 mt-1">
                etsy_sync: {`{"shop_id":"..."}`} &nbsp;|&nbsp;
                bulk_edit_draft: {`{"listing_ids":[...],"changes":[{"field_name":"title","operation":"set","value":"..."}]}`}
              </p>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={creating}
                className="rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium px-5 py-2.5 transition-colors"
              >
                {creating ? "Creating…" : "Create Job"}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="rounded-lg border border-gray-300 text-gray-700 text-sm px-5 py-2.5 hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Jobs table */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Jobs</h2>
          </div>
          {loading ? (
            <p className="text-sm text-gray-400 px-6 py-8 text-center">Loading…</p>
          ) : jobs.length === 0 ? (
            <p className="text-sm text-gray-400 px-6 py-8 text-center">No scheduled jobs yet. Create one above.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs text-gray-500 font-medium">Name</th>
                    <th className="text-left px-4 py-3 text-xs text-gray-500 font-medium">Type</th>
                    <th className="text-left px-4 py-3 text-xs text-gray-500 font-medium">Schedule</th>
                    <th className="text-left px-4 py-3 text-xs text-gray-500 font-medium">Status</th>
                    <th className="text-left px-4 py-3 text-xs text-gray-500 font-medium">Next run</th>
                    <th className="text-left px-4 py-3 text-xs text-gray-500 font-medium">Runs</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {jobs.map(job => (
                    <tr key={job.id} className="hover:bg-gray-50">
                      <td className="px-6 py-3 font-medium text-gray-900 max-w-[200px] truncate">{job.name}</td>
                      <td className="px-4 py-3 text-gray-500">{job.job_type.replace(/_/g, " ")}</td>
                      <td className="px-4 py-3 text-gray-500 capitalize">{job.schedule_type.replace(/_/g, " ")}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${STATUS_COLORS[job.status] || "bg-gray-100 text-gray-500"}`}>
                          {job.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{fmtDate(job.next_run_at)}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{job.run_count} / {job.failure_count} fail</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1.5">
                          {job.status === "active" && (
                            <button
                              onClick={() => handleAction("pause", job.id)}
                              className="text-xs text-yellow-700 hover:underline"
                            >Pause</button>
                          )}
                          {job.status === "paused" && (
                            <button
                              onClick={() => handleAction("resume", job.id)}
                              className="text-xs text-green-700 hover:underline"
                            >Resume</button>
                          )}
                          {job.status !== "disabled" && job.status !== "completed" && (
                            <button
                              onClick={() => handleAction("disable", job.id)}
                              className="text-xs text-gray-500 hover:underline"
                            >Disable</button>
                          )}
                          <button
                            onClick={() => handleAction("run", job.id)}
                            disabled={runningJob === job.id}
                            className="text-xs text-indigo-600 hover:underline disabled:opacity-40"
                          >{runningJob === job.id ? "Running…" : "Run now"}</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Run history */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Recent Run History</h2>
          </div>
          {runs.length === 0 ? (
            <p className="text-sm text-gray-400 px-6 py-8 text-center">No runs yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs text-gray-500 font-medium">Job type</th>
                    <th className="text-left px-4 py-3 text-xs text-gray-500 font-medium">Trigger</th>
                    <th className="text-left px-4 py-3 text-xs text-gray-500 font-medium">Status</th>
                    <th className="text-left px-4 py-3 text-xs text-gray-500 font-medium">Duration</th>
                    <th className="text-left px-4 py-3 text-xs text-gray-500 font-medium">Created resource</th>
                    <th className="text-left px-4 py-3 text-xs text-gray-500 font-medium">Started</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {runs.slice(0, 50).map(run => (
                    <tr key={run.id} className="hover:bg-gray-50">
                      <td className="px-6 py-3 text-gray-700">{run.job_type.replace(/_/g, " ")}</td>
                      <td className="px-4 py-3 text-gray-500 capitalize">{run.trigger_type}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${STATUS_COLORS[run.status] || "bg-gray-100 text-gray-500"}`}>
                          {run.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {run.duration_ms != null ? `${run.duration_ms}ms` : "—"}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {run.created_resource_type
                          ? `${run.created_resource_type.replace(/_/g, " ")} ${run.created_resource_id?.slice(0, 8)}…`
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{fmtDate(run.started_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </main>
  );
}
