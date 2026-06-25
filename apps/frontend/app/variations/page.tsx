"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getAccessToken,
  getListings,
  createVariationJob,
  listVariationJobs,
  generateVariationPreview,
  getVariationPreview,
  applyVariationJob,
  getVariationResults,
  ApiError,
  type ListingListItem,
  type VariationJob,
  type VariationPreviewItem,
  type VariationResult,
} from "../../lib/api";

const OPERATION_OPTIONS = [
  { value: "set_variation_price", label: "Set Variation Price" },
  { value: "adjust_variation_price_percent", label: "Adjust Price by %" },
  { value: "adjust_variation_price_fixed", label: "Adjust Price by Fixed Amount" },
  { value: "set_variation_quantity", label: "Set Variation Quantity" },
  { value: "adjust_variation_quantity_fixed", label: "Adjust Quantity by Fixed Amount" },
  { value: "set_variation_sku", label: "Set Variation SKU" },
  { value: "replace_variation_sku_text", label: "Replace SKU Text" },
  { value: "set_variation_availability", label: "Set Variation Availability" },
];

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-700",
    preview_ready: "bg-blue-100 text-blue-700",
    running: "bg-yellow-100 text-yellow-700",
    completed: "bg-green-100 text-green-700",
    completed_with_errors: "bg-orange-100 text-orange-700",
    failed: "bg-red-100 text-red-700",
    success: "bg-green-100 text-green-700",
    skipped: "bg-gray-100 text-gray-500",
    pending: "bg-gray-100 text-gray-600",
    valid: "bg-green-100 text-green-700",
    warning: "bg-yellow-100 text-yellow-700",
    invalid: "bg-red-100 text-red-700",
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colors[status] ?? "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}

function buildPayload(
  opType: string,
  amount: string,
  findText: string,
  replaceText: string,
  available: string,
  propertyName: string,
  valueName: string,
): Record<string, unknown> {
  const selector =
    propertyName.trim()
      ? { property_name: propertyName.trim(), value_name: valueName.trim() || undefined }
      : undefined;

  const base: Record<string, unknown> = {};
  if (selector) base.selector = selector;

  switch (opType) {
    case "set_variation_price":
      return { ...base, price: parseFloat(amount) };
    case "adjust_variation_price_percent":
      return { ...base, percent: parseFloat(amount) };
    case "adjust_variation_price_fixed":
      return { ...base, delta: parseFloat(amount) };
    case "set_variation_quantity":
      return { ...base, quantity: parseInt(amount, 10) };
    case "adjust_variation_quantity_fixed":
      return { ...base, delta: parseInt(amount, 10) };
    case "set_variation_sku":
      return { ...base, sku: amount };
    case "replace_variation_sku_text":
      return { ...base, find: findText, replace: replaceText };
    case "set_variation_availability":
      return { ...base, available: available === "true" };
    default:
      return base;
  }
}

