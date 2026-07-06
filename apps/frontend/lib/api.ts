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

export interface VideoRenderSummary {
  id: string;
  status: string;
  template_id: string;
  source: string; // "generated" (Product Video Generator) | "uploaded" (own MP4 file)
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

export function listVideoRenders(etsyReadyOnly = false): Promise<VideoRenderSummary[]> {
  return apiFetch(`/api/v1/video-generator/renders?etsy_ready_only=${etsyReadyOnly}`);
}

// Uploads a local MP4 file for use by Add Video / Replace Video. The file is
// validated and stored server-side immediately — nothing is sent to Etsy
// until a media job that references it is applied.
export async function uploadVideoFile(file: File): Promise<VideoRenderSummary> {
  const token = getAccessToken();
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BACKEND_URL}/api/v1/video-generator/uploads`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json();
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

// ---- Variation Job Types ----

export interface VariationJob {
  id: string;
  organization_id: string;
  created_by_user_id: string | null;
  operation_type: string;
  operation_payload: unknown;
  selected_listing_ids: string[];
  status: string;
  selected_count: number;
  preview_count: number;
  success_count: number;
  failure_count: number;
  skipped_count: number;
  preview_generated_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface VariationPreviewItem {
  id: string;
  organization_id: string;
  variation_job_id: string;
  listing_id: string;
  etsy_listing_id: string;
  listing_title: string | null;
  before_variations: unknown;
  after_variations: unknown;
  diff: unknown;
  validation_status: string;
  validation_messages: unknown;
  created_at: string;
  updated_at: string;
}

export interface VariationPreviewPage {
  items: VariationPreviewItem[];
  page: number;
  per_page: number;
  total: number;
  variation_job_id: string;
}

export interface VariationResult {
  id: string;
  organization_id: string;
  variation_job_id: string;
  listing_id: string;
  etsy_listing_id: string;
  status: string;
  request_payload: unknown;
  response_payload: unknown;
  error_message: string | null;
  attempted_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface VariationResultPage {
  items: VariationResult[];
  page: number;
  per_page: number;
  total: number;
  variation_job_id: string;
}

export interface VariationBackupSnapshot {
  id: string;
  organization_id: string;
  variation_job_id: string | null;
  listing_id: string;
  etsy_listing_id: string;
  snapshot_type: string;
  local_variations_snapshot: unknown;
  etsy_inventory_snapshot: unknown;
  created_at: string;
  updated_at: string;
}

// ---- Variation API helpers ----

export function createVariationJob(
  listingIds: string[],
  operationType: string,
  payload: Record<string, unknown> = {},
): Promise<VariationJob> {
  return apiFetch("/api/v1/bulk-edit/variations/jobs", {
    method: "POST",
    body: JSON.stringify({ listing_ids: listingIds, operation_type: operationType, payload }),
  });
}

export function listVariationJobs(): Promise<VariationJob[]> {
  return apiFetch("/api/v1/bulk-edit/variations/jobs");
}

export function getVariationJob(jobId: string): Promise<VariationJob> {
  return apiFetch(`/api/v1/bulk-edit/variations/jobs/${jobId}`);
}

export function generateVariationPreview(jobId: string): Promise<VariationJob> {
  return apiFetch(`/api/v1/bulk-edit/variations/jobs/${jobId}/preview`, { method: "POST" });
}

export function getVariationPreview(
  jobId: string,
  params: { page?: number; per_page?: number } = {},
): Promise<VariationPreviewPage> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) qs.set(k, String(v));
  }
  const q = qs.toString();
  return apiFetch(`/api/v1/bulk-edit/variations/jobs/${jobId}/preview${q ? `?${q}` : ""}`);
}

export function applyVariationJob(jobId: string): Promise<VariationJob> {
  return apiFetch(`/api/v1/bulk-edit/variations/jobs/${jobId}/apply`, { method: "POST" });
}

export function getVariationResults(
  jobId: string,
  params: { page?: number; per_page?: number } = {},
): Promise<VariationResultPage> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) qs.set(k, String(v));
  }
  const q = qs.toString();
  return apiFetch(`/api/v1/bulk-edit/variations/jobs/${jobId}/results${q ? `?${q}` : ""}`);
}

export function getVariationBackups(jobId: string): Promise<VariationBackupSnapshot[]> {
  return apiFetch(`/api/v1/bulk-edit/variations/jobs/${jobId}/backups`);
}

// ---- AI Tools Types ----

export interface AISuggestion {
  id: string;
  organization_id: string;
  ai_session_id: string;
  listing_id: string | null;
  field: string;
  suggested_value: unknown;
  reasoning: string | null;
  status: string;
  accepted_at: string | null;
  rejected_at: string | null;
  converted_to_session_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AISession {
  id: string;
  organization_id: string;
  created_by_user_id: string | null;
  listing_id: string | null;
  tool: string;
  status: string;
  input_payload: Record<string, unknown>;
  ai_provider: string | null;
  ai_model: string | null;
  error_message: string | null;
  suggestion_count: number;
  suggestions: AISuggestion[];
  created_at: string;
  updated_at: string;
}

export interface AISessionPage {
  items: AISession[];
  total: number;
  page: number;
  page_size: number;
}

export interface AIUsage {
  ai_credits_used: number;
  ai_credits_limit: number;
  period_key: string;
}

export interface ConvertResult {
  bulk_edit_session_id: string;
  message: string;
}

// ---- AI Tools API helpers ----

export function createAISession(
  listingId: string,
  tool: string,
  extraContext: Record<string, unknown> = {},
): Promise<AISession> {
  return apiFetch("/api/v1/ai/sessions", {
    method: "POST",
    body: JSON.stringify({ listing_id: listingId, tool, extra_context: extraContext }),
  });
}

export function listAISessions(
  params: { listing_id?: string; tool?: string; page?: number; page_size?: number } = {},
): Promise<AISessionPage> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) qs.set(k, String(v));
  }
  const q = qs.toString();
  return apiFetch(`/api/v1/ai/sessions${q ? `?${q}` : ""}`);
}

export function getAISession(sessionId: string): Promise<AISession> {
  return apiFetch(`/api/v1/ai/sessions/${sessionId}`);
}

export function runAISession(sessionId: string): Promise<AISession> {
  return apiFetch(`/api/v1/ai/sessions/${sessionId}/run`, { method: "POST" });
}

export function getAISuggestions(sessionId: string): Promise<AISuggestion[]> {
  return apiFetch(`/api/v1/ai/sessions/${sessionId}/suggestions`);
}

export function acceptSuggestion(suggestionId: string): Promise<AISuggestion> {
  return apiFetch(`/api/v1/ai/suggestions/${suggestionId}/accept`, { method: "POST" });
}

export function rejectSuggestion(suggestionId: string): Promise<AISuggestion> {
  return apiFetch(`/api/v1/ai/suggestions/${suggestionId}/reject`, { method: "POST" });
}

export function convertAISession(sessionId: string): Promise<ConvertResult> {
  return apiFetch(`/api/v1/ai/sessions/${sessionId}/convert`, { method: "POST" });
}

export function getAIUsage(): Promise<AIUsage> {
  return apiFetch("/api/v1/ai/usage");
}

// ---- CSV Types ----

export interface CSVJob {
  id: string;
  organization_id: string;
  user_id: string | null;
  job_type: string;
  status: string;
  filename: string | null;
  original_filename: string | null;
  row_count: number;
  valid_row_count: number;
  invalid_row_count: number;
  changed_row_count: number;
  unchanged_row_count: number;
  ignored_column_count: number;
  ignored_columns: string[] | null;
  summary: Record<string, unknown> | null;
  error_message: string | null;
  converted_bulk_edit_session_id: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CSVRow {
  id: string;
  organization_id: string;
  csv_job_id: string;
  row_number: number;
  listing_id: string | null;
  etsy_listing_id: string | null;
  listing_title: string | null;
  raw_data: Record<string, unknown>;
  normalized_data: Record<string, unknown> | null;
  diff: Record<string, unknown> | null;
  status: string;
  validation_errors: string[] | null;
  validation_warnings: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface CSVPreviewPage {
  items: CSVRow[];
  total: number;
  page: number;
  per_page: number;
  csv_job_id: string;
}

export interface CSVImportSummary {
  job_id: string;
  status: string;
  row_count: number;
  valid_row_count: number;
  invalid_row_count: number;
  changed_row_count: number;
  unchanged_row_count: number;
  ignored_columns: string[];
  message: string;
}

export interface CSVConvertResult {
  bulk_edit_session_id: string;
  converted_rows: number;
  created_changes: number;
  message: string;
}

// ---- CSV API helpers ----

export function exportCSV(shopId?: string, state?: string): string {
  const token = getAccessToken();
  const qs = new URLSearchParams();
  if (shopId) qs.set("shop_id", shopId);
  if (state) qs.set("state", state);
  if (token) qs.set("_token", token);
  const q = qs.toString();
  return `${BACKEND_URL}/api/v1/csv/export${q ? `?${q}` : ""}`;
}

export function downloadCSVTemplate(): string {
  return `${BACKEND_URL}/api/v1/csv/template`;
}

export async function importCSV(file: File): Promise<CSVImportSummary> {
  const token = getAccessToken();
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BACKEND_URL}/api/v1/csv/import`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json();
}

