"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getShops, getListings, getListing, syncShop, getAccessToken, ApiError,
  type Shop, type ListingListItem, type ListingDetail, type ListingsParams,
} from "../../lib/api";

// ---- constants ----

const STATE_TABS = ["All", "active", "inactive", "draft", "expired"] as const;

const STATE_BADGE: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  inactive: "bg-gray-100 text-gray-500",
  draft: "bg-yellow-100 text-yellow-700",
  expired: "bg-red-100 text-red-600",
};

const SORTABLE_COLS = ["title", "state", "price_amount", "quantity", "last_synced_at", "etsy_updated_at", "updated_at"] as const;
type SortCol = (typeof SORTABLE_COLS)[number];

const COL_LABELS: Record<string, string> = {
  thumbnail: "Thumb",
  title: "Title",
  state: "State",
  price_amount: "Price",
  quantity: "Qty",
  sku: "SKU",
  has_variations: "Variations",
  last_synced_at: "Last Synced",
};

const ALL_COLS = Object.keys(COL_LABELS);
const DEFAULT_VISIBLE = new Set(ALL_COLS);

function loadColVisibility(): Set<string> {
  try {
    const raw = localStorage.getItem("listings_col_visibility");
    if (raw) return new Set(JSON.parse(raw) as string[]);
  } catch {}
  return new Set(DEFAULT_VISIBLE);
}

function saveColVisibility(cols: Set<string>) {
  localStorage.setItem("listings_col_visibility", JSON.stringify([...cols]));
}

type SavedView = { name: string; params: ListingsParams };

function loadSavedViews(): SavedView[] {
  try {
    const raw = localStorage.getItem("listings_saved_views");
    if (raw) return JSON.parse(raw) as SavedView[];
  } catch {}
  return [];
}

function saveSavedViews(views: SavedView[]) {
  localStorage.setItem("listings_saved_views", JSON.stringify(views));
}

// ---- helpers ----

function formatPrice(amount: number | null, divisor: number | null, currency: string | null): string {
  if (amount == null) return "—";
  const val = amount / (divisor ?? 100);
  return `${currency ?? ""} ${val.toFixed(2)}`.trim();
}

function SortIcon({ col, sortBy, sortDir }: { col: string; sortBy: string; sortDir: string }) {
  if (col !== sortBy) return <span className="text-gray-300 ml-1">↕</span>;
  return <span className="text-indigo-600 ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>;
}

// ---- Detail Sidebar ----

