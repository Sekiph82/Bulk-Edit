"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

const NAV = [
  { href: "/owner", label: "Dashboard" },
  { href: "/owner/users", label: "Users" },
  { href: "/owner/organizations", label: "Organizations" },
  { href: "/owner/shops", label: "Shops" },
  { href: "/owner/jobs", label: "Jobs" },
  { href: "/owner/contact-submissions", label: "Contact Submissions" },
  { href: "/owner/emails", label: "Emails" },
  { href: "/owner/audit-logs", label: "Audit Logs" },
  { href: "/owner/system-health", label: "System Health" },
  { href: "/owner/feature-flags", label: "Feature Flags" },
  { href: "/owner/content", label: "Content" },
];

type GateState = "checking" | "denied" | "allowed";

// Owner console gate. This app stores auth tokens in localStorage, so
// middleware (edge, no localStorage access) cannot enforce this — the check
// has to happen here, client-side, before any child page is mounted. Child
// pages never render (and never fire their data-fetch effects) until this
// resolves to "allowed".
export default function OwnerShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [gate, setGate] = useState<GateState>("checking");
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setGate("denied");
      return;
    }
    fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.user?.is_superuser === true) {
          setEmail(d.user.email);
          setGate("allowed");
        } else {
          setGate("denied");
        }
      })
      .catch(() => setGate("denied"));
  }, []);

  if (gate === "checking") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-sm text-gray-400">Checking access…</p>
      </div>
    );
  }

  if (gate === "denied") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50" data-testid="owner-access-denied">
        <div className="bg-white border border-gray-200 rounded-2xl p-10 text-center max-w-md shadow-sm">
          <p className="text-xl font-bold text-gray-900 mb-2">404</p>
          <p className="text-gray-500 text-sm mb-6">This page doesn&apos;t exist.</p>
          <Link href="/login" className="inline-block bg-indigo-600 text-white text-sm font-medium px-5 py-2 rounded-lg hover:bg-indigo-700 transition-colors">
            Sign in
          </Link>
        </div>
      </div>
    );
  }

  async function handleLogout() {
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
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <aside className="w-60 flex flex-col bg-white border-r border-gray-200 flex-shrink-0">
        <div className="h-14 flex items-center px-4 border-b border-gray-200">
          <span className="text-sm font-semibold text-gray-800">Bulk‑Edit Owner</span>
        </div>
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block px-2.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-3 border-t border-gray-200">
          {email && <p className="text-xs text-gray-400 truncate px-2 mb-2">{email}</p>}
          <button
            type="button"
            onClick={handleLogout}
            className="w-full text-left px-2.5 py-2 rounded-lg text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>
      <div className="flex-1 overflow-y-auto">{children}</div>
    </div>
  );
}
