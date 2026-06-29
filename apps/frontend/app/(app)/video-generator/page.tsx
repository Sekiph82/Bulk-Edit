"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

interface RendererStatus {
  renderer_enabled: boolean;
  renderer_available: boolean;
  message: string;
}

interface AspectRatioOption {
  value: string;
  label: string;
  width: number;
  height: number;
  recommended: boolean;
}

interface EtsySpecs {
  max_file_size_mb: number;
  min_duration_seconds: number;
  max_duration_seconds: number;
  min_resolution_px: number;
  supported_aspect_ratios: string[];
  format: string;
}

interface VideoTemplate {
  id: string;
  name: string;
  description: string;
  implemented: boolean;
  max_images: number;
  output_format: string;
}

interface TemplatesData {
  templates: VideoTemplate[];
  aspect_ratios: AspectRatioOption[];
  etsy_specs: EtsySpecs;
  renderer_enabled: boolean;
  renderer_available: boolean;
}

interface RenderStatus {
  id: string;
  status: "pending" | "rendering" | "completed" | "failed";
  template_id: string;
  image_count: number;
  aspect_ratio: string | null;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  file_size_bytes: number | null;
  is_etsy_ready: boolean | null;
  etsy_issues: string[] | null;
  error_message: string | null;
  download_url: string | null;
  created_at: string;
  completed_at: string | null;
}

const FALLBACK_ASPECT_RATIOS: AspectRatioOption[] = [
  { value: "9:16", label: "9:16 Vertical (Recommended)", width: 1080, height: 1920, recommended: true },
  { value: "1:1", label: "1:1 Square", width: 1080, height: 1080, recommended: false },
  { value: "4:5", label: "4:5 Vertical", width: 1080, height: 1350, recommended: false },
  { value: "16:9", label: "16:9 Horizontal", width: 1920, height: 1080, recommended: false },
];

const FALLBACK_TEMPLATES: VideoTemplate[] = [
  {
    id: "clean_zoom",
    name: "Clean Zoom",
    description: "Gentle zoom on each product photo with letterbox padding.",
    implemented: true,
    max_images: 20,
    output_format: "MP4 (H.264)",
  },
  {
    id: "soft_pan",
    name: "Soft Pan",
    description: "Subtle horizontal pan across each photo.",
    implemented: false,
    max_images: 20,
    output_format: "MP4 (H.264)",
  },
  {
    id: "marketplace_promo",
    name: "Marketplace Promo",
    description: "Bold title card intro with product photos.",
    implemented: false,
    max_images: 20,
    output_format: "MP4 (H.264)",
  },
];

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

// ---------------------------------------------------------------------------
// VideoUnavailableModal
// ---------------------------------------------------------------------------

