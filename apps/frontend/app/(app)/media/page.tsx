"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  getAccessToken,
  getListings,
  createMediaJob,
  listMediaJobs,
  applyMediaJob,
  getMediaResults,
  getMediaBackups,
  listVideoRenders,
  uploadVideoFile,
  ApiError,
  type ListingListItem,
  type MediaJob,
  type MediaResult,
  type VideoRenderSummary,
} from "@/lib/api";

// ── Local upload types & constants ──────────────────────────────────────────
const IMAGE_ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;
const IMAGE_ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"] as const;
const MAX_IMAGE_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const MAX_FILES = 20;

// Only MP4 is accepted — it's the one format our backend actually validates
// (via ffprobe) and uploads to Etsy. Listing MOV/WEBM here would be a promise
// the backend can't keep.
const VIDEO_ALLOWED_TYPES = ["video/mp4"] as const;
const VIDEO_ALLOWED_EXTENSIONS = [".mp4"] as const;
const MAX_VIDEO_FILE_SIZE = 100 * 1024 * 1024; // 100 MB — matches Etsy's listing video limit

type LocalUpload = { id: string; file: File; preview: string; sizeLabel: string };

function isAllowedImageFile(file: File): boolean {
  const ext = ("." + (file.name.split(".").pop() ?? "")).toLowerCase();
  return (
    (IMAGE_ALLOWED_TYPES as readonly string[]).includes(file.type) &&
    (IMAGE_ALLOWED_EXTENSIONS as readonly string[]).includes(ext)
  );
}

function isAllowedVideoFile(file: File): boolean {
  const ext = ("." + (file.name.split(".").pop() ?? "")).toLowerCase();
  return (
    (VIDEO_ALLOWED_TYPES as readonly string[]).includes(file.type) &&
    (VIDEO_ALLOWED_EXTENSIONS as readonly string[]).includes(ext)
  );
}

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

type VideoUpload = {
  id: string;
  file: File;
  sizeLabel: string;
  status: "uploading" | "success" | "error";
  error?: string;
  render?: VideoRenderSummary;
};

