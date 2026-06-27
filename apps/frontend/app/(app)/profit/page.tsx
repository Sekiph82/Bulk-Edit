"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getProfitSummary, getProfitListings, updateListingCosts,
  getAccessToken, ApiError,
  type ProfitSummary, type ProfitListingRow, type ListingCostUpdate,
} from "@/lib/api";

type ProfitStatus = "profitable" | "low_margin" | "loss" | "missing_costs";

function statusBadgeClass(status: ProfitStatus): string {
  const map: Record<ProfitStatus, string> = {
    profitable: "bg-green-100 text-green-700",
    low_margin: "bg-yellow-100 text-yellow-700",
    loss: "bg-red-100 text-red-700",
    missing_costs: "bg-gray-100 text-gray-500",
  };
  return map[status] ?? "bg-gray-100 text-gray-500";
}

function statusLabel(status: ProfitStatus): string {
  const map: Record<ProfitStatus, string> = {
    profitable: "Profitable",
    low_margin: "Low Margin",
    loss: "Loss",
    missing_costs: "Missing Costs",
  };
  return map[status] ?? status;
}

function fmt(val: string | null, prefix = ""): string {
  if (val == null) return "—";
  const n = parseFloat(val);
  if (isNaN(n)) return "—";
  return `${prefix}${n.toFixed(2)}`;
}

