"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";
import AccountPlaceholder from "@/components/account/AccountPlaceholder";

export default function AccountActivityPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); }
  }, []);

  return (
    <div className="space-y-5">
      <AccountPlaceholder
        title="Activity & Audit"
        description="Activity & Audit will show Bulk Edit jobs, Magic Revert events, account changes, and future automation history."
      />
    </div>
  );
}
