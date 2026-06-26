"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getAccessToken,
  getListings,
  createDynamicPricingJob,
  generateDynamicPricingPreview,
  getDynamicPricingRecommendations,
  acceptDynamicPricingRecommendation,
  rejectDynamicPricingRecommendation,
  acceptAllDynamicPricingRecommendations,
  convertDynamicPricingJob,
  getDynamicPricingSummary,
  listDynamicPricingJobs,
  ApiError,
  type ListingListItem,
  type DynamicPricingJob,
  type DynamicPricingRecommendation,
  type DynamicPricingRecommendationPage,
  type DynamicPricingSummary,
} from "@/lib/api";

const RULE_TYPES = [
  { value: "percentage_adjustment", label: "Percentage Adjustment" },
  { value: "fixed_amount_adjustment", label: "Fixed Amount Adjustment" },
  { value: "set_price", label: "Set Price" },
  { value: "reference_price", label: "Reference Price" },
];

const REFERENCE_MODES = [
  { value: "match", label: "Match reference price" },
  { value: "reference_minus_percent", label: "Reference minus %" },
  { value: "reference_plus_percent", label: "Reference plus %" },
  { value: "reference_minus_amount", label: "Reference minus amount" },
  { value: "reference_plus_amount", label: "Reference plus amount" },
];

const ROUNDING_RULES = [
  { value: "none", label: "No rounding" },
  { value: "ending_99", label: "Ending .99" },
  { value: "ending_95", label: "Ending .95" },
  { value: "nearest_50", label: "Nearest $0.50" },
  { value: "nearest_100", label: "Nearest $1.00" },
];

const STATUS_COLORS: Record<string, string> = {
  recommended: "bg-green-100 text-green-700",
  warning: "bg-yellow-100 text-yellow-700",
  invalid: "bg-red-100 text-red-700",
  skipped: "bg-gray-100 text-gray-500",
  accepted: "bg-blue-100 text-blue-700",
  rejected: "bg-red-50 text-red-500",
  converted: "bg-purple-100 text-purple-700",
};

function cents(amount: number | null | undefined): string {
  if (amount == null) return "â€”";
  return "$" + (amount / 100).toFixed(2);
}

