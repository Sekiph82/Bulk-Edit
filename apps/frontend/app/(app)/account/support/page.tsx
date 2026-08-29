"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";

const SUPPORT_EMAIL = "support@bulkeditapp.com";

export default function AccountSupportPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); }
  }, []);

  return (
    <div className="space-y-5">
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-2">Contact support</h2>
        <p className="text-sm text-gray-700">
          Email <a href={`mailto:${SUPPORT_EMAIL}`} className="text-indigo-600 hover:underline">{SUPPORT_EMAIL}</a> for help with your account, billing, or a bug report.
        </p>
      </div>
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-2">System status</h2>
        <p className="text-sm text-gray-400">A live status page is coming soon.</p>
      </div>
    </div>
  );
}
