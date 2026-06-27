"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import OnboardingChecklist from "@/components/onboarding/OnboardingChecklist";

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
  { title: "Scheduled Jobs", description: "Schedule safe syncs, draft creation, and pricing previews — nothing publishes without your approval", href: "/scheduled" },
  { title: "Admin Panel", description: "Platform-level user and subscription management (superusers only)", href: "/admin" },
  { title: "Pricing", description: "View plans and feature limits", href: "/pricing" },
  { title: "Billing", description: "Manage your subscription", href: "/billing" },
];

export default function DashboardPage() {
  const [email, setEmail] = useState<string | null>(null);
  const [shopCount, setShopCount] = useState<number | null>(null);
  const [listingCount, setListingCount] = useState<number | null>(null);

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
