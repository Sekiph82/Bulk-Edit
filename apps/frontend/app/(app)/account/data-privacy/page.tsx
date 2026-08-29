"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";
import AccountPlaceholder from "@/components/account/AccountPlaceholder";

export default function AccountDataPrivacyPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); }
  }, []);

  return (
    <div className="space-y-5">
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-2">AI data usage</h2>
        <p className="text-sm text-gray-700">
          Your Etsy listing data is not sent to any external AI provider unless this is explicitly enabled for your account.
        </p>
      </div>
      <AccountPlaceholder
        title="Data controls"
        description="Data export, account data deletion, and Etsy shop disconnection are managed today from Connected Shops and Plan & Billing. A consolidated Data & Privacy control center is coming soon."
        items={["Export your data — coming soon", "Delete account data — see Plan & Billing", "Disconnect Etsy shop — see Connected Shops"]}
      />
    </div>
  );
}