export function listCSVJobs(jobType?: string): Promise<CSVJob[]> {
  const qs = jobType ? `?job_type=${encodeURIComponent(jobType)}` : "";
  return apiFetch(`/api/v1/csv/jobs${qs}`);
}

export function getCSVJob(jobId: string): Promise<CSVJob> {
  return apiFetch(`/api/v1/csv/jobs/${jobId}`);
}

export function getCSVPreview(
  jobId: string,
  params: { page?: number; per_page?: number; status?: string } = {},
): Promise<CSVPreviewPage> {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.per_page) qs.set("per_page", String(params.per_page));
  if (params.status) qs.set("status", params.status);
  const q = qs.toString();
  return apiFetch(`/api/v1/csv/jobs/${jobId}/preview${q ? `?${q}` : ""}`);
}

export function convertCSVJob(
  jobId: string,
  ignoreInvalid = false,
): Promise<CSVConvertResult> {
  return apiFetch(`/api/v1/csv/jobs/${jobId}/convert`, {
    method: "POST",
    body: JSON.stringify({ ignore_invalid: ignoreInvalid }),
  });
}

// ── Dynamic Pricing ──────────────────────────────────────────────────────────

export interface DynamicPricingJob {
  id: string;
  organization_id: string;
  user_id: string | null;
  status: string;
  selected_listing_ids: string[];
  rule_type: string;
  rule_payload: Record<string, unknown>;
  safety_payload: Record<string, unknown> | null;
  row_count: number;
  recommended_count: number;
  skipped_count: number;
  warning_count: number;
  invalid_count: number;
  converted_bulk_edit_session_id: string | null;
  error_message: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DynamicPricingRecommendation {
  id: string;
  organization_id: string;
  dynamic_pricing_job_id: string;
  listing_id: string | null;
  etsy_listing_id: string | null;
  listing_title: string | null;
  currency_code: string | null;
  current_price_amount: number | null;
  recommended_price_amount: number | null;
  reference_price_amount: number | null;
  cost_amount: number | null;
  margin_percent: string | null;
  diff_amount: number | null;
  diff_percent: string | null;
  status: string;
  reason: string | null;
  calculation_details: Record<string, unknown> | null;
  validation_errors: string[] | null;
  validation_warnings: string[] | null;
  decided_at: string | null;
  decided_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DynamicPricingRecommendationPage {
  items: DynamicPricingRecommendation[];
  total: number;
  page: number;
  per_page: number;
  job_id: string;
}

export interface DynamicPricingSummary {
  job_id: string;
  total_listings: number;
  current_total_price: number;
  recommended_total_price: number;
  total_diff_amount: number;
  total_diff_percent: string | null;
  recommended_count: number;
  accepted_count: number;
  skipped_count: number;
  warning_count: number;
  invalid_count: number;
  converted_count: number;
}

export interface DynamicPricingConvertResponse {
  bulk_edit_session_id: string;
  converted_count: number;
  created_changes: number;
  message: string;
}

const DP = "/api/v1/dynamic-pricing";

export function createDynamicPricingJob(body: {
  selected_listing_ids: string[];
  rule_type: string;
  rule_payload: Record<string, unknown>;
  safety_payload?: Record<string, unknown> | null;
}): Promise<DynamicPricingJob> {
  return apiFetch(`${DP}/jobs`, { method: "POST", body: JSON.stringify(body) });
}

export function listDynamicPricingJobs(): Promise<DynamicPricingJob[]> {
  return apiFetch(`${DP}/jobs`);
}

export function getDynamicPricingJob(jobId: string): Promise<DynamicPricingJob> {
  return apiFetch(`${DP}/jobs/${jobId}`);
}

export function generateDynamicPricingPreview(jobId: string): Promise<DynamicPricingJob> {
  return apiFetch(`${DP}/jobs/${jobId}/preview`, { method: "POST" });
}

export function getDynamicPricingRecommendations(
  jobId: string,
  params?: { page?: number; per_page?: number; status?: string },
): Promise<DynamicPricingRecommendationPage> {
  const q = new URLSearchParams();
  if (params?.page) q.set("page", String(params.page));
  if (params?.per_page) q.set("per_page", String(params.per_page));
  if (params?.status) q.set("status", params.status);
  const qs = q.toString();
  return apiFetch(`${DP}/jobs/${jobId}/recommendations${qs ? `?${qs}` : ""}`);
}

export function acceptDynamicPricingRecommendation(
  recommendationId: string,
): Promise<DynamicPricingRecommendation> {
  return apiFetch(`${DP}/recommendations/${recommendationId}/accept`, { method: "POST" });
}

export function rejectDynamicPricingRecommendation(
  recommendationId: string,
): Promise<DynamicPricingRecommendation> {
  return apiFetch(`${DP}/recommendations/${recommendationId}/reject`, { method: "POST" });
}

export function acceptAllDynamicPricingRecommendations(
  jobId: string,
): Promise<{ accepted_count: number; message: string }> {
  return apiFetch(`${DP}/jobs/${jobId}/accept-all`, { method: "POST" });
}

export function convertDynamicPricingJob(jobId: string): Promise<DynamicPricingConvertResponse> {
  return apiFetch(`${DP}/jobs/${jobId}/convert`, { method: "POST" });
}

export function getDynamicPricingSummary(jobId: string): Promise<DynamicPricingSummary> {
  return apiFetch(`${DP}/jobs/${jobId}/summary`);
}

// ── Scheduled Jobs ────────────────────────────────────────────────────────────

export interface ScheduledJob {
  id: string;
  organization_id: string;
  created_by_user_id: string | null;
  name: string;
  job_type: string;
  status: string;
  schedule_type: string;
  schedule_payload: Record<string, unknown>;
  job_payload: Record<string, unknown> | null;
  timezone: string;
  next_run_at: string | null;
  last_run_at: string | null;
  run_count: number;
  failure_count: number;
  max_runs: number | null;
  starts_at: string | null;
  ends_at: string | null;
  disabled_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduledJobRun {
  id: string;
  organization_id: string;
  scheduled_job_id: string;
  triggered_by_user_id: string | null;
  trigger_type: string;
  job_type: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  output_payload: Record<string, unknown> | null;
  error_message: string | null;
  created_resource_type: string | null;
  created_resource_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface RunDueResponse {
  executed: number;
  run_ids: string[];
}

const SJ = "/api/v1/scheduled-jobs";

export function createScheduledJob(body: {
  name: string;
  job_type: string;
  schedule_type: string;
  schedule_payload: Record<string, unknown>;
  job_payload?: Record<string, unknown> | null;
  timezone?: string;
  max_runs?: number | null;
  starts_at?: string | null;
  ends_at?: string | null;
}): Promise<ScheduledJob> {
  return apiFetch(`${SJ}/jobs`, { method: "POST", body: JSON.stringify(body) });
}

export function listScheduledJobs(params?: {
  status?: string;
  job_type?: string;
  limit?: number;
  offset?: number;
}): Promise<ScheduledJob[]> {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.job_type) q.set("job_type", params.job_type);
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  const qs = q.toString();
  return apiFetch(`${SJ}/jobs${qs ? `?${qs}` : ""}`);
}

export function getScheduledJob(jobId: string): Promise<ScheduledJob> {
  return apiFetch(`${SJ}/jobs/${jobId}`);
}

export function pauseScheduledJob(jobId: string): Promise<ScheduledJob> {
  return apiFetch(`${SJ}/jobs/${jobId}/pause`, { method: "POST" });
}

export function resumeScheduledJob(jobId: string): Promise<ScheduledJob> {
  return apiFetch(`${SJ}/jobs/${jobId}/resume`, { method: "POST" });
}

export function disableScheduledJob(jobId: string): Promise<ScheduledJob> {
  return apiFetch(`${SJ}/jobs/${jobId}/disable`, { method: "POST" });
}

export function runScheduledJobNow(jobId: string): Promise<ScheduledJobRun> {
  return apiFetch(`${SJ}/jobs/${jobId}/run-now`, { method: "POST" });
}

export function getJobRuns(jobId: string): Promise<ScheduledJobRun[]> {
  return apiFetch(`${SJ}/jobs/${jobId}/runs`);
}

export function getAllRuns(): Promise<ScheduledJobRun[]> {
  return apiFetch(`${SJ}/runs`);
}

export function runDueJobs(): Promise<RunDueResponse> {
  return apiFetch(`${SJ}/run-due`, { method: "POST" });
}

// ── Admin Panel ───────────────────────────────────────────────────────────────

export interface AdminPage<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface AdminOverview {
  total_users: number;
  total_organizations: number;
  active_subscriptions: number;
  paid_subscriptions: number;
  total_listings: number;
  total_scheduled_jobs: number;
  total_ai_sessions: number;
  total_csv_jobs: number;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  organization_id: string | null;
  organization_name: string | null;
  plan: string | null;
}

export interface AdminUserOrgMembership {
  organization_id: string;
  organization_name: string;
  role: string;
}

export interface AdminUserUsageSummary {
  bulk_edit_sessions_count: number;
  ai_sessions_count: number;
  csv_jobs_count: number;
  dynamic_pricing_jobs_count: number;
  media_jobs_count: number;
}

export interface AdminUserDetail extends AdminUser {
  organizations: AdminUserOrgMembership[];
  usage: AdminUserUsageSummary;
  recent_events: AdminAuditEvent[];
}

export interface AdminOrganization {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  owner_email: string | null;
  plan: string | null;
  subscription_status: string | null;
  etsy_connected: boolean;
  users_count: number;
}

export interface AdminOrgMemberItem {
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
}

export interface AdminOrgUsageSummary {
  bulk_edit_sessions_count: number;
  ai_sessions_count: number;
  csv_jobs_count: number;
  dynamic_pricing_jobs_count: number;
  sync_jobs_count: number;
  media_jobs_count: number;
  video_renders_count: number;
}

export interface AdminOrgRiskSummary {
  failed_bulk_edit_count: number;
  failed_ai_count: number;
  failed_scheduled_runs_count: number;
  etsy_disconnected: boolean;
  billing_issue: boolean;
}

export interface AdminOrganizationDetail extends AdminOrganization {
  subscription: AdminSubscription | null;
  shop_count: number;
  listing_count: number;
  members: AdminOrgMemberItem[];
  shops: AdminShop[];
  usage: AdminOrgUsageSummary;
  recent_events: AdminAuditEvent[];
  risk: AdminOrgRiskSummary;
  effective_access: AdminEffectiveAccess;
}

export interface AdminSubscription {
  id: string;
  organization_id: string;
  plan: string;
  status: string;
  stripe_customer_id: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminShop {
  id: string;
  organization_id: string;
  etsy_shop_id: string;
  shop_name: string;
  is_connected: boolean;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminScheduledJobSummary {
  id: string;
  organization_id: string;
  name: string;
  job_type: string;
  status: string;
  schedule_type: string;
  timezone: string;
  next_run_at: string | null;
  last_run_at: string | null;
  run_count: number;
  failure_count: number;
  created_at: string;
  updated_at: string;
}

export interface AdminAuditEvent {
  id: string;
  organization_id: string;
  user_id: string | null;
  event_type: string;
  entity_type: string | null;
  entity_id: string | null;
  message: string | null;
  created_at: string;
}

export interface AdminActionResult {
  ok: boolean;
  message: string;
}

const ADM = "/api/v1/admin";

export function adminGetOverview(): Promise<AdminOverview> {
  return apiFetch(`${ADM}/overview`);
}

export interface AdminUserFilters {
  q?: string;
  status?: "active" | "disabled" | "all";
  role?: "superuser" | "user" | "all";
  organization_id?: string;
  plan?: string;
  created_from?: string;
  created_to?: string;
}

export interface AdminOrganizationFilters {
  q?: string;
  plan?: string;
  subscription_status?: string;
  etsy_connected?: boolean;
  created_from?: string;
  created_to?: string;
}

function toQueryString(params: Record<string, unknown>): string {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  }
  return qs.toString();
}

export function adminListUsers(
  page = 1,
  page_size = 25,
  filters: AdminUserFilters = {},
): Promise<AdminPage<AdminUser>> {
  const qs = toQueryString({ page, page_size, ...filters });
  return apiFetch(`${ADM}/users?${qs}`);
}

export function adminGetUserDetail(userId: string): Promise<AdminUserDetail> {
  return apiFetch(`${ADM}/users/${userId}`);
}

export function adminListOrganizations(
  page = 1,
  page_size = 25,
  filters: AdminOrganizationFilters = {},
): Promise<AdminPage<AdminOrganization>> {
  const qs = toQueryString({ page, page_size, ...filters });
  return apiFetch(`${ADM}/organizations?${qs}`);
}

export function adminGetOrganizationDetail(orgId: string): Promise<AdminOrganizationDetail> {
  return apiFetch(`${ADM}/organizations/${orgId}`);
}

// ── Plan change / comp access / effective access ──────────────────────────────

export interface AdminCompGrantOut {
  id: string;
  organization_id: string;
  comp_plan: string;
  reason: string;
  granted_by_user_id: string | null;
  starts_at: string;
  ends_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface AdminEffectiveAccess {
  subscription_plan: string | null;
  subscription_status: string | null;
  stripe_managed: boolean;
  comp: AdminCompGrantOut | null;
  effective_plan: string;
}

export function adminGetEffectiveAccess(orgId: string): Promise<AdminEffectiveAccess> {
  return apiFetch(`${ADM}/organizations/${orgId}/effective-access`);
}

export function adminChangePlan(orgId: string, plan: string, reason: string): Promise<AdminActionResult> {
  return apiFetch(`${ADM}/organizations/${orgId}/plan`, {
    method: "POST",
    body: JSON.stringify({ plan, reason }),
  });
}

export function adminGrantComp(orgId: string, comp_plan: string, reason: string, ends_at?: string | null): Promise<AdminCompGrantOut> {
  return apiFetch(`${ADM}/organizations/${orgId}/comp`, {
    method: "POST",
    body: JSON.stringify({ comp_plan, reason, ends_at: ends_at ?? null }),
  });
}

export function adminRevokeComp(orgId: string): Promise<AdminCompGrantOut> {
  return apiFetch(`${ADM}/organizations/${orgId}/comp`, { method: "DELETE" });
}

// ── Manual Etsy sync ───────────────────────────────────────────────────────────

export interface AdminSyncTriggerResult {
  status: string;
  job_id: string;
  message: string;
}

export function adminTriggerSync(orgId: string, shop_id?: string | null, reason?: string | null): Promise<AdminSyncTriggerResult> {
  return apiFetch(`${ADM}/organizations/${orgId}/sync`, {
    method: "POST",
    body: JSON.stringify({ shop_id: shop_id ?? null, reason: reason ?? null }),
  });
}

// ── Password reset ─────────────────────────────────────────────────────────────

export function adminSendPasswordReset(userId: string): Promise<{ message: string }> {
  return apiFetch(`${ADM}/users/${userId}/send-password-reset`, { method: "POST" });
}

// ── Payments ──────────────────────────────────────────────────────────────────

export interface AdminPaymentItem {
  id: string;
  organization_id: string | null;
  organization_name: string | null;
  owner_email: string | null;
  plan: string | null;
  subscription_status: string | null;
  event_type: string;
  status: string;
  amount: number | null;
  currency: string | null;
  stripe_customer_id: string | null;
  refundable_ref: string | null;
  created_at: string;
}

export interface AdminPaymentFilters {
  q?: string;
  organization_id?: string;
  plan?: string;
  subscription_status?: string;
  created_from?: string;
  created_to?: string;
}

export function adminListPayments(
  page = 1,
  page_size = 25,
  filters: AdminPaymentFilters = {},
): Promise<AdminPage<AdminPaymentItem>> {
  const qs = toQueryString({ page, page_size, ...filters });
  return apiFetch(`${ADM}/payments?${qs}`);
}

export function adminRefundPayment(paymentId: string, reason: string, amount?: number | null): Promise<AdminActionResult> {
  return apiFetch(`${ADM}/payments/${paymentId}/refund`, {
    method: "POST",
    body: JSON.stringify({ reason, amount: amount ?? null }),
  });
}

// ── Alerts ────────────────────────────────────────────────────────────────────

export interface AdminAlertRuleOut {
  id: string;
  name: string;
  event_type: string;
  enabled: boolean;
  threshold_count: number;
  window_minutes: number;
  channel_email_enabled: boolean;
  channel_email_to: string | null;
  channel_slack_enabled: boolean;
  slack_webhook_configured: boolean;
  last_triggered_at: string | null;
  updated_at: string;
}

export interface AdminAlertRuleUpdate {
  enabled?: boolean;
  threshold_count?: number;
  window_minutes?: number;
  channel_email_enabled?: boolean;
  channel_email_to?: string | null;
  channel_slack_enabled?: boolean;
  slack_webhook_url?: string;
}

export function adminListAlerts(): Promise<AdminAlertRuleOut[]> {
  return apiFetch(`${ADM}/alerts`);
}

export function adminUpdateAlert(ruleId: string, update: AdminAlertRuleUpdate): Promise<AdminAlertRuleOut> {
  return apiFetch(`${ADM}/alerts/${ruleId}`, {
    method: "PUT",
    body: JSON.stringify(update),
  });
}

export function adminTestAlert(ruleId: string): Promise<AdminActionResult> {
  return apiFetch(`${ADM}/alerts/${ruleId}/test`, { method: "POST" });
}

export function adminRunAlertCheck(): Promise<{ checked: number; triggered: string[] }> {
  return apiFetch(`${ADM}/alerts/run-check`, { method: "POST" });
}

export function adminListSubscriptions(page = 1, page_size = 25): Promise<AdminPage<AdminSubscription>> {
  return apiFetch(`${ADM}/subscriptions?page=${page}&page_size=${page_size}`);
}

export function adminListShops(page = 1, page_size = 25): Promise<AdminPage<AdminShop>> {
  return apiFetch(`${ADM}/shops?page=${page}&page_size=${page_size}`);
}

export function adminListScheduledJobs(page = 1, page_size = 25): Promise<AdminPage<AdminScheduledJobSummary>> {
  return apiFetch(`${ADM}/scheduled-jobs?page=${page}&page_size=${page_size}`);
}

export function adminListEvents(page = 1, page_size = 25): Promise<AdminPage<AdminAuditEvent>> {
  return apiFetch(`${ADM}/events?page=${page}&page_size=${page_size}`);
}

export function adminDisableUser(userId: string): Promise<AdminActionResult> {
  return apiFetch(`${ADM}/users/${userId}/disable`, { method: "POST" });
}

export function adminEnableUser(userId: string): Promise<AdminActionResult> {
  return apiFetch(`${ADM}/users/${userId}/enable`, { method: "POST" });
}

export function adminPauseScheduledJob(jobId: string): Promise<AdminActionResult> {
  return apiFetch(`${ADM}/scheduled-jobs/${jobId}/pause`, { method: "POST" });
}

export function adminResumeScheduledJob(jobId: string): Promise<AdminActionResult> {
  return apiFetch(`${ADM}/scheduled-jobs/${jobId}/resume`, { method: "POST" });
}

// ── Admin Business Dashboard Types ────────────────────────────────────────────

export interface AdminUsageSummary {
  id: string;
  organization_id: string;
  period_key: string;
  listings_synced: number;
  bulk_edits_used: number;
  ai_credits_used: number;
  media_assets_used: number;
  dynamic_pricing_jobs_used: number;
  created_at: string;
  updated_at: string;
}

export interface AdminBillingSummary {
  total_subscriptions: number;
  free_plan_count: number;
  basic_monthly_count: number;
  basic_yearly_count: number;
  pro_monthly_count: number;
  pro_yearly_count: number;
  active_count: number;
  trialing_count: number;
  canceled_count: number;
  cancel_at_period_end_count: number;
  estimated_monthly_revenue: number;
}

export interface AdminStripeSummary {
  total_stripe_customers: number;
  subscriptions_with_stripe_sub: number;
  active_stripe_subscriptions: number;
  canceling_at_period_end: number;
  total_billing_events: number;
}

export interface AdminProductUsage {
  total_listings: number;
  total_bulk_edit_sessions: number;
  total_ai_sessions: number;
  total_csv_jobs: number;
  total_dynamic_pricing_jobs: number;
  total_sync_jobs: number;
  total_shops: number;
}

export interface AdminSystemHealth {
  database_status: string;
  redis_status: string;
  rate_limit_backend: string;
  rate_limit_enabled: boolean;
  sentry_configured: boolean;
  worker_status: string;
  csp_mode: string;
  total_users: number;
  total_organizations: number;
  total_audit_events: number;
  recent_failed_scheduled_runs: number;
  recent_failed_ai_sessions: number;
}

// ── Admin Business Dashboard API helpers ──────────────────────────────────────

export function adminGetBillingSummary(): Promise<AdminBillingSummary> {
  return apiFetch(`${ADM}/billing-summary`);
}

export function adminGetStripeSummary(): Promise<AdminStripeSummary> {
  return apiFetch(`${ADM}/stripe-summary`);
}

export function adminGetProductUsage(): Promise<AdminProductUsage> {
  return apiFetch(`${ADM}/product-usage`);
}

export function adminGetSystemHealth(): Promise<AdminSystemHealth> {
  return apiFetch(`${ADM}/system-health`);
}

// ── Admin Trends ───────────────────────────────────────────────────────────────

export interface AdminTrendPoint {
  date: string;
  count: number;
}

export interface AdminTrendSeries {
  users: AdminTrendPoint[];
  organizations: AdminTrendPoint[];
  bulk_edit_jobs: AdminTrendPoint[];
  media_jobs: AdminTrendPoint[];
}

export interface AdminTrendsOut {
  days: number;
  series: AdminTrendSeries;
}

export function adminGetTrends(days = 30): Promise<AdminTrendsOut> {
  return apiFetch(`${ADM}/metrics/trends?days=${days}`);
}

export function adminListAuditLog(page = 1, page_size = 25): Promise<AdminPage<AdminAuditEvent>> {
  return apiFetch(`${ADM}/audit-log?page=${page}&page_size=${page_size}`);
}

export function adminListUsage(page = 1, page_size = 25): Promise<AdminPage<AdminUsageSummary>> {
  return apiFetch(`${ADM}/usage?page=${page}&page_size=${page_size}`);
}

// ── Contact Submissions ────────────────────────────────────────────────────────

export interface AdminContactSubmission {
  id: string;
  name: string;
  email: string;
  subject: string;
  message: string;
  email_delivered: boolean;
  created_at: string;
}

export function adminListContactSubmissions(page = 1, page_size = 25): Promise<AdminPage<AdminContactSubmission>> {
  return apiFetch(`${ADM}/contact-submissions?page=${page}&page_size=${page_size}`);
}

// ── Feature Flags (read-only) ─────────────────────────────────────────────────

export interface AdminFeatureFlag {
  key: string;
  enabled: boolean;
  source: string;
}

export interface AdminFeatureFlags {
  flags: AdminFeatureFlag[];
}

export function adminGetFeatureFlags(): Promise<AdminFeatureFlags> {
  return apiFetch(`${ADM}/feature-flags`);
}

// ── Listing Health Types ──────────────────────────────────────────────────────

export interface HealthIssue {
  category: string;
  severity: "low" | "medium" | "high" | "critical";
  field: string;
  message: string;
  recommended_fix: string;
  ai_can_help: boolean;
}

export interface ListingHealthRow {
  listing_id: string;
  title: string | null;
  state: string | null;
  score: number;
  grade: "excellent" | "good" | "needs_work" | "critical";
  priority: "low" | "medium" | "high" | "critical";
  issue_count: number;
  top_issues: HealthIssue[];
  photo_count: number;
  tag_count: number;
  has_video: boolean;
  price: number | null;
  currency: string | null;
  last_synced_at: string | null;
}

export interface ListingHealthDetail extends ListingHealthRow {
  all_issues: HealthIssue[];
  suggested_actions: string[];
}

export interface ListingHealthPage {
  items: ListingHealthRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface ListingHealthSummary {
  average_score: number;
  total_listings: number;
  excellent_count: number;
  good_count: number;
  needs_work_count: number;
  critical_count: number;
  high_priority_count: number;
  top_issue_categories: string[];
  last_calculated_at: string;
}

export interface AISuggestions {
  listing_id: string;
  improved_title?: string | null;
  suggested_tags?: string[] | null;
  improved_description?: string | null;
  explanation?: string | null;
  confidence?: string | null;
  ai_available: boolean;
  message?: string | null;
}

// ── Listing Health API helpers ────────────────────────────────────────────────

const LH = "/api/v1/listing-health";

export function getListingHealthSummary(): Promise<ListingHealthSummary> {
  return apiFetch(`${LH}/summary`);
}

export function getListingHealthListings(params?: {
  grade?: string; priority?: string; search?: string; sort?: string; page?: number; page_size?: number;
}): Promise<ListingHealthPage> {
  const q = new URLSearchParams();
  if (params?.grade) q.set("grade", params.grade);
  if (params?.priority) q.set("priority", params.priority);
  if (params?.search) q.set("search", params.search);
  if (params?.sort) q.set("sort", params.sort);
  if (params?.page) q.set("page", String(params.page));
  if (params?.page_size) q.set("page_size", String(params.page_size));
  const qs = q.toString();
  return apiFetch(`${LH}/listings${qs ? "?" + qs : ""}`);
}

export function getListingHealthDetail(listingId: string): Promise<ListingHealthDetail> {
  return apiFetch(`${LH}/listings/${listingId}`);
}

export function getListingHealthAISuggestions(listingId: string): Promise<AISuggestions> {
  return apiFetch(`${LH}/listings/${listingId}/ai-suggestions`, { method: "POST" });
}

// ── Profit Types ──────────────────────────────────────────────────────────────

export type ProfitStatus = "profitable" | "low_margin" | "loss" | "missing_costs";

export interface CostProfile {
  id: string;
  organization_id: string;
  name: string;
  currency: string;
  transaction_fee_percent: string;
  payment_fee_percent: string;
  payment_fixed_fee: string;
  listing_fee: string;
  offsite_ads_percent: string;
  currency_conversion_percent: string;
  default_shipping_cost: string;
  default_packaging_cost: string;
  target_margin_percent: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ListingCostUpdate {
  product_cost: string;
  shipping_cost: string;
  packaging_cost: string;
  ad_cost: string;
  other_cost: string;
  include_offsite_ads: boolean;
  cost_profile_id?: string | null;
  notes?: string | null;
}

export interface ProfitListingRow {
  listing_id: string;
  title: string | null;
  price: string | null;
  currency: string | null;
  product_cost: string | null;
  shipping_cost: string | null;
  total_etsy_fees: string | null;
  net_profit: string | null;
  margin_percent: string | null;
  break_even_price: string | null;
  recommended_min_price: string | null;
  status: ProfitStatus;
  health_score: number | null;
}

export interface ProfitListingPage {
  items: ProfitListingRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProfitSummary {
  listings_with_costs: number;
  listings_missing_costs: number;
  average_margin: string | null;
  low_margin_count: number;
  loss_making_count: number;
  estimated_total_profit: string | null;
  currency: string;
}

export interface ProfitCalculation {
  listing_id: string;
  title: string | null;
  price: string | null;
  currency: string | null;
  sale_price: string;
  shipping_charged: string;
  gross_revenue: string;
  product_cost: string;
  shipping_cost: string;
  packaging_cost: string;
  ad_cost: string;
  other_cost: string;
  etsy_transaction_fee: string;
  etsy_payment_fee: string;
  etsy_listing_fee: string;
  etsy_offsite_ads_fee: string;
  total_etsy_fees: string;
  total_costs: string;
  net_profit: string;
  margin_percent: string;
  break_even_price: string;
  recommended_min_price: string;
  roi_percent: string;
  status: ProfitStatus;
}

// ── Profit API helpers ────────────────────────────────────────────────────────

const PROFIT = "/api/v1/profit";

export function getProfitSummary(): Promise<ProfitSummary> {
  return apiFetch(`${PROFIT}/summary`);
}

export function getProfitListings(params?: {
  page?: number; page_size?: number; loss_only?: boolean; missing_costs?: boolean; search?: string;
}): Promise<ProfitListingPage> {
  const q = new URLSearchParams();
  if (params?.page) q.set("page", String(params.page));
  if (params?.page_size) q.set("page_size", String(params.page_size));
  if (params?.loss_only) q.set("loss_only", "true");
  if (params?.missing_costs) q.set("missing_costs", "true");
  if (params?.search) q.set("search", params.search);
  const qs = q.toString();
  return apiFetch(`${PROFIT}/listings${qs ? "?" + qs : ""}`);
}

export function getProfitListingDetail(listingId: string): Promise<ProfitCalculation> {
  return apiFetch(`${PROFIT}/listings/${listingId}`);
}

export function updateListingCosts(listingId: string, costs: ListingCostUpdate): Promise<{ message: string; listing_id: string }> {
  return apiFetch(`${PROFIT}/listings/${listingId}/costs`, { method: "PUT", body: JSON.stringify(costs) });
}

export function getCostProfiles(): Promise<CostProfile[]> {
  return apiFetch(`${PROFIT}/cost-profiles`);
}

export function createCostProfile(profile: Omit<CostProfile, "id" | "organization_id" | "created_at" | "updated_at">): Promise<CostProfile> {
  return apiFetch(`${PROFIT}/cost-profiles`, { method: "POST", body: JSON.stringify(profile) });
}

export function updateCostProfile(profileId: string, profile: Omit<CostProfile, "id" | "organization_id" | "created_at" | "updated_at">): Promise<CostProfile> {
  return apiFetch(`${PROFIT}/cost-profiles/${profileId}`, { method: "PUT", body: JSON.stringify(profile) });
}
