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
