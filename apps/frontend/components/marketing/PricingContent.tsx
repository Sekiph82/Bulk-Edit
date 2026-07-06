"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import { PLAN_PRICE_DISPLAY as PLAN_DISPLAY, PLAN_ORDER } from "@/lib/pricingPlans";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

type PlanLimits = {
  max_shops: number;
  max_listings: number;
  bulk_edits_per_month: number;
  ai_credits_per_month: number;
  media_assets: number;
  can_bulk_edit_photos: boolean;
  can_bulk_edit_variations: boolean;
  can_use_magic_revert: boolean;
  can_use_dynamic_pricing: boolean;
  can_schedule_jobs: boolean;
};

function FeatureRow({ label, value }: { label: string; value: boolean | number | string }) {
  if (typeof value === "boolean") {
    return (
      <li className="flex items-center gap-2 text-sm text-gray-600">
        {value ? (
          <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-4 h-4 text-gray-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )}
        {label}
      </li>
    );
  }
  return (
    <li className="flex items-center gap-2 text-sm text-gray-600">
      <span className="text-indigo-500 font-medium">{value}</span>
      {label}
    </li>
  );
}

export default function PricingContent() {
  const router = useRouter();
  const [plans, setPlans] = useState<Record<string, PlanLimits>>({});
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/v1/billing/plans`)
      .then((r) => r.json())
      .then((data) => setPlans(data.plans || {}))
      .catch(() => setError("Failed to load plans."))
      .finally(() => setLoading(false));
  }, []);

  const handleUpgrade = async (plan: string) => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }
    setCheckoutLoading(plan);
    setError("");
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/billing/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ plan }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Checkout failed. Please try again.");
        return;
      }
      window.location.href = data.checkout_url;
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setCheckoutLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <MarketingNav />
        <div className="flex items-center justify-center py-40">
          <p className="text-gray-500 text-sm">Loading plans…</p>
        </div>
        <MarketingFooter />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />
      <main className="py-16 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900">Simple, transparent pricing</h1>
          <p className="text-gray-500 mt-2">Start free. Upgrade when you need more.</p>
        </div>

        {error && (
          <div className="mb-6 max-w-lg mx-auto rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm text-center">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
          {PLAN_ORDER.filter((p) => plans[p]).map((planKey) => {
            const limits = plans[planKey];
            const display = PLAN_DISPLAY[planKey] || { label: planKey, price: "—" };
            const isFree = planKey === "free";

            return (
              <div
                key={planKey}
                className={`bg-white rounded-2xl border p-6 flex flex-col gap-4 shadow-sm relative ${
                  planKey === "pro_monthly" ? "border-indigo-400 ring-2 ring-indigo-200" : "border-gray-200"
                }`}
              >
                {display.badge && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                    {display.badge}
                  </span>
                )}
                <div>
                  <h2 className="font-bold text-gray-900 text-lg">{display.label}</h2>
                  <p className="text-indigo-600 font-semibold mt-1">{display.price}</p>
                </div>

                <ul className="space-y-1.5 flex-1">
                  <FeatureRow label="shops" value={limits.max_shops} />
                  <FeatureRow label="listings" value={limits.max_listings.toLocaleString()} />
                  <FeatureRow label="bulk edits/month" value={limits.bulk_edits_per_month.toLocaleString()} />
                  <FeatureRow label="AI credits/month" value={limits.ai_credits_per_month.toLocaleString()} />
                  <FeatureRow label="media assets" value={limits.media_assets.toLocaleString()} />
                  <FeatureRow label="Photo bulk edit" value={limits.can_bulk_edit_photos} />
                  <FeatureRow label="Variation edit" value={limits.can_bulk_edit_variations} />
                  <FeatureRow label="Magic Revert" value={limits.can_use_magic_revert} />
                  <FeatureRow label="Dynamic Pricing" value={limits.can_use_dynamic_pricing} />
                  <FeatureRow label="Scheduled Jobs" value={limits.can_schedule_jobs} />
                  <FeatureRow label="Listing Health Score" value={true} />
                  <FeatureRow label="Profit Calculator" value={true} />
                  <FeatureRow
                    label="AI listing suggestions"
                    value={planKey !== "free"}
                  />
                  <FeatureRow
                    label="Multiple cost profiles"
                    value={planKey === "pro_monthly" || planKey === "pro_yearly"}
                  />
                </ul>

                {isFree ? (
                  <Link
                    href="/register"
                    className="w-full text-center rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2.5 text-sm transition-colors"
                  >
                    Start Free
                  </Link>
                ) : (
                  <button
                    onClick={() => handleUpgrade(planKey)}
                    disabled={checkoutLoading === planKey}
                    className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium py-2.5 text-sm transition-colors"
                  >
                    {checkoutLoading === planKey ? "Redirecting…" : "Upgrade"}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <p className="text-center text-xs text-gray-400 mt-10">
          All paid plans include a 7-day money-back guarantee. Cancel anytime.
        </p>
      </div>
      </main>

      <MarketingFooter />
    </div>
  );
}