function DetailSidebar({ listingId, onClose }: { listingId: string; onClose: () => void }) {
  const [detail, setDetail] = useState<ListingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setDetail(null);
    setError(null);
    getListing(listingId)
      .then(setDetail)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load."))
      .finally(() => setLoading(false));
  }, [listingId]);

  return (
    <div className="fixed inset-0 z-40 flex justify-end" onClick={onClose}>
      <div
        className="relative w-full max-w-md bg-white shadow-xl border-l border-gray-200 overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <h2 className="text-base font-semibold text-gray-900 truncate">{detail?.title ?? "Listing Detail"}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none ml-4">×</button>
        </div>

        {loading && (
          <div className="flex justify-center py-12">
            <div className="w-6 h-6 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {error && <p className="text-red-600 text-sm px-6 py-4">{error}</p>}

        {detail && (
          <div className="px-6 py-5 space-y-5 text-sm">
            {detail.thumbnail_url && (
              <img src={detail.thumbnail_url} alt={detail.title ?? ""} className="w-full aspect-square object-cover rounded-lg border border-gray-100" />
            )}

            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">State</p>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATE_BADGE[detail.state ?? ""] ?? "bg-gray-100 text-gray-500"}`}>
                  {detail.state ?? "—"}
                </span>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">Price</p>
                <p className="text-gray-900 font-medium">{formatPrice(detail.price_amount, detail.price_divisor, detail.currency_code)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">Quantity</p>
                <p className="text-gray-900">{detail.quantity ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">SKU</p>
                <p className="text-gray-900">{detail.sku ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">Has Variations</p>
                <p className="text-gray-900">{detail.has_variations ? "Yes" : "No"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">Personalizable</p>
                <p className="text-gray-900">{detail.is_personalizable == null ? "—" : detail.is_personalizable ? "Yes" : "No"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">Customizable</p>
                <p className="text-gray-900">{detail.is_customizable == null ? "—" : detail.is_customizable ? "Yes" : "No"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">Who Made</p>
                <p className="text-gray-900">{detail.who_made ?? "—"}</p>
              </div>
              {detail.taxonomy_id && (
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wide">Taxonomy ID</p>
                  <p className="text-gray-900">{detail.taxonomy_id}</p>
                </div>
              )}
              {detail.section_id && (
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wide">Section ID</p>
                  <p className="text-gray-900">{detail.section_id}</p>
                </div>
              )}
            </div>

            {detail.tags && detail.tags.length > 0 && (
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-1.5">Tags</p>
                <div className="flex flex-wrap gap-1.5">
                  {detail.tags.map((t, i) => (
                    <span key={i} className="bg-indigo-50 text-indigo-700 text-xs px-2 py-0.5 rounded-full">{t}</span>
                  ))}
                </div>
              </div>
            )}

            {detail.description && (
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-1.5">Description</p>
                <p className="text-gray-700 text-sm leading-relaxed line-clamp-6">{detail.description}</p>
              </div>
            )}

            {detail.url && (
              <a href={detail.url} target="_blank" rel="noopener noreferrer"
                className="inline-block text-indigo-600 text-sm font-medium hover:underline">
                View on Etsy →
              </a>
            )}

            <div className="border-t border-gray-100 pt-4 text-xs text-gray-400 space-y-1">
              <p>Listing ID: #{detail.etsy_listing_id}</p>
              {detail.last_synced_at && <p>Synced: {new Date(detail.last_synced_at).toLocaleString()}</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---- Main content ----

function ListingsContent() {
  const router = useRouter();

  const [shops, setShops] = useState<Shop[]>([]);
  const [listings, setListings] = useState<ListingListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  // Filters
  const [selectedShopId, setSelectedShopId] = useState("");
  const [stateTab, setStateTab] = useState<string>("All");
  const [search, setSearch] = useState("");
  const [tag, setTag] = useState("");
  const [priceMin, setPriceMin] = useState("");
  const [priceMax, setPriceMax] = useState("");
  const [qtyMin, setQtyMin] = useState("");
  const [qtyMax, setQtyMax] = useState("");
  const [sectionId, setSectionId] = useState("");
  const [taxonomyId, setTaxonomyId] = useState("");
  const [hasVariations, setHasVariations] = useState("");
  const [isPersonalizable, setIsPersonalizable] = useState("");
  const [isCustomizable, setIsCustomizable] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Sort
  const [sortBy, setSortBy] = useState<SortCol>("updated_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  // Selection
  const [selected, setSelected] = useState<Set<string>>(new Set());

  // Column visibility
  const [visibleCols, setVisibleCols] = useState<Set<string>>(DEFAULT_VISIBLE);
  const [showColMenu, setShowColMenu] = useState(false);

  // Saved views
  const [savedViews, setSavedViews] = useState<SavedView[]>([]);
  const [viewName, setViewName] = useState("");
  const [showSaveView, setShowSaveView] = useState(false);

  // Detail sidebar
  const [detailId, setDetailId] = useState<string | null>(null);

  const perPage = 50;

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    setVisibleCols(loadColVisibility());
    setSavedViews(loadSavedViews());
    fetchShops();
  }, []);

  async function fetchShops() {
    try {
      const data = await getShops();
      const connected = (data.shops ?? []).filter((s) => s.is_connected);
      setShops(connected);
      if (connected.length > 0) setSelectedShopId(connected[0].id);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) { router.push("/login"); return; }
      setApiError("Failed to load shops.");
    }
  }

  const buildParams = useCallback((p: number): ListingsParams => {
    const params: ListingsParams = {
      page: p,
      per_page: perPage,
      sort_by: sortBy,
      sort_dir: sortDir,
    };
    if (selectedShopId) params.shop_id = selectedShopId;
    if (stateTab !== "All") params.state = stateTab;
    if (search) params.search = search;
    if (tag) params.tag = tag;
    if (priceMin) params.price_min = Number(priceMin);
    if (priceMax) params.price_max = Number(priceMax);
    if (qtyMin) params.quantity_min = Number(qtyMin);
    if (qtyMax) params.quantity_max = Number(qtyMax);
    if (sectionId) params.section_id = sectionId;
    if (taxonomyId) params.taxonomy_id = taxonomyId;
    if (hasVariations !== "") params.has_variations = hasVariations === "true";
    if (isPersonalizable !== "") params.is_personalizable = isPersonalizable === "true";
    if (isCustomizable !== "") params.is_customizable = isCustomizable === "true";
    return params;
  }, [selectedShopId, stateTab, search, tag, priceMin, priceMax, qtyMin, qtyMax, sectionId, taxonomyId, hasVariations, isPersonalizable, isCustomizable, sortBy, sortDir]);

  const fetchListings = useCallback(async (p: number = 1) => {
    if (!getAccessToken()) return;
    setLoading(true);
    setApiError(null);
    try {
      const data = await getListings(buildParams(p));
      setListings(data.items);
      setTotal(data.total);
      setPage(p);
      setSelected(new Set());
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) { router.push("/login"); return; }
      setApiError(e instanceof ApiError ? e.message : "Failed to load listings.");
    } finally {
      setLoading(false);
    }
  }, [buildParams]);

  useEffect(() => { fetchListings(1); }, [selectedShopId, stateTab, sortBy, sortDir]);

  async function triggerSync() {
    if (!selectedShopId) { setApiError("Select a shop first."); return; }
    setSyncing(true);
    setSyncMsg(null);
    try {
      const data = await syncShop(selectedShopId);
      if (data.status === "completed") {
        setSyncMsg({ ok: true, text: `Sync complete — ${data.processed_items} listings synced.` });
        await fetchListings(1);
      } else {
        setSyncMsg({ ok: false, text: `Sync failed: ${data.error_message ?? "Unknown error"}` });
      }
    } catch (e) {
      setSyncMsg({ ok: false, text: e instanceof ApiError ? e.message : "Sync failed." });
    } finally {
      setSyncing(false);
    }
  }

  function handleSort(col: SortCol) {
    if (sortBy === col) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortBy(col); setSortDir("desc"); }
  }

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  function toggleSelectAll() {
    if (selected.size === listings.length) setSelected(new Set());
    else setSelected(new Set(listings.map((l) => l.id)));
  }

  function toggleCol(col: string) {
    setVisibleCols((prev) => {
      const next = new Set(prev);
      if (next.has(col)) { if (next.size > 1) next.delete(col); }
      else next.add(col);
      saveColVisibility(next);
      return next;
    });
  }

  function saveCurrentView() {
    if (!viewName.trim()) return;
    const view: SavedView = { name: viewName.trim(), params: buildParams(1) };
    const updated = [...savedViews.filter((v) => v.name !== view.name), view];
    setSavedViews(updated);
    saveSavedViews(updated);
    setViewName("");
    setShowSaveView(false);
  }

  function applyView(view: SavedView) {
    const p = view.params;
    if (p.shop_id !== undefined) setSelectedShopId(p.shop_id);
    if (p.state !== undefined) setStateTab(p.state); else setStateTab("All");
    if (p.search !== undefined) setSearch(p.search); else setSearch("");
    if (p.tag !== undefined) setTag(p.tag); else setTag("");
    if (p.price_min !== undefined) setPriceMin(String(p.price_min)); else setPriceMin("");
    if (p.price_max !== undefined) setPriceMax(String(p.price_max)); else setPriceMax("");
    if (p.quantity_min !== undefined) setQtyMin(String(p.quantity_min)); else setQtyMin("");
    if (p.quantity_max !== undefined) setQtyMax(String(p.quantity_max)); else setQtyMax("");
    if (p.section_id !== undefined) setSectionId(p.section_id); else setSectionId("");
    if (p.taxonomy_id !== undefined) setTaxonomyId(p.taxonomy_id); else setTaxonomyId("");
    if (p.has_variations !== undefined) setHasVariations(String(p.has_variations)); else setHasVariations("");
    if (p.is_personalizable !== undefined) setIsPersonalizable(String(p.is_personalizable)); else setIsPersonalizable("");
    if (p.is_customizable !== undefined) setIsCustomizable(String(p.is_customizable)); else setIsCustomizable("");
    if (p.sort_by) setSortBy(p.sort_by as SortCol);
    if (p.sort_dir) setSortDir(p.sort_dir);
  }

  function deleteView(name: string) {
    const updated = savedViews.filter((v) => v.name !== name);
    setSavedViews(updated);
    saveSavedViews(updated);
  }

  const totalPages = Math.ceil(total / perPage);
  const activeCount = listings.filter((l) => l.state === "active").length;
  const outOfStockCount = listings.filter((l) => l.quantity === 0).length;

  const colVisible = (c: string) => visibleCols.has(c);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <nav className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="text-xl font-bold text-indigo-600">BulkEdit</Link>
          <Link href="/shops" className="text-sm text-gray-500 hover:text-gray-700">Shops</Link>
          <span className="text-sm font-medium text-gray-900">Listings</span>
        </div>
        <Link href="/billing" className="text-sm text-gray-500 hover:text-gray-700">Billing</Link>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Listings</h1>
            <p className="text-sm text-gray-500 mt-0.5">{total.toLocaleString()} total</p>
          </div>
          <div className="flex gap-2">
            {selected.size > 0 && (
              <button
                disabled
                title="Bulk edit coming in Sprint 7"
                className="bg-indigo-100 text-indigo-400 font-medium px-4 py-2 rounded-lg text-sm cursor-not-allowed"
              >
                Bulk Edit {selected.size} Selected
              </button>
            )}
            <button
              onClick={triggerSync}
              disabled={syncing || !selectedShopId}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
            >
              {syncing ? "Syncing…" : "Sync Listings"}
            </button>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Total (page)", value: listings.length },
            { label: "Selected", value: selected.size },
            { label: "Active (page)", value: activeCount },
            { label: "Out of Stock (page)", value: outOfStockCount },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white border border-gray-200 rounded-xl px-5 py-4">
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
            </div>
          ))}
        </div>

        {/* Messages */}
        {syncMsg && (
          <div className={`px-4 py-3 rounded-lg text-sm border ${syncMsg.ok ? "bg-green-50 border-green-200 text-green-800" : "bg-red-50 border-red-200 text-red-800"}`}>
            {syncMsg.text}
          </div>
        )}
        {apiError && (
          <div className="px-4 py-3 bg-red-50 border border-red-200 text-red-800 rounded-lg text-sm">{apiError}</div>
        )}

        {/* Saved views */}
        {savedViews.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-gray-400 uppercase tracking-wide">Saved views:</span>
            {savedViews.map((v) => (
              <div key={v.name} className="flex items-center gap-1 bg-white border border-gray-200 rounded-full px-3 py-1 text-xs text-gray-700">
                <button onClick={() => applyView(v)} className="hover:text-indigo-600">{v.name}</button>
                <button onClick={() => deleteView(v.name)} className="text-gray-300 hover:text-red-400 ml-1">×</button>
              </div>
            ))}
          </div>
        )}

        {/* State tabs */}
        <div className="flex gap-1 bg-white border border-gray-200 rounded-xl p-1 w-fit">
          {STATE_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => { setStateTab(tab); }}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${stateTab === tab ? "bg-indigo-600 text-white" : "text-gray-500 hover:text-gray-700"}`}
            >
              {tab === "All" ? "All" : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Filter panel */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="flex flex-wrap items-center gap-3 px-4 py-3">
            {/* Shop selector */}
            <select
              value={selectedShopId}
              onChange={(e) => setSelectedShopId(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All shops</option>
              {shops.map((s) => <option key={s.id} value={s.id}>{s.shop_name ?? s.etsy_shop_id}</option>)}
            </select>

            {/* Search */}
            <div className="flex gap-2 flex-1 min-w-48">
              <input
                type="text"
                placeholder="Search by title…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") fetchListings(1); }}
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button onClick={() => fetchListings(1)} className="bg-gray-100 hover:bg-gray-200 border border-gray-300 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg">
                Search
              </button>
            </div>

            <button
              onClick={() => setShowAdvanced((v) => !v)}
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium ml-auto"
            >
              {showAdvanced ? "Hide filters ▲" : "More filters ▼"}
            </button>
          </div>

          {/* Advanced filters */}
          {showAdvanced && (
            <div className="border-t border-gray-100 px-4 py-4 grid grid-cols-3 gap-3 text-sm">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Tag</label>
                <input value={tag} onChange={(e) => setTag(e.target.value)}
                  placeholder="e.g. handmade" className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Price min (cents)</label>
                <input type="number" value={priceMin} onChange={(e) => setPriceMin(e.target.value)}
                  placeholder="e.g. 500" className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Price max (cents)</label>
                <input type="number" value={priceMax} onChange={(e) => setPriceMax(e.target.value)}
                  placeholder="e.g. 5000" className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Qty min</label>
                <input type="number" value={qtyMin} onChange={(e) => setQtyMin(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Qty max</label>
                <input type="number" value={qtyMax} onChange={(e) => setQtyMax(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Section ID</label>
                <input value={sectionId} onChange={(e) => setSectionId(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Taxonomy ID</label>
                <input value={taxonomyId} onChange={(e) => setTaxonomyId(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Has Variations</label>
                <select value={hasVariations} onChange={(e) => setHasVariations(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Personalizable</label>
                <select value={isPersonalizable} onChange={(e) => setIsPersonalizable(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Customizable</label>
                <select value={isCustomizable} onChange={(e) => setIsCustomizable(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option value="">Any</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>

              <div className="col-span-3 flex gap-2 pt-1">
                <button onClick={() => fetchListings(1)} className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg">Apply Filters</button>
                <button onClick={() => {
                  setTag(""); setPriceMin(""); setPriceMax(""); setQtyMin(""); setQtyMax("");
                  setSectionId(""); setTaxonomyId(""); setHasVariations(""); setIsPersonalizable(""); setIsCustomizable("");
                }} className="bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg">Clear</button>

                {/* Save view */}
                {showSaveView ? (
                  <div className="flex gap-2 ml-auto">
                    <input value={viewName} onChange={(e) => setViewName(e.target.value)}
                      placeholder="View name" className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                    <button onClick={saveCurrentView} className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-3 py-1.5 rounded-lg">Save</button>
                    <button onClick={() => setShowSaveView(false)} className="text-gray-400 hover:text-gray-600 text-sm px-2">Cancel</button>
                  </div>
                ) : (
                  <button onClick={() => setShowSaveView(true)} className="ml-auto text-sm text-gray-500 hover:text-gray-700 font-medium">
                    Save as view
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            {selected.size > 0 ? `${selected.size} of ${listings.length} selected` : `${listings.length} on page`}
          </p>
          <div className="relative">
            <button
              onClick={() => setShowColMenu((v) => !v)}
              className="border border-gray-300 bg-white rounded-lg text-sm text-gray-600 px-3 py-1.5 hover:bg-gray-50"
            >
              Columns ▾
            </button>
            {showColMenu && (
              <div className="absolute right-0 top-9 z-20 bg-white border border-gray-200 rounded-xl shadow-lg p-3 min-w-40 space-y-1.5">
                {ALL_COLS.map((col) => (
                  <label key={col} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer hover:text-gray-900">
                    <input type="checkbox" checked={visibleCols.has(col)} onChange={() => toggleCol(col)} className="rounded" />
                    {COL_LABELS[col]}
                  </label>
                ))}
              </div>
            )}
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
                    <th className="px-4 py-3 w-10">
                      <input type="checkbox"
                        checked={selected.size === listings.length && listings.length > 0}
                        onChange={toggleSelectAll}
                        className="rounded" />
                    </th>
                    {colVisible("thumbnail") && <th className="px-2 py-3 w-12" />}
                    {(["title", "state", "price_amount", "quantity", "sku", "has_variations", "last_synced_at"] as const).map((col) => {
                      if (!colVisible(col === "price_amount" ? "price_amount" : col) && col !== "title") {
                        const colKey = col === "price_amount" ? "price_amount" : col;
                        if (!colVisible(colKey)) return null;
                      }
                      const isSortable = SORTABLE_COLS.includes(col as SortCol);
                      return (
                        <th key={col}
                          className={`text-left px-4 py-3 font-medium text-gray-600 ${isSortable ? "cursor-pointer select-none hover:text-gray-900" : ""}`}
                          onClick={isSortable ? () => handleSort(col as SortCol) : undefined}
                        >
                          {COL_LABELS[col === "price_amount" ? "price_amount" : col] ?? col}
                          {isSortable && <SortIcon col={col} sortBy={sortBy} sortDir={sortDir} />}
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {listings.map((listing) => (
                    <tr
                      key={listing.id}
                      className={`hover:bg-gray-50 transition-colors cursor-pointer ${selected.has(listing.id) ? "bg-indigo-50" : ""}`}
                      onClick={() => setDetailId(listing.id)}
                    >
                      <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                        <input type="checkbox" checked={selected.has(listing.id)} onChange={() => toggleSelect(listing.id)} className="rounded" />
                      </td>
                      {colVisible("thumbnail") && (
                        <td className="px-2 py-2">
                          {listing.thumbnail_url
                            ? <img src={listing.thumbnail_url} alt="" className="w-9 h-9 object-cover rounded-lg border border-gray-100" />
                            : <div className="w-9 h-9 bg-gray-100 rounded-lg" />}
                        </td>
                      )}
                      {colVisible("title") && (
                        <td className="px-4 py-3 max-w-xs">
                          <p className="font-medium text-gray-900 truncate">{listing.title ?? "—"}</p>
                          <p className="text-xs text-gray-400">#{listing.etsy_listing_id}</p>
                        </td>
                      )}
                      {colVisible("state") && (
                        <td className="px-4 py-3">
                          {listing.state
                            ? <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATE_BADGE[listing.state] ?? "bg-gray-100 text-gray-500"}`}>{listing.state}</span>
                            : "—"}
                        </td>
                      )}
                      {colVisible("price_amount") && (
                        <td className="px-4 py-3 text-gray-700">{formatPrice(listing.price_amount, listing.price_divisor, listing.currency_code)}</td>
                      )}
                      {colVisible("quantity") && (
                        <td className="px-4 py-3 text-gray-700">{listing.quantity ?? "—"}</td>
                      )}
                      {colVisible("sku") && (
                        <td className="px-4 py-3 text-gray-500 text-xs">{listing.sku ?? "—"}</td>
                      )}
                      {colVisible("has_variations") && (
                        <td className="px-4 py-3 text-gray-500 text-xs">{listing.has_variations ? "Yes" : "No"}</td>
                      )}
                      {colVisible("last_synced_at") && (
                        <td className="px-4 py-3 text-gray-400 text-xs">
                          {listing.last_synced_at ? new Date(listing.last_synced_at).toLocaleDateString() : "Never"}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">Page {page} of {totalPages} ({total.toLocaleString()} total)</p>
                <div className="flex gap-2">
                  <button onClick={() => fetchListings(page - 1)} disabled={page <= 1}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50">Previous</button>
                  <button onClick={() => fetchListings(page + 1)} disabled={page >= totalPages}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50">Next</button>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Detail sidebar */}
      {detailId && <DetailSidebar listingId={detailId} onClose={() => setDetailId(null)} />}
    </div>
  );
}

export default function ListingsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-400">Loading…</div>}>
      <ListingsContent />
    </Suspense>
  );
}
