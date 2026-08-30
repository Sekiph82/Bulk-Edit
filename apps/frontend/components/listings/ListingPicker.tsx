"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getListings, getShops, ApiError,
  type ListingListItem, type ListingsParams, type Shop,
} from "@/lib/api";
import { decodeEntities } from "@/lib/decodeEntities";

/**
 * Shared listing picker (M03.04). Wraps the same getListings() every other
 * page already used ad hoc — this centralizes shop/status filter, title
 * search, pagination, thumbnails, variation indicator, and loading/error/
 * empty states so consumers stop hand-rolling their own (usually client-side
 * only, unpaginated, no thumbnail) version.
 *
 * Selection state is owned by the caller (selectedIds/onSelectionChange) so
 * it survives page/filter changes and each consumer can wire it into its own
 * apply/job-creation flow without this component knowing about any of that.
 */
export interface ListingPickerProps {
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
  multiSelect?: boolean;
  pageSize?: number;
  showShopFilter?: boolean;
  showStatusFilter?: boolean;
  /** Extra fixed getListings() params this consumer always wants applied
   * (e.g. { has_variations: true } for the Variations page) — merged under
   * whatever the picker's own filters produce. */
  extraParams?: Partial<ListingsParams>;
  disabled?: boolean;
  className?: string;
  /** Override the default "No listings found." empty state — e.g. to
   * distinguish "nothing synced yet" from "nothing matches your search"
   * (see the Variations page's has_variations empty state). Receives
   * whether a search term is currently active. */
  renderEmpty?: (hasSearch: boolean) => React.ReactNode;
}

const STATE_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "draft", label: "Draft" },
  { value: "inactive", label: "Inactive" },
  { value: "expired", label: "Expired" },
  { value: "sold_out", label: "Sold Out" },
];

export default function ListingPicker({
  selectedIds,
  onSelectionChange,
  multiSelect = true,
  pageSize = 20,
  showShopFilter = false,
  showStatusFilter = true,
  extraParams,
  disabled = false,
  className,
  renderEmpty,
}: ListingPickerProps) {
  const [listings, setListings] = useState<ListingListItem[]>([]);
  const [shops, setShops] = useState<Shop[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [shopId, setShopId] = useState("");
  const [state, setState] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (p: number) => {
    setLoading(true);
    setError(null);
    try {
      const pg = await getListings({
        page: p,
        per_page: pageSize,
        search: search || undefined,
        shop_id: shopId || undefined,
        state: state || undefined,
        ...extraParams,
      });
      setListings(pg.items);
      setTotal(pg.total);
      setPage(p);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load listings.");
    } finally {
      setLoading(false);
    }
    // extraParams is an object literal from the caller — compare by JSON to
    // avoid re-fetching on every render if the caller doesn't memoize it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageSize, search, shopId, state, JSON.stringify(extraParams)]);

  useEffect(() => {
    load(1);
  }, [load]);

  useEffect(() => {
    if (!showShopFilter) return;
    getShops().then((r) => setShops(r.shops)).catch(() => setShops([]));
  }, [showShopFilter]);

  function toggle(id: string) {
    if (disabled) return;
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      if (!multiSelect) next.clear();
      next.add(id);
    }
    onSelectionChange(next);
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className={className}>
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <input
          type="text"
          placeholder="Search listings…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-40 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
        {showStatusFilter && (
          <select
            value={state}
            onChange={(e) => setState(e.target.value)}
            className="border border-gray-200 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            {STATE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        )}
        {showShopFilter && shops.length > 1 && (
          <select
            value={shopId}
            onChange={(e) => setShopId(e.target.value)}
            className="border border-gray-200 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            <option value="">All shops</option>
            {shops.map((s) => (
              <option key={s.id} value={s.id}>{s.shop_name}</option>
            ))}
          </select>
        )}
      </div>

      <p className="text-xs text-gray-400 mb-2">
        {selectedIds.size} selected
      </p>

      {error && (
        <div className="p-3 rounded bg-red-50 border border-red-200 text-red-700 text-sm mb-2">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="w-6 h-6 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : listings.length === 0 ? (
        renderEmpty ? renderEmpty(!!search) : (
          <p className="text-sm text-gray-400 text-center py-6">No listings found.</p>
        )
      ) : (
        <div className="max-h-72 overflow-y-auto space-y-1 border border-gray-100 rounded-lg p-1">
          {listings.map((l) => (
            <label
              key={l.id}
              className={`flex items-center gap-3 p-2 rounded transition-colors ${disabled ? "cursor-not-allowed opacity-60" : "hover:bg-gray-50 cursor-pointer"} ${selectedIds.has(l.id) ? "bg-indigo-50/60" : ""}`}
            >
              <input
                type={multiSelect ? "checkbox" : "radio"}
                checked={selectedIds.has(l.id)}
                onChange={() => toggle(l.id)}
                disabled={disabled}
                className="accent-indigo-600"
              />
              {l.thumbnail_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={l.thumbnail_url} alt="" className="w-8 h-8 rounded object-cover border border-gray-200 flex-shrink-0" />
              ) : (
                <div className="w-8 h-8 rounded border border-dashed border-gray-200 flex-shrink-0" />
              )}
              <span className="text-sm text-gray-800 truncate flex-1">
                {l.title ? decodeEntities(l.title) : l.etsy_listing_id}
              </span>
              {l.has_variations && (
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-purple-100 text-purple-700 flex-shrink-0">
                  Variations
                </span>
              )}
              <span className="text-xs text-gray-400 shrink-0">{l.etsy_listing_id}</span>
            </label>
          ))}
        </div>
      )}

      {totalPages > 1 && !loading && (
        <div className="flex items-center justify-between mt-2">
          <p className="text-xs text-gray-400">Page {page} of {totalPages} ({total.toLocaleString()} total)</p>
          <div className="flex gap-2">
            <button
              onClick={() => load(page - 1)}
              disabled={page <= 1}
              className="px-2.5 py-1 text-xs border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => load(page + 1)}
              disabled={page >= totalPages}
              className="px-2.5 py-1 text-xs border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
