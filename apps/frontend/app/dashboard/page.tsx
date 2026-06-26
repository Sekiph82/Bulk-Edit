"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

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
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (data) setEmail(data.user.email); })
      .catch(() => {});
  }, []);

  const handleLogout = () => {
    const rt = localStorage.getItem("refresh_token");
    if (rt) {
      fetch(`${BACKEND_URL}/api/v1/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: rt }),
      }).catch(() => {});
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <Link href="/" className="text-xl font-extrabold text-gray-900 hover:text-indigo-600 transition-colors">
          Bulk-Edit
        </Link>
        <div className="flex items-center gap-4">
          {email ? (
            <>
              <span className="text-sm text-gray-600">{email}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-red-600 hover:underline font-medium"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-sm text-indigo-600 hover:underline font-medium">
                Sign in
              </Link>
              <Link
                href="/register"
                className="text-sm bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-4 py-1.5 rounded-lg transition-colors"
              >
                Register
              </Link>
            </>
          )}
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-8 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">
            {email ? `Welcome, ${email}` : "Sign in to access your listings"}
          </p>
        </div>

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
    </div>
  );
}
