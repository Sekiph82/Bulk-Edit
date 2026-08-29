"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getAccessToken, ApiError } from "@/lib/api";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

type Subscription = {
  effective_plan: string;
  billing_charge_status: "charged" | "no_charge";
  limits: Record<string, number | boolean>;
};

type Usage = {
  period_key: string;
  usage: Record<string, number>;
  limits: Record<string, number | boolean>;
};

type Shop = { id: string; shop_name: string | null; is_connected: boolean };

const CAPABILITIES: Array<{ key: string; label: string }> = [
  { key: "can_use_magic_revert", label: "Magic Revert" },
  { key: "can_bulk_edit_variations", label: "Bulk edit variations" },
  { key: "can_bulk_edit_photos", label: "Bulk edit photos/media" },
  { key: "can_use_dynamic_pricing", label: "Dynamic Pricing" },
  { key: "can_schedule_jobs", label: "Scheduled jobs" },
];

function planDisplayName(plan: string): string {
  return plan.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function Card({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
        {action}
      </div>
      {children}
    </div>
  );
}

function UsageBar({ label, used, limit }: { label: string; used: number; limit: number }) {
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-600 mb-1">
        <span>{label}</span>
        <span>{used.toLocaleString()} / {limit.toLocaleString()}</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${pct >= 100 ? "bg-red-500" : pct >= 80 ? "bg-amber-500" : "bg-indigo-500"}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function AccountOverviewPage() {
  const router = useRouter();
  const [sub, setSub] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [shops, setShops] = useState<Shop[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    Promise.all([
      fetch(`${BACKEND_URL}/api/v1/billing/subscription`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => (r.ok ? r.json() : null)),
      fetch(`${BACKEND_URL}/api/v1/billing/usage`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => (r.ok ? r.json() : null)),
      fetch(`${BACKEND_URL}/api/v1/etsy/shops`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => (r.ok ? r.json() : { shops: [] })),
    ])
      .then(([subData, usageData, shopsData]) => {
        setSub(subData);
        setUsage(usageData);
        setShops(shopsData?.shops ?? []);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load account overview."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex justify-center py-16"><div className="w-6 h-6 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" /></div>;
  }

  if (error) {
    return <p className="text-red-600 text-sm">{error}</p>;
  }

  const connectedCount = shops.filter((s) => s.is_connected).length;

  return (
    <div className="space-y-5">
      <Card title="Plan" action={<Link href="/account/billing" className="text-xs font-medium text-indigo-600 hover:underline">Manage →</Link>}>
        <p className="text-xl font-bold text-gray-900">{sub ? planDisplayName(sub.effective_plan) : "—"}</p>
        <p className="text-xs text-gray-500">
          {sub?.billing_charge_status === "charged" ? "Stripe subscription active." : "Not billed through Stripe."}
        </p>
      </Card>

      {usage && (
        <Card title="Usage this period" action={<Link href="/account/usage" className="text-xs font-medium text-indigo-600 hover:underline">View all →</Link>}>
          <p className="text-xs text-gray-400">{usage.period_key}</p>
          <UsageBar label="Bulk edits" used={usage.usage.bulk_edits_used ?? 0} limit={Number(usage.limits.bulk_edits_per_month ?? 0)} />
          <UsageBar label="AI credits" used={usage.usage.ai_credits_used ?? 0} limit={Number(usage.limits.ai_credits_per_month ?? 0)} />
        </Card>
      )}

      <Card title="Connected Shops" action={<Link href="/account/connected-shops" className="text-xs font-medium text-indigo-600 hover:underline">Manage →</Link>}>
        <p className="text-sm text-gray-700">{connectedCount} connected shop{connectedCount === 1 ? "" : "s"}</p>
        {shops.slice(0, 3).map((s) => (
          <p key={s.id} className="text-xs text-gray-500">{s.shop_name ?? "Unnamed Shop"} — {s.is_connected ? "Connected" : "Disconnected"}</p>
        ))}
      </Card>

      <Card title="Key capabilities">
        <div className="grid grid-cols-2 gap-2">
          {CAPABILITIES.map((c) => {
            const enabled = Boolean(sub?.limits[c.key]);
            return (
              <div key={c.key} className="flex items-center gap-1.5 text-xs">
                <span className={enabled ? "text-green-600" : "text-gray-300"}>{enabled ? "✓" : "—"}</span>
                <span className={enabled ? "text-gray-700" : "text-gray-400"}>{c.label}</span>
              </div>
            );
          })}
        </div>
      </Card>

      <Card title="Recent Activity" action={<Link href="/account/activity" className="text-xs font-medium text-indigo-600 hover:underline">View all →</Link>}>
        <p className="text-sm text-gray-400">Activity & Audit will show Bulk Edit jobs, Magic Revert events, account changes, and future automation history.</p>
      </Card>
    </div>
  );
}
