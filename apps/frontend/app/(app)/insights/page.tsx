"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getAccessToken, ApiError, getAffectedListings, type AffectedListingsSection } from "@/lib/api";

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

function AffectedListingsCard({ section }: { section: AffectedListingsSection }) {
  if (section.items.length === 0) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
        <p className="text-sm font-semibold text-gray-800">{section.label}</p>
        <span className="text-xs text-gray-400">
          {section.count} listing{section.count !== 1 ? "s" : ""}
          {section.count > section.items.length ? ` (showing first ${section.items.length})` : ""}
        </span>
      </div>
      <ul className="divide-y divide-gray-100">
        {section.items.map((item) => (
          <li key={item.listing_id} className="px-5 py-3 flex items-center gap-3">
            {item.thumbnail_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={item.thumbnail_url} alt="" className="w-10 h-10 rounded-lg object-cover border border-gray-200 flex-shrink-0" />
            ) : (
              <div className="w-10 h-10 rounded-lg border border-dashed border-gray-200 flex-shrink-0" />
            )}
            <div className="min-w-0 flex-1">
              <p className="text-sm text-gray-800 truncate">{item.title ?? "Untitled listing"}</p>
              <p className="text-xs text-gray-400">{item.metric}</p>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              <Link href={`/listings/${item.listing_id}`} className="text-xs font-medium text-indigo-600 hover:underline">
                View Product
              </Link>
              <Link href={`/bulk-edit?listing_ids=${item.listing_id}`} className="text-xs font-medium text-gray-500 hover:text-gray-700">
                Fix in Bulk Edit
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function InsightsPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<InsightSummary | null>(null);
  const [affectedSections, setAffectedSections] = useState<AffectedListingsSection[]>([]);
  const [affectedError, setAffectedError] = useState<string | null>(null);
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

  const fetchAffected = useCallback(async () => {
    try {
      const data = await getAffectedListings();
      setAffectedSections(data.sections);
    } catch (e) {
      setAffectedError(e instanceof ApiError ? e.message : "Failed to load affected listings.");
    }
  }, []);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    fetchSummary();
    fetchAffected();
  }, [router, fetchSummary, fetchAffected]);

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

              {affectedError && (
                <div className="px-4 py-3 bg-red-50 border border-red-200 text-red-800 rounded-lg text-sm">{affectedError}</div>
              )}
              {affectedSections.some((s) => s.items.length > 0) && (
                <div className="space-y-4">
                  <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Affected Listings</h2>
                  {affectedSections.map((section) => (
                    <AffectedListingsCard key={section.category} section={section} />
                  ))}
                </div>
              )}
            </>
          )}
        </>
      ) : null}
    </main>
  );
}
