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
