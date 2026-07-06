"use client";

// On owner.bulkeditapp.com the middleware rewrites clean paths
// (owner.bulkeditapp.com/users/123) to the internal /owner/* route tree, so
// links FROM that host must use the clean form or they'd be rewritten twice
// and 404 as /owner/owner/users/123. On any other host (e.g. testing
// staging.bulkeditapp.com/owner directly) the real path keeps the /owner
// prefix. Call this once per page and prefix all owner-internal hrefs with it.
export function useOwnerBase(): string {
  if (typeof window === "undefined") return "/owner";
  return window.location.hostname === "owner.bulkeditapp.com" ? "" : "/owner";
}

// Client-side CSV export — no secrets, no tokens, no password hashes. Callers
// pass already-fetched/filtered rows and the exact column order/keys to emit.
export function downloadCsv(filename: string, rows: Record<string, unknown>[], columns: string[]): void {
  const escape = (v: unknown): string => {
    const s = v === null || v === undefined ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const header = columns.join(",");
  const body = rows.map((r) => columns.map((c) => escape(r[c])).join(",")).join("\n");
  const blob = new Blob([`${header}\n${body}`], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function todayStamp(): string {
  return new Date().toISOString().slice(0, 10);
}

// Lightweight bar chart — no chart library dependency. Renders an honest
// "No activity yet" state instead of a flat/fake-looking empty chart.
export function TrendBarChart({ points, label }: { points: { date: string; count: number }[]; label: string }) {
  const max = Math.max(1, ...points.map((p) => p.count));
  const hasActivity = points.some((p) => p.count > 0);
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">{label}</p>
      {!hasActivity ? (
        <div className="h-24 flex items-center justify-center">
          <p className="text-sm text-gray-400">No activity yet</p>
        </div>
      ) : (
        <div className="h-24 flex items-end gap-px">
          {points.map((p) => (
            <div
              key={p.date}
              className="flex-1 bg-indigo-500 hover:bg-indigo-600 rounded-t-sm transition-colors"
              style={{ height: `${Math.max(4, Math.round((p.count / max) * 96))}px` }}
              title={`${p.date}: ${p.count}`}
            />
          ))}
        </div>
      )}
      {points.length > 0 && (
        <div className="flex justify-between mt-2 text-[10px] text-gray-400">
          <span>{points[0].date}</span>
          <span>{points[points.length - 1].date}</span>
        </div>
      )}
    </div>
  );
}

export function fmt(dt: string | null | undefined): string {
  if (!dt) return "—";
  return new Date(dt).toLocaleString();
}

export function currency(n: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 }).format(n);
}

export function Badge({ status }: { status: string }) {
  const color: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    inactive: "bg-gray-100 text-gray-600",
    free: "bg-gray-100 text-gray-600",
    paused: "bg-yellow-100 text-yellow-800",
    completed: "bg-blue-100 text-blue-800",
    failed: "bg-red-100 text-red-800",
    canceled: "bg-red-100 text-red-700",
    ok: "bg-green-100 text-green-800",
    superuser: "bg-purple-100 text-purple-800",
    true: "bg-green-100 text-green-800",
    false: "bg-gray-100 text-gray-600",
  };
  const cls = color[status] ?? "bg-indigo-100 text-indigo-800";
  return <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>{status}</span>;
}

export function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{typeof value === "number" ? value.toLocaleString() : value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export function SectionHeader({ title, total, onRefresh }: { title: string; total?: number; onRefresh: () => void }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h2 className="text-base font-semibold text-gray-800">
        {title}
        {total !== undefined && <span className="text-gray-400 font-normal text-sm ml-1">({total})</span>}
      </h2>
      <button type="button" onClick={onRefresh} className="text-xs text-indigo-600 hover:underline">
        Refresh
      </button>
    </div>
  );
}

export function PaginationBar({
  page,
  total,
  pageSize,
  onPage,
}: {
  page: number;
  total: number;
  pageSize: number;
  onPage: (p: number) => void;
}) {
  const pages = Math.ceil(total / pageSize);
  if (pages <= 1) return null;
  return (
    <div className="flex gap-2 items-center justify-end mt-3 text-sm">
      <button
        type="button"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
        className="px-2 py-1 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
      >
        ←
      </button>
      <span className="text-gray-500">
        {page} / {pages}
      </span>
      <button
        type="button"
        disabled={page >= pages}
        onClick={() => onPage(page + 1)}
        className="px-2 py-1 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
      >
        →
      </button>
    </div>
  );
}

export function Card({ children }: { children: React.ReactNode }) {
  return <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">{children}</div>;
}

export function PageHeader({ title, sub }: { title: string; sub: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
      <p className="text-gray-400 text-sm mt-0.5">{sub}</p>
    </div>
  );
}
