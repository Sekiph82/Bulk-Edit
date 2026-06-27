"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

interface RendererStatus {
  renderer_state: "disabled" | "dependency_missing" | "working";
  message: string;
}

interface VideoTemplate {
  id: string;
  name: string;
  description: string;
  max_images: number;
  duration_seconds_per_image: number;
  output_format: string;
}

interface RenderStatus {
  id: string;
  status: "pending" | "rendering" | "completed" | "failed";
  template_id: string;
  image_count: number;
  duration_seconds: number | null;
  file_size_bytes: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

function authFetch(path: string, options?: RequestInit) {
  const token = getAccessToken();
  return fetch(`${BACKEND_URL}${path}`, {
    ...options,
    headers: {
      ...(options?.headers ?? {}),
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
}

function VideoGeneratorContent() {
  const router = useRouter();
  const [rendererStatus, setRendererStatus] = useState<RendererStatus | null>(null);
  const [templates, setTemplates] = useState<VideoTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedTemplate, setSelectedTemplate] = useState("slideshow");
  const [imageUrlsText, setImageUrlsText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [renderJob, setRenderJob] = useState<RenderStatus | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    authFetch("/api/v1/video-generator/status")
      .then((r) => r.ok ? r.json() : null)
      .then(async (d: RendererStatus | null) => {
        setRendererStatus(d);
        if (d?.renderer_state === "working") {
          const tr = await authFetch("/api/v1/video-generator/templates");
          if (tr.ok) setTemplates(await tr.json());
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (renderJob && (renderJob.status === "pending" || renderJob.status === "rendering")) {
      pollRef.current = setInterval(async () => {
        try {
          const r = await authFetch(`/api/v1/video-generator/renders/${renderJob.id}`);
          if (r.ok) {
            const data: RenderStatus = await r.json();
            setRenderJob(data);
            if (data.status === "completed" || data.status === "failed") {
              if (pollRef.current) clearInterval(pollRef.current);
            }
          }
        } catch { /* ignore */ }
      }, 2000);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [renderJob?.id, renderJob?.status]);

  async function handleRender(e: React.FormEvent) {
    e.preventDefault();
    const urls = imageUrlsText.split("\n").map((u) => u.trim()).filter(Boolean);
    if (!urls.length) return;
    setSubmitting(true);
    setRenderJob(null);
    try {
      const r = await authFetch("/api/v1/video-generator/render", {
        method: "POST",
        body: JSON.stringify({ template_id: selectedTemplate, image_urls: urls }),
      });
      if (r.ok) {
        const data = await r.json();
        setRenderJob({ ...data, duration_seconds: null, file_size_bytes: null, error_message: null, completed_at: null });
      } else {
        const err = await r.json().catch(() => ({}));
        alert(err.detail ?? "Failed to start render.");
      }
    } catch {
      alert("Network error — could not start render.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleDownload() {
    if (!renderJob) return;
    const token = getAccessToken();
    const a = document.createElement("a");
    a.href = `${BACKEND_URL}/api/v1/video-generator/renders/${renderJob.id}/download`;
    // Append auth token as query param so the browser can follow the download
    // (FileResponse streams the file directly, auth is checked server-side via Bearer header)
    // Since we can't set headers on an <a> tag, open in a new fetch
    fetch(`${BACKEND_URL}/api/v1/video-generator/renders/${renderJob.id}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        a.href = url;
        a.download = `product_video_${renderJob.id.slice(0, 8)}.mp4`;
        a.click();
        URL.revokeObjectURL(url);
      })
      .catch(() => alert("Download failed."));
  }

  if (loading) {
    return (
      <main className="max-w-3xl mx-auto px-6 py-6">
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Product Video Generator</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Turn listing photos into a short product showcase video. Review and download before using.
        </p>
      </div>

      <div className="px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        Generated videos are <strong>never auto-uploaded</strong> to Etsy. Download first, then publish manually when ready.
      </div>

      {rendererStatus?.renderer_state === "disabled" && (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <div className="text-4xl mb-4">🎬</div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Renderer disabled</h2>
          <p className="text-sm text-gray-500 mb-4 max-w-md mx-auto">{rendererStatus.message}</p>
          <code className="inline-block px-4 py-2 bg-gray-100 text-gray-600 text-xs rounded-lg">
            VIDEO_RENDERER_ENABLED=true
          </code>
        </div>
      )}

      {rendererStatus?.renderer_state === "dependency_missing" && (
        <div className="bg-white border border-amber-200 rounded-xl p-8 text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">ffmpeg not found</h2>
          <p className="text-sm text-gray-500 mb-4 max-w-md mx-auto">{rendererStatus.message}</p>
          <code className="inline-block px-4 py-2 bg-gray-100 text-gray-600 text-xs rounded-lg">
            apt-get install ffmpeg
          </code>
        </div>
      )}

      {rendererStatus?.renderer_state === "working" && (
        <div className="space-y-5">
          {/* Template selector */}
          {templates.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
              <h2 className="text-sm font-semibold text-gray-900">Template</h2>
              <div className="space-y-2">
                {templates.map((t) => (
                  <label
                    key={t.id}
                    className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedTemplate === t.id
                        ? "border-indigo-500 bg-indigo-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <input
                      type="radio"
                      name="template"
                      value={t.id}
                      checked={selectedTemplate === t.id}
                      onChange={() => setSelectedTemplate(t.id)}
                      className="mt-0.5 accent-indigo-600"
                    />
                    <div>
                      <div className="text-sm font-medium text-gray-900">{t.name}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{t.description}</div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {t.output_format} · up to {t.max_images} images · {t.duration_seconds_per_image}s/image
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Render form */}
          <form onSubmit={handleRender} className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-900">Image URLs</h2>
            <p className="text-xs text-gray-500">
              Paste one image URL per line (e.g. from your listing images). Maximum{" "}
              {templates[0]?.max_images ?? 20} images.
            </p>
            <textarea
              value={imageUrlsText}
              onChange={(e) => setImageUrlsText(e.target.value)}
              placeholder={"https://i.etsystatic.com/...\nhttps://i.etsystatic.com/..."}
              rows={5}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 font-mono resize-y focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={submitting || !imageUrlsText.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {submitting ? "Starting…" : "Generate Video"}
            </button>
          </form>

          {/* Render progress */}
          {renderJob && (
            <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
              <h2 className="text-sm font-semibold text-gray-900">Render Status</h2>

              <div className="flex items-center gap-2">
                {(renderJob.status === "pending" || renderJob.status === "rendering") && (
                  <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                )}
                <span
                  className={`text-sm font-medium ${
                    renderJob.status === "completed"
                      ? "text-green-700"
                      : renderJob.status === "failed"
                      ? "text-red-600"
                      : "text-indigo-600"
                  }`}
                >
                  {renderJob.status === "pending" && "Queued…"}
                  {renderJob.status === "rendering" && "Rendering…"}
                  {renderJob.status === "completed" && "Ready to download"}
                  {renderJob.status === "failed" && "Render failed"}
                </span>
              </div>

              {renderJob.status === "completed" && (
                <div className="space-y-2">
                  <div className="text-xs text-gray-500">
                    {renderJob.duration_seconds?.toFixed(1)}s ·{" "}
                    {renderJob.file_size_bytes
                      ? (renderJob.file_size_bytes / 1024 / 1024).toFixed(1) + " MB"
                      : ""}
                  </div>
                  <div className="px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
                    Review the video before using it. Do not upload to Etsy without checking it first.
                  </div>
                  <button
                    onClick={handleDownload}
                    className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                  >
                    Download MP4
                  </button>
                </div>
              )}

              {renderJob.status === "failed" && renderJob.error_message && (
                <p className="text-sm text-red-600">{renderJob.error_message}</p>
              )}
            </div>
          )}
        </div>
      )}
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