export default function VariationsPage() {
  const router = useRouter();
  const [listings, setListings] = useState<ListingListItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [operationType, setOperationType] = useState("set_variation_price");
  const [amount, setAmount] = useState("");
  const [findText, setFindText] = useState("");
  const [replaceText, setReplaceText] = useState("");
  const [available, setAvailable] = useState("true");
  const [propertyName, setPropertyName] = useState("");
  const [valueName, setValueName] = useState("");
  const [jobs, setJobs] = useState<VariationJob[]>([]);
  const [previewItems, setPreviewItems] = useState<VariationPreviewItem[]>([]);
  const [results, setResults] = useState<VariationResult[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [confirmText, setConfirmText] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadListings = useCallback(async () => {
    try {
      const page = await getListings({ has_variations: true, per_page: 200, search: search || undefined });
      setListings(page.items);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) router.push("/login");
    }
  }, [search, router]);

  const loadJobs = useCallback(async () => {
    try {
      const j = await listVariationJobs();
      setJobs(j);
    } catch (_) {}
  }, []);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    loadListings();
    loadJobs();
  }, [loadListings, loadJobs, router]);

  const toggleListing = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const handleCreateAndPreview = async () => {
    if (selectedIds.size === 0) { setError("Select at least one listing."); return; }
    setLoading(true); setError(null); setSuccess(null);
    try {
      const payload = buildPayload(operationType, amount, findText, replaceText, available, propertyName, valueName);
      const job = await createVariationJob([...selectedIds], operationType, payload);
      setActiveJobId(job.id);
      const updated = await generateVariationPreview(job.id);
      setJobs((prev) => [updated, ...prev]);
      const preview = await getVariationPreview(job.id, { per_page: 200 });
      setPreviewItems(preview.items);
      setResults([]);
      setSuccess(`Preview ready — ${preview.total} listing(s).`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!activeJobId) return;
    setShowConfirm(false); setLoading(true); setError(null); setSuccess(null);
    try {
      const updated = await applyVariationJob(activeJobId);
      setJobs((prev) => prev.map((j) => (j.id === activeJobId ? updated : j)));
      const res = await getVariationResults(activeJobId, { per_page: 200 });
      setResults(res.items);
      setSuccess(`Apply done — ${updated.success_count} success, ${updated.failure_count} failed, ${updated.skipped_count} skipped.`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setLoading(false);
      setConfirmText("");
    }
  };

  const activeJob = jobs.find((j) => j.id === activeJobId) ?? null;
  const hasInvalidPreview = previewItems.some((p) => p.validation_status === "invalid");
  const canApply = activeJob?.status === "preview_ready" && !hasInvalidPreview;

  const filteredListings = listings.filter(
    (l) => !search || (l.title ?? "").toLowerCase().includes(search.toLowerCase()),
  );

  const needsAmount = [
    "set_variation_price", "adjust_variation_price_percent", "adjust_variation_price_fixed",
    "set_variation_quantity", "adjust_variation_quantity_fixed", "set_variation_sku",
  ].includes(operationType);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-8 py-4 flex items-center gap-4">
        <Link href="/dashboard" className="text-xl font-extrabold text-gray-900 hover:text-indigo-600">
          Bulk-Edit
        </Link>
        <span className="text-gray-300">/</span>
        <span className="text-sm font-medium text-gray-600">Variation Editor</span>
      </nav>

      <main className="max-w-7xl mx-auto px-8 py-8 space-y-8">
        <h1 className="text-2xl font-bold text-gray-900">Variation Bulk Editor</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">{error}</div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-700">{success}</div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Listing selector */}
          <div className="lg:col-span-1 bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-3">
            <h2 className="font-semibold text-gray-800">Select Listings (with variations)</h2>
            <input
              type="text"
              placeholder="Search listings..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
            <div className="overflow-y-auto max-h-96 divide-y divide-gray-100">
              {filteredListings.length === 0 && (
                <p className="text-sm text-gray-400 py-4 text-center">No variation listings found.</p>
              )}
              {filteredListings.map((l) => (
                <label key={l.id} className="flex items-start gap-2 py-2 cursor-pointer hover:bg-gray-50 px-1 rounded">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(l.id)}
                    onChange={() => toggleListing(l.id)}
                    className="mt-0.5"
                  />
                  <span className="text-xs text-gray-700 leading-snug">{l.title ?? l.etsy_listing_id}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-400">{selectedIds.size} selected</p>
          </div>

          {/* Right: Operation config */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-4">
            <h2 className="font-semibold text-gray-800">Configure Operation</h2>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Operation</label>
              <select
                value={operationType}
                onChange={(e) => setOperationType(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-indigo-300"
              >
                {OPERATION_OPTIONS.map((op) => (
                  <option key={op.value} value={op.value}>{op.label}</option>
                ))}
              </select>
            </div>

            {operationType === "replace_variation_sku_text" ? (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Find text</label>
                  <input
                    type="text"
                    value={findText}
                    onChange={(e) => setFindText(e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    placeholder="OLD-PREFIX"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Replace with</label>
                  <input
                    type="text"
                    value={replaceText}
                    onChange={(e) => setReplaceText(e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    placeholder="NEW-PREFIX"
                  />
                </div>
              </div>
            ) : operationType === "set_variation_availability" ? (
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Availability</label>
                <select
                  value={available}
                  onChange={(e) => setAvailable(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  <option value="true">Available (enabled)</option>
                  <option value="false">Unavailable (disabled)</option>
                </select>
              </div>
            ) : needsAmount ? (
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  {operationType === "set_variation_sku" ? "SKU value" : "Value"}
                </label>
                <input
                  type={operationType === "set_variation_sku" ? "text" : "number"}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  placeholder={operationType === "set_variation_sku" ? "MY-SKU" : "0"}
                />
              </div>
            ) : null}

            <div className="border-t border-gray-100 pt-4">
              <p className="text-xs font-medium text-gray-600 mb-2">
                Selector (optional — leave blank to apply to ALL variations)
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Property name (e.g. Size)</label>
                  <input
                    type="text"
                    value={propertyName}
                    onChange={(e) => setPropertyName(e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    placeholder="Size"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Value name (e.g. Large)</label>
                  <input
                    type="text"
                    value={valueName}
                    onChange={(e) => setValueName(e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    placeholder="Large"
                  />
                </div>
              </div>
            </div>

            <button
              onClick={handleCreateAndPreview}
              disabled={loading || selectedIds.size === 0}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium px-5 py-2.5 rounded-lg text-sm transition-colors"
            >
              {loading ? "Working..." : "Preview Changes"}
            </button>
          </div>
        </div>

        {/* Preview table */}
        {previewItems.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-800">Preview ({previewItems.length} listings)</h2>
              {canApply && (
                <button
                  onClick={() => setShowConfirm(true)}
                  className="bg-green-600 hover:bg-green-700 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors"
                >
                  Apply Variations
                </button>
              )}
              {hasInvalidPreview && (
                <span className="text-sm text-red-600 font-medium">Cannot apply — invalid items present</span>
              )}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-3 text-gray-600 font-medium">Listing</th>
                    <th className="text-left py-2 px-3 text-gray-600 font-medium">Status</th>
                    <th className="text-left py-2 px-3 text-gray-600 font-medium">Before</th>
                    <th className="text-left py-2 px-3 text-gray-600 font-medium">After</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {previewItems.map((item) => {
                    const before = (item.before_variations as Array<Record<string, unknown>>) ?? [];
                    const after = (item.after_variations as Array<Record<string, unknown>>) ?? [];
                    return (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="py-2 px-3 text-gray-700 max-w-xs truncate">
                          {item.listing_title ?? item.etsy_listing_id}
                        </td>
                        <td className="py-2 px-3">
                          <StatusBadge status={item.validation_status} />
                        </td>
                        <td className="py-2 px-3 text-gray-500">
                          {before.slice(0, 3).map((v, i) => (
                            <div key={i} className="whitespace-nowrap">
                              {v.property_name ? `${v.property_name}: ${v.value_name}` : ""}
                              {v.price_amount != null ? ` — $${(Number(v.price_amount) / (Number(v.price_divisor) || 100)).toFixed(2)}` : ""}
                              {v.quantity != null ? ` qty:${v.quantity}` : ""}
                              {v.sku ? ` sku:${v.sku}` : ""}
                            </div>
                          ))}
                          {before.length > 3 && <div className="text-gray-400">+{before.length - 3} more</div>}
                        </td>
                        <td className="py-2 px-3 text-indigo-700">
                          {after.slice(0, 3).map((v, i) => (
                            <div key={i} className="whitespace-nowrap">
                              {v.property_name ? `${v.property_name}: ${v.value_name}` : ""}
                              {v.price_amount != null ? ` — $${(Number(v.price_amount) / (Number(v.price_divisor) || 100)).toFixed(2)}` : ""}
                              {v.quantity != null ? ` qty:${v.quantity}` : ""}
                              {v.sku ? ` sku:${v.sku}` : ""}
                            </div>
                          ))}
                          {after.length > 3 && <div className="text-gray-400">+{after.length - 3} more</div>}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Results panel */}
        {results.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h2 className="font-semibold text-gray-800 mb-4">Results</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-3 text-gray-600 font-medium">Listing</th>
                    <th className="text-left py-2 px-3 text-gray-600 font-medium">Status</th>
                    <th className="text-left py-2 px-3 text-gray-600 font-medium">Error</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {results.map((r) => (
                    <tr key={r.id} className="hover:bg-gray-50">
                      <td className="py-2 px-3 text-gray-700">{r.etsy_listing_id}</td>
                      <td className="py-2 px-3"><StatusBadge status={r.status} /></td>
                      <td className="py-2 px-3 text-red-600">{r.error_message ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Job history */}
        {jobs.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h2 className="font-semibold text-gray-800 mb-4">Recent Jobs</h2>
            <div className="space-y-2">
              {jobs.slice(0, 10).map((job) => (
                <div
                  key={job.id}
                  onClick={() => setActiveJobId(job.id)}
                  className={`flex items-center justify-between px-4 py-3 rounded-lg border cursor-pointer transition-colors ${
                    activeJobId === job.id
                      ? "border-indigo-300 bg-indigo-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="text-xs text-gray-600">
                    <span className="font-medium text-gray-800">{job.operation_type}</span>
                    <span className="ml-2 text-gray-400">{job.selected_count} listings</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={job.status} />
                    <span className="text-xs text-gray-400">
                      {new Date(job.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Apply confirm modal */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full mx-4">
            <h2 className="text-lg font-bold text-gray-900 mb-2">Confirm Apply Variations</h2>
            <p className="text-sm text-gray-600 mb-4">
              This will write variation changes to Etsy for <strong>{previewItems.length}</strong> listing(s).
              A backup snapshot is created automatically before each write.
            </p>
            <p className="text-xs text-gray-500 mb-3">
              Type <strong>APPLY VARIATIONS</strong> to confirm:
            </p>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full mb-4 focus:outline-none focus:ring-2 focus:ring-green-300"
              placeholder="APPLY VARIATIONS"
            />
            <div className="flex gap-3">
              <button
                onClick={handleApply}
                disabled={confirmText !== "APPLY VARIATIONS" || loading}
                className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors"
              >
                Apply
              </button>
              <button
                onClick={() => { setShowConfirm(false); setConfirmText(""); }}
                className="flex-1 border border-gray-300 text-gray-700 font-medium py-2.5 rounded-lg text-sm hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
