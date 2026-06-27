"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, ApiError } from "@/lib/api";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

interface InsightSummary {
  date_from: string;
  date_to: string;
  total_views: number;
  total_favourites: number;
  total_revenue_cents: number;
  currency: string;
  listing_count: number;
  note: string;
}

function MetricCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl px-5 py-4">
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function InsightsContent() {
  const router = useRouter();
  const [summary, setSummary] = useState<InsightSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().split("T")[0];
  });
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().split("T")[0]);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    fetchSummary();
  }, []);

  async function fetchSummary() {
    setLoading(true);
    setError(null);
    const token = getAccessToken();
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/v1/insights/summary?date_from=${dateFrom}&date_to=${dateTo}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error(await res.text());
      setSummary(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load insights.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Shop Insights</h1>
        <p className="text-sm text-gray-500 mt-0.5">Date-range analytics for your Etsy shop.</p>
      </div>

      {/* Date range picker */}
      <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex flex-wrap items-center gap-3">
        <div className="flex flex-col gap-0.5">
          <label className="text-xs text-gray-500">From</label>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div className="flex flex-col gap-0.5">
          <label className="text-xs text-gray-500">To</label>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <button onClick={fetchSummary} className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          Apply
        </button>
      </div>

      {error && <div className="px-4 py-3 bg-red-50 border border-red-200 text-red-800 rounded-lg text-sm">{error}</div>}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : summary ? (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricCard label="Views" value={summary.total_views.toLocaleString()} />
            <MetricCard label="Favourites" value={summary.total_favourites.toLocaleString()} />
            <MetricCard
              label="Revenue"
              value={`${summary.currency} ${(summary.total_revenue_cents / 100).toFixed(2)}`}
            />
            <MetricCard label="Listings" value={summary.listing_count.toLocaleString()} />
          </div>

          {summary.note && (
            <div className="flex items-start gap-3 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
              <span className="mt-0.5 flex-shrink-0">ℹ️</span>
              <span>{summary.note}</span>
            </div>
          )}
        </>
      ) : null}
    </main>
  );
}

export default function InsightsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">Loading…</div>}>
      <InsightsContent />
    </Suspense>
  );
}
