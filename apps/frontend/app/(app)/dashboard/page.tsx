"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import OnboardingChecklist from "@/components/onboarding/OnboardingChecklist";
import { getListingHealthSummary, getProfitSummary, type ListingHealthSummary, type ProfitSummary } from "@/lib/api";

interface ActionItem {
  id: string;
  type: string;
  label: string;
  href: string;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

const activeFeatures = [
  { title: "Etsy Shops", description: "Connect and manage your Etsy shops", href: "/shops" },
  { title: "Listings", description: "Browse, filter, and sync your listings", href: "/listings" },
  { title: "Bulk Edit", description: "Edit titles, tags, prices, and more across listings", href: "/bulk-edit" },
  { title: "Media Editor", description: "Add, replace, and delete listing photos", href: "/media" },
  { title: "Variation Editor", description: "Bulk edit prices, quantities, and SKUs for variation listings", href: "/variations" },
  { title: "AI Optimizer", description: "AI-powered title, description, tag, and alt text suggestions", href: "/ai" },
  { title: "CSV Import / Export", description: "Export listings to CSV, import changes as a draft bulk edit session", href: "/csv" },
  { title: "Dynamic Pricing", description: "Generate rules-based price recommendations and convert to a bulk edit draft", href: "/pricing-rules" },
  { title: "Listing Health", description: "Score every listing 0–100 for title, tags, description, and photos — prioritise your fixes", href: "/listing-health" },
  { title: "Profit Calculator", description: "Track product costs, Etsy fees, and margins — find which listings are actually profitable", href: "/profit" },
  { title: "Scheduled Jobs", description: "Schedule safe syncs, draft creation, and pricing previews — nothing publishes without your approval", href: "/scheduled" },
  { title: "Pricing", description: "View plans and feature limits", href: "/pricing" },
  { title: "Billing", description: "Manage your subscription", href: "/billing" },
];

export default function DashboardPage() {
  const [email, setEmail] = useState<string | null>(null);
  const [shopCount, setShopCount] = useState<number | null>(null);
  const [listingCount, setListingCount] = useState<number | null>(null);
  const [healthSummary, setHealthSummary] = useState<ListingHealthSummary | null>(null);
  const [profitSummary, setProfitSummary] = useState<ProfitSummary | null>(null);
  const [actionQueue, setActionQueue] = useState<ActionItem[]>([]);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (data) setEmail(data.user.email); })
      .catch(() => {});

    fetch(`${BACKEND_URL}/api/v1/etsy/shops`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { setShopCount(data?.shops?.length ?? 0); })
      .catch(() => { setShopCount(0); });

    fetch(`${BACKEND_URL}/api/v1/listings?limit=1`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { setListingCount(data?.total ?? data?.listings?.length ?? 0); })
      .catch(() => { setListingCount(0); });

    fetch(`${BACKEND_URL}/api/v1/action-queue`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (data?.items) setActionQueue(data.items); })
      .catch(() => {});

    getListingHealthSummary().then(setHealthSummary).catch(() => {});
    getProfitSummary().then(setProfitSummary).catch(() => {});
  }, []);

  const showChecklist = shopCount !== null && listingCount !== null;

  return (
    <main className="max-w-7xl mx-auto px-8 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">
          {email ? `Welcome, ${email}` : "Manage your Etsy listings"}
        </p>
      </div>

      {showChecklist && (
        <OnboardingChecklist shopCount={shopCount!} listingCount={listingCount!} />
      )}

      {/* Health + Profit widgets */}
      {(healthSummary || profitSummary) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          {healthSummary && (
            <Link href="/listing-health" className="bg-white border border-gray-200 rounded-xl p-5 hover:border-indigo-300 transition-colors">
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">Listing Health</p>
              <div className="flex items-end gap-3 mb-3">
                <span className="text-3xl font-bold text-gray-900">{healthSummary.average_score.toFixed(0)}</span>
                <span className="text-sm text-gray-500 mb-1">/100 avg score</span>
              </div>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div><p className="font-semibold text-green-600">{healthSummary.excellent_count}</p><p className="text-gray-400">Excellent</p></div>
                <div><p className="font-semibold text-yellow-600">{healthSummary.good_count}</p><p className="text-gray-400">Good</p></div>
                <div><p className="font-semibold text-orange-600">{healthSummary.needs_work_count}</p><p className="text-gray-400">Needs Work</p></div>
                <div><p className="font-semibold text-red-600">{healthSummary.critical_count}</p><p className="text-gray-400">Critical</p></div>
              </div>
            </Link>
          )}
          {profitSummary && (
            <Link href="/profit" className="bg-white border border-gray-200 rounded-xl p-5 hover:border-indigo-300 transition-colors">
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">Profit Overview</p>
              <div className="flex items-end gap-3 mb-3">
                <span className="text-3xl font-bold text-gray-900">
                  {profitSummary.average_margin != null ? `${parseFloat(profitSummary.average_margin).toFixed(1)}%` : "—"}
                </span>
                <span className="text-sm text-gray-500 mb-1">avg margin</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div><p className="font-semibold text-gray-700">{profitSummary.listings_with_costs}</p><p className="text-gray-400">With Costs</p></div>
                <div><p className={`font-semibold ${profitSummary.low_margin_count > 0 ? "text-yellow-600" : "text-gray-700"}`}>{profitSummary.low_margin_count}</p><p className="text-gray-400">Low Margin</p></div>
                <div><p className={`font-semibold ${profitSummary.loss_making_count > 0 ? "text-red-600" : "text-gray-700"}`}>{profitSummary.loss_making_count}</p><p className="text-gray-400">Loss</p></div>
              </div>
            </Link>
          )}
        </div>
      )}

      {/* Action Queue widget */}
      {actionQueue.length > 0 && (
        <div className="mb-6 bg-white border border-amber-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">⏳</span>
            <h2 className="text-base font-semibold text-gray-900">Action Queue</h2>
            <span className="ml-auto text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium">
              {actionQueue.length} awaiting approval
            </span>
          </div>
          <ul className="divide-y divide-gray-100">
            {actionQueue.map((item) => (
              <li key={item.id} className="py-2.5 flex items-center gap-3">
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-medium capitalize">
                  {item.type.replace(/_/g, " ")}
                </span>
                <span className="text-sm text-gray-700 flex-1 truncate">{item.label}</span>
                <Link href={item.href} className="text-xs text-indigo-600 font-medium hover:underline flex-shrink-0">
                  Review →
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {activeFeatures.map((feature) => (
          <Link
            key={feature.title}
            href={feature.href}
            className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-1.5 hover:border-indigo-300 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            <h3 className="font-semibold text-gray-800 text-sm">{feature.title}</h3>
            <p className="text-xs text-gray-500">{feature.description}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