export default function PricingRulesPage() {
  const router = useRouter();
  const [authed, setAuthed] = useState(false);

  // Step: "setup" | "preview" | "history"
  const [step, setStep] = useState<"setup" | "preview" | "history">("setup");

  // Listings
  const [listings, setListings] = useState<ListingListItem[]>([]);
  const [loadingListings, setLoadingListings] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Rule builder
  const [ruleType, setRuleType] = useState("percentage_adjustment");
  const [pctValue, setPctValue] = useState("10");
  const [fixedValue, setFixedValue] = useState("100");
  const [setPriceValue, setSetPriceValue] = useState("1999");
  const [refPrice, setRefPrice] = useState("2000");
  const [refMode, setRefMode] = useState("match");
  const [refPct, setRefPct] = useState("5");
  const [refAmount, setRefAmount] = useState("100");

  // Safety payload
  const [enableMarginFloor, setEnableMarginFloor] = useState(false);
  const [minMarginPct, setMinMarginPct] = useState("20");
  const [enablePriceFloor, setEnablePriceFloor] = useState(false);
  const [minPriceValue, setMinPriceValue] = useState("500");
  const [enablePriceCap, setEnablePriceCap] = useState(false);
  const [maxPriceValue, setMaxPriceValue] = useState("9999");
  const [roundingRule, setRoundingRule] = useState("none");

  // Job / preview state
  const [currentJob, setCurrentJob] = useState<DynamicPricingJob | null>(null);
  const [creatingJob, setCreatingJob] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [summary, setSummary] = useState<DynamicPricingSummary | null>(null);

  // Recommendations table
  const [recPage, setRecPage] = useState<DynamicPricingRecommendationPage | null>(null);
  const [recPageNum, setRecPageNum] = useState(1);
  const [recStatusFilter, setRecStatusFilter] = useState<string>("");
  const [recLoading, setRecLoading] = useState(false);
  const [pendingRec, setPendingRec] = useState<string | null>(null);

  // Accept-all
  const [acceptingAll, setAcceptingAll] = useState(false);

  // Convert modal
  const [showConvertModal, setShowConvertModal] = useState(false);
  const [convertConfirmText, setConvertConfirmText] = useState("");
  const [converting, setConverting] = useState(false);
  const [convertResult, setConvertResult] = useState<string | null>(null);

  // Job history
  const [jobs, setJobs] = useState<DynamicPricingJob[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getAccessToken()) {
      router.push("/auth/login");
      return;
    }
    setAuthed(true);
  }, [router]);

  useEffect(() => {
    if (!authed) return;
    setLoadingListings(true);
    getListings({ per_page: 200 })
      .then((d) => setListings(d.items))
      .catch(() => setListings([]))
      .finally(() => setLoadingListings(false));
  }, [authed]);

  const buildRulePayload = useCallback((): Record<string, unknown> => {
    if (ruleType === "percentage_adjustment") return { percent: parseFloat(pctValue) };
    if (ruleType === "fixed_amount_adjustment") return { amount: parseInt(fixedValue, 10) };
    if (ruleType === "set_price") return { price_amount: parseInt(setPriceValue, 10) };
    if (ruleType === "reference_price") {
      const p: Record<string, unknown> = {
        reference_price_amount: parseInt(refPrice, 10),
        mode: refMode,
      };
      if (refMode.includes("percent")) p.percent = parseFloat(refPct);
      if (refMode.includes("amount")) p.amount = parseInt(refAmount, 10);
      return p;
    }
    return {};
  }, [ruleType, pctValue, fixedValue, setPriceValue, refPrice, refMode, refPct, refAmount]);

  const buildSafetyPayload = useCallback((): Record<string, unknown> | null => {
    const p: Record<string, unknown> = {};
    if (enableMarginFloor) p.minimum_margin_percent = parseFloat(minMarginPct);
    if (enablePriceFloor) p.minimum_price_amount = parseInt(minPriceValue, 10);
    if (enablePriceCap) p.max_price_amount = parseInt(maxPriceValue, 10);
    if (roundingRule !== "none") p.rounding_rule = roundingRule;
    return Object.keys(p).length > 0 ? p : null;
  }, [enableMarginFloor, minMarginPct, enablePriceFloor, minPriceValue, enablePriceCap, maxPriceValue, roundingRule]);

  async function handleRunPreview() {
    setError(null);
    if (selectedIds.size === 0) { setError("Select at least one listing."); return; }
    setCreatingJob(true);
    try {
      const job = await createDynamicPricingJob({
        selected_listing_ids: Array.from(selectedIds),
        rule_type: ruleType,
        rule_payload: buildRulePayload(),
        safety_payload: buildSafetyPayload(),
      });
      setPreviewLoading(true);
      const previewed = await generateDynamicPricingPreview(job.id);
      setCurrentJob(previewed);
      const sum = await getDynamicPricingSummary(previewed.id);
      setSummary(sum);
      await loadRecs(previewed.id, 1, "");
      setStep("preview");
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
      else setError("Failed to generate preview.");
    } finally {
      setCreatingJob(false);
      setPreviewLoading(false);
    }
  }

  async function loadRecs(jobId: string, page: number, statusFilter: string) {
    setRecLoading(true);
    try {
      const data = await getDynamicPricingRecommendations(jobId, {
        page,
        per_page: 50,
        status: statusFilter || undefined,
      });
      setRecPage(data);
      setRecPageNum(page);
    } finally {
      setRecLoading(false);
    }
  }

  async function handleAccept(recId: string) {
    if (!currentJob) return;
    setPendingRec(recId);
    try {
      await acceptDynamicPricingRecommendation(recId);
      const sum = await getDynamicPricingSummary(currentJob.id);
      setSummary(sum);
      await loadRecs(currentJob.id, recPageNum, recStatusFilter);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    } finally {
      setPendingRec(null);
    }
  }

  async function handleReject(recId: string) {
    if (!currentJob) return;
    setPendingRec(recId);
    try {
      await rejectDynamicPricingRecommendation(recId);
      await loadRecs(currentJob.id, recPageNum, recStatusFilter);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    } finally {
      setPendingRec(null);
    }
  }

  async function handleAcceptAll() {
    if (!currentJob) return;
    setAcceptingAll(true);
    try {
      await acceptAllDynamicPricingRecommendations(currentJob.id);
      const sum = await getDynamicPricingSummary(currentJob.id);
      setSummary(sum);
      await loadRecs(currentJob.id, recPageNum, recStatusFilter);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    } finally {
      setAcceptingAll(false);
    }
  }

  async function handleConvert() {
    if (!currentJob || convertConfirmText !== "CONVERT PRICES") return;
    setConverting(true);
    try {
      const result = await convertDynamicPricingJob(currentJob.id);
      setConvertResult(result.bulk_edit_session_id);
      setShowConvertModal(false);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    } finally {
      setConverting(false);
    }
  }

  async function handleLoadHistory() {
    setStep("history");
    setJobsLoading(true);
    try {
      const data = await listDynamicPricingJobs();
      setJobs(data);
    } catch {
      setJobs([]);
    } finally {
      setJobsLoading(false);
    }
  }

  function handleSelectAll() {
    setSelectedIds(new Set(listings.map((l) => l.id)));
  }

  function handleDeselectAll() {
    setSelectedIds(new Set());
  }

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  if (!authed) return null;

  return (
    <main>
      {/* Safety Banner */}
      <div className="bg-amber-50 border-b border-amber-200 px-6 py-3 flex items-start gap-3">
        <span className="text-amber-600 font-bold text-lg leading-none">!</span>
        <p className="text-sm text-amber-800">
          <strong>Safety Notice:</strong> Dynamic Pricing does NOT publish changes to Etsy.
          Approved recommendations are converted into a Draft Bulk Edit session.
          You must review and apply that session separately before anything changes on Etsy.
        </p>
      </div>

      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700 flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-4 text-red-400 hover:text-red-600">âœ•</button>
        </div>
      )}

      {/* â”€â”€ SETUP STEP â”€â”€ */}
      {step === "setup" && (
        <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

          {/* Listing Selector */}
          <section className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="font-medium text-gray-900">
                Select Listings ({selectedIds.size} selected)
              </h2>
              <div className="flex gap-2">
                <button onClick={handleSelectAll} className="text-xs text-indigo-600 hover:underline">All</button>
                <span className="text-gray-300">|</span>
                <button onClick={handleDeselectAll} className="text-xs text-gray-500 hover:underline">None</button>
              </div>
            </div>
            {loadingListings ? (
              <div className="px-5 py-8 text-center text-gray-400 text-sm">Loading listingsâ€¦</div>
            ) : listings.length === 0 ? (
              <div className="px-5 py-8 text-center text-gray-400 text-sm">No listings found.</div>
            ) : (
              <div className="max-h-72 overflow-y-auto divide-y divide-gray-50">
                {listings.map((l) => (
                  <label key={l.id} className="flex items-center gap-3 px-5 py-2.5 hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(l.id)}
                      onChange={() => toggleSelect(l.id)}
                      className="w-4 h-4 text-indigo-600"
                    />
                    <span className="text-sm text-gray-700 flex-1 truncate">{l.title || l.id}</span>
                    {l.price_amount != null && (
                      <span className="text-sm text-gray-400">{cents(l.price_amount)}</span>
                    )}
                    {(l as unknown as { has_variations?: boolean }).has_variations && (
                      <span className="text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded">
                        variations â€” will skip
                      </span>
                    )}
                  </label>
                ))}
              </div>
            )}
          </section>

          {/* Rule Builder */}
          <section className="bg-white rounded-lg border border-gray-200 p-5 space-y-5">
            <h2 className="font-medium text-gray-900">Pricing Rule</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rule Type</label>
              <select
                value={ruleType}
                onChange={(e) => setRuleType(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              >
                {RULE_TYPES.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>

            {ruleType === "percentage_adjustment" && (
              <div className="flex items-center gap-3">
                <label className="text-sm text-gray-700 w-40">Adjust by %</label>
                <input
                  type="number"
                  value={pctValue}
                  onChange={(e) => setPctValue(e.target.value)}
                  className="w-28 border border-gray-300 rounded px-3 py-2 text-sm"
                  placeholder="e.g. 10 or -5"
                />
                <span className="text-sm text-gray-500">%  (negative = decrease)</span>
              </div>
            )}

            {ruleType === "fixed_amount_adjustment" && (
              <div className="flex items-center gap-3">
                <label className="text-sm text-gray-700 w-40">Adjust by (cents)</label>
                <input
                  type="number"
                  value={fixedValue}
                  onChange={(e) => setFixedValue(e.target.value)}
                  className="w-28 border border-gray-300 rounded px-3 py-2 text-sm"
                  placeholder="e.g. 100 = $1.00"
                />
                <span className="text-sm text-gray-500">(negative = decrease)</span>
              </div>
            )}

            {ruleType === "set_price" && (
              <div className="flex items-center gap-3">
                <label className="text-sm text-gray-700 w-40">New price (cents)</label>
                <input
                  type="number"
                  value={setPriceValue}
                  onChange={(e) => setSetPriceValue(e.target.value)}
                  className="w-28 border border-gray-300 rounded px-3 py-2 text-sm"
                  placeholder="e.g. 1999 = $19.99"
                />
                <span className="text-sm text-gray-500">= {cents(parseInt(setPriceValue, 10) || 0)}</span>
              </div>
            )}

            {ruleType === "reference_price" && (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <label className="text-sm text-gray-700 w-40">Reference price (cents)</label>
                  <input
                    type="number"
                    value={refPrice}
                    onChange={(e) => setRefPrice(e.target.value)}
                    className="w-28 border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                  <span className="text-sm text-gray-500">= {cents(parseInt(refPrice, 10) || 0)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <label className="text-sm text-gray-700 w-40">Mode</label>
                  <select
                    value={refMode}
                    onChange={(e) => setRefMode(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-2 text-sm"
                  >
                    {REFERENCE_MODES.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>
                {refMode.includes("percent") && (
                  <div className="flex items-center gap-3">
                    <label className="text-sm text-gray-700 w-40">Percent</label>
                    <input
                      type="number"
                      value={refPct}
                      onChange={(e) => setRefPct(e.target.value)}
                      className="w-28 border border-gray-300 rounded px-3 py-2 text-sm"
                    />
                    <span className="text-sm text-gray-500">%</span>
                  </div>
                )}
                {refMode.includes("amount") && (
                  <div className="flex items-center gap-3">
                    <label className="text-sm text-gray-700 w-40">Amount (cents)</label>
                    <input
                      type="number"
                      value={refAmount}
                      onChange={(e) => setRefAmount(e.target.value)}
                      className="w-28 border border-gray-300 rounded px-3 py-2 text-sm"
                    />
                  </div>
                )}
              </div>
            )}
          </section>

          {/* Safety Guardrails */}
          <section className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
            <h2 className="font-medium text-gray-900">Safety Guardrails</h2>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={enableMarginFloor}
                onChange={(e) => setEnableMarginFloor(e.target.checked)}
                className="w-4 h-4 text-indigo-600"
              />
              <span className="text-sm text-gray-700">Minimum margin floor</span>
              {enableMarginFloor && (
                <div className="flex items-center gap-2 ml-2">
                  <input
                    type="number"
                    value={minMarginPct}
                    onChange={(e) => setMinMarginPct(e.target.value)}
                    className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
                  />
                  <span className="text-sm text-gray-500">% (requires cost data on listings)</span>
                </div>
              )}
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={enablePriceFloor}
                onChange={(e) => setEnablePriceFloor(e.target.checked)}
                className="w-4 h-4 text-indigo-600"
              />
              <span className="text-sm text-gray-700">Minimum price floor</span>
              {enablePriceFloor && (
                <div className="flex items-center gap-2 ml-2">
                  <input
                    type="number"
                    value={minPriceValue}
                    onChange={(e) => setMinPriceValue(e.target.value)}
                    className="w-24 border border-gray-300 rounded px-2 py-1 text-sm"
                  />
                  <span className="text-sm text-gray-500">cents = {cents(parseInt(minPriceValue, 10) || 0)}</span>
                </div>
              )}
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={enablePriceCap}
                onChange={(e) => setEnablePriceCap(e.target.checked)}
                className="w-4 h-4 text-indigo-600"
              />
              <span className="text-sm text-gray-700">Maximum price cap</span>
              {enablePriceCap && (
                <div className="flex items-center gap-2 ml-2">
                  <input
                    type="number"
                    value={maxPriceValue}
                    onChange={(e) => setMaxPriceValue(e.target.value)}
                    className="w-24 border border-gray-300 rounded px-2 py-1 text-sm"
                  />
                  <span className="text-sm text-gray-500">cents = {cents(parseInt(maxPriceValue, 10) || 0)}</span>
                </div>
              )}
            </label>

            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-700 w-32">Rounding rule</label>
              <select
                value={roundingRule}
                onChange={(e) => setRoundingRule(e.target.value)}
                className="border border-gray-300 rounded px-3 py-2 text-sm"
              >
                {ROUNDING_RULES.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
          </section>

          <div className="flex justify-end">
            <button
              onClick={handleRunPreview}
              disabled={creatingJob || previewLoading || selectedIds.size === 0}
              className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {creatingJob || previewLoading ? "Generating previewâ€¦" : "Generate Price Preview"}
            </button>
          </div>
        </div>
      )}

      {/* â”€â”€ PREVIEW STEP â”€â”€ */}
      {step === "preview" && currentJob && (
        <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">

          {/* Convert success banner */}
          {convertResult && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-800">
                  Draft Bulk Edit session created successfully.
                </p>
                <p className="text-xs text-green-600 mt-0.5">
                  Review and apply it in Bulk Edit before anything changes on Etsy.
                </p>
              </div>
              <Link
                href={`/bulk-edit`}
                className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700"
              >
                Go to Bulk Edit â†’
              </Link>
            </div>
          )}

          {/* Summary cards */}
          {summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Recommended", value: summary.recommended_count, color: "text-green-600" },
                { label: "Accepted", value: summary.accepted_count, color: "text-blue-600" },
                { label: "Skipped", value: summary.skipped_count, color: "text-gray-500" },
                { label: "Invalid", value: summary.invalid_count, color: "text-red-600" },
              ].map((s) => (
                <div key={s.label} className="bg-white rounded-lg border border-gray-200 p-4">
                  <p className="text-sm text-gray-500">{s.label}</p>
                  <p className={`text-2xl font-semibold ${s.color}`}>{s.value}</p>
                </div>
              ))}
            </div>
          )}

          {summary && (
            <div className="bg-white rounded-lg border border-gray-200 p-5">
              <h3 className="font-medium text-gray-900 mb-3">Price Impact Summary</h3>
              <div className="grid grid-cols-3 gap-6 text-sm">
                <div>
                  <p className="text-gray-500">Current total</p>
                  <p className="text-lg font-semibold text-gray-900">{cents(summary.current_total_price)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Recommended total</p>
                  <p className="text-lg font-semibold text-indigo-700">{cents(summary.recommended_total_price)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Difference</p>
                  <p className={`text-lg font-semibold ${summary.total_diff_amount >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {summary.total_diff_amount >= 0 ? "+" : ""}{cents(summary.total_diff_amount)}
                    {summary.total_diff_percent != null && (
                      <span className="text-sm font-normal ml-1">
                        ({parseFloat(summary.total_diff_percent) >= 0 ? "+" : ""}{parseFloat(summary.total_diff_percent).toFixed(1)}%)
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Controls bar */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <select
                value={recStatusFilter}
                onChange={(e) => {
                  setRecStatusFilter(e.target.value);
                  if (currentJob) loadRecs(currentJob.id, 1, e.target.value);
                }}
                className="border border-gray-300 rounded px-3 py-1.5 text-sm"
              >
                <option value="">All statuses</option>
                <option value="recommended">Recommended</option>
                <option value="warning">Warning</option>
                <option value="accepted">Accepted</option>
                <option value="rejected">Rejected</option>
                <option value="skipped">Skipped</option>
                <option value="invalid">Invalid</option>
                <option value="converted">Converted</option>
              </select>
              {recPage && (
                <span className="text-sm text-gray-500">{recPage.total} items</span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleAcceptAll}
                disabled={acceptingAll}
                className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {acceptingAll ? "Acceptingâ€¦" : "Accept All Recommended"}
              </button>
              <button
                onClick={() => { setConvertConfirmText(""); setShowConvertModal(true); }}
                disabled={!summary || summary.accepted_count === 0 || !!convertResult}
                className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Convert to Bulk Edit Draft
              </button>
            </div>
          </div>

          {/* Recommendations table */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {recLoading ? (
              <div className="p-8 text-center text-gray-400 text-sm">Loadingâ€¦</div>
            ) : !recPage || recPage.items.length === 0 ? (
              <div className="p-8 text-center text-gray-400 text-sm">No recommendations.</div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="px-4 py-3 text-left text-gray-600 font-medium">Listing</th>
                    <th className="px-4 py-3 text-right text-gray-600 font-medium">Current</th>
                    <th className="px-4 py-3 text-right text-gray-600 font-medium">Recommended</th>
                    <th className="px-4 py-3 text-right text-gray-600 font-medium">Diff</th>
                    <th className="px-4 py-3 text-center text-gray-600 font-medium">Status</th>
                    <th className="px-4 py-3 text-left text-gray-600 font-medium">Reason</th>
                    <th className="px-4 py-3 text-center text-gray-600 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {recPage.items.map((rec) => (
                    <tr key={rec.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 max-w-xs truncate text-gray-800">
                        {rec.listing_title || rec.listing_id || rec.id}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">{cents(rec.current_price_amount)}</td>
                      <td className="px-4 py-3 text-right font-medium text-gray-900">{cents(rec.recommended_price_amount)}</td>
                      <td className="px-4 py-3 text-right">
                        {rec.diff_amount != null ? (
                          <span className={rec.diff_amount >= 0 ? "text-green-600" : "text-red-600"}>
                            {rec.diff_amount >= 0 ? "+" : ""}{cents(rec.diff_amount)}
                          </span>
                        ) : "â€”"}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[rec.status] ?? "bg-gray-100 text-gray-600"}`}>
                          {rec.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500 max-w-xs truncate text-xs">
                        {rec.reason || ""}
                        {rec.validation_warnings?.length ? (
                          <span className="ml-1 text-yellow-600">{rec.validation_warnings.join("; ")}</span>
                        ) : null}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {(rec.status === "recommended" || rec.status === "warning") && (
                          <div className="flex items-center justify-center gap-1">
                            <button
                              onClick={() => handleAccept(rec.id)}
                              disabled={pendingRec === rec.id}
                              className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 disabled:opacity-50"
                            >
                              Accept
                            </button>
                            <button
                              onClick={() => handleReject(rec.id)}
                              disabled={pendingRec === rec.id}
                              className="px-2 py-1 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100 disabled:opacity-50"
                            >
                              Reject
                            </button>
                          </div>
                        )}
                        {rec.status === "accepted" && (
                          <button
                            onClick={() => handleReject(rec.id)}
                            disabled={pendingRec === rec.id}
                            className="px-2 py-1 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100 disabled:opacity-50"
                          >
                            Undo
                          </button>
                        )}
                        {rec.status === "rejected" && (
                          <button
                            onClick={() => handleAccept(rec.id)}
                            disabled={pendingRec === rec.id}
                            className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 disabled:opacity-50"
                          >
                            Re-accept
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* Pagination */}
            {recPage && recPage.total > recPage.per_page && (
              <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
                <span>Page {recPage.page} of {Math.ceil(recPage.total / recPage.per_page)}</span>
                <div className="flex gap-2">
                  <button
                    onClick={() => currentJob && loadRecs(currentJob.id, recPageNum - 1, recStatusFilter)}
                    disabled={recPageNum <= 1}
                    className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-40"
                  >
                    Prev
                  </button>
                  <button
                    onClick={() => currentJob && loadRecs(currentJob.id, recPageNum + 1, recStatusFilter)}
                    disabled={recPageNum >= Math.ceil(recPage.total / recPage.per_page)}
                    className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* â”€â”€ HISTORY STEP â”€â”€ */}
      {step === "history" && (
        <div className="max-w-5xl mx-auto px-6 py-8">
          <h2 className="font-medium text-gray-900 mb-4">Pricing Job History</h2>
          {jobsLoading ? (
            <p className="text-sm text-gray-400">Loadingâ€¦</p>
          ) : jobs.length === 0 ? (
            <p className="text-sm text-gray-400">No jobs yet.</p>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Rule</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-600">Status</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Listings</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Recommended</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">Skipped</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Converted Session</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {jobs.map((j) => (
                    <tr key={j.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-800">{j.rule_type}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[j.status] ?? "bg-gray-100 text-gray-600"}`}>
                          {j.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">{j.row_count}</td>
                      <td className="px-4 py-3 text-right text-gray-600">{j.recommended_count}</td>
                      <td className="px-4 py-3 text-right text-gray-600">{j.skipped_count}</td>
                      <td className="px-4 py-3 text-gray-600">
                        {j.converted_bulk_edit_session_id ? (
                          <Link href="/bulk-edit" className="text-indigo-600 hover:underline text-xs">
                            View session â†’
                          </Link>
                        ) : "â€”"}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {new Date(j.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* â”€â”€ CONVERT MODAL â”€â”€ */}
      {showConvertModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Convert to Bulk Edit Draft</h3>
            <div className="p-3 bg-amber-50 border border-amber-200 rounded text-sm text-amber-800 space-y-1">
              <p><strong>This will NOT publish any changes to Etsy.</strong></p>
              <p>A draft Bulk Edit session will be created with {summary?.accepted_count} price change(s).
                You must review and apply it in Bulk Edit before anything is published.</p>
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">
                Type <strong>CONVERT PRICES</strong> to confirm:
              </label>
              <input
                type="text"
                value={convertConfirmText}
                onChange={(e) => setConvertConfirmText(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono"
                placeholder="CONVERT PRICES"
                autoFocus
              />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowConvertModal(false)}
                className="px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleConvert}
                disabled={convertConfirmText !== "CONVERT PRICES" || converting}
                className="px-4 py-2 text-sm text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {converting ? "Convertingâ€¦" : "Convert"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

