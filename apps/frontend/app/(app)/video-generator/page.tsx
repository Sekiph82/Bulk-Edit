"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, getListingImages, ApiError, type ListingImage } from "@/lib/api";
import ListingPicker from "@/components/listings/ListingPicker";

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
  source?: string; // "generated" (Product Video Generator) | "uploaded" (own MP4 file)
  branding?: Record<string, unknown> | null;
  branding_text_rendered?: boolean | null;
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
// RenderDetails — generated-video result fields
// ---------------------------------------------------------------------------

function RenderDetails({ render }: { render: RenderStatus }) {
  const rows: [string, string][] = [
    ["Render ID", render.id.slice(0, 8)],
    ["Created", new Date(render.created_at).toLocaleString()],
    ["Status", render.status],
    ["Template", render.template_id],
    ["Source", render.source === "uploaded" ? "Uploaded file" : "Generated (listing photos)"],
    ["Aspect ratio", render.aspect_ratio ?? "—"],
    ["Duration", render.duration_seconds != null ? `${render.duration_seconds.toFixed(1)}s` : "—"],
    ["Photos", render.image_count > 0 ? String(render.image_count) : "—"],
  ];
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
      {rows.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-2 border-b border-gray-50 py-1">
          <dt className="text-gray-400">{k}</dt>
          <dd className="text-gray-700 font-medium text-right truncate" title={v}>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

// ---------------------------------------------------------------------------
// UploadToEtsyGateModal — Upload to Etsy is not enabled yet (Option A gate)
// ---------------------------------------------------------------------------

function UploadToEtsyGateModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-900">Upload to Etsy</h3>
        </div>
        <div className="p-5 space-y-3 text-sm text-gray-700">
          <p className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
            Upload to Etsy remains disabled until owner-approved live upload testing. It is not enabled yet — no video is sent to Etsy from here.
          </p>
          <p>You can <strong>preview the video in this app</strong> before downloading. For now, use <strong>Download to your computer</strong>, then upload the video through the Etsy listing editor.</p>
          <div className="text-xs text-gray-500 space-y-1">
            <p className="font-medium text-gray-600">When enabled, uploading will:</p>
            <ul className="list-disc list-inside space-y-0.5">
              <li>Let you pick the target listing.</li>
              <li>Add the video, or replace an existing one (Etsy allows one video per listing).</li>
              <li>Back up the current video before any replace.</li>
              <li>Require explicit confirmation — it is a live Etsy write, never automatic.</li>
            </ul>
          </div>
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
// ConfirmGenerateModal — lightweight "generate local MP4?" confirm (C2)
// ---------------------------------------------------------------------------

function ConfirmGenerateModal({
  open,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onCancel}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-900">Generate local MP4?</h3>
        </div>
        <div className="p-5 space-y-2 text-sm text-gray-700">
          <p>This will create a local video file from the selected images.</p>
          <p className="text-xs px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-blue-800">
            It will <strong>not</strong> upload to Etsy. You can review and download it after generation.
          </p>
        </div>
        <div className="p-5 pt-0 flex gap-2">
          <button
            onClick={onConfirm}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            Generate
          </button>
          <button
            onClick={onCancel}
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Branding overlay foundation (preview-only this release)
// ---------------------------------------------------------------------------

type LogoPosition = "top-left" | "top-right" | "bottom-left" | "bottom-right";
type TextPlacement = "bottom" | "center" | "intro-card" | "outro-card";

interface Branding {
  logoUrl: string;
  headline: string;
  slogan: string;
  outro: string;
  cta: string;
  logoPosition: LogoPosition;
  textPlacement: TextPlacement;
  brandColor: string;
}

const DEFAULT_BRANDING: Branding = {
  logoUrl: "",
  headline: "",
  slogan: "",
  outro: "",
  cta: "",
  logoPosition: "bottom-right",
  textPlacement: "bottom",
  brandColor: "#4f46e5",
};

const BRANDING_LIMITS = { headline: 60, slogan: 80, outro: 80, cta: 30 } as const;

// ---------------------------------------------------------------------------
// VideoPreview — in-app player. Fetches the auth-protected file as a blob and
// plays it locally; never contacts Etsy. Object URL is revoked on unmount.
// ---------------------------------------------------------------------------

function VideoPreview({
  downloadUrl,
  onReviewed,
}: {
  downloadUrl: string;
  onReviewed?: () => void;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let obj: string | null = null;
    let cancelled = false;
    setUrl(null);
    setErr(false);
    const token = getAccessToken();
    fetch(`${BACKEND_URL}${downloadUrl}`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => {
        if (!r.ok) throw new Error("preview failed");
        return r.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        // Force video/mp4 so the <video> element decodes it. The download
        // endpoint returns the file with Content-Disposition: attachment, and
        // some proxies hand the fetched blob back with a generic/empty MIME
        // type — which downloads fine but leaves <video> unable to play it.
        // Re-wrapping with the known type (these are always MP4 H.264) fixes
        // in-browser playback while download keeps working unchanged.
        const playable = blob.type === "video/mp4" ? blob : new Blob([blob], { type: "video/mp4" });
        obj = URL.createObjectURL(playable);
        setUrl(obj);
      })
      .catch(() => {
        if (!cancelled) setErr(true);
      });
    return () => {
      cancelled = true;
      if (obj) URL.revokeObjectURL(obj);
    };
  }, [downloadUrl]);

  if (err) {
    return (
      <p className="text-xs text-gray-500 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
        Preview could not load. Download the video to review it.
      </p>
    );
  }
  if (!url) {
    return <p className="text-xs text-gray-400">Loading preview…</p>;
  }
  return (
    // eslint-disable-next-line jsx-a11y/media-has-caption
    <video
      src={url}
      controls
      preload="metadata"
      onPlay={onReviewed}
      onError={() => setErr(true)}
      aria-label="Generated product video preview"
      className="w-full max-h-[480px] rounded-lg bg-black"
    />
  );
}

// ---------------------------------------------------------------------------
// PreviewModal — plays a Recent Videos render in a modal (no second render)
// ---------------------------------------------------------------------------

function PreviewModal({ render, onClose }: { render: RenderStatus | null; onClose: () => void }) {
  if (!render || !render.download_url) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900">Video preview</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-sm" aria-label="Close preview">✕</button>
        </div>
        <div className="p-4 space-y-2">
          <VideoPreview downloadUrl={render.download_url} />
          <p className="text-xs text-gray-400">Preview only — this video is not uploaded to Etsy.</p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// BrandingSection — branding overlay foundation (preview-only, M13.05B)
// ---------------------------------------------------------------------------

function BrandingSection({
  branding,
  setBranding,
}: {
  branding: Branding;
  setBranding: React.Dispatch<React.SetStateAction<Branding>>;
}) {
  const set = <K extends keyof Branding>(k: K, v: Branding[K]) =>
    setBranding((b) => ({ ...b, [k]: v }));

  const hasAny =
    branding.logoUrl || branding.headline || branding.slogan || branding.outro || branding.cta;

  const field = (
    key: "headline" | "slogan" | "outro" | "cta",
    label: string,
    placeholder: string,
  ) => (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-700" htmlFor={`branding-${key}`}>
        {label} <span className="text-gray-400">(optional)</span>
      </label>
      <input
        id={`branding-${key}`}
        type="text"
        maxLength={BRANDING_LIMITS[key]}
        value={branding[key]}
        onChange={(e) => set(key, e.target.value)}
        placeholder={placeholder}
        className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
      <p className="text-[11px] text-gray-400 text-right">{branding[key].length}/{BRANDING_LIMITS[key]}</p>
    </div>
  );

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-gray-900">Branding options</h2>
        <p className="text-xs px-3 py-2 mt-1 bg-blue-50 border border-blue-200 rounded-lg text-blue-800">
          <strong>Text branding</strong> (headline, slogan, CTA, outro) <strong>will be rendered into this MP4</strong>. <strong>Logo is preview-only</strong> — logo rendering is still pending. Branding is never uploaded to Etsy.
        </p>
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-gray-700" htmlFor="branding-logo">
          Shop logo URL <span className="text-gray-400">(optional)</span>
        </label>
        <input
          id="branding-logo"
          type="url"
          value={branding.logoUrl}
          onChange={(e) => set("logoUrl", e.target.value)}
          placeholder="https://…/logo.png"
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        {branding.logoUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={branding.logoUrl} alt="Logo preview" className="mt-1 h-12 w-auto rounded border border-gray-200 object-contain bg-gray-50" />
        ) : null}
      </div>

      {field("headline", "Headline text", "e.g. Handmade Ceramic Mug")}
      {field("slogan", "Slogan", "e.g. Crafted to last a lifetime")}
      {field("outro", "Outro text", "e.g. Thanks for visiting our shop")}
      {field("cta", "Call to action", "e.g. Shop now")}

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-700" htmlFor="branding-logopos">Logo position</label>
          <select
            id="branding-logopos"
            value={branding.logoPosition}
            onChange={(e) => set("logoPosition", e.target.value as LogoPosition)}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="top-left">Top left</option>
            <option value="top-right">Top right</option>
            <option value="bottom-left">Bottom left</option>
            <option value="bottom-right">Bottom right</option>
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-700" htmlFor="branding-textplace">Text placement</label>
          <select
            id="branding-textplace"
            value={branding.textPlacement}
            onChange={(e) => set("textPlacement", e.target.value as TextPlacement)}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="bottom">Lower third (bottom)</option>
            <option value="center">Center</option>
            <option value="intro-card">Intro card</option>
            <option value="outro-card">Outro card</option>
          </select>
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-gray-700" htmlFor="branding-color">Brand color</label>
        <input
          id="branding-color"
          type="color"
          value={branding.brandColor}
          onChange={(e) => set("brandColor", e.target.value)}
          className="h-9 w-16 border border-gray-200 rounded cursor-pointer"
        />
      </div>

      {hasAny && (
        <div className="rounded-lg border border-gray-200 p-3 text-xs space-y-0.5">
          <p className="font-medium text-gray-700">Branding summary:</p>
          {branding.logoUrl && <p className="text-gray-600">Logo: {branding.logoPosition} <span className="text-amber-600">(preview-only, not rendered)</span></p>}
          {branding.headline && <p className="text-gray-600">Headline: “{branding.headline}”</p>}
          {branding.slogan && <p className="text-gray-600">Slogan: “{branding.slogan}”</p>}
          {branding.cta && <p className="text-gray-600">CTA: “{branding.cta}”</p>}
          {branding.outro && <p className="text-gray-600">Outro: “{branding.outro}”</p>}
          <p className="text-gray-600">Text placement: {branding.textPlacement}</p>
          <p className="text-gray-500">Text fields are rendered into the MP4. Logo rendering is pending.</p>
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
  const [imageSource, setImageSource] = useState<"manual" | "listing">("manual");
  const [pickedListingId, setPickedListingId] = useState<Set<string>>(new Set());
  const [loadingListingImages, setLoadingListingImages] = useState(false);
  const [listingImagesError, setListingImagesError] = useState<string | null>(null);
  const [pickedImages, setPickedImages] = useState<ListingImage[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [renderJob, setRenderJob] = useState<RenderStatus | null>(null);
  const [history, setHistory] = useState<RenderStatus[]>([]);

  const [unavailableModalOpen, setUnavailableModalOpen] = useState(false);
  const [unavailableReason, setUnavailableReason] = useState<"disabled" | "dependency_missing">("disabled");
  const [uploadGateOpen, setUploadGateOpen] = useState(false);
  const [confirmGenerateOpen, setConfirmGenerateOpen] = useState(false);

  // Result checklist interaction (UI-only, resets per render)
  const [reviewed, setReviewed] = useState(false);
  const [downloaded, setDownloaded] = useState(false);
  // Recent Videos preview modal
  const [previewModalRender, setPreviewModalRender] = useState<RenderStatus | null>(null);

  // Branding overlay foundation (preview-only this release — not rendered into MP4)
  const [branding, setBranding] = useState<Branding>(DEFAULT_BRANDING);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function loadHistory() {
    authFetch("/api/v1/video-generator/renders?all_statuses=true")
      .then((r) => (r.ok ? r.json() : []))
      .then((data: RenderStatus[]) => setHistory(Array.isArray(data) ? data : []))
      .catch(() => {});
  }

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
    loadHistory();
  }, []);

  useEffect(() => {
    const id = Array.from(pickedListingId)[0];
    if (!id) return;
    setLoadingListingImages(true);
    setListingImagesError(null);
    setPickedImages([]);
    getListingImages(id)
      .then((imgs) => {
        const sorted = imgs.slice().sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0));
        const urls = sorted
          .map((img) => img.url_fullxfull ?? img.url_570xN ?? img.url_170x135)
          .filter((u): u is string => !!u);
        if (urls.length === 0) {
          setListingImagesError("No synced photos available for this listing.");
        }
        setPickedImages(sorted);
        setImageUrlsText(urls.join("\n"));
      })
      .catch((e) => {
        setListingImagesError(e instanceof ApiError ? e.message : "Failed to load this listing's photos.");
      })
      .finally(() => setLoadingListingImages(false));
  }, [pickedListingId]);

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
              loadHistory();
            }
          }
        } catch { /* ignore */ }
      }, 2000);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [renderJob?.id, renderJob?.status]);

  function handleRender(e: React.FormEvent) {
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
    // Lightweight confirm — reinforce that this creates a local MP4 only and
    // never uploads to Etsy, before any render starts.
    setConfirmGenerateOpen(true);
  }

  async function confirmAndRender() {
    const urls = imageUrlsText.split("\n").map((u) => u.trim()).filter(Boolean);
    if (!urls.length) return;
    setConfirmGenerateOpen(false);
    setSubmitting(true);
    setRenderJob(null);
    setReviewed(false);
    setDownloaded(false);
    try {
      const brandingHasText = !!(branding.headline || branding.slogan || branding.outro || branding.cta);
      const brandingHasAny = brandingHasText || !!branding.logoUrl;
      const r = await authFetch("/api/v1/video-generator/render", {
        method: "POST",
        body: JSON.stringify({
          template_id: selectedTemplate,
          image_urls: urls,
          aspect_ratio: selectedAspectRatio,
          duration_seconds: durationSeconds,
          branding: brandingHasAny
            ? {
                logo_url: branding.logoUrl || null,
                headline: branding.headline || null,
                slogan: branding.slogan || null,
                outro_text: branding.outro || null,
                cta_text: branding.cta || null,
                logo_position: branding.logoPosition,
                text_placement: branding.textPlacement,
                brand_color: branding.brandColor || null,
              }
            : null,
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

  function downloadRender(downloadUrl: string, renderId: string) {
    const token = getAccessToken();
    fetch(`${BACKEND_URL}${downloadUrl}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `product_video_${renderId.slice(0, 8)}.mp4`;
        a.click();
        URL.revokeObjectURL(url);
      })
      .catch(() => alert("Download failed."));
  }

  function handleDownload() {
    if (!renderJob?.download_url) return;
    downloadRender(renderJob.download_url, renderJob.id);
    setDownloaded(true);
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

          <div className="flex gap-4 text-xs font-medium">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                checked={imageSource === "manual"}
                onChange={() => setImageSource("manual")}
                className="accent-indigo-600"
              />
              Paste URLs
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                checked={imageSource === "listing"}
                onChange={() => setImageSource("listing")}
                className="accent-indigo-600"
              />
              Select from a listing&apos;s synced photos
            </label>
          </div>

          {imageSource === "listing" && (
            <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
              <ListingPicker
                selectedIds={pickedListingId}
                onSelectionChange={setPickedListingId}
                multiSelect={false}
                pageSize={10}
              />
              {loadingListingImages && <p className="text-xs text-gray-400 mt-2">Loading photos…</p>}
              {listingImagesError && <p className="text-xs text-red-600 mt-2">{listingImagesError}</p>}
              {!loadingListingImages && pickedImages.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-500 mb-1.5">{pickedImages.length} synced photo{pickedImages.length === 1 ? "" : "s"}, in image order:</p>
                  <div className="flex gap-2 flex-wrap">
                    {pickedImages.map((img, i) => (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        key={img.id}
                        src={img.url_170x135 ?? img.url_570xN ?? img.url_fullxfull ?? ""}
                        alt=""
                        title={i === 0 ? "First in order" : undefined}
                        className={`w-14 h-14 rounded-lg object-cover border ${i === 0 ? "border-indigo-400 border-2" : "border-gray-200"}`}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <p className="text-xs text-gray-500">
            {imageSource === "manual"
              ? `Paste one image URL per line (e.g. from your listing images). Maximum ${maxImages} images.`
              : `Photo URLs from the selected listing, in image order. Maximum ${maxImages} images — edit the list below if needed.`}
          </p>
          <textarea
            value={imageUrlsText}
            onChange={(e) => setImageUrlsText(e.target.value)}
            placeholder={"https://i.etsystatic.com/...\nhttps://i.etsystatic.com/..."}
            rows={5}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 font-mono resize-y focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {/* Pre-generation safety panel (C1) */}
          <div className="px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600 space-y-1">
            <p className="font-medium text-slate-700">Before you generate:</p>
            <ul className="list-disc list-inside space-y-0.5">
              <li>Generation creates a <strong>local MP4 only</strong> — it does <strong>not</strong> upload to Etsy.</li>
              <li>No Etsy listing changes happen from Generate Video.</li>
              <li>After generation you can <strong>Download to your computer</strong> or open the gated Upload to Etsy info.</li>
              <li>Upload to Etsy is <strong>not enabled yet</strong>.</li>
            </ul>
          </div>
          <button
            type="submit"
            disabled={submitting || !imageUrlsText.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            {submitting ? "Starting…" : "Generate Video"}
          </button>
        </form>

        <BrandingSection branding={branding} setBranding={setBranding} />

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
                <div className="px-4 py-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
                  <strong>Your video was generated.</strong> Review it before publishing. Videos are never auto-uploaded to Etsy.
                </div>

                <RenderDetails render={renderJob} />

                {renderJob.branding && (
                  <div className="rounded-lg border border-gray-200 p-3 text-xs space-y-0.5">
                    <p className="font-medium text-gray-700">Branding:</p>
                    <p className={renderJob.branding_text_rendered ? "text-green-700" : "text-gray-500"}>
                      {renderJob.branding_text_rendered
                        ? "✓ Text branding rendered into this MP4"
                        : "Text branding was not rendered (no text provided, or font unavailable)"}
                    </p>
                    {typeof renderJob.branding.logo_url === "string" && renderJob.branding.logo_url && (
                      <p className="text-amber-600">Logo: preview-only, not rendered into the MP4</p>
                    )}
                  </div>
                )}

                {/* In-app video preview/player (M13.05B) */}
                {renderJob.download_url ? (
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-gray-700">Preview (plays in your browser — not uploaded to Etsy):</p>
                    <VideoPreview downloadUrl={renderJob.download_url} onReviewed={() => setReviewed(true)} />
                  </div>
                ) : (
                  <p className="text-xs text-gray-500 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                    Preview unavailable. Download the video to review it.
                  </p>
                )}

                <EtsyReadyChecklist render={renderJob} specs={etsySpecs} />

                {/* Owner result checklist (C3) — interactive (M13.05B) */}
                <div className="rounded-lg border border-gray-200 p-3 space-y-1 text-xs">
                  <p className="font-medium text-gray-700">Result checklist:</p>
                  <p className="text-green-700">✓ Video generated</p>
                  <p className={reviewed ? "text-green-700" : "text-gray-600"}>{reviewed ? "✓" : "☐"} Review the video</p>
                  <p className={downloaded ? "text-green-700" : "text-gray-600"}>{downloaded ? "✓" : "☐"} Download to your computer</p>
                  <p className="text-gray-500">• Upload to Etsy is gated / not enabled yet</p>
                  <p className="text-gray-500">• No Etsy upload occurred</p>
                </div>

                <div className="px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
                  Review the video before uploading. Do not upload to Etsy without checking it first.
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={handleDownload}
                    className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                  >
                    Download to your computer
                  </button>
                  <button
                    onClick={() => setUploadGateOpen(true)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-500 text-sm font-medium px-4 py-2 rounded-lg transition-colors cursor-not-allowed"
                    title="Upload to Etsy is coming after owner-approved live video upload testing."
                    aria-disabled="true"
                  >
                    Upload to Etsy
                  </button>
                </div>
              </div>
            )}

            {renderJob.status === "failed" && renderJob.error_message && (
              <p className="text-sm text-red-600">{renderJob.error_message}</p>
            )}
          </div>
        )}

        {/* Render history (M13.05) */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
          <h2 className="text-sm font-semibold text-gray-900">Recent Videos</h2>
          {history.length === 0 ? (
            <p className="text-sm text-gray-400">No videos generated yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                    <th className="pb-2 pr-4">Created</th>
                    <th className="pb-2 pr-4">Template</th>
                    <th className="pb-2 pr-4">Source</th>
                    <th className="pb-2 pr-4">Photos</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.id} className="border-b border-gray-50">
                      <td className="py-2 pr-4 text-gray-400 text-xs">{new Date(h.created_at).toLocaleString()}</td>
                      <td className="py-2 pr-4 text-gray-700">{h.template_id}</td>
                      <td className="py-2 pr-4 text-gray-500 text-xs">{h.source === "uploaded" ? "Uploaded file" : "Generated"}</td>
                      <td className="py-2 pr-4 text-gray-600">{h.image_count > 0 ? h.image_count : "—"}</td>
                      <td className="py-2 pr-4">
                        <span
                          className={`text-xs px-2 py-0.5 rounded font-medium ${
                            h.status === "completed"
                              ? "bg-green-100 text-green-700"
                              : h.status === "failed"
                              ? "bg-red-100 text-red-700"
                              : "bg-blue-100 text-blue-700"
                          }`}
                        >
                          {h.status}
                        </span>
                        {h.status === "failed" && h.error_message && (
                          <p className="text-xs text-red-600 mt-0.5">{h.error_message}</p>
                        )}
                      </td>
                      <td className="py-2">
                        {h.status === "completed" && h.download_url ? (
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => setPreviewModalRender(h)}
                              className="text-xs text-indigo-600 hover:underline"
                              title="Preview the video in your browser"
                            >
                              Preview
                            </button>
                            <button
                              onClick={() => downloadRender(h.download_url as string, h.id)}
                              className="text-xs text-indigo-600 hover:underline"
                              title="Download to your computer"
                            >
                              Download
                            </button>
                            <button
                              onClick={() => setUploadGateOpen(true)}
                              className="text-xs text-gray-400 hover:underline cursor-not-allowed"
                              title="Upload to Etsy is coming after owner-approved live video upload testing."
                            >
                              Upload to Etsy
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-300">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-xs text-gray-400">
            After a video is generated you have two choices: <strong>Download to your computer</strong>, or <strong>Upload to Etsy</strong> (coming after owner-approved live upload testing). Videos are never auto-uploaded to Etsy — download, review, then publish.
          </p>
        </div>
      </div>

      <VideoUnavailableModal
        open={unavailableModalOpen}
        reason={unavailableReason}
        isSuperuser={isSuperuser}
        onClose={() => setUnavailableModalOpen(false)}
      />

      <UploadToEtsyGateModal open={uploadGateOpen} onClose={() => setUploadGateOpen(false)} />

      <ConfirmGenerateModal
        open={confirmGenerateOpen}
        onConfirm={confirmAndRender}
        onCancel={() => setConfirmGenerateOpen(false)}
      />

      <PreviewModal render={previewModalRender} onClose={() => setPreviewModalRender(null)} />
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
