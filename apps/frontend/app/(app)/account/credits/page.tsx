"use client";

import { useEffect, useState } from "react";
import { getAccessToken, ApiError } from "@/lib/api";
import { useRouter } from "next/navigation";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

type Usage = { usage: Record<string, number>; limits: Record<string, number | boolean> };

const CONSUMERS = [
  "AI suggestions",
  "Title generation",
  "Description generation",
  "Tag generation",
  "Future video/promote generation",
];

export default function AccountCreditsPage() {
  const router = useRouter();
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    fetch(`${BACKEND_URL}/api/v1/billing/usage`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : Promise.reject(new ApiError(r.status, "Failed to load credits."))))
      .then(setUsage)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load credits."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-16"><div className="w-6 h-6 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" /></div>;
  if (error) return <p className="text-red-600 text-sm">{error}</p>;

  const used = usage?.usage.ai_credits_used ?? 0;
  const limit = Number(usage?.limits.ai_credits_per_month ?? 0);
  const remaining = Math.max(0, limit - used);

  return (
    <div className="space-y-5">
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">AI Credits</h2>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-gray-900">{remaining.toLocaleString()}</span>
          <span className="text-sm text-gray-500">remaining of {limit.toLocaleString()} this month</span>
        </div>
        <p className="text-xs text-gray-400 mt-1">Used {used.toLocaleString()} this period.</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">What consumes AI credits</h2>
        <ul className="space-y-1.5 text-sm text-gray-700">
          {CONSUMERS.map((c) => (
            <li key={c} className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              {c}
            </li>
          ))}
        </ul>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-2">Credit history</h2>
        <p className="text-sm text-gray-400">Credit history will appear here once per-use transaction logging ships.</p>
      </div>
    </div>
  );
}
