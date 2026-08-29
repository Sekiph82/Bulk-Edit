"use client";

import { useEffect, useState } from "react";
import { getAccessToken, ApiError } from "@/lib/api";
import { useRouter } from "next/navigation";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

type Usage = {
  period_key: string;
  usage: Record<string, number>;
  limits: Record<string, number | boolean>;
};

const ROWS: Array<{ usageKey: string; limitKey: string; label: string }> = [
  { usageKey: "bulk_edits_used", limitKey: "bulk_edits_per_month", label: "Bulk edits this month" },
  { usageKey: "ai_credits_used", limitKey: "ai_credits_per_month", label: "AI credits this month" },
  { usageKey: "media_assets_used", limitKey: "media_assets", label: "Media assets" },
  { usageKey: "listings_synced", limitKey: "max_listings", label: "Listings synced" },
];

function Row({ label, used, limit }: { label: string; used: number; limit: number }) {
  const remaining = Math.max(0, limit - used);
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  return (
    <div className="py-3 border-b border-gray-100 last:border-0">
      <div className="flex justify-between text-sm text-gray-800 mb-1">
        <span className="font-medium">{label}</span>
        <span>{used.toLocaleString()} / {limit.toLocaleString()} used — {remaining.toLocaleString()} remaining</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${pct >= 100 ? "bg-red-500" : pct >= 80 ? "bg-amber-500" : "bg-indigo-500"}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function AccountUsagePage() {
  const router = useRouter();
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    fetch(`${BACKEND_URL}/api/v1/billing/usage`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : Promise.reject(new ApiError(r.status, "Failed to load usage."))))
      .then(setUsage)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load usage."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-16"><div className="w-6 h-6 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" /></div>;
  if (error) return <p className="text-red-600 text-sm">{error}</p>;
  if (!usage) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-900">Usage this period</h2>
        <span className="text-xs text-gray-400">Resets: {usage.period_key} (monthly)</span>
      </div>
      {ROWS.map((r) => {
        const limitVal = usage.limits[r.limitKey];
        if (limitVal == null) return null;
        return <Row key={r.usageKey} label={r.label} used={usage.usage[r.usageKey] ?? 0} limit={Number(limitVal)} />;
      })}
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-gray-500">
        {usage.limits.dynamic_pricing_jobs_per_month != null && (
          <p>Dynamic pricing jobs/month: {Number(usage.limits.dynamic_pricing_jobs_per_month).toLocaleString()}</p>
        )}
        {usage.limits.max_scheduled_jobs != null && (
          <p>Max scheduled jobs: {Number(usage.limits.max_scheduled_jobs).toLocaleString()}</p>
        )}
        {usage.limits.max_shops != null && (
          <p>Max connected shops: {Number(usage.limits.max_shops).toLocaleString()}</p>
        )}
      </div>
    </div>
  );
}
