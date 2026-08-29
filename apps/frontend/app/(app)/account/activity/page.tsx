"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getAccessToken, ApiError, getApplyJobHistory, type ApplyJobHistoryItem } from "@/lib/api";
import AccountPlaceholder from "@/components/account/AccountPlaceholder";

type ActivityRow = {
  key: string;
  type: "Bulk Edit Apply" | "Magic Revert";
  date: string | null;
  status: string;
  summary: string;
  applyJobId: string;
};

const STATUS_BADGE: Record<string, string> = {
  completed: "bg-green-100 text-green-700",
  completed_with_errors: "bg-orange-100 text-orange-700",
  failed: "bg-red-100 text-red-700",
  running: "bg-blue-100 text-blue-700",
};

function toRows(items: ApplyJobHistoryItem[]): ActivityRow[] {
  const rows: ActivityRow[] = [];
  for (const item of items) {
    rows.push({
      key: `apply-${item.id}`,
      type: "Bulk Edit Apply",
      date: item.created_at,
      status: item.status,
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
                      <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium ${STATUS_BADGE[row.status] ?? "bg-gray-100 text-gray-600"}`}>
                        {row.status.replace(/_/g, " ")}
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

      <AccountPlaceholder
        title="More activity types coming soon"
        description="Account events like Etsy shop connected/disconnected, plan changes, AI usage, and media jobs aren't tracked here yet."
      />
    </div>
  );
}
