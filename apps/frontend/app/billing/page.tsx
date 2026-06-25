"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

type Subscription = {
  plan: string;
  status: string;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  limits: Record<string, number | boolean>;
};

const STATUS_LABEL: Record<string, string> = {
  free: "Free Plan",
  active: "Active",
  trialing: "Trialing",
  past_due: "Past Due",
  canceled: "Canceled",
  incomplete: "Incomplete",
  unpaid: "Unpaid",
};

const STATUS_COLOR: Record<string, string> = {
  free: "bg-gray-100 text-gray-600",
  active: "bg-green-100 text-green-700",
  trialing: "bg-blue-100 text-blue-700",
  past_due: "bg-yellow-100 text-yellow-700",
  canceled: "bg-red-100 text-red-700",
  incomplete: "bg-orange-100 text-orange-700",
  unpaid: "bg-red-100 text-red-700",
};

export default function BillingPage() {
  const searchParams = useSearchParams();
  const success = searchParams.get("success") === "true";
  const canceled = searchParams.get("canceled") === "true";

  const [sub, setSub] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [portalLoading, setPortalLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    fetch(`${BACKEND_URL}/api/v1/billing/subscription`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setSub(data))
      .catch(() => setError("Failed to load subscription."))
      .finally(() => setLoading(false));
  }, []);

  const openPortal = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    setPortalLoading(true);
    setError("");
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/billing/portal`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Could not open billing portal.");
        return;
      }
      window.location.href = data.portal_url;
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setPortalLoading(false);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500 text-sm">Loading billing…</p>
      </main>
    );
  }

  const hasPaidCustomer = sub?.stripe_customer_id != null;
  const statusKey = sub?.status ?? "free";

  return (
    <main className="min-h-screen bg-gray-50 py-16 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <Link href="/" className="text-xl font-extrabold text-indigo-600">Bulk-Edit</Link>
            <h1 className="text-2xl font-bold text-gray-900 mt-1">Billing</h1>
          </div>
          <Link href="/dashboard" className="text-sm text-indigo-600 hover:underline">← Dashboard</Link>
        </div>

        {success && (
          <div className="mb-6 rounded-lg bg-green-50 border border-green-200 text-green-700 px-4 py-3 text-sm">
            Payment successful! Your plan has been upgraded.
          </div>
        )}
        {canceled && (
          <div className="mb-6 rounded-lg bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 text-sm">
            Checkout canceled. Your plan was not changed.
          </div>
        )}
        {error && (
          <div className="mb-6 rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {!sub ? (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 text-center">
            <p className="text-gray-500 text-sm">Please <Link href="/login" className="text-indigo-600 hover:underline">sign in</Link> to view your billing.</p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm divide-y divide-gray-100">
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Current plan</p>
                  <p className="text-xl font-bold text-gray-900 capitalize mt-0.5">
                    {sub.plan.replace(/_/g, " ")}
                  </p>
                </div>
                <span className={`inline-flex items-center text-xs font-semibold px-3 py-1 rounded-full ${STATUS_COLOR[statusKey] || STATUS_COLOR.free}`}>
                  {STATUS_LABEL[statusKey] || statusKey}
                </span>
              </div>

              {sub.current_period_end && (
                <p className="text-xs text-gray-400 mt-3">
                  {sub.cancel_at_period_end ? "Cancels" : "Renews"} on{" "}
                  {new Date(sub.current_period_end).toLocaleDateString()}
                </p>
              )}
            </div>

            <div className="p-6">
              <p className="text-sm font-semibold text-gray-700 mb-3">Plan limits</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
                {Object.entries(sub.limits).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between text-xs">
                    <dt className="text-gray-500">{key.replace(/_/g, " ")}</dt>
                    <dd className="font-medium text-gray-700">
                      {typeof val === "boolean" ? (val ? "Yes" : "No") : val.toLocaleString()}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="p-6 flex flex-col sm:flex-row gap-3">
              {hasPaidCustomer ? (
                <button
                  onClick={openPortal}
                  disabled={portalLoading}
                  className="flex-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium py-2.5 text-sm transition-colors text-center"
                >
                  {portalLoading ? "Opening portal…" : "Manage Subscription"}
                </button>
              ) : (
                <div className="flex-1 rounded-lg bg-gray-50 border border-gray-200 text-gray-500 text-sm text-center py-2.5">
                  You are on the Free plan.
                </div>
              )}
              <Link
                href="/pricing"
                className="flex-1 rounded-lg border border-indigo-300 text-indigo-600 hover:bg-indigo-50 font-medium py-2.5 text-sm transition-colors text-center"
              >
                View Plans
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
