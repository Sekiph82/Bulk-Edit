"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";

export default function MagicRevertPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); }
  }, []);

  return (
    <main className="max-w-2xl mx-auto px-6 py-16 text-center space-y-5">
      <div className="text-4xl">↩️</div>
      <h1 className="text-2xl font-bold text-gray-900">Magic Revert</h1>
      <p className="text-sm text-gray-600 max-w-md mx-auto">
        Magic Revert currently appears as a button on the Bulk Edit page immediately after a successful apply,
        so you can undo that specific run. Reverting from your past job history — not just the run you just did —
        is planned under Activity &amp; Audit and isn&apos;t built yet.
      </p>
      <div className="flex items-center justify-center gap-4 pt-2">
        <Link
          href="/bulk-edit"
          className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg"
        >
          Go to Bulk Edit
        </Link>
        <Link
          href="/account/activity"
          className="text-sm font-medium text-indigo-600 hover:underline"
        >
          View Activity &amp; Audit →
        </Link>
      </div>
    </main>
  );
}
