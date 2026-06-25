"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getAccessToken, getListings, createBulkEditSession, getBulkEditSession,
  addBulkEditChange, removeBulkEditChange, generateBulkEditPreview,
  getBulkEditPreview, cancelBulkEditSession, ApiError,
  type ListingListItem, type BulkEditSession, type BulkEditSessionDetail,
  type BulkEditChange, type BulkEditPreviewItem, type BulkEditPreviewGenerateResponse,
} from "../../lib/api";

// ---- constants ----

const FIELD_OPTIONS = [
  { value: "title", label: "Title", type: "text" },
  { value: "description", label: "Description", type: "text" },
  { value: "tags", label: "Tags", type: "array" },
  { value: "materials", label: "Materials", type: "array" },
  { value: "price_amount", label: "Price (cents)", type: "number" },
  { value: "quantity", label: "Quantity", type: "number" },
  { value: "sku", label: "SKU", type: "text" },
  { value: "is_personalizable", label: "Is Personalizable", type: "bool" },
  { value: "is_customizable", label: "Is Customizable", type: "bool" },
  { value: "personalization_is_required", label: "Personalization Required", type: "bool" },
  { value: "section_id", label: "Section ID", type: "text" },
  { value: "taxonomy_id", label: "Taxonomy ID", type: "text" },
  { value: "processing_min", label: "Processing Min (days)", type: "number" },
  { value: "processing_max", label: "Processing Max (days)", type: "number" },
  { value: "personalization_instructions", label: "Personalization Instructions", type: "text" },
];

const OPS_BY_TYPE: Record<string, { value: string; label: string }[]> = {
  text: [
    { value: "set", label: "Set to" },
    { value: "append", label: "Append" },
    { value: "prepend", label: "Prepend" },
    { value: "replace", label: "Find & Replace" },
  ],
  bool: [{ value: "set", label: "Set to" }],
  number: [
    { value: "set", label: "Set to" },
    { value: "percentage_change", label: "Change by %" },
    { value: "fixed_amount_change", label: "Add fixed amount" },
  ],
  array: [
    { value: "set", label: "Replace all" },
    { value: "add_tag", label: "Add item" },
    { value: "remove_tag", label: "Remove item" },
  ],
};

const VALIDATION_BADGE: Record<string, string> = {
  valid: "bg-green-100 text-green-700",
  warning: "bg-yellow-100 text-yellow-700",
  invalid: "bg-red-100 text-red-700",
};

function formatVal(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (Array.isArray(v)) return v.join(", ") || "(empty)";
  return String(v);
}

// ---- Listing selector ----

function ListingSelector({
  preselected,
  onConfirm,
}: {
  preselected: string[];
  onConfirm: (ids: string[]) => void;
}) {
  const [listings, setListings] = useState<ListingListItem[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set(preselected));
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 20;

  const load = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const data = await getListings({ page: p, per_page: perPage, search: search || undefined });
      setListings(data.items);
      setTotal(data.total);
      setPage(p);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load listings.");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { load(1); }, []);

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search listings…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") load(1); }}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button onClick={() => load(1)} className="bg-gray-100 hover:bg-gray-200 border border-gray-300 text-gray-700 text-sm px-4 py-2 rounded-lg">Search</button>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="w-6 h-6 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 w-10" />
                <th className="text-left px-4 py-3 font-medium text-gray-600">Title</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">State</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Price</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {listings.map((l) => (
                <tr key={l.id} className={`hover:bg-gray-50 cursor-pointer ${selected.has(l.id) ? "bg-indigo-50" : ""}`} onClick={() => toggleSelect(l.id)}>
                  <td className="px-4 py-3">
                    <input type="checkbox" readOnly checked={selected.has(l.id)} className="rounded" />
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-900 truncate max-w-xs">{l.title ?? "—"}</p>
                    <p className="text-xs text-gray-400">#{l.etsy_listing_id}</p>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{l.state ?? "—"}</td>
                  <td className="px-4 py-3 text-gray-700">
                    {l.price_amount != null ? `${l.currency_code ?? ""} ${(l.price_amount / (l.price_divisor ?? 100)).toFixed(2)}` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <p className="text-gray-500">Page {page} of {totalPages}</p>
          <div className="flex gap-2">
            <button onClick={() => load(page - 1)} disabled={page <= 1} className="px-3 py-1.5 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50">Prev</button>
            <button onClick={() => load(page + 1)} disabled={page >= totalPages} className="px-3 py-1.5 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50">Next</button>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between pt-2 border-t border-gray-100">
        <p className="text-sm text-gray-500">{selected.size} listing{selected.size !== 1 ? "s" : ""} selected</p>
        <button
          onClick={() => onConfirm([...selected])}
          disabled={selected.size === 0}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-medium px-5 py-2 rounded-lg text-sm"
        >
          Create Bulk Edit Session →
        </button>
      </div>
    </div>
  );
}