function SummaryCard({ label, value, sub, warn }: { label: string; value: string | number; sub?: string; warn?: boolean }) {
  return (
    <div className={`bg-white border rounded-xl px-5 py-4 ${warn ? "border-orange-300" : "border-gray-200"}`}>
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-2xl font-bold ${warn ? "text-orange-700" : "text-gray-900"}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function CostEditor({ row, onSaved }: { row: ProfitListingRow; onSaved: () => void }) {
  const [form, setForm] = useState<ListingCostUpdate>({
    product_cost: row.product_cost ?? "0.00",
    shipping_cost: row.shipping_cost ?? "0.00",
    packaging_cost: "0.00",
    ad_cost: "0.00",
    other_cost: "0.00",
    include_offsite_ads: false,
    notes: null,
  });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function save() {
    setSaving(true);
    setMsg(null);
    try {
      await updateListingCosts(row.listing_id, form);
      setMsg({ ok: true, text: "Saved." });
      onSaved();
    } catch (e) {
      setMsg({ ok: false, text: e instanceof ApiError ? e.message : "Save failed." });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 mt-2 text-sm space-y-3">
      <p className="font-medium text-gray-700 text-xs uppercase tracking-wide">Edit Costs</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {(["product_cost", "shipping_cost", "packaging_cost", "ad_cost", "other_cost"] as const).map((field) => (
          <div key={field} className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 capitalize">{field.replace("_", " ")}</label>
            <input
              type="number" step="0.01" min="0"
              value={form[field]}
              onChange={(e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        ))}
        <div className="flex items-center gap-2 mt-3">
          <input type="checkbox" id={`offsite-${row.listing_id}`} checked={form.include_offsite_ads}
            onChange={(e) => setForm((prev) => ({ ...prev, include_offsite_ads: e.target.checked }))}
            className="rounded" />
          <label htmlFor={`offsite-${row.listing_id}`} className="text-xs text-gray-600">Include Offsite Ads fee</label>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button onClick={save} disabled={saving}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg">
          {saving ? "Saving…" : "Save Costs"}
        </button>
        {msg && (
          <span className={`text-xs ${msg.ok ? "text-green-600" : "text-red-600"}`}>{msg.text}</span>
        )}
      </div>
    </div>
  );
}

function ProfitContent() {
  const router = useRouter();
  const [summary, setSummary] = useState<ProfitSummary | null>(null);
  const [listings, setListings] = useState<ProfitListingRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCostEditor, setExpandedCostEditor] = useState<string | null>(null);
  const [search, setSearch] = useState("");

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
        getProfitSummary(),
        getProfitListings({ page: p, page_size: pageSize, search: search || undefined }),
      ]);
      setSummary(sum);
      setListings(lst.items);
      setTotal(lst.total);
      setPage(p);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) { router.push("/login"); return; }
      setError(e instanceof ApiError ? e.message : "Failed to load profit data.");
    } finally {
      setLoading(false);
    }
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <main className="max-w-7xl mx-auto px-6 py-6 space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profit & Cost Calculator</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Track product costs, Etsy fees, shipping, and margins for each listing.
        </p>
      </div>

      {/* Warning banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
        Fee rates are configurable. Confirm your Etsy fee profile before relying on profit calculations.
        Etsy fees may vary by account region and program eligibility.
      </div>

      {error && (
        <div className="px-4 py-3 bg-red-50 border border-red-200 text-red-800 rounded-lg text-sm">{error}</div>
      )}

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <SummaryCard
            label="Avg Margin"
            value={summary.average_margin != null ? `${parseFloat(summary.average_margin).toFixed(1)}%` : "—"}
          />
          <SummaryCard label="With Costs" value={summary.listings_with_costs} />
          <SummaryCard label="Missing Costs" value={summary.listings_missing_costs} warn={summary.listings_missing_costs > 0} />
          <SummaryCard label="Low Margin" value={summary.low_margin_count} warn={summary.low_margin_count > 0} />
          <SummaryCard label="Loss Making" value={summary.loss_making_count} warn={summary.loss_making_count > 0} />
        </div>
      )}

      {summary && summary.estimated_total_profit != null && (
        <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-800">
          Estimated total profit (listings with cost data): <strong>{summary.currency} {parseFloat(summary.estimated_total_profit).toFixed(2)}</strong>
        </div>
      )}

      {/* Search */}
      <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex items-center gap-3">
        <input type="text" placeholder="Search listings…" value={search} onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") fetchData(1); }}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        <button onClick={() => fetchData(1)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg">Search</button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : listings.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-10 text-center">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">No listings found</h3>
          <p className="text-gray-500 text-sm mb-5">
            {summary?.listings_with_costs === 0
              ? "Sync your Etsy listings, then add product costs to calculate profit."
              : "No listings match your search."}
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
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Listing</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Price</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Product Cost</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Shipping</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Etsy Fees</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Net Profit</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Margin</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {listings.map((row) => (
                    <>
                      <tr key={row.listing_id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 max-w-xs">
                          <p className="font-medium text-gray-900 truncate text-sm">{row.title ?? "—"}</p>
                        </td>
                        <td className="px-4 py-3 text-gray-700">{fmt(row.price, `${row.currency ?? ""} `)}</td>
                        <td className="px-4 py-3 text-gray-700">{fmt(row.product_cost, "$")}</td>
                        <td className="px-4 py-3 text-gray-700">{fmt(row.shipping_cost, "$")}</td>
                        <td className="px-4 py-3 text-gray-700">{fmt(row.total_etsy_fees, "$")}</td>
                        <td className="px-4 py-3">
                          {row.net_profit != null ? (
                            <span className={parseFloat(row.net_profit) < 0 ? "text-red-600 font-medium" : "text-green-700 font-medium"}>
                              ${parseFloat(row.net_profit).toFixed(2)}
                            </span>
                          ) : "—"}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {row.margin_percent != null ? `${parseFloat(row.margin_percent).toFixed(1)}%` : "—"}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusBadgeClass(row.status)}`}>
                            {statusLabel(row.status)}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => setExpandedCostEditor(expandedCostEditor === row.listing_id ? null : row.listing_id)}
                            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                          >
                            {expandedCostEditor === row.listing_id ? "Close" : "Edit Costs"}
                          </button>
                        </td>
                      </tr>
                      {expandedCostEditor === row.listing_id && (
                        <tr key={`${row.listing_id}-editor`}>
                          <td colSpan={9} className="px-4 pb-3">
                            <CostEditor row={row} onSaved={() => fetchData(page)} />
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

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

export default function ProfitPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">Loading…</div>}>
      <ProfitContent />
    </Suspense>
  );
}
