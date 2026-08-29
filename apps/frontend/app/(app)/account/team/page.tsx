"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";
import AccountPlaceholder from "@/components/account/AccountPlaceholder";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8100";

export default function AccountTeamPage() {
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
        <h2 className="text-sm font-semibold text-gray-900 mb-3">Account Owner</h2>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-xs font-bold text-white">
            {email ? email[0].toUpperCase() : "?"}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">{email ?? "—"}</p>
            <p className="text-xs text-gray-400">Owner</p>
          </div>
        </div>
      </div>
      <AccountPlaceholder
        title="Team roles"
        description="Team roles are coming soon. When available, you'll be able to invite teammates with a scoped role."
        items={["Owner", "Manager", "Editor", "Viewer"]}
      />
    </div>
  );
}
