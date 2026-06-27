"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

interface GeneratorStatus {
  renderer_enabled: boolean;
  message: string;
}

function VideoGeneratorContent() {
  const router = useRouter();
  const [status, setStatus] = useState<GeneratorStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    const token = getAccessToken();
    fetch(`${BACKEND_URL}/api/v1/video-generator/status`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : null)
      .then((d) => setStatus(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-3xl mx-auto px-6 py-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Product Video Generator</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Turn listing photos into a short product showcase video. Review the result before saving.
        </p>
      </div>

      <div className="px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        Generated videos are <strong>never auto-uploaded</strong> to Etsy. You review and download first, then manually publish when ready.
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : status && !status.renderer_enabled ? (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <div className="text-4xl mb-4">🎬</div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Renderer not configured</h2>
          <p className="text-sm text-gray-500 mb-4 max-w-md mx-auto">
            {status.message}
          </p>
          <div className="inline-block px-4 py-2 bg-gray-100 text-gray-500 text-xs rounded-lg font-mono">
            VIDEO_RENDERER_ENABLED=true
          </div>
        </div>
      ) : status?.renderer_enabled ? (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-3">Generate a Product Video</h2>
          <p className="text-sm text-gray-500 mb-4">
            Select a listing with photos to generate a 10-second MP4 product showcase.
            The video will be available for download and review before you decide to use it.
          </p>
          <button className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
            Select Listing
          </button>
        </div>
      ) : null}
    </main>
  );
}

export default function VideoGeneratorPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">Loading…</div>}>
      <VideoGeneratorContent />
    </Suspense>
  );
}
