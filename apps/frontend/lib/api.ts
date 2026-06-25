const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function clearLocalSession(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BACKEND_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

// ---- Types ----

export interface Shop {
  id: string;
  etsy_shop_id: string;
  shop_name: string;
  is_connected: boolean;
  created_at: string;
  updated_at: string;
}

export interface ListingListItem {
  id: string;
  organization_id: string;
  etsy_shop_id: string;
  etsy_listing_id: string;
  title: string | null;
  state: string | null;
  price_amount: number | null;
  price_divisor: number | null;
  currency_code: string | null;
  quantity: number | null;
  sku: string | null;
  has_variations: boolean;
  thumbnail_url: string | null;
  last_synced_at: string | null;
  etsy_updated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ListingDetail extends ListingListItem {
  description: string | null;
  url: string | null;
  tags: string[] | null;
  materials: string[] | null;
  taxonomy_id: string | null;
  section_id: string | null;
  shipping_profile_id: string | null;
  return_policy_id: string | null;
  processing_min: number | null;
  processing_max: number | null;
  who_made: string | null;
  when_made: string | null;
  is_supply: boolean | null;
  is_customizable: boolean | null;
  is_personalizable: boolean | null;
  personalization_is_required: boolean | null;
  personalization_char_count_max: number | null;
  personalization_instructions: string | null;
  item_weight: number | null;
  item_weight_unit: string | null;
  item_length: number | null;
  item_width: number | null;
  item_height: number | null;
  item_dimensions_unit: string | null;
}

export interface ListingImage {
  id: string;
  listing_id: string;
  etsy_image_id: string | null;
  url_fullxfull: string | null;
  url_570xN: string | null;
  url_170x135: string | null;
  alt_text: string | null;
  rank: number | null;
  width: number | null;
  height: number | null;
}

export interface ListingVideo {
  id: string;
  listing_id: string;
  etsy_video_id: string | null;
  video_url: string | null;
  thumbnail_url: string | null;
  rank: number | null;
}

export interface ListingVariation {
  id: string;
  listing_id: string;
  etsy_product_id: string | null;
  sku: string | null;
  property_name: string | null;
  value_name: string | null;
  price_amount: number | null;
  price_divisor: number | null;
  currency_code: string | null;
  quantity: number | null;
  is_available: boolean;
}

export interface ListingPage {
  items: ListingListItem[];
  page: number;
  per_page: number;
  total: number;
  filters: Record<string, unknown> | null;
}

export interface SyncJobResult {
  sync_job_id: string;
  status: string;
  processed_items: number;
  total_items: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface ListingsParams {
  shop_id?: string;
  state?: string;
  search?: string;
  tag?: string;
  has_variations?: boolean;
  price_min?: number;
  price_max?: number;
  quantity_min?: number;
  quantity_max?: number;
  section_id?: string;
  taxonomy_id?: string;
  is_personalizable?: boolean;
  is_customizable?: boolean;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
}

// ---- API helpers ----

export function getShops(): Promise<{ shops: Shop[] }> {
  return apiFetch("/api/v1/etsy/shops");
}

export function getListings(params: ListingsParams = {}): Promise<ListingPage> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  }
  const query = qs.toString();
  return apiFetch(`/api/v1/listings${query ? `?${query}` : ""}`);
}

export function getListing(id: string): Promise<ListingDetail> {
  return apiFetch(`/api/v1/listings/${id}`);
}

export function getListingImages(id: string): Promise<ListingImage[]> {
  return apiFetch(`/api/v1/listings/${id}/images`);
}

export function getListingVideos(id: string): Promise<ListingVideo[]> {
  return apiFetch(`/api/v1/listings/${id}/videos`);
}

export function getListingVariations(id: string): Promise<ListingVariation[]> {
  return apiFetch(`/api/v1/listings/${id}/variations`);
}

export function syncShop(shopId: string): Promise<SyncJobResult> {
  return apiFetch(`/api/v1/shops/${shopId}/sync`, { method: "POST" });
}

export function logoutLocalSession(): void {
  clearLocalSession();
}

// ---- Bulk Edit Types ----

export interface BulkEditSession {
  id: string;
  organization_id: string;
  created_by_user_id: string | null;
  name: string | null;
  status: string;
  selected_listing_ids: string[];
  selected_count: number;
  change_count: number;
  preview_generated_at: string | null;
  applied_at: string | null;
  canceled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BulkEditSessionDetail extends BulkEditSession {
  changes: BulkEditChange[];
  preview_item_count: number;
}

export interface BulkEditChange {
  id: string;
  bulk_edit_session_id: string;
  listing_id: string | null;
  field_name: string;
  operation: string;
  old_value: unknown;
  new_value: unknown;
  operation_value: unknown;
  validation_status: string;
  validation_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface BulkEditPreviewItem {
  id: string;
  bulk_edit_session_id: string;
  listing_id: string;
  listing_title: string | null;
  before_data: Record<string, unknown>;
  after_data: Record<string, unknown>;
  diff: Record<string, { before: unknown; after: unknown }>;
  validation_status: string;
  validation_messages: Array<{ level: string; field: string; message: string }> | null;
  created_at: string;
  updated_at: string;
}

export interface BulkEditPreviewPage {
  items: BulkEditPreviewItem[];
  page: number;
  per_page: number;
  total: number;
  session_id: string;
}

export interface BulkEditPreviewGenerateResponse {
  session: BulkEditSession;
  summary: {
    selected_count: number;
    preview_items: number;
    valid: number;
    warning: number;
    invalid: number;
  };
}

export interface ApplyJob {
  id: string;
  organization_id: string;
  bulk_edit_session_id: string;
  created_by_user_id: string | null;
  status: string;
  total_items: number;
  success_count: number;
  failure_count: number;
  skipped_count: number;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplyResult {
  id: string;
  organization_id: string;
  apply_job_id: string;
  bulk_edit_session_id: string;
  listing_id: string;
  etsy_listing_id: string;
  status: string;
  request_payload: unknown;
  response_payload: unknown;
  error_message: string | null;
  backup_snapshot_id: string | null;
  attempted_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplyJobWithResults {
  job: ApplyJob;
  results: ApplyResult[];
}

export interface BackupSnapshot {
  id: string;
  organization_id: string;
  bulk_edit_session_id: string | null;
  listing_id: string;
  etsy_shop_id: string;
  etsy_listing_id: string;
  snapshot_type: string;
  snapshot_data: Record<string, unknown>;
  created_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

// ---- Bulk Edit API helpers ----

export function createBulkEditSession(listingIds: string[], name?: string): Promise<BulkEditSession> {
  return apiFetch("/api/v1/bulk-edit/sessions", {
    method: "POST",
    body: JSON.stringify({ listing_ids: listingIds, name: name ?? null }),
  });
}

export function listBulkEditSessions(): Promise<BulkEditSession[]> {
  return apiFetch("/api/v1/bulk-edit/sessions");
}

export function getBulkEditSession(sessionId: string): Promise<BulkEditSessionDetail> {
  return apiFetch(`/api/v1/bulk-edit/sessions/${sessionId}`);
}

export function cancelBulkEditSession(sessionId: string): Promise<BulkEditSession> {
  return apiFetch(`/api/v1/bulk-edit/sessions/${sessionId}`, { method: "DELETE" });
}

export function addBulkEditChange(
  sessionId: string,
  payload: { field_name: string; operation: string; operation_value?: unknown },
): Promise<BulkEditChange> {
  return apiFetch(`/api/v1/bulk-edit/sessions/${sessionId}/changes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeBulkEditChange(sessionId: string, changeId: string): Promise<void> {
  return apiFetch(`/api/v1/bulk-edit/sessions/${sessionId}/changes/${changeId}`, { method: "DELETE" });
}

export function generateBulkEditPreview(sessionId: string): Promise<BulkEditPreviewGenerateResponse> {
  return apiFetch(`/api/v1/bulk-edit/sessions/${sessionId}/preview`, { method: "POST" });
}

export function getBulkEditPreview(
  sessionId: string,
  params: { page?: number; per_page?: number; validation_status?: string } = {},
): Promise<BulkEditPreviewPage> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  }
  const q = qs.toString();
  return apiFetch(`/api/v1/bulk-edit/sessions/${sessionId}/preview${q ? `?${q}` : ""}`);
}

export function applyBulkEditSession(sessionId: string): Promise<ApplyJob> {
  return apiFetch(`/api/v1/bulk-edit/sessions/${sessionId}/apply`, { method: "POST" });
}

export function listApplyJobs(sessionId: string): Promise<ApplyJob[]> {
  return apiFetch(`/api/v1/bulk-edit/sessions/${sessionId}/apply-jobs`);
}

export function getApplyJobDetail(jobId: string): Promise<ApplyJobWithResults> {
  return apiFetch(`/api/v1/bulk-edit/apply-jobs/${jobId}`);
}

export function listBackupSnapshots(sessionId: string): Promise<BackupSnapshot[]> {
  return apiFetch(`/api/v1/bulk-edit/sessions/${sessionId}/backups`);
}

// ---- Revert Types ----

export interface RevertJob {
  id: string;
  organization_id: string;
  bulk_edit_session_id: string;
  apply_job_id: string;
  created_by_user_id: string | null;
  status: string;
  total_items: number;
  success_count: number;
  failure_count: number;
  skipped_count: number;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface RevertResult {
  id: string;
  organization_id: string;
  revert_job_id: string;
  apply_job_id: string;
  bulk_edit_session_id: string;
  listing_id: string;
  etsy_listing_id: string;
  backup_snapshot_id: string | null;
  status: string;
  request_payload: unknown;
  response_payload: unknown;
  error_message: string | null;
  attempted_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RevertJobWithResults {
  job: RevertJob;
  results: RevertResult[];
}

export interface RevertResultPage {
  items: RevertResult[];
  page: number;
  per_page: number;
  total: number;
  revert_job_id: string;
}

// ---- Revert API helpers ----

export function revertApplyJob(applyJobId: string): Promise<RevertJob> {
  return apiFetch(`/api/v1/bulk-edit/apply-jobs/${applyJobId}/revert`, { method: "POST" });
}

export function listRevertJobs(applyJobId: string): Promise<RevertJob[]> {
  return apiFetch(`/api/v1/bulk-edit/apply-jobs/${applyJobId}/revert-jobs`);
}

export function getRevertJob(revertJobId: string): Promise<RevertJobWithResults> {
  return apiFetch(`/api/v1/bulk-edit/revert-jobs/${revertJobId}`);
}

export function getRevertResults(
  revertJobId: string,
  params: { page?: number; per_page?: number } = {},
): Promise<RevertResultPage> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) qs.set(k, String(v));
  }
  const q = qs.toString();
  return apiFetch(`/api/v1/bulk-edit/revert-jobs/${revertJobId}/results${q ? `?${q}` : ""}`);
}

// ---- Media Job Types ----

export interface MediaJob {
  id: string;
  organization_id: string;
  bulk_edit_session_id: string | null;
  created_by_user_id: string | null;
  operation_type: string;
  operation_payload: unknown;
  status: string;
  total_items: number;
  success_count: number;
  failure_count: number;
  skipped_count: number;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface MediaResult {
  id: string;
  organization_id: string;
  media_job_id: string;
  listing_id: string;
  etsy_listing_id: string;
  operation_type: string;
  status: string;
  before_media: unknown;
  after_media: unknown;
  request_payload: unknown;
  response_payload: unknown;
  error_message: string | null;
  attempted_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MediaResultPage {
  items: MediaResult[];
  page: number;
  per_page: number;
  total: number;
  media_job_id: string;
}

export interface MediaBackupSnapshot {
  id: string;
  organization_id: string;
  media_job_id: string | null;
  listing_id: string;
  etsy_listing_id: string;
  snapshot_type: string;
  images_snapshot: unknown;
  videos_snapshot: unknown;
  created_at: string;
  updated_at: string;
}

// ---- Media API helpers ----

export function createMediaJob(
  listingIds: string[],
  operationType: string,
  payload: Record<string, unknown> = {},
): Promise<MediaJob> {
  return apiFetch("/api/v1/bulk-edit/media/jobs", {
    method: "POST",
    body: JSON.stringify({ listing_ids: listingIds, operation_type: operationType, payload }),
  });
}

export function listMediaJobs(): Promise<MediaJob[]> {
  return apiFetch("/api/v1/bulk-edit/media/jobs");
}

export function getMediaJob(jobId: string): Promise<MediaJob & { results: MediaResult[] }> {
  return apiFetch(`/api/v1/bulk-edit/media/jobs/${jobId}`);
}

export function applyMediaJob(jobId: string): Promise<MediaJob> {
  return apiFetch(`/api/v1/bulk-edit/media/jobs/${jobId}/apply`, { method: "POST" });
}

export function getMediaResults(
  jobId: string,
  params: { page?: number; per_page?: number } = {},
): Promise<MediaResultPage> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) qs.set(k, String(v));
  }
  const q = qs.toString();
  return apiFetch(`/api/v1/bulk-edit/media/jobs/${jobId}/results${q ? `?${q}` : ""}`);
}

export function getMediaBackups(jobId: string): Promise<MediaBackupSnapshot[]> {
  return apiFetch(`/api/v1/bulk-edit/media/jobs/${jobId}/backups`);
}
