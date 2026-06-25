"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getAccessToken,
  getListings,
  createMediaJob,
  listMediaJobs,
  applyMediaJob,
  getMediaResults,
  getMediaBackups,
  ApiError,
  type ListingListItem,
  type MediaJob,
  type MediaResult,
} from "../../lib/api";

const OPERATION_OPTIONS = [
  { value: "add_image", label: "Add Image", implemented: true },
  { value: "replace_image", label: "Replace Image (at rank)", implemented: true },
  { value: "delete_image", label: "Delete Image", implemented: true },
  { value: "reorder_images", label: "Reorder Images (not available in Sprint 11)", implemented: false },
  { value: "replace_video", label: "Replace Video (not available in Sprint 11)", implemented: false },
  { value: "delete_video", label: "Delete Video (not available in Sprint 11)", implemented: false },
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
      const [pg, jobList] = await Promise.all([
        getListings({ per_page: 200 }),
        listMediaJobs(),
      ]);
      setListings(pg.items);
      setJobs(jobList);
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
    }
    return p;
  };

  const handleCreateJob = async () => {
    setError(null);
    setMsg(null);
    if (selectedIds.size === 0) { setError("Select at least one listing."); return; }
    const op = OPERATION_OPTIONS.find(o => o.value === operationType);
    if (!op?.implemented) { setError("This operation is not available in Sprint 11."); return; }
    if ((operationType === "add_image" || operationType === "replace_image") && !imageUrl) {
      setError("Image URL is required."); return;
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
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <Link href="/" className="text-xl font-extrabold text-gray-900 hover:text-indigo-600 transition-colors">
          Bulk-Edit
        </Link>
        <div className="flex items-center gap-6 text-sm">
          <Link href="/dashboard" className="text-gray-600 hover:text-indigo-600">Dashboard</Link>
          <Link href="/listings" className="text-gray-600 hover:text-indigo-600">Listings</Link>
          <Link href="/bulk-edit" className="text-gray-600 hover:text-indigo-600">Bulk Edit</Link>
          <Link href="/media" className="text-indigo-600 font-semibold">Photo & Video</Link>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Photo & Video Bulk Editor</h1>
        <p className="text-sm text-gray-500 mb-6">
          Safely add, replace, or delete images across multiple listings. Backups are created before every write.
        </p>

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

            <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 mb-4">
              <p className="text-xs text-amber-800 font-medium">Backup Warning</p>
              <p className="text-xs text-amber-700 mt-0.5">
                A backup snapshot of each listing's current media will be created before any changes are applied to Etsy.
              </p>
            </div>

            <button
              onClick={handleCreateJob}
              disabled={loading || selectedIds.size === 0}
              className="w-full py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition disabled:opacity-40"
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
                This will apply <strong>{operationType}</strong> to <strong>{selectedIds.size}</strong> listing(s) on Etsy.
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
                  className="flex-1 py-2 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleApply}
                  disabled={confirmText !== "APPLY MEDIA" || loading}
                  className="flex-1 py-2 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition disabled:opacity-40"
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
                        {job.success_count}✓ {job.failure_count}✗ {job.skipped_count}–
                      </td>
                      <td className="py-2 pr-4 text-gray-400 text-xs">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => loadResults(job.id)}
                          className="text-xs text-indigo-600 hover:underline"
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
    </div>
  );
}