// ── Change editor ────────────────────────────────────────────────────────────

function ChangeEditor({
  sessionId,
  changes,
  onChangeAdded,
  onChangeRemoved,
}: {
  sessionId: string;
  changes: BulkEditChange[];
  onChangeAdded: () => void;
  onChangeRemoved: (id: string) => void;
}) {
  const [field, setField] = useState(FIELD_OPTIONS[0].value);
  const [operation, setOperation] = useState("");
  const [opValue, setOpValue] = useState("");
  const [findStr, setFindStr] = useState("");
  const [replaceStr, setReplaceStr] = useState("");
  const [boolValue, setBoolValue] = useState("true");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fieldMeta = FIELD_OPTIONS.find((f) => f.value === field)!;
  const ops = OPS_BY_TYPE[fieldMeta.type] ?? [];

  useEffect(() => {
    if (ops.length > 0) setOperation(ops[0].value);
  }, [field]);

  async function handleAdd() {
    setAdding(true);
    setError(null);
    try {
      let finalValue: unknown = opValue;
      if (fieldMeta.type === "bool") finalValue = boolValue === "true";
      else if (fieldMeta.type === "number") finalValue = Number(opValue);
      else if (operation === "replace") finalValue = { find: findStr, replace: replaceStr };

      await addBulkEditChange(sessionId, {
        field_name: field,
        operation,
        operation_value: finalValue,
      });
      setOpValue("");
      setFindStr("");
      setReplaceStr("");
      onChangeAdded();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to add change.");
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3 items-end">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Field</label>
          <select value={field} onChange={(e) => setField(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
            {FIELD_OPTIONS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Operation</label>
          <select value={operation} onChange={(e) => setOperation(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
            {ops.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Value</label>
          {fieldMeta.type === "bool" ? (
            <select value={boolValue} onChange={(e) => setBoolValue(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option value="true">True</option>
              <option value="false">False</option>
            </select>
          ) : operation === "replace" ? (
            <div className="flex gap-2">
              <input placeholder="Find" value={findStr} onChange={(e) => setFindStr(e.target.value)}
                className="flex-1 border border-gray-300 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <input placeholder="Replace" value={replaceStr} onChange={(e) => setReplaceStr(e.target.value)}
                className="flex-1 border border-gray-300 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
          ) : (
            <input
              type={fieldMeta.type === "number" ? "number" : "text"}
              value={opValue}
              onChange={(e) => setOpValue(e.target.value)}
              placeholder={fieldMeta.type === "number" ? "Enter number" : "Enter value"}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          )}
        </div>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <button onClick={handleAdd} disabled={adding}
        className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg">
        {adding ? "Adding…" : "+ Add Change"}
      </button>

      {changes.length > 0 && (
        <div className="border border-gray-200 rounded-xl overflow-hidden mt-2">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-2 font-medium text-gray-600">Field</th>
                <th className="text-left px-4 py-2 font-medium text-gray-600">Operation</th>
                <th className="text-left px-4 py-2 font-medium text-gray-600">Value</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {changes.map((c) => (
                <tr key={c.id}>
                  <td className="px-4 py-2 text-gray-800">{c.field_name}</td>
                  <td className="px-4 py-2 text-gray-600">{c.operation}</td>
                  <td className="px-4 py-2 text-gray-500 font-mono text-xs">
                    {formatVal(c.operation_value)}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button onClick={() => onChangeRemoved(c.id)}
                      className="text-xs text-red-500 hover:text-red-700">Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Preview diff table ───────────────────────────────────────────────────────

function PreviewTable({ items }: { items: BulkEditPreviewItem[] }) {
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="text-left px-4 py-3 font-medium text-gray-600 w-48">Listing</th>
            <th className="text-left px-4 py-3 font-medium text-gray-600 w-24">Status</th>
            <th className="text-left px-4 py-3 font-medium text-gray-600">Field</th>
            <th className="text-left px-4 py-3 font-medium text-gray-600">Before</th>
            <th className="text-left px-4 py-3 font-medium text-gray-600">After</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {items.map((item) => {
            const diffKeys = Object.keys(item.diff ?? {});
            if (diffKeys.length === 0) {
              return (
                <tr key={item.id}>
                  <td className="px-4 py-3 text-gray-700 font-medium">{item.listing_title ?? item.listing_id}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${VALIDATION_BADGE[item.validation_status] ?? "bg-gray-100 text-gray-500"}`}>
                      {item.validation_status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs italic" colSpan={3}>No changes</td>
                </tr>
              );
            }
            return diffKeys.map((field, fi) => (
              <tr key={`${item.id}-${field}`} className={fi === 0 ? "" : "border-t-0"}>
                {fi === 0 && (
                  <>
                    <td className="px-4 py-3 text-gray-700 font-medium align-top" rowSpan={diffKeys.length}>
                      <p className="truncate max-w-[180px]">{item.listing_title ?? item.listing_id}</p>
                    </td>
                    <td className="px-4 py-3 align-top" rowSpan={diffKeys.length}>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${VALIDATION_BADGE[item.validation_status] ?? "bg-gray-100 text-gray-500"}`}>
                        {item.validation_status}
                      </span>
                    </td>
                  </>
                )}
                <td className="px-4 py-3 text-indigo-700 font-mono text-xs">{field}</td>
                <td className="px-4 py-3 text-gray-500 text-xs max-w-[200px] truncate">
                  {formatVal(item.diff[field]?.before)}
                </td>
                <td className="px-4 py-3 text-gray-900 text-xs max-w-[200px] truncate">
                  {formatVal(item.diff[field]?.after)}
                </td>
              </tr>
            ));
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

function BulkEditContent() {
  const router = useRouter();

  // Phase: select | session | preview
  const [phase, setPhase] = useState<"select" | "session" | "preview">("select");

  const [session, setSession] = useState<BulkEditSessionDetail | null>(null);
  const [previewResp, setPreviewResp] = useState<BulkEditPreviewGenerateResponse | null>(null);
  const [previewItems, setPreviewItems] = useState<BulkEditPreviewItem[]>([]);
  const [previewPage, setPreviewPage] = useState(1);
  const [previewTotal, setPreviewTotal] = useState(0);
  const [previewLoading, setPreviewLoading] = useState(false);

  const [creating, setCreating] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const preselected: string[] = (() => {
    if (typeof window === "undefined") return [];
    try {
      const raw = localStorage.getItem("bulk_edit_selected_listing_ids");
      return raw ? JSON.parse(raw) : [];
    } catch { return []; }
  })();

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); }
  }, []);

  async function handleCreateSession(listingIds: string[]) {
    setCreating(true);
    setApiError(null);
    try {
      const s = await createBulkEditSession(listingIds);
      const detail = await getBulkEditSession(s.id);
      setSession(detail);
      setPhase("session");
      localStorage.removeItem("bulk_edit_selected_listing_ids");
    } catch (e) {
      setApiError(e instanceof ApiError ? e.message : "Failed to create session.");
    } finally {
      setCreating(false);
    }
  }

  async function refreshSession() {
    if (!session) return;
    try {
      const detail = await getBulkEditSession(session.id);
      setSession(detail);
    } catch {}
  }

  async function handleChangeAdded() {
    await refreshSession();
    setSuccessMsg("Change added.");
    setTimeout(() => setSuccessMsg(null), 2000);
  }

  async function handleChangeRemoved(changeId: string) {
    if (!session) return;
    try {
      await removeBulkEditChange(session.id, changeId);
      await refreshSession();
    } catch (e) {
      setApiError(e instanceof ApiError ? e.message : "Failed to remove change.");
    }
  }

  async function handleGeneratePreview() {
    if (!session) return;
    setPreviewLoading(true);
    setApiError(null);
    try {
      const resp = await generateBulkEditPreview(session.id);
      setPreviewResp(resp);
      await loadPreviewItems(session.id, 1);
      await refreshSession();
      setPhase("preview");
    } catch (e) {
      setApiError(e instanceof ApiError ? e.message : "Failed to generate preview.");
    } finally {
      setPreviewLoading(false);
    }
  }

  async function loadPreviewItems(sessionId: string, p: number) {
    const data = await getBulkEditPreview(sessionId, { page: p, per_page: 50 });
    setPreviewItems(data.items);
    setPreviewTotal(data.total);
    setPreviewPage(p);
  }

  async function handleCancel() {
    if (!session) return;
    try {
      await cancelBulkEditSession(session.id);
      setPhase("select");
      setSession(null);
      setPreviewResp(null);
      setPreviewItems([]);
    } catch (e) {
      setApiError(e instanceof ApiError ? e.message : "Failed to cancel.");
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="text-xl font-bold text-indigo-600">BulkEdit</Link>
          <Link href="/listings" className="text-sm text-gray-500 hover:text-gray-700">Listings</Link>
          <span className="text-sm font-medium text-gray-900">Bulk Edit</span>
        </div>
        <Link href="/billing" className="text-sm text-gray-500 hover:text-gray-700">Billing</Link>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Bulk Edit</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {phase === "select" && "Select listings to edit"}
              {phase === "session" && `Session: ${session?.id.slice(0, 8)}… — ${session?.selected_count} listings`}
              {phase === "preview" && "Preview changes before applying"}
            </p>
          </div>
          {phase !== "select" && (
            <button onClick={handleCancel} className="text-sm text-gray-400 hover:text-red-600 border border-gray-200 rounded-lg px-3 py-1.5">
              Discard Session
            </button>
          )}
        </div>

        {/* Progress steps */}
        <div className="flex items-center gap-3 text-sm">
          {[
            { key: "select", label: "1. Select Listings" },
            { key: "session", label: "2. Add Changes" },
            { key: "preview", label: "3. Preview & Apply" },
          ].map(({ key, label }) => (
            <span key={key} className={`px-3 py-1 rounded-full ${phase === key ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-400"}`}>
              {label}
            </span>
          ))}
        </div>

        {/* Messages */}
        {apiError && <div className="px-4 py-3 bg-red-50 border border-red-200 text-red-800 rounded-lg text-sm">{apiError}</div>}
        {successMsg && <div className="px-4 py-3 bg-green-50 border border-green-200 text-green-800 rounded-lg text-sm">{successMsg}</div>}

        {/* Phase: select */}
        {phase === "select" && (
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Select Listings</h2>
            {creating ? (
              <div className="flex justify-center py-8">
                <div className="w-6 h-6 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <ListingSelector preselected={preselected} onConfirm={handleCreateSession} />
            )}
          </div>
        )}

        {/* Phase: session — add changes */}
        {phase === "session" && session && (
          <>
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Add Changes</h2>
              <p className="text-sm text-gray-500 mb-4">
                Each change applies to all {session.selected_count} selected listings.
              </p>
              <ChangeEditor
                sessionId={session.id}
                changes={session.changes}
                onChangeAdded={handleChangeAdded}
                onChangeRemoved={handleChangeRemoved}
              />
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleGeneratePreview}
                disabled={previewLoading || session.changes.length === 0}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-medium px-6 py-2.5 rounded-lg text-sm"
              >
                {previewLoading ? "Generating Preview…" : `Preview Changes (${session.changes.length} rule${session.changes.length !== 1 ? "s" : ""})`}
              </button>
            </div>
          </>
        )}

        {/* Phase: preview */}
        {phase === "preview" && previewResp && session && (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-4 gap-4">
              {[
                { label: "Listings", value: previewResp.summary.selected_count },
                { label: "Valid", value: previewResp.summary.valid, color: "text-green-600" },
                { label: "Warning", value: previewResp.summary.warning, color: "text-yellow-600" },
                { label: "Invalid", value: previewResp.summary.invalid, color: "text-red-600" },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-white border border-gray-200 rounded-xl px-5 py-4">
                  <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
                  <p className={`text-2xl font-bold ${color ?? "text-gray-900"}`}>{value}</p>
                </div>
              ))}
            </div>

            {/* Diff table */}
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Field-level Preview</h2>
              {previewItems.length === 0 ? (
                <p className="text-gray-400 text-sm">No preview items. Add changes and generate preview.</p>
              ) : (
                <PreviewTable items={previewItems} />
              )}

              {previewTotal > 50 && (
                <div className="flex items-center justify-between mt-4 text-sm">
                  <p className="text-gray-500">Page {previewPage} ({previewTotal} total)</p>
                  <div className="flex gap-2">
                    <button onClick={() => loadPreviewItems(session.id, previewPage - 1)} disabled={previewPage <= 1} className="px-3 py-1.5 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50">Prev</button>
                    <button onClick={() => loadPreviewItems(session.id, previewPage + 1)} disabled={previewPage * 50 >= previewTotal} className="px-3 py-1.5 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50">Next</button>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 justify-end">
              <button
                onClick={() => setPhase("session")}
                className="border border-gray-300 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-50"
              >
                ← Edit Changes
              </button>
              <button
                disabled
                title="Etsy write operations start in Sprint 8"
                className="bg-gray-200 text-gray-400 font-medium px-6 py-2.5 rounded-lg text-sm cursor-not-allowed"
              >
                Apply to Etsy — starts in Sprint 8
              </button>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-xl px-5 py-3 text-sm text-amber-800">
              <strong>Note:</strong> Applying changes to Etsy is a Sprint 8 feature. The preview above shows exactly what will change. No listings have been modified.
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default function BulkEditPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-400">Loading…</div>}>
      <BulkEditContent />
    </Suspense>
  );
}