function VideoUnavailableModal({
  open,
  reason,
  isSuperuser,
  onClose,
}: {
  open: boolean;
  reason: "disabled" | "dependency_missing";
  isSuperuser: boolean;
  onClose: () => void;
}) {
  if (!open) return null;

  const title =
    reason === "disabled"
      ? "Video generation is not available yet"
      : "Video generation is temporarily unavailable";

  const body =
    reason === "disabled"
      ? "Video generation is not available in this workspace yet. You can still prepare your listings and come back when video generation is enabled."
      : "Video generation is temporarily unavailable. Please try again later.";

  const adminNote =
    reason === "disabled"
      ? "Admin setup required: enable the video renderer and make sure ffmpeg is available."
      : "Admin setup required: ffmpeg is not available to the backend container.";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="p-5 space-y-3">
          <p className="text-sm text-gray-700">{body}</p>
          {isSuperuser && (
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              {adminNote}
            </p>
          )}
        </div>
        <div className="p-5 pt-0">
          <button
            onClick={onClose}
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// EtsyReadyChecklist
// ---------------------------------------------------------------------------

function EtsyReadyChecklist({
  render,
  specs,
}: {
  render: RenderStatus;
  specs: EtsySpecs | null;
}) {
  if (!specs || render.is_etsy_ready === null) return null;

  const fileSizeMb = render.file_size_bytes ? render.file_size_bytes / 1024 / 1024 : null;
  const fileSizeOk = fileSizeMb !== null && fileSizeMb <= specs.max_file_size_mb;
  const durationOk =
    render.duration_seconds !== null &&
    render.duration_seconds >= specs.min_duration_seconds &&
    render.duration_seconds <= specs.max_duration_seconds;
  const formatOk = true;
  const aspectOk =
    render.aspect_ratio !== null &&
    specs.supported_aspect_ratios.includes(render.aspect_ratio);
  const resOk =
    render.width !== null &&
    render.height !== null &&
    render.width >= specs.min_resolution_px &&
    render.height >= specs.min_resolution_px;

  const checks = [
    { label: "Format: MP4 (H.264)", ok: formatOk },
    {
      label: `Duration: ${render.duration_seconds?.toFixed(1)}s (${specs.min_duration_seconds}–${specs.max_duration_seconds}s required)`,
      ok: durationOk,
    },
    {
      label: `File size: ${fileSizeMb?.toFixed(1) ?? "—"} MB (max ${specs.max_file_size_mb} MB)`,
      ok: fileSizeOk,
    },
    {
      label: `Resolution: ${render.width ?? "—"}×${render.height ?? "—"} (min ${specs.min_resolution_px}px per side)`,
      ok: resOk,
    },
    {
      label: `Aspect ratio: ${render.aspect_ratio ?? "—"} (supported: ${specs.supported_aspect_ratios.join(", ")})`,
      ok: aspectOk,
    },
  ];

  return (
    <div className="mt-3 space-y-1.5">
      <p className="text-xs font-medium text-gray-700">Etsy listing video checklist:</p>
      {checks.map((c) => (
        <div key={c.label} className="flex items-start gap-2">
          <span className={c.ok ? "text-green-600" : "text-red-500"}>{c.ok ? "✓" : "✗"}</span>
          <span className={`text-xs ${c.ok ? "text-gray-600" : "text-red-600"}`}>{c.label}</span>
        </div>
      ))}
      {render.etsy_issues && render.etsy_issues.length > 0 && (
        <div className="mt-2 space-y-1">
          {render.etsy_issues.map((issue) => (
            <p key={issue} className="text-xs text-red-600">
              {issue}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main content
// ---------------------------------------------------------------------------

function VideoGeneratorContent() {
  const router = useRouter();
  const [isSuperuser, setIsSuperuser] = useState(false);
  const [rendererStatus, setRendererStatus] = useState<RendererStatus | null>(null);
  const [templatesData, setTemplatesData] = useState<TemplatesData | null>(null);
  const [loading, setLoading] = useState(true);

  const [selectedTemplate, setSelectedTemplate] = useState("clean_zoom");
  const [selectedAspectRatio, setSelectedAspectRatio] = useState("9:16");
  const [durationSeconds, setDurationSeconds] = useState(10);
  const [imageUrlsText, setImageUrlsText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [renderJob, setRenderJob] = useState<RenderStatus | null>(null);

  const [unavailableModalOpen, setUnavailableModalOpen] = useState(false);
  const [unavailableReason, setUnavailableReason] = useState<"disabled" | "dependency_missing">("disabled");

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    Promise.all([
      authFetch("/api/v1/auth/me").then((r) => r.ok ? r.json() : null),
      authFetch("/api/v1/video-generator/status").then((r) => r.ok ? r.json() : null),
      authFetch("/api/v1/video-generator/templates").then((r) => r.ok ? r.json() : null),
    ])
      .then(([me, status, templates]) => {
        if (me) setIsSuperuser(me.user?.is_superuser === true);
        setRendererStatus(status);
        setTemplatesData(templates);
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

    if (!rendererStatus?.renderer_enabled) {
      setUnavailableReason("disabled");
      setUnavailableModalOpen(true);
      return;
    }
    if (!rendererStatus?.renderer_available) {
      setUnavailableReason("dependency_missing");
      setUnavailableModalOpen(true);
      return;
    }

    setSubmitting(true);
    setRenderJob(null);
    try {
      const r = await authFetch("/api/v1/video-generator/render", {
        method: "POST",
        body: JSON.stringify({
          template_id: selectedTemplate,
          image_urls: urls,
          aspect_ratio: selectedAspectRatio,
          duration_seconds: durationSeconds,
        }),
      });
      if (r.ok) {
        const data = await r.json();
        setRenderJob({
          ...data,
          width: null,
          height: null,
          file_size_bytes: null,
          is_etsy_ready: null,
          etsy_issues: null,
          error_message: null,
          download_url: null,
          completed_at: null,
        });
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
    if (!renderJob?.download_url) return;
    const token = getAccessToken();
    fetch(`${BACKEND_URL}${renderJob.download_url}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
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

  const templates = templatesData?.templates ?? FALLBACK_TEMPLATES;
  const aspectRatios = templatesData?.aspect_ratios ?? FALLBACK_ASPECT_RATIOS;
  const etsySpecs = templatesData?.etsy_specs ?? null;
  const maxImages = templates.find((t) => t.id === selectedTemplate)?.max_images ?? 20;

  return (
    <main className="max-w-3xl mx-auto px-6 py-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Product Video Generator</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Turn listing photos into a short product showcase video.
        </p>
      </div>

      <div className="px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        Videos are <strong>never auto-uploaded</strong> to Etsy. Download, review, then publish manually.
      </div>

      <div className="space-y-5">
        {/* Template selector */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
          <h2 className="text-sm font-semibold text-gray-900">Template</h2>
          <div className="space-y-2">
            {templates.map((t) => (
              <label
                key={t.id}
                className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                  !t.implemented
                    ? "border-gray-100 bg-gray-50 opacity-60 cursor-not-allowed"
                    : selectedTemplate === t.id
                    ? "border-indigo-500 bg-indigo-50 cursor-pointer"
                    : "border-gray-200 hover:border-gray-300 cursor-pointer"
                }`}
              >
                <input
                  type="radio"
                  name="template"
                  value={t.id}
                  checked={selectedTemplate === t.id}
                  disabled={!t.implemented}
                  onChange={() => t.implemented && setSelectedTemplate(t.id)}
                  className="mt-0.5 accent-indigo-600"
                />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">{t.name}</span>
                    {!t.implemented && (
                      <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">Coming soon</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">{t.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Format & duration */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-900">Format</h2>

          <div className="space-y-2">
            <label className="text-xs font-medium text-gray-700">Aspect Ratio</label>
            <div className="grid grid-cols-2 gap-2">
              {aspectRatios.map((ar) => (
                <label
                  key={ar.value}
                  className={`flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer text-sm transition-colors ${
                    selectedAspectRatio === ar.value
                      ? "border-indigo-500 bg-indigo-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <input
                    type="radio"
                    name="aspect_ratio"
                    value={ar.value}
                    checked={selectedAspectRatio === ar.value}
                    onChange={() => setSelectedAspectRatio(ar.value)}
                    className="accent-indigo-600"
                  />
                  <span className="text-xs text-gray-700">{ar.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700" htmlFor="duration-input">
              Duration (seconds)
            </label>
            <input
              id="duration-input"
              type="number"
              min={5}
              max={15}
              step={1}
              value={durationSeconds}
              onChange={(e) => setDurationSeconds(Number(e.target.value))}
              className="w-32 text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <p className="text-xs text-gray-400">Etsy requires 5–15 seconds.</p>
          </div>
        </div>

        {/* Render form */}
        <form onSubmit={handleRender} className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-900">Image URLs</h2>
          <p className="text-xs text-gray-500">
            Paste one image URL per line (e.g. from your listing images). Maximum {maxImages} images.
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
              <div className="space-y-3">
                <EtsyReadyChecklist render={renderJob} specs={etsySpecs} />

                <div className="px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
                  Review the video before uploading. Do not upload to Etsy without checking it first.
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleDownload}
                    className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                  >
                    Download MP4
                  </button>
                  <span className="text-xs text-gray-400">
                    Then upload manually via Etsy listing editor.
                  </span>
                </div>
              </div>
            )}

            {renderJob.status === "failed" && renderJob.error_message && (
              <p className="text-sm text-red-600">{renderJob.error_message}</p>
            )}
          </div>
        )}
      </div>

      <VideoUnavailableModal
        open={unavailableModalOpen}
        reason={unavailableReason}
        isSuperuser={isSuperuser}
        onClose={() => setUnavailableModalOpen(false)}
      />
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
