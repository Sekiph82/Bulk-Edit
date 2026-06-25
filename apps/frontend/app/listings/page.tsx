"use client";

import { useEffect, useState, Suspense, useCallback } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

type Shop = {
  id: string;
  etsy_shop_id: string;
  shop_name: string | null;
  is_connected: boolean;
};

type Listing = {
  id: string;
  etsy_listing_id: string;
  title: string | null;
  state: string | null;
  price_amount: number | null;
  price_divisor: number | null;
  currency_code: string | null;
  quantity: number | null;
  has_variations: boolean;
  last_synced_at: string | null;
};

type ListingPage = {
  items: Listing[];
  page: number;
  per_page: number;
  total: number;
};

type SyncResult = {
  sync_job_id: string;
  status: string;
  processed_items: number;
  total_items: number;
  error_message?: string;
};

const STATE_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  inactive: "bg-gray-100 text-gray-500",
  draft: "bg-yellow-100 text-yellow-700",
  expired: "bg-red-100 text-red-600",
};

function formatPrice(amount: number | null, divisor: number | null, currency: string | null): string {
  if (amount == null) return "—";
  const div = divisor ?? 100;
  const val = amount / div;
  return `${currency ?? ""} ${val.toFixed(2)}`.trim();
}

function ListingsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [shops, setShops] = useState<Shop[]>([]);
  const [selectedShopId, setSelectedShopId] = useState<string>("");
  const [listings, setListings] = useState<Listing[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const perPage = 50;

  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const token = () => typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const authHeaders = () => ({ Authorization: `Bearer ${token()}` });

  useEffect(() => {
    if (!token()) {
      router.push("/login");
      return;
    }
    fetchShops();
  }, []);

  async function fetchShops() {
    try {
      const r = await fetch(`${BACKEND_URL}/api/v1/etsy/shops`, { headers: authHeaders() });
      if (r.status === 401) { router.push("/login"); return; }
      const data = await r.json();
      const connected = (data.shops ?? []).filter((s: Shop) => s.is_connected);
      setShops(connected);
      if (connected.length > 0) setSelectedShopId(connected[0].id);
    } catch {
      setError("Failed to load shops.");
    }
  }

  const fetchListings = useCallback(async (p: number = 1) => {
    const t = token();
    if (!t) return;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: String(p),
        per_page: String(perPage),
        sort_by: "updated_at",
        sort_dir: "desc",
      });
      if (selectedShopId) params.set("shop_id", selectedShopId);
      if (stateFilter) params.set("state", stateFilter);
      if (search) params.set("search", search);

      const r = await fetch(`${BACKEND_URL}/api/v1/listings?${params}`, { headers: authHeaders() });
      if (r.status === 401) { router.push("/login"); return; }
      const data: ListingPage = await r.json();
      setListings(data.items);
      setTotal(data.total);
      setPage(p);
    } catch {
      setError("Failed to load listings.");
    } finally {
      setLoading(false);
    }
  }, [selectedShopId, stateFilter, search]);

  useEffect(() => {
    fetchListings(1);
  }, [selectedShopId, stateFilter]);

  async function triggerSync() {
    if (!selectedShopId) { setError("Select a shop to sync."); return; }
    setSyncing(true);
    setSyncResult(null);
    setError(null);
    try {
      const r = await fetch(`${BACKEND_URL}/api/v1/shops/${selectedShopId}/sync`, {
        method: "POST",
        headers: authHeaders(),
      });
      const data: SyncResult = await r.json();
      if (!r.ok) {
        setError((data as any).detail ?? "Sync failed.");
      } else {
        setSyncResult(data);
        await fetchListings(1);
      }
    } catch {
      setError("Sync request failed.");
    } finally {
      setSyncing(false);
    }
  }

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="text-xl font-bold text-indigo-600">BulkEdit</Link>
          <Link href="/shops" className="text-sm text-gray-500 hover:text-gray-700">Shops</Link>
          <span className="text-sm font-medium text-gray-900">Listings</span>
        </div>
        <Link href="/billing" className="text-sm text-gray-500 hover:text-gray-700">Billing</Link>
      </nav>

      <main className="max-w-7xl mx-auto px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Listings</h1>
            <p className="text-gray-500 mt-1">{total.toLocaleString()} listings synced</p>
          </div>
          <button
            onClick={triggerSync}
            disabled={syncing || !selectedShopId}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-medium px-5 py-2.5 rounded-lg text-sm transition-colors"
          >
            {syncing ? "Syncing..." : "Sync Listings"}
          </button>
        </div>

        {syncResult && (
          <div className={`mb-5 px-5 py-3 rounded-lg text-sm border ${syncResult.status === "completed" ? "bg-green-50 border-green-200 text-green-800" : "bg-red-50 border-red-200 text-red-800"}`}>
            {syncResult.status === "completed"
              ? `Sync complete — ${syncResult.processed_items} listings synced.`
              : `Sync failed: ${syncResult.error_message ?? "Unknown error"}`}
          </div>
        )}

        {error && (
          <div className="mb-5 bg-red-50 border border-red-200 text-red-800 rounded-lg px-5 py-3 text-sm">{error}</div>
        )}

        {/* Filters */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 mb-5 flex flex-wrap gap-3">
          <select
            value={selectedShopId}
            onChange={(e) => { setSelectedShopId(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All shops</option>
            {shops.map((s) => (
              <option key={s.id} value={s.id}>{s.shop_name ?? s.etsy_shop_id}</option>
            ))}
          </select>

          <select
            value={stateFilter}
            onChange={(e) => { setStateFilter(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All states</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="draft">Draft</option>
            <option value="expired">Expired</option>
          </select>

          <div className="flex gap-2 flex-1 min-w-48">
            <input
              type="text"
              placeholder="Search by title..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") fetchListings(1); }}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={() => fetchListings(1)}
              className="bg-gray-100 hover:bg-gray-200 border border-gray-300 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Search
            </button>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex justify-center py-16">
            <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : listings.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-xl p-10 text-center">
            <p className="text-4xl mb-3">📦</p>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">No listings yet</h3>
            <p className="text-gray-500 text-sm mb-5">Connect a shop and sync to import your listings.</p>
            <Link href="/shops" className="text-indigo-600 text-sm font-medium hover:underline">Go to Shops →</Link>
          </div>
        ) : (
          <>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-5 py-3 font-medium text-gray-600">Title</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">State</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Price</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Qty</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Last Synced</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {listings.map((listing) => (
                    <tr key={listing.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-5 py-3 max-w-xs">
                        <p className="font-medium text-gray-900 truncate">{listing.title ?? "—"}</p>
                        <p className="text-xs text-gray-400">#{listing.etsy_listing_id}</p>
                      </td>
                      <td className="px-4 py-3">
                        {listing.state ? (
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATE_COLORS[listing.state] ?? "bg-gray-100 text-gray-500"}`}>
                            {listing.state}
                          </span>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {formatPrice(listing.price_amount, listing.price_divisor, listing.currency_code)}
                      </td>
                      <td className="px-4 py-3 text-gray-700">{listing.quantity ?? "—"}</td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {listing.last_synced_at ? new Date(listing.last_synced_at).toLocaleString() : "Never"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-gray-500">
                  Page {page} of {totalPages} ({total.toLocaleString()} total)
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => fetchListings(page - 1)}
                    disabled={page <= 1}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => fetchListings(page + 1)}
                    disabled={page >= totalPages}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default function ListingsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-400">Loading...</div>}>
      <ListingsContent />
    </Suspense>
  );
}
