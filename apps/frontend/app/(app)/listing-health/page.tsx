"use client";

import { useEffect, useState, Suspense, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getListingHealthSummary, getListingHealthListings, getListingHealthAISuggestions,
  getAccessToken, ApiError,
  type ListingHealthSummary, type ListingHealthRow, type AISuggestions,
} from "@/lib/api";

function scoreBadgeClass(score: number): string {
  if (score >= 90) return "bg-green-100 text-green-700";
  if (score >= 75) return "bg-yellow-100 text-yellow-700";
  if (score >= 50) return "bg-orange-100 text-orange-700";
  return "bg-red-100 text-red-700";
}

function gradeBadgeClass(grade: string): string {
  const map: Record<string, string> = {
    excellent: "bg-green-100 text-green-700",
    good: "bg-yellow-100 text-yellow-700",
    needs_work: "bg-orange-100 text-orange-700",
    critical: "bg-red-100 text-red-700",
  };
  return map[grade] ?? "bg-gray-100 text-gray-500";
}

function priorityBadgeClass(priority: string): string {
  const map: Record<string, string> = {
    critical: "bg-red-100 text-red-700",
    high: "bg-orange-100 text-orange-700",
    medium: "bg-yellow-100 text-yellow-700",
    low: "bg-gray-100 text-gray-500",
  };
  return map[priority] ?? "bg-gray-100 text-gray-500";
}

function SummaryCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl px-5 py-4">
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function ListingHealthContent() {
  const router = useRouter();
  const [summary, setSummary] = useState<ListingHealthSummary | null>(null);
  const [listings, setListings] = useState<ListingHealthRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [gradeFilter, setGradeFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("score_asc");
  const [aiResults, setAiResults] = useState<Record<string, AISuggestions>>({});
  const [aiLoading, setAiLoading] = useState<Record<string, boolean>>({});
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const pageSize = 50;

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    fetchData(1);
  }, []);

  async function fetchData(p: number) {
    setLoading(true);
    setError(null);
    try {
      const [sum, lst] = await Promise.all([
        getListingHealthSummary(),
        getListingHealthListings({ grade: gradeFilter || undefined, priority: priorityFilter || undefined, search: search || undefined, sort, page: p, page_size: pageSize }),
      ]);
      setSummary(sum);
      setListings(lst.items);
      setTotal(lst.total);
      setPage(p);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) { router.push("/login"); return; }
      setError(e instanceof ApiError ? e.message : "Failed to load health data.");
    } finally {
      setLoading(false);
    }
  }

  async function applyFilters() {
    await fetchData(1);
  }

  async function fetchAISuggestions(listingId: string) {
    setAiLoading((prev) => ({ ...prev, [listingId]: true }));
    try {
      const result = await getListingHealthAISuggestions(listingId);
      setAiResults((prev) => ({ ...prev, [listingId]: result }));
    } catch {
      setAiResults((prev) => ({ ...prev, [listingId]: { listing_id: listingId, ai_available: false, message: "Failed to get AI suggestions." } }));
    } finally {
      setAiLoading((prev) => ({ ...prev, [listingId]: false }));
    }
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <main className="max-w-7xl mx-auto px-6 py-6 space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Listing Health</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Find weak listings, prioritize fixes, and improve your Etsy shop safely.
        </p>
      </div>

      {/* Cross-link to Profit */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-violet-50 border border-violet-200 rounded-lg text-sm text-violet-800">
        <span>📈</span>
        <span>Combine margin data with listing health to prioritize profitable improvements.</span>
        <Link href="/profit" className="font-medium underline underline-offset-2 hover:text-violet-900">
          View Profit →
        </Link>
      </div>

      {error && (
        <div className="px-4 py-3 bg-red-50 border border-red-200 text-red-800 rounded-lg text-sm">{error}</div>
      )}

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <SummaryCard label="Avg Score" value={`${summary.average_score.toFixed(0)}/100`} />
          <SummaryCard label="Total" value={summary.total_listings} />
          <SummaryCard label="Excellent" value={summary.excellent_count} sub="90-100" />
          <SummaryCard label="Good" value={summary.good_count} sub="75-89" />
          <SummaryCard label="Needs Work" value={summary.needs_work_count} sub="50-74" />
          <SummaryCard label="Critical" value={summary.critical_count} sub="0-49" />
        </div>
      )}

      {summary && summary.top_issue_categories.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 text-sm text-orange-800">
          <strong>Top issues:</strong> {summary.top_issue_categories.join(", ")}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex flex-wrap items-center gap-3">
        <select value={gradeFilter} onChange={(e) => setGradeFilter(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
          <option value="">All grades</option>
          <option value="excellent">Excellent</option>
          <option value="good">Good</option>
          <option value="needs_work">Needs Work</option>
          <option value="critical">Critical</option>
        </select>
        <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
          <option value="">All priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
          <option value="score_asc">Lowest Score First</option>
          <option value="score_desc">Highest Score First</option>
          <option value="issue_count_desc">Most Issues First</option>
          <option value="title_asc">Title A-Z</option>
        </select>
        <input type="text" placeholder="Search listings…" value={search} onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") applyFilters(); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm flex-1 min-w-48 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        <button onClick={applyFilters}
          className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          Apply
        </button>
      </div>

      {/* Bulk action bar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-3 px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm">
          <span className="font-medium">{selectedIds.size} listing{selectedIds.size !== 1 ? "s" : ""} selected</span>
          <Link
            href={`/bulk-edit?listing_ids=${Array.from(selectedIds).join(",")}`}
            className="ml-auto bg-white text-indigo-700 font-semibold px-3 py-1 rounded hover:bg-indigo-50 transition-colors"
          >
            Send to Bulk Edit →
          </Link>
          <button
            onClick={() => setSelectedIds(new Set())}
            className="text-indigo-200 hover:text-white text-xs"
          >
            Clear
          </button>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : listings.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-10 text-center">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">No listings found</h3>
          <p className="text-gray-500 text-sm mb-5">
            Sync your Etsy listings to calculate your shop health.
          </p>
          <Link href="/shops" className="text-indigo-600 text-sm font-medium hover:underline">Go to Shops →</Link>
        </div>
      ) : (
        <>
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 w-8">
                      <input
                        type="checkbox"
                        aria-label="Select all on this page"
                        checked={listings.length > 0 && listings.every((l) => selectedIds.has(l.listing_id))}
                        onChange={(e) => {
                          setSelectedIds((prev) => {
                            const next = new Set(prev);
                            if (e.target.checked) listings.forEach((l) => next.add(l.listing_id));
                            else listings.forEach((l) => next.delete(l.listing_id));
                            return next;
                          });
                        }}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Listing</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Score</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Grade</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Priority</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Issues</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Tags</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Photos</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Price</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {listings.map((listing) => (
                    <tr key={listing.listing_id} className={`hover:bg-gray-50 transition-colors ${selectedIds.has(listing.listing_id) ? "bg-indigo-50/40" : ""}`}>
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          aria-label={`Select ${listing.title ?? listing.listing_id}`}
                          checked={selectedIds.has(listing.listing_id)}
                          onChange={(e) => {
                            setSelectedIds((prev) => {
                              const next = new Set(prev);
                              if (e.target.checked) next.add(listing.listing_id);
                              else next.delete(listing.listing_id);
                              return next;
                            });
                          }}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="px-4 py-3 max-w-xs">
                        <p className="font-medium text-gray-900 truncate text-sm">{listing.title ?? "—"}</p>
                        <p className="text-xs text-gray-400">{listing.state ?? ""}</p>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-bold px-2 py-1 rounded-full ${scoreBadgeClass(listing.score)}`}>
                          {listing.score}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${gradeBadgeClass(listing.grade)}`}>
                          {listing.grade.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${priorityBadgeClass(listing.priority)}`}>
                          {listing.priority}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-700">{listing.issue_count}</td>
                      <td className="px-4 py-3 text-gray-700">{listing.tag_count}/13</td>
                      <td className="px-4 py-3 text-gray-700">{listing.photo_count}</td>
                      <td className="px-4 py-3 text-gray-700">
                        {listing.price != null ? `${listing.currency ?? ""} ${Number(listing.price).toFixed(2)}` : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col gap-1">
                          <button
                            onClick={() => fetchAISuggestions(listing.listing_id)}
                            disabled={aiLoading[listing.listing_id]}
                            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium text-left disabled:opacity-60"
                          >
                            {aiLoading[listing.listing_id] ? "Loading…" : "AI Suggestions"}
                          </button>
                          <Link
                            href={`/bulk-edit?listing_ids=${listing.listing_id}`}
                            className="text-xs text-gray-500 hover:text-gray-700"
                          >
                            Bulk Edit
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* AI suggestion results */}
          {Object.entries(aiResults).map(([id, result]) => (
            <div key={id} className="bg-indigo-50 border border-indigo-200 rounded-lg px-4 py-3 text-sm space-y-2">
              <div className="flex items-center justify-between">
                <p className="font-medium text-indigo-900">AI Suggestions — Listing {id.slice(0, 8)}…</p>
                <button onClick={() => setAiResults((prev) => { const n = { ...prev }; delete n[id]; return n; })}
                  className="text-indigo-400 hover:text-indigo-600 text-xs">Dismiss</button>
              </div>
              {!result.ai_available && <p className="text-indigo-700 italic">{result.message}</p>}
              {result.improved_title && (
                <div>
                  <p className="text-xs text-indigo-500 font-medium">Suggested title:</p>
                  <p className="text-indigo-800">{result.improved_title}</p>
                </div>
              )}
              {result.suggested_tags && result.suggested_tags.length > 0 && (
                <div>
                  <p className="text-xs text-indigo-500 font-medium">Suggested tags:</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {result.suggested_tags.map((t, i) => (
                      <span key={i} className="bg-indigo-100 text-indigo-700 text-xs px-2 py-0.5 rounded-full">{t}</span>
                    ))}
                  </div>
                </div>
              )}
              {result.explanation && (
                <p className="text-indigo-600 text-xs italic">{result.explanation}</p>
              )}
              <p className="text-xs text-indigo-400">
                Suggestions are not auto-applied. Review and use via Bulk Edit.
              </p>
            </div>
          ))}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500">Page {page} of {totalPages} ({total.toLocaleString()} total)</p>
              <div className="flex gap-2">
                <button onClick={() => fetchData(page - 1)} disabled={page <= 1}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50">Previous</button>
                <button onClick={() => fetchData(page + 1)} disabled={page >= totalPages}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50">Next</button>
              </div>
            </div>
          )}
        </>
      )}
    </main>
  );
}

export default function ListingHealthPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">Loading…</div>}>
      <ListingHealthContent />
    </Suspense>
  );
}
