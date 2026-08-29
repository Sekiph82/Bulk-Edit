"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";
import AccountPlaceholder from "@/components/account/AccountPlaceholder";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

export default function AccountSecurityPage() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    fetch(`${BACKEND_URL}/api/v1/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setEmail(d?.user?.email ?? null))
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-5">
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-1">Account identity</h2>
        <p className="text-sm text-gray-700">{email ?? "—"}</p>
      </div>
      <AccountPlaceholder
        title="Password & sessions"
        description="Password change, active session management, and two-factor authentication are coming soon."
        items={["Change password — coming soon", "Active sessions — coming soon", "Two-factor authentication (2FA) — coming soon"]}
      />
    </div>
  );
}
