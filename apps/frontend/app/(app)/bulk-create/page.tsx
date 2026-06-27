"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

interface BulkCreateStatus {
  status: string;
  message: string;
}

function BulkCreateContent() {
  const router = useRouter();
  const [status, setStatus] = useState<BulkCreateStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    const token = getAccessToken();
    fetch(`${BACKEND_URL}/api/v1/bulk-create/status`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : null)
      .then((d) => setStatus(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-4xl mx-auto px-6 py-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Bulk Create Listings</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Upload photos and create multiple Etsy listings in one workflow. Review drafts before publishing.
        </p>
      </div>

      <div className="px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        Drafts are <strong>never auto-published</strong>. You review each listing before it goes live on Etsy.
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : status?.status === "not_configured" ? (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <div className="text-4xl mb-4">✨</div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Connect your Etsy shop first</h2>
          <p className="text-sm text-gray-500 mb-6 max-w-md mx-auto">
            {status.message}
          </p>
          <a href="/shops" className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-5 py-2 rounded-lg">
            Go to Shops →
          </a>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-5">
          <h2 className="text-base font-semibold text-gray-900">Upload Photos</h2>
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center">
            <div className="text-3xl mb-2">🖼️</div>
            <p className="text-sm text-gray-500">
              Drag and drop photos here, or{" "}
              <label className="text-indigo-600 font-medium cursor-pointer hover:underline">
                browse files
                <input type="file" multiple accept="image/*" className="hidden" />
              </label>
            </p>
            <p className="text-xs text-gray-400 mt-1">Each photo becomes a separate listing draft</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500 font-medium">Base Title</label>
              <input type="text" placeholder="e.g. Handmade ceramic mug"
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500 font-medium">Price (USD)</label>
              <input type="number" placeholder="0.00" min="0" step="0.01"
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
          </div>
          <p className="text-xs text-gray-400">Drafts will be created for review. No listings are published without your explicit confirmation.</p>
          <button className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-5 py-2 rounded-lg">
            Create Drafts
          </button>
        </div>
      )}
    </main>
  );
}

export default function BulkCreatePage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">Loading…</div>}>
      <BulkCreateContent />
    </Suspense>
  );
}
