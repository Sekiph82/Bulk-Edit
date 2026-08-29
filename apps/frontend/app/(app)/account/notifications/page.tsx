"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";
import AccountPlaceholder from "@/components/account/AccountPlaceholder";

export default function AccountNotificationsPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); }
  }, []);

  return (
    <div className="space-y-5">
      <AccountPlaceholder
        title="Notification preferences"
        description="In-app and email notification preferences are coming soon. Planned notifications:"
        items={[
          "Bulk edit completed",
          "Bulk edit failed",
          "Magic Revert completed",
          "Usage at 80% of plan limit",
          "Usage at 100% of plan limit",
          "Etsy connection issue",
        ]}
      />
    </div>
  );
}
