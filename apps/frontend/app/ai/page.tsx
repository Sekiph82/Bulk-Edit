"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getAccessToken,
  getListings,
  createAISession,
  runAISession,
  listAISessions,
  acceptSuggestion,
  rejectSuggestion,
  convertAISession,
  getAIUsage,
  ApiError,
  type ListingListItem,
  type AISession,
  type AISuggestion,
  type AIUsage,
} from "../../lib/api";

const TOOL_OPTIONS = [
  { value: "title", label: "Optimize Title", description: "SEO-optimized title suggestions" },
  { value: "description", label: "Optimize Description", description: "Compelling, keyword-rich descriptions" },
  { value: "tags", label: "Optimize Tags", description: "Up to 13 high-traffic Etsy tags" },
  { value: "alt_text", label: "Generate Alt Text", description: "Accessible image descriptions" },
  { value: "seo_score", label: "SEO Score", description: "Score your listing SEO quality" },
];

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-gray-100 text-gray-600",
    running: "bg-yellow-100 text-yellow-700",
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
    accepted: "bg-indigo-100 text-indigo-700",
    rejected: "bg-gray-100 text-gray-500",
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colors[status] ?? "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}

function UsageBar({ used, limit }: { used: number; limit: number }) {
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const barColor = pct >= 90 ? "bg-red-500" : pct >= 70 ? "bg-yellow-500" : "bg-indigo-500";
  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div className={`${barColor} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
    </div>
  );
}

function SuggestionCard({
  s,
  onAccept,
  onReject,
}: {
  s: AISuggestion;
  onAccept: (id: string) => void;
  onReject: (id: string) => void;
}) {
  const isPending = s.status === "pending";
  const value = s.suggested_value;

  let display: string;
  if (s.field === "tags" && Array.isArray(value)) {
    display = (value as string[]).join(", ");
  } else if (s.field === "seo_score" && typeof value === "object" && value !== null) {
    const v = value as Record<string, unknown>;
    display = `Score: ${v.score}/100 | Title: ${v.title_score} | Desc: ${v.description_score} | Tags: ${v.tags_score}`;
  } else {
    display = String(value);
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{s.field.replace("_", " ")}</span>
        <StatusBadge status={s.status} />
      </div>
      <p className="text-sm text-gray-800 whitespace-pre-wrap break-words">{display}</p>
      {s.reasoning && (
        <p className="text-xs text-gray-400 italic">{s.reasoning}</p>
      )}
      {s.field === "seo_score" && typeof value === "object" && value !== null && (
        <div className="space-y-1 pt-1">
          {((value as Record<string, unknown>).issues as string[] | undefined)?.map((issue, i) => (
            <p key={i} className="text-xs text-red-600">
              <span className="font-medium">Issue:</span> {issue}
            </p>
          ))}
          {((value as Record<string, unknown>).suggestions as string[] | undefined)?.map((sug, i) => (
            <p key={i} className="text-xs text-indigo-600">
              <span className="font-medium">Tip:</span> {sug}
            </p>
          ))}
        </div>
      )}
      {isPending && s.field !== "seo_score" && (
        <div className="flex gap-2 pt-1">
          <button
            onClick={() => onAccept(s.id)}
            className="text-xs px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-medium focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            Accept
          </button>
          <button
            onClick={() => onReject(s.id)}
            className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded font-medium focus:outline-none focus:ring-2 focus:ring-gray-300"
          >
            Reject
          </button>
        </div>
      )}
    </div>
  );
}

export default function AIToolsPage() {
  const router = useRouter();
  const [listings, setListings] = useState<ListingListItem[]>([]);
  const [selectedListingId, setSelectedListingId] = useState<string>("");
  const [selectedTool, setSelectedTool] = useState<string>("title");
  const [usage, setUsage] = useState<AIUsage | null>(null);
  const [activeSession, setActiveSession] = useState<AISession | null>(null);
  const [sessions, setSessions] = useState<AISession[]>([]);
  const [running, setRunning] = useState(false);
  const [converting, setConverting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [convertMsg, setConvertMsg] = useState<string | null>(null);

  const checkAuth = useCallback(() => {
    const token = getAccessToken();
    if (!token) router.push("/login");
  }, [router]);

  const loadData = useCallback(async () => {
    try {
      const [lPage, usageData, sessionsData] = await Promise.all([
        getListings({ per_page: 100 }),
        getAIUsage(),
        listAISessions({ page: 1, page_size: 10 }),
      ]);
      setListings(lPage.items);
      setUsage(usageData);
      setSessions(sessionsData.items);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) router.push("/login");
    }
  }, [router]);

  useEffect(() => {
    checkAuth();
    loadData();
  }, [checkAuth, loadData]);

  async function handleRun() {
    if (!selectedListingId) { setError("Select a listing first."); return; }
    setError(null);
    setConvertMsg(null);
    setRunning(true);
    try {
      const session = await createAISession(selectedListingId, selectedTool);
      const ran = await runAISession(session.id);
      setActiveSession(ran);
      const usageData = await getAIUsage();
      setUsage(usageData);
      const sessionsData = await listAISessions({ page: 1, page_size: 10 });
      setSessions(sessionsData.items);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    } finally {
      setRunning(false);
    }
  }

  async function handleAccept(suggestionId: string) {
    if (!activeSession) return;
    try {
      await acceptSuggestion(suggestionId);
      const updated = await runAISession(activeSession.id).catch(() => null);
      if (updated) { setActiveSession(updated); return; }
      setActiveSession({
        ...activeSession,
        suggestions: activeSession.suggestions.map((s) =>
          s.id === suggestionId ? { ...s, status: "accepted", accepted_at: new Date().toISOString() } : s
        ),
      });
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    }
  }

  async function handleReject(suggestionId: string) {
    if (!activeSession) return;
    try {
      await rejectSuggestion(suggestionId);
      setActiveSession({
        ...activeSession,
        suggestions: activeSession.suggestions.map((s) =>
          s.id === suggestionId ? { ...s, status: "rejected", rejected_at: new Date().toISOString() } : s
        ),
      });
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    }
  }

  async function handleAcceptLocal(suggestionId: string) {
    try {
      await acceptSuggestion(suggestionId);
      if (activeSession) {
        setActiveSession({
          ...activeSession,
          suggestions: activeSession.suggestions.map((s) =>
            s.id === suggestionId ? { ...s, status: "accepted", accepted_at: new Date().toISOString() } : s
          ),
        });
      }
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    }
  }

  async function handleRejectLocal(suggestionId: string) {
    try {
      await rejectSuggestion(suggestionId);
      if (activeSession) {
        setActiveSession({
          ...activeSession,
          suggestions: activeSession.suggestions.map((s) =>
            s.id === suggestionId ? { ...s, status: "rejected", rejected_at: new Date().toISOString() } : s
          ),
        });
      }
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    }
  }

  async function handleConvert() {
    if (!activeSession) return;
    setConverting(true);
    setConvertMsg(null);
    setError(null);
    try {
      const result = await convertAISession(activeSession.id);
      setConvertMsg(result.message + ` Session ID: ${result.bulk_edit_session_id}`);
    } catch (e) {
      if (e instanceof ApiError) setError(e.message);
    } finally {
      setConverting(false);
    }
  }

  const hasAccepted = activeSession?.suggestions.some((s) => s.status === "accepted" && s.field !== "seo_score");

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <Link href="/dashboard" className="text-xl font-extrabold text-gray-900 hover:text-indigo-600 transition-colors">
          Bulk-Edit
        </Link>
        <Link href="/dashboard" className="text-sm text-indigo-600 hover:underline font-medium">
          Dashboard
        </Link>
      </nav>

      <main className="max-w-5xl mx-auto px-6 py-10 space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Listing Optimizer</h1>
          <p className="text-sm text-gray-500 mt-1">
            Generate AI-powered suggestions for titles, descriptions, tags, and more. Review and accept before applying.
          </p>
        </div>

        {/* Usage card */}
        {usage && (
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-semibold text-gray-700">AI Credits — {usage.period_key}</h2>
              <span className="text-sm text-gray-500">
                {usage.ai_credits_used} / {usage.ai_credits_limit}
              </span>
            </div>
            <UsageBar used={usage.ai_credits_used} limit={usage.ai_credits_limit} />
            {usage.ai_credits_limit === 0 && (
              <p className="text-xs text-red-600 mt-2">
                AI tools require a paid plan.{" "}
                <Link href="/pricing" className="underline font-medium">Upgrade</Link>
              </p>
            )}
          </div>
        )}

        {/* Tool selector */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-4">
          <h2 className="text-sm font-semibold text-gray-700">Generate Suggestions</h2>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Listing</label>
            <select
              value={selectedListingId}
              onChange={(e) => setSelectedListingId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              <option value="">Select a listing...</option>
              {listings.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.title ?? l.etsy_listing_id}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">AI Tool</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {TOOL_OPTIONS.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setSelectedTool(t.value)}
                  className={`text-left p-3 rounded-lg border text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300 ${
                    selectedTool === t.value
                      ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                      : "border-gray-200 bg-white text-gray-700 hover:border-indigo-300"
                  }`}
                >
                  <span className="font-medium block">{t.label}</span>
                  <span className="text-xs text-gray-500">{t.description}</span>
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            onClick={handleRun}
            disabled={running || !selectedListingId}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            {running ? "Generating..." : "Generate Suggestions"}
          </button>
        </div>

        {/* Suggestions panel */}
        {activeSession && (
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-700">
                Suggestions
                <span className="ml-2 text-xs text-gray-400">
                  ({activeSession.tool} — {activeSession.ai_provider ?? "mock"})
                </span>
              </h2>
              <StatusBadge status={activeSession.status} />
            </div>

            {activeSession.status === "failed" && (
              <p className="text-sm text-red-600">{activeSession.error_message}</p>
            )}

            {activeSession.suggestions.length === 0 && activeSession.status === "completed" && (
              <p className="text-sm text-gray-500">No suggestions generated.</p>
            )}

            <div className="space-y-3">
              {activeSession.suggestions.map((s) => (
                <SuggestionCard
                  key={s.id}
                  s={s}
                  onAccept={handleAcceptLocal}
                  onReject={handleRejectLocal}
                />
              ))}
            </div>

            {hasAccepted && (
              <div className="pt-2 border-t border-gray-100 space-y-2">
                <p className="text-xs text-gray-500">
                  Accepted suggestions will be converted into a Bulk Edit session for review before applying.
                </p>
                <button
                  onClick={handleConvert}
                  disabled={converting}
                  className="px-5 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-300"
                >
                  {converting ? "Converting..." : "Convert to Bulk Edit"}
                </button>
                {convertMsg && (
                  <p className="text-xs text-green-700">{convertMsg}</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Session history */}
        {sessions.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-3">
            <h2 className="text-sm font-semibold text-gray-700">Recent Sessions</h2>
            <div className="space-y-2">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between border border-gray-100 rounded-lg px-4 py-2.5 cursor-pointer hover:border-indigo-200 transition-colors"
                  onClick={() => setActiveSession(s)}
                >
                  <div>
                    <span className="text-sm font-medium text-gray-700">{s.tool}</span>
                    <span className="ml-2 text-xs text-gray-400">
                      {s.suggestion_count} suggestion{s.suggestion_count !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">{new Date(s.created_at).toLocaleDateString()}</span>
                    <StatusBadge status={s.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
