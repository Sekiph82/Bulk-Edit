"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, ApiError } from "@/lib/api";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

interface ListingStateCount {
  state: string;
  count: number;
}

interface InsightSummary {
  shop_connected: boolean;
  last_synced_at: string | null;
  total_listings: number;
  listings_by_state: ListingStateCount[];
  listings_missing_tags: number;
  listings_low_photo_count: number;
  average_price_cents: number | null;
  min_price_cents: number | null;
  max_price_cents: number | null;
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

function money(cents: number | null): string {
  if (cents === null) return "—";
  return `$${(cents / 100).toFixed(2)}`;
}

export default function InsightsPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<InsightSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    const token = getAccessToken();
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/insights/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new ApiError(res.status, await res.text());
      setSummary(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load insights.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    fetchSummary();
  }, [router, fetchSummary]);

  return (
    <main className="max-w-5xl mx-auto px-6 py-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Shop Insights</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Real data from your connected, synced Etsy shop — listing status, tag and photo
          coverage, and price range. Revenue, views, and favourites are not shown here since
          Etsy does not expose reliable trend data through this app&apos;s connection.
        </p>
      </div>

      {error && <div className="px-4 py-3 bg-red-50 border border-red-200 text-red-800 rounded-lg text-sm">{error}</div>}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : summary ? (
        <>
          {!summary.shop_connected ? (
            <div className="bg-white border border-gray-200 rounded-xl px-6 py-10 text-center">
              <p className="text-gray-500 text-sm">{summary.note}</p>
            </div>
          ) : summary.total_listings === 0 ? (
            <div className="bg-white border border-gray-200 rounded-xl px-6 py-10 text-center">
              <p className="text-gray-500 text-sm">{summary.note}</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <MetricCard label="Total Listings" value={summary.total_listings.toLocaleString()} />
                <MetricCard label="Missing Tags" value={summary.listings_missing_tags} sub="listings with no tags" />
                <MetricCard label="Low Photo Count" value={summary.listings_low_photo_count} sub="fewer than 3 photos" />
                <MetricCard label="Price Range" value={`${money(summary.min_price_cents)} – ${money(summary.max_price_cents)}`} sub={`avg ${money(summary.average_price_cents)}`} />
              </div>

              <div className="bg-white border border-gray-200 rounded-xl px-5 py-4">
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Listings by state</p>
                <div className="flex flex-wrap gap-2">
                  {summary.listings_by_state.map((row) => (
                    <span key={row.state} className="text-sm bg-gray-50 border border-gray-200 rounded-full px-3 py-1">
                      {row.state}: <span className="font-semibold">{row.count}</span>
                    </span>
                  ))}
                </div>
              </div>

              {summary.last_synced_at && (
                <p className="text-xs text-gray-400">
                  Last synced: {new Date(summary.last_synced_at).toLocaleString()}
                </p>
              )}
            </>
          )}
        </>
      ) : null}
    </main>
  );
}