function LocalUploadPanel({ onVideoUploaded }: { onVideoUploaded: (render: VideoRenderSummary) => void }) {
  const [uploads, setUploads] = useState<LocalUpload[]>([]);
  const [videoUploads, setVideoUploads] = useState<VideoUpload[]>([]);
  const [rejections, setRejections] = useState<string[]>([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function uploadVideo(file: File) {
    const id = crypto.randomUUID();
    setVideoUploads((prev) => [...prev, { id, file, sizeLabel: fmtSize(file.size), status: "uploading" }]);
    try {
      const render = await uploadVideoFile(file);
      setVideoUploads((prev) => prev.map((v) => (v.id === id ? { ...v, status: "success", render } : v)));
      onVideoUploaded(render);
    } catch (e) {
      const message = e instanceof ApiError ? e.message : "Upload failed.";
      setVideoUploads((prev) => prev.map((v) => (v.id === id ? { ...v, status: "error", error: message } : v)));
    }
  }

  function processFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const errs: string[] = [];
    const accepted: LocalUpload[] = [];
    const videoFiles: File[] = [];

    if (uploads.length + files.length > MAX_FILES) {
      errs.push(`Max ${MAX_FILES} files allowed. Clear some before adding more.`);
      setRejections(errs);
      return;
    }

    Array.from(files).forEach((file) => {
      if (isAllowedVideoFile(file)) {
        if (file.size > MAX_VIDEO_FILE_SIZE) {
          errs.push(`"${file.name}" — file too large (${fmtSize(file.size)}). Max 100 MB.`);
          return;
        }
        videoFiles.push(file);
        return;
      }
      if (!isAllowedImageFile(file)) {
        errs.push(`"${file.name}" — unsupported type. Images: JPG, PNG, WEBP. Videos: MP4.`);
        return;
      }
      if (file.size > MAX_IMAGE_FILE_SIZE) {
        errs.push(`"${file.name}" — file too large (${fmtSize(file.size)}). Max 10 MB.`);
        return;
      }
      accepted.push({
        id: crypto.randomUUID(),
        file,
        preview: URL.createObjectURL(file),
        sizeLabel: fmtSize(file.size),
      });
    });

    setRejections(errs);
    setUploads((prev) => [...prev, ...accepted]);
    videoFiles.forEach((f) => { void uploadVideo(f); });
  }

  function handleRemove(id: string) {
    setUploads((prev) => {
      const item = prev.find((u) => u.id === id);
      if (item) URL.revokeObjectURL(item.preview);
      return prev.filter((u) => u.id !== id);
    });
  }

  function handleClearAll() {
    uploads.forEach((u) => URL.revokeObjectURL(u.preview));
    setUploads([]);
    setVideoUploads([]);
    setRejections([]);
  }

  useEffect(() => {
    return () => { uploads.forEach((u) => URL.revokeObjectURL(u.preview)); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function copyUrlToClipboard(preview: string) {
    navigator.clipboard.writeText(preview).catch(() => {});
  }

  const totalCount = uploads.length + videoUploads.length;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-gray-800">Upload Images / Videos from Computer</h2>
        {totalCount > 0 && (
          <button
            onClick={handleClearAll}
            className="text-xs text-gray-400 hover:text-red-600 transition-colors"
          >
            Clear all ({totalCount})
          </button>
        )}
      </div>

      <p className="text-xs text-gray-400 mb-1">
        Images: JPG, PNG, WEBP up to 10 MB · Preview-only (not uploaded anywhere until used in a job below)
      </p>
      <p className="text-xs text-gray-400 mb-3">
        Videos: MP4 up to 100 MB · Uploaded to secure storage right away so they can be validated and selected
        for Add Video / Replace Video below — nothing is sent to Etsy until you create and apply a media job.
      </p>

      {/* Drop zone */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors mb-4 ${
          dragging
            ? "border-indigo-400 bg-indigo-50"
            : "border-gray-200 hover:border-indigo-300 hover:bg-gray-50"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          processFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload images or videos"
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.webp,.mp4"
          multiple
          className="sr-only"
          onChange={(e) => processFiles(e.target.files)}
        />
        <svg className="w-8 h-8 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <p className="text-sm text-gray-500">
          <span className="font-medium text-indigo-600">Click to upload images or videos</span>, or drag and drop
        </p>
        <p className="text-xs text-gray-400 mt-1">Images: JPG, PNG, WEBP · Videos: MP4</p>
      </div>

      {/* Rejections */}
      {rejections.length > 0 && (
        <div className="mb-3 p-3 rounded-lg bg-red-50 border border-red-200">
          {rejections.map((r, i) => (
            <p key={i} className="text-xs text-red-700">{r}</p>
          ))}
        </div>
      )}

      {/* Video upload progress/results */}
      {videoUploads.length > 0 && (
        <div className="mb-4 space-y-2">
          {videoUploads.map((v) => (
            <div key={v.id} className="flex items-center gap-3 p-2 rounded-lg border border-gray-100 bg-gray-50">
              <svg className="w-5 h-5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-700 truncate font-medium" title={v.file.name}>{v.file.name}</p>
                <p className="text-xs text-gray-400">{v.sizeLabel}</p>
                {v.status === "error" && <p className="text-xs text-red-600 mt-0.5">{v.error}</p>}
              </div>
              {v.status === "uploading" && <span className="text-xs text-gray-400 shrink-0">Uploading…</span>}
              {v.status === "success" && <span className="text-xs text-green-600 font-medium shrink-0">Ready to select below</span>}
              {v.status === "error" && <span className="text-xs text-red-600 font-medium shrink-0">Failed</span>}
            </div>
          ))}
        </div>
      )}

      {/* Uploaded preview grid */}
      {uploads.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {uploads.map((u) => (
            <div key={u.id} className="relative group border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={u.preview}
                alt={u.file.name}
                className="w-full h-24 object-cover"
              />
              <div className="p-2">
                <p className="text-xs text-gray-700 truncate font-medium" title={u.file.name}>
                  {u.file.name}
                </p>
                <p className="text-xs text-gray-400">{u.sizeLabel}</p>
                <button
                  onClick={() => copyUrlToClipboard(u.preview)}
                  className="text-xs text-indigo-600 hover:underline mt-1"
                  title="Copy preview URL to use in Image URL field above"
                >
                  Copy URL
                </button>
              </div>
              <button
                onClick={() => handleRemove(u.id)}
                className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/50 text-white text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                aria-label={`Remove ${u.file.name}`}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {totalCount === 0 && rejections.length === 0 && (
        <p className="text-xs text-gray-400 text-center">No files uploaded yet.</p>
      )}
    </div>
  );
}

const OPERATION_OPTIONS = [
  { value: "add_image", label: "Add Image", implemented: true },
  { value: "replace_image", label: "Replace Image (at rank)", implemented: true },
  { value: "delete_image", label: "Delete Image", implemented: true },
  { value: "add_video", label: "Add Video", implemented: true },
  { value: "replace_video", label: "Replace Video", implemented: true },
  { value: "delete_video", label: "Delete Video", implemented: true },
  {
    value: "reorder_images",
    label: "Reorder Images (not available)",
    implemented: false,
    reason:
      "Etsy has no endpoint to change an existing image's rank without re-uploading it. The only workaround (delete then re-upload) has a real window where your live listing could show fewer or missing photos if it fails partway — so this isn't offered rather than risking that silently.",
  },
];

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-gray-100 text-gray-700",
    running: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    completed_with_errors: "bg-yellow-100 text-yellow-700",
    failed: "bg-red-100 text-red-700",
    success: "bg-green-100 text-green-700",
    skipped: "bg-gray-100 text-gray-500",
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colors[status] ?? "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}

export default function MediaPage() {
  const router = useRouter();
  const [listings, setListings] = useState<ListingListItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [operationType, setOperationType] = useState("add_image");
  const [imageUrl, setImageUrl] = useState("");
  const [rank, setRank] = useState<number | "">("");
  const [targetRank, setTargetRank] = useState<number | "">("");
  const [imageId, setImageId] = useState("");
  const [altText, setAltText] = useState("");
  const [videoRenders, setVideoRenders] = useState<VideoRenderSummary[]>([]);
  const [selectedVideoRenderId, setSelectedVideoRenderId] = useState("");
  const [addVideoTab, setAddVideoTab] = useState<"generated" | "upload">("generated");
  const [selectedAddVideoId, setSelectedAddVideoId] = useState("");
  const [jobs, setJobs] = useState<MediaJob[]>([]);
  const [results, setResults] = useState<MediaResult[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [confirmText, setConfirmText] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingJobId, setPendingJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [backupCount, setBackupCount] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const [pg, jobList, renders] = await Promise.all([
        getListings({ per_page: 200 }),
        listMediaJobs(),
        listVideoRenders(true).catch(() => []),
      ]);
      setListings(pg.items);
      setJobs(jobList);
      setVideoRenders(renders);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) { router.push("/login"); return; }
      setError("Failed to load listings.");
    }
  }, [router]);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    load();
  }, [load, router]);

  const toggleListing = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleVideoUploaded = (render: VideoRenderSummary) => {
    setVideoRenders(prev => [render, ...prev]);
    if (operationType === "add_video") {
      setAddVideoTab("upload");
      setSelectedAddVideoId(render.id);
    }
  };

  const buildPayload = (): Record<string, unknown> => {
    const p: Record<string, unknown> = {};
    if (operationType === "add_image") {
      p.image_url = imageUrl;
      if (rank !== "") p.rank = Number(rank);
      if (altText) p.alt_text = altText;
    } else if (operationType === "replace_image") {
      p.image_url = imageUrl;
      if (targetRank !== "") p.target_rank = Number(targetRank);
      if (altText) p.alt_text = altText;
    } else if (operationType === "delete_image") {
      if (imageId) p.image_id = imageId;
      else if (targetRank !== "") p.target_rank = Number(targetRank);
    } else if (operationType === "add_video") {
      if (addVideoTab === "upload") p.uploaded_video_id = selectedAddVideoId;
      else p.video_render_id = selectedAddVideoId;
    } else if (operationType === "replace_video") {
      p.video_render_id = selectedVideoRenderId;
    }
    return p;
  };

  const handleCreateJob = async () => {
    setError(null);
    setMsg(null);
    if (selectedIds.size === 0) { setError("Select at least one listing."); return; }
    const op = OPERATION_OPTIONS.find(o => o.value === operationType);
    if (!op?.implemented) { setError("This operation is not yet available."); return; }
    if ((operationType === "add_image" || operationType === "replace_image") && !imageUrl) {
      setError("Image URL is required."); return;
    }
    if (operationType === "add_video" && !selectedAddVideoId) {
      setError("Choose or upload an Etsy-ready video first."); return;
    }
    if (operationType === "replace_video" && !selectedVideoRenderId) {
      setError("Choose a completed, Etsy-ready video render first."); return;
    }
    setLoading(true);
    try {
      const job = await createMediaJob([...selectedIds], operationType, buildPayload());
      await load();
      setMsg(`Job created (${job.id.slice(0, 8)}...). Click Apply to execute.`);
      setPendingJobId(job.id);
      setShowConfirm(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to create job.");
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (confirmText !== "APPLY MEDIA") { setError('Type "APPLY MEDIA" to confirm.'); return; }
    if (!pendingJobId) return;
    setShowConfirm(false);
    setConfirmText("");
    setLoading(true);
    setError(null);
    try {
      const job = await applyMediaJob(pendingJobId);
      await load();
      setActiveJobId(job.id);
      const [resPage, backups] = await Promise.all([
        getMediaResults(job.id),
        getMediaBackups(job.id),
      ]);
      setResults(resPage.items);
      setBackupCount(backups.length);
      setMsg(`Job finished: ${job.success_count} success, ${job.failure_count} failed, ${job.skipped_count} skipped.`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Apply failed.");
    } finally {
      setLoading(false);
    }
  };

  const loadResults = async (jobId: string) => {
    setActiveJobId(jobId);
    setResults([]);
    setBackupCount(null);
    try {
      const [resPage, backups] = await Promise.all([
        getMediaResults(jobId),
        getMediaBackups(jobId),
      ]);
      setResults(resPage.items);
      setBackupCount(backups.length);
    } catch {
      setError("Failed to load results.");
    }
  };

  const filtered = listings.filter(l =>
    !search || l.title?.toLowerCase().includes(search.toLowerCase()) || l.etsy_listing_id.includes(search)
  );

  return (
    <main className="max-w-6xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Photo & Video Bulk Editor</h1>
        <p className="text-sm text-gray-500 mb-6">
          Safely add, replace, or delete images across multiple listings, or attach a generated video. Backups are created before every write.
        </p>

        {/* Local image/video upload — images are preview-only, videos upload to storage immediately */}
        <LocalUploadPanel onVideoUploaded={handleVideoUploaded} />

        {error && (
          <div className="mb-4 p-3 rounded bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
        )}
        {msg && (
          <div className="mb-4 p-3 rounded bg-green-50 border border-green-200 text-green-700 text-sm">{msg}</div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Listing selector */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-3">1. Select Listings ({selectedIds.size} selected)</h2>
            <input
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              placeholder="Search listings..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <div className="max-h-64 overflow-y-auto space-y-1">
              {filtered.map(l => (
                <label key={l.id} className="flex items-center gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(l.id)}
                    onChange={() => toggleListing(l.id)}
                    className="accent-indigo-600"
                  />
                  <span className="text-sm text-gray-800 truncate flex-1">{l.title ?? l.etsy_listing_id}</span>
                  <span className="text-xs text-gray-400 shrink-0">{l.etsy_listing_id}</span>
                </label>
              ))}
              {filtered.length === 0 && (
                <p className="text-sm text-gray-400 text-center py-4">No listings found.</p>
              )}
            </div>
          </div>

          {/* Operation form */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-3">2. Choose Operation</h2>
            <select
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              value={operationType}
              onChange={e => setOperationType(e.target.value)}
            >
              {OPERATION_OPTIONS.map(op => (
                <option key={op.value} value={op.value} disabled={!op.implemented}>
                  {op.label}
                </option>
              ))}
            </select>

            {(operationType === "add_image" || operationType === "replace_image") && (
              <>
                <label className="block text-xs font-medium text-gray-700 mb-1">Image URL *</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  placeholder="https://example.com/image.jpg"
                  value={imageUrl}
                  onChange={e => setImageUrl(e.target.value)}
                />
              </>
            )}

            {operationType === "add_image" && (
              <>
                <label className="block text-xs font-medium text-gray-700 mb-1">Rank (position, optional)</label>
                <input
                  type="number"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  placeholder="e.g. 1"
                  value={rank}
                  onChange={e => setRank(e.target.value === "" ? "" : Number(e.target.value))}
                />
              </>
            )}

            {(operationType === "replace_image" || operationType === "delete_image") && (
              <>
                <label className="block text-xs font-medium text-gray-700 mb-1">Target Rank (position to replace/delete)</label>
                <input
                  type="number"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  placeholder="e.g. 1"
                  value={targetRank}
                  onChange={e => setTargetRank(e.target.value === "" ? "" : Number(e.target.value))}
                />
              </>
            )}

            {operationType === "delete_image" && (
              <>
                <label className="block text-xs font-medium text-gray-700 mb-1">Image ID (alternative to rank)</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  placeholder="Etsy image ID"
                  value={imageId}
                  onChange={e => setImageId(e.target.value)}
                />
              </>
            )}

            {(operationType === "add_image" || operationType === "replace_image") && (
              <>
                <label className="block text-xs font-medium text-gray-700 mb-1">Alt Text (optional)</label>
                <input
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  placeholder="Describe the image"
                  value={altText}
                  onChange={e => setAltText(e.target.value)}
                />
              </>
            )}

            {operationType === "reorder_images" && (
              <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 mb-3">
                <p className="text-xs text-gray-600">
                  {OPERATION_OPTIONS.find((o) => o.value === "reorder_images")?.reason}
                </p>
              </div>
            )}

            {(operationType === "add_video" || operationType === "replace_video" || operationType === "delete_video") && (
              <div className="rounded-lg bg-purple-50 border border-purple-200 p-3 mb-3">
                <p className="text-xs text-purple-800 font-medium">New — not yet exercised against your live shop</p>
                <p className="text-xs text-purple-700 mt-0.5">
                  Uses the same Etsy video endpoint a working third-party tool relies on. Your first
                  use here is the real end-to-end confirmation for your shop — if Etsy rejects it,
                  you&apos;ll see a clear error rather than a silent failure.
                </p>
              </div>
            )}

            {operationType === "add_video" && (
              <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 mb-3">
                <p className="text-xs text-blue-800">
                  Add Video uploads the selected MP4 video to the selected Etsy listing through the
                  media job flow. Nothing is sent to Etsy until you apply the job.
                </p>
              </div>
            )}
            {operationType === "replace_video" && (
              <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 mb-3">
                <p className="text-xs text-blue-800">
                  Replace Video removes the existing listing video first, then uploads the selected MP4 video.
                </p>
              </div>
            )}
            {operationType === "delete_video" && (
              <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 mb-3">
                <p className="text-xs text-blue-800">Delete Video removes the current listing video.</p>
              </div>
            )}

            {operationType === "add_video" && (() => {
              const tabRenders = videoRenders.filter(r => r.source === (addVideoTab === "upload" ? "uploaded" : "generated"));
              const selected = videoRenders.find(r => r.id === selectedAddVideoId);
              return (
                <>
                  <div className="flex rounded-lg border border-gray-200 p-1 mb-3 text-sm">
                    <button
                      type="button"
                      onClick={() => { setAddVideoTab("generated"); setSelectedAddVideoId(""); }}
                      className={`flex-1 py-1.5 rounded-md transition ${addVideoTab === "generated" ? "bg-indigo-600 text-white" : "text-gray-600 hover:bg-gray-50"}`}
                    >
                      Use generated video
                    </button>
                    <button
                      type="button"
                      onClick={() => { setAddVideoTab("upload"); setSelectedAddVideoId(""); }}
                      className={`flex-1 py-1.5 rounded-md transition ${addVideoTab === "upload" ? "bg-indigo-600 text-white" : "text-gray-600 hover:bg-gray-50"}`}
                    >
                      Upload video from computer
                    </button>
                  </div>

                  <label className="block text-xs font-medium text-gray-700 mb-1">Video *</label>
                  <select
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    value={selectedAddVideoId}
                    onChange={e => setSelectedAddVideoId(e.target.value)}
                  >
                    <option value="">Select a completed, Etsy-ready video…</option>
                    {tabRenders.map(r => (
                      <option key={r.id} value={r.id}>
                        {r.template_id} · {r.aspect_ratio ?? "?"} · {r.duration_seconds?.toFixed(0)}s · {new Date(r.created_at).toLocaleDateString()}
                      </option>
                    ))}
                  </select>

                  {tabRenders.length === 0 && addVideoTab === "generated" && (
                    <p className="text-xs text-gray-400 mb-3">
                      No Etsy-ready videos yet. Generate one in Product Video Generator first or upload an MP4 video above.{" "}
                      <a href="/video-generator" className="text-indigo-600 hover:underline">Go to Product Video Generator →</a>
                    </p>
                  )}
                  {tabRenders.length === 0 && addVideoTab === "upload" && (
                    <p className="text-xs text-gray-400 mb-3">
                      No uploaded videos yet — use the upload panel above to add one.
                    </p>
                  )}

                  {selected && (
                    <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 mb-3 text-xs text-gray-600 space-y-1">
                      <p><span className="font-medium text-gray-700">Source:</span> {selected.source === "uploaded" ? "Uploaded file" : "Generated"}</p>
                      <p><span className="font-medium text-gray-700">Template / file:</span> {selected.template_id}</p>
                      <p><span className="font-medium text-gray-700">Aspect ratio:</span> {selected.aspect_ratio ?? "unknown"}</p>
                      <p><span className="font-medium text-gray-700">Duration:</span> {selected.duration_seconds?.toFixed(1) ?? "?"}s</p>
                      <p><span className="font-medium text-gray-700">File size:</span> {selected.file_size_bytes ? fmtSize(selected.file_size_bytes) : "unknown"}</p>
                      <p><span className="font-medium text-gray-700">Created:</span> {new Date(selected.created_at).toLocaleString()}</p>
                      {selected.completed_at && (
                        <p><span className="font-medium text-gray-700">Completed:</span> {new Date(selected.completed_at).toLocaleString()}</p>
                      )}
                      <p><span className="font-medium text-gray-700">Etsy-ready:</span> {selected.is_etsy_ready ? "Yes" : "No"}</p>
                      {selected.download_url && (
                        <p><a href={`${process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100"}${selected.download_url}`} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">Preview / download →</a></p>
                      )}
                    </div>
                  )}
                </>
              );
            })()}

            {operationType === "replace_video" && (
              <>
                <label className="block text-xs font-medium text-gray-700 mb-1">Video Render *</label>
                <select
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  value={selectedVideoRenderId}
                  onChange={e => setSelectedVideoRenderId(e.target.value)}
                >
                  <option value="">Select a completed, Etsy-ready render…</option>
                  {videoRenders.map(r => (
                    <option key={r.id} value={r.id}>
                      {r.source === "uploaded" ? "Uploaded" : "Generated"} · {r.template_id} · {r.aspect_ratio ?? "?"} · {r.duration_seconds?.toFixed(0)}s · {new Date(r.created_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
                {videoRenders.length === 0 && (
                  <p className="text-xs text-gray-400 mb-3">
                    No Etsy-ready renders yet — generate one on the Video Generator page first, or upload an MP4 video above.
                  </p>
                )}
              </>
            )}

            <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 mb-4">
              <p className="text-xs text-amber-800 font-medium">Backup Warning</p>
              <p className="text-xs text-amber-700 mt-0.5">
                A backup snapshot of each listing&apos;s current media will be created before any changes are applied to Etsy.
              </p>
            </div>

            <button
              onClick={handleCreateJob}
              disabled={loading || selectedIds.size === 0}
              className="w-full py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              {loading ? "Processing..." : `Create Job for ${selectedIds.size} listing(s)`}
            </button>
          </div>
        </div>

        {/* Confirm modal */}
        {showConfirm && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
            <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
              <h3 className="text-lg font-bold text-gray-900 mb-2">Confirm Media Changes</h3>
              <p className="text-sm text-gray-600 mb-4">
                This will apply <strong>{OPERATION_OPTIONS.find((o) => o.value === operationType)?.label ?? operationType}</strong> to <strong>{selectedIds.size}</strong> listing(s) on Etsy.
                A backup snapshot will be created first.
                Type <code className="bg-gray-100 px-1 rounded">APPLY MEDIA</code> to confirm.
              </p>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                placeholder="Type APPLY MEDIA"
                value={confirmText}
                onChange={e => setConfirmText(e.target.value)}
              />
              <div className="flex gap-3">
                <button
                  onClick={() => { setShowConfirm(false); setConfirmText(""); setPendingJobId(null); }}
                  className="flex-1 py-2 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 transition focus:outline-none focus:ring-2 focus:ring-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleApply}
                  disabled={confirmText !== "APPLY MEDIA" || loading}
                  className="flex-1 py-2 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  Apply Now
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Job history */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h2 className="font-semibold text-gray-800 mb-3">Job History</h2>
          {jobs.length === 0 ? (
            <p className="text-sm text-gray-400">No media jobs yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                    <th className="pb-2 pr-4">ID</th>
                    <th className="pb-2 pr-4">Operation</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2 pr-4">Items</th>
                    <th className="pb-2 pr-4">Created</th>
                    <th className="pb-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map(job => (
                    <tr key={job.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-4 font-mono text-xs text-gray-500">{job.id.slice(0, 8)}…</td>
                      <td className="py-2 pr-4 text-gray-700">{job.operation_type}</td>
                      <td className="py-2 pr-4"><StatusBadge status={job.status} /></td>
                      <td className="py-2 pr-4 text-gray-600">
                        {job.success_count} ok / {job.failure_count} err / {job.skipped_count} skip
                      </td>
                      <td className="py-2 pr-4 text-gray-400 text-xs">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => loadResults(job.id)}
                          className="text-xs text-indigo-600 hover:underline focus:outline-none focus:ring-1 focus:ring-indigo-300 rounded"
                        >
                          Results
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Results panel */}
        {activeJobId && results.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-gray-800">
                Results for {activeJobId.slice(0, 8)}…
              </h2>
              {backupCount !== null && (
                <span className="text-xs text-gray-500">{backupCount} backup snapshot(s) saved</span>
              )}
            </div>
            <div className="space-y-2">
              {results.map(r => (
                <div
                  key={r.id}
                  className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 border border-gray-100"
                >
                  <StatusBadge status={r.status} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700 font-medium truncate">
                      Listing: {r.etsy_listing_id}
                    </p>
                    {r.error_message && (
                      <p className="text-xs text-red-600 mt-0.5">{r.error_message}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
  );
}

