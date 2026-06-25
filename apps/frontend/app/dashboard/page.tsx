"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

const placeholderFeatures = [
  { title: "Connect Etsy Shop", description: "OAuth connection — Sprint 4", icon: "🔗" },
  { title: "Sync Listings", description: "Full & incremental sync — Sprint 5", icon: "🔄" },
  { title: "Bulk Edit", description: "Titles, tags, prices & more — Sprint 7", icon: "✏️" },
  { title: "AI Tools", description: "Title optimizer, tag generator — Sprint 13", icon: "🤖" },
  { title: "Magic Revert", description: "Undo bulk changes — Sprint 9", icon: "↩️" },
  { title: "Media Library", description: "Photo & video management — Sprint 10", icon: "🖼️" },
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

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-10">
          {placeholderFeatures.map((feature) => (
            <div
              key={feature.title}
              className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 flex flex-col gap-2"
            >
              <span className="text-2xl">{feature.icon}</span>
              <h3 className="font-semibold text-gray-800">{feature.title}</h3>
              <p className="text-sm text-gray-400">{feature.description}</p>
            </div>
          ))}
        </div>

        <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-6">
          <p className="text-sm font-semibold text-indigo-800 mb-2">Auth Endpoints (Sprint 2)</p>
          <div className="space-y-1">
            {[
              "/api/v1/auth/register",
              "/api/v1/auth/login",
              "/api/v1/auth/refresh",
              "/api/v1/auth/logout",
              "/api/v1/auth/me",
            ].map((path) => (
              <code key={path} className="block text-xs text-indigo-600">
                {BACKEND_URL}{path}
              </code>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
