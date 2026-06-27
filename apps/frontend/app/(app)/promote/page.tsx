"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

interface ConfigStatus {
  pinterest_configured: boolean;
  instagram_configured: boolean;
}

function NotConfiguredCard({ platform, icon, description }: { platform: string; icon: string; description: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-3">
        <span className="text-2xl">{icon}</span>
        <h2 className="text-base font-semibold text-gray-900">{platform}</h2>
        <span className="ml-auto text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Not configured</span>
      </div>
      <p className="text-sm text-gray-500 mb-4">{description}</p>
      <div className="px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-500">
        To enable {platform} sharing, add your {platform} app credentials to your environment configuration.
        Social posts are never auto-published — you will always review and confirm before sharing.
      </div>
    </div>
  );
}

function PromoteContent() {
  const router = useRouter();
  const [config, setConfig] = useState<ConfigStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    const token = getAccessToken();
    fetch(`${BACKEND_URL}/api/v1/promote/config-status`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : null)
      .then((d) => setConfig(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-3xl mx-auto px-6 py-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Promote</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Share your listings to Pinterest and Instagram. Always review before posting.
        </p>
      </div>

      <div className="px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        Social posts are <strong>never auto-published</strong>. You will copy a caption, download an image, or explicitly confirm before anything is shared.
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="space-y-4">
          {!config?.pinterest_configured && (
            <NotConfiguredCard
              platform="Pinterest"
              icon="📌"
              description="Pin your listing photos directly to Pinterest boards with an auto-generated caption."
            />
          )}
          {config?.pinterest_configured && (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">📌</span>
                <h2 className="text-base font-semibold text-gray-900">Pinterest</h2>
                <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Configured</span>
              </div>
              <p className="text-sm text-gray-500">Pinterest integration is ready. Select a listing to generate a pin caption and image.</p>
            </div>
          )}

          {!config?.instagram_configured && (
            <NotConfiguredCard
              platform="Instagram"
              icon="📸"
              description="Generate an Instagram caption from your listing and download the image for posting."
            />
          )}
          {config?.instagram_configured && (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">📸</span>
                <h2 className="text-base font-semibold text-gray-900">Instagram</h2>
                <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Configured</span>
              </div>
              <p className="text-sm text-gray-500">Instagram integration is ready. Select a listing to generate a caption and download the image.</p>
            </div>
          )}
        </div>
      )}
    </main>
  );
}

export default function PromotePage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">Loading…</div>}>
      <PromoteContent />
    </Suspense>
  );
}
