"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  getListing, getListingImages, getAccessToken, ApiError,
  type ListingDetail, type ListingImage,
} from "@/lib/api";
import { decodeEntities } from "@/lib/decodeEntities";

const STATE_BADGE: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  inactive: "bg-gray-100 text-gray-500",
  draft: "bg-yellow-100 text-yellow-700",
  expired: "bg-red-100 text-red-600",
};

function formatPrice(amount: number | null, divisor: number | null, currency: string | null): string {
  if (amount == null) return "—";
  const val = amount / (divisor ?? 100);
  return `${currency ?? ""} ${val.toFixed(2)}`.trim();
}

function yesNo(v: boolean | null | undefined): string {
  return v == null ? "—" : v ? "Yes" : "No";
}

// ---- reusable pieces ----

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
      <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
      {children}
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs text-gray-400 uppercase tracking-wide">{label}</p>
      <p className="text-gray-900 text-sm">{value ?? "—"}</p>
    </div>
  );
}

function BulkEditLink({ listingId, children }: { listingId: string; children: React.ReactNode }) {
  return (
    <Link
      href={`/bulk-edit?listing_ids=${listingId}`}
      className="inline-block text-xs font-medium text-indigo-600 hover:text-indigo-800 hover:underline"
    >
      {children}
    </Link>
  );
}

// ---- page ----

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const listingId = String(params.listingId);

  const [listing, setListing] = useState<ListingDetail | null>(null);
  const [images, setImages] = useState<ListingImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) { router.push("/login"); return; }
    load();
  }, [listingId]);

  function load() {
    setLoading(true);
    setError(null);
    setNotFound(false);
    getListing(listingId)
      .then((d) => {
        setListing(d);
        return getListingImages(listingId).catch(() => []);
      })
      .then((imgs) => setImages(imgs ?? []))
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) { router.push("/login"); return; }
        if (e instanceof ApiError && e.status === 404) { setNotFound(true); return; }
        setError(e instanceof ApiError ? e.message : "Failed to load product.");
      })
      .finally(() => setLoading(false));
  }

  if (loading) {
    return (
      <main className="max-w-5xl mx-auto px-6 py-16 flex justify-center">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </main>
    );
  }

  if (notFound) {
    return (
      <main className="max-w-5xl mx-auto px-6 py-16 text-center space-y-4">
        <p className="text-gray-500">Listing not found, or it doesn&apos;t belong to your account.</p>
        <Link href="/listings" className="text-indigo-600 font-medium hover:underline">← Back to Listings</Link>
      </main>
    );
  }

  if (error || !listing) {
    return (
      <main className="max-w-5xl mx-auto px-6 py-16 text-center space-y-4">
        <p className="text-red-600">{error ?? "Failed to load product."}</p>
        <div className="flex justify-center gap-4">
          <button onClick={load} className="text-indigo-600 font-medium hover:underline">Retry</button>
          <Link href="/listings" className="text-gray-500 hover:underline">← Back to Listings</Link>
        </div>
      </main>
    );
  }

  const title = listing.title ? decodeEntities(listing.title) : "Untitled listing";
  const description = listing.description ? decodeEntities(listing.description) : null;
  const tags = listing.tags ?? [];
  const materials = listing.materials ?? [];

  return (
    <main className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      {/* Header / hero */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="flex flex-col sm:flex-row gap-6">
          <div className="w-full sm:w-40 shrink-0">
            {listing.thumbnail_url ? (
              <img src={listing.thumbnail_url} alt={title} className="w-full aspect-square object-cover rounded-lg border border-gray-100" />
            ) : (
              <div className="w-full aspect-square bg-gray-100 rounded-lg border border-gray-100" />
            )}
          </div>
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-lg font-bold text-gray-900">{title}</h1>
              {listing.state && (
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATE_BADGE[listing.state] ?? "bg-gray-100 text-gray-500"}`}>
                  {listing.state}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400">Etsy listing #{listing.etsy_listing_id}</p>
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-gray-700 pt-1">
              <span><strong>{formatPrice(listing.price_amount, listing.price_divisor, listing.currency_code)}</strong></span>
              <span>Qty: {listing.quantity ?? "—"}</span>
              {listing.sku && <span>SKU: {listing.sku}</span>}
              <span className="text-gray-400">
                {listing.last_synced_at ? `Synced ${new Date(listing.last_synced_at).toLocaleString()}` : "Never synced"}
              </span>
            </div>
            <div className="flex flex-wrap gap-3 pt-3">
              <Link href="/listings" className="text-sm font-medium border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50">
                ← Back to Listings
              </Link>
              {listing.url && (
                <a href={listing.url} target="_blank" rel="noopener noreferrer"
                  className="text-sm font-medium border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50">
                  View on Etsy ↗
                </a>
              )}
              <Link href={`/bulk-edit?listing_ids=${listing.id}`}
                className="text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg">
                Quick Bulk Edit
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Product Overview */}
        <Card title="Product Overview">
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Field label="State" value={listing.state} />
            <Field label="Price" value={formatPrice(listing.price_amount, listing.price_divisor, listing.currency_code)} />
            <Field label="Quantity" value={listing.quantity} />
            <Field label="SKU" value={listing.sku} />
            <Field label="Has Variations" value={yesNo(listing.has_variations)} />
            <Field label="Personalizable" value={yesNo(listing.is_personalizable)} />
            <Field label="Customizable" value={yesNo(listing.is_customizable)} />
            <Field label="Who Made" value={listing.who_made} />
            <Field label="Taxonomy ID" value={listing.taxonomy_id} />
            <Field label="Section ID" value={listing.section_id} />
            <Field label="Last Synced" value={listing.last_synced_at ? new Date(listing.last_synced_at).toLocaleString() : "Never"} />
            <Field label="Etsy Updated" value={listing.etsy_updated_at ? new Date(listing.etsy_updated_at).toLocaleString() : "—"} />
          </div>
        </Card>

        {/* Title */}
        <Card title="Title">
          <p className="text-gray-800 text-sm">{title}</p>
          <p className="text-xs text-gray-400">{listing.title?.length ?? 0} characters</p>
          <BulkEditLink listingId={listing.id}>Edit title in Bulk Edit →</BulkEditLink>
        </Card>

        {/* Description */}
        <Card title="Description">
          {description ? (
            <>
              <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{description}</p>
              <p className="text-xs text-gray-400">{description.length} characters</p>
            </>
          ) : (
            <p className="text-sm text-gray-400">No description synced.</p>
          )}
          <BulkEditLink listingId={listing.id}>Edit description in Bulk Edit →</BulkEditLink>
        </Card>

        {/* Tags */}
        <Card title="Tags">
          <p className="text-xs text-gray-400">{tags.length}/13</p>
          {tags.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {tags.map((t, i) => (
                <span key={i} className="bg-indigo-50 text-indigo-700 text-xs px-2 py-0.5 rounded-full">{decodeEntities(t)}</span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              No tags synced — this listing is missing all 13 tag slots.
            </p>
          )}
          <BulkEditLink listingId={listing.id}>Edit tags in Bulk Edit →</BulkEditLink>
        </Card>

        {/* Materials */}
        <Card title="Materials">
          {materials.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {materials.map((m, i) => (
                <span key={i} className="bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full">{decodeEntities(m)}</span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">Not synced / unavailable.</p>
          )}
        </Card>

        {/* Price & Inventory */}
        <Card title="Price & Inventory">
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Field label="Price" value={formatPrice(listing.price_amount, listing.price_divisor, listing.currency_code)} />
            <Field label="Quantity" value={listing.quantity} />
            <Field label="Has Variations" value={yesNo(listing.has_variations)} />
          </div>
          {listing.has_variations && (
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              This listing has variations. Price/quantity writes use Etsy inventory-specific handling and are managed through Bulk Edit/Variations workflows.
            </p>
          )}
          <div className="flex gap-4">
            <BulkEditLink listingId={listing.id}>Edit price in Bulk Edit →</BulkEditLink>
            <BulkEditLink listingId={listing.id}>Edit quantity in Bulk Edit →</BulkEditLink>
          </div>
        </Card>

        {/* Media */}
        <Card title="Media">
          {listing.thumbnail_url ? (
            <img src={listing.thumbnail_url} alt={title} className="w-24 h-24 object-cover rounded-lg border border-gray-100" />
          ) : (
            <div className="w-24 h-24 bg-gray-100 rounded-lg border border-gray-100" />
          )}
          <p className="text-xs text-gray-400">
            {images.length > 0 ? `${images.length} photo${images.length === 1 ? "" : "s"} synced` : "Photo count unavailable."}
          </p>
          <p className="text-xs text-gray-400">Full image gallery is not available yet — only the primary thumbnail is shown.</p>
          <Link href="/media" className="inline-block text-xs font-medium text-indigo-600 hover:text-indigo-800 hover:underline">
            Open Media tools →
          </Link>
        </Card>

        {/* Health / Improvement */}
        <Card title="Listing Health">
          <p className="text-sm text-gray-400">Listing Health details are coming in UX-01C.</p>
          <div className="flex gap-4">
            <Link href="/listing-health" className="text-xs font-medium text-indigo-600 hover:text-indigo-800 hover:underline">
              View in Listing Health →
            </Link>
            <BulkEditLink listingId={listing.id}>Fix in Bulk Edit →</BulkEditLink>
          </div>
        </Card>
      </div>

      {/* Safe Actions */}
      <Card title="Safe Actions">
        <p className="text-xs text-gray-500">
          Actions open existing safe workflows. Direct single-field edits from this page will be added after credit/plan/write-surface design.
        </p>
        <div className="flex flex-wrap gap-x-6 gap-y-2 pt-1">
          <BulkEditLink listingId={listing.id}>Edit title in Bulk Edit →</BulkEditLink>
          <BulkEditLink listingId={listing.id}>Edit description in Bulk Edit →</BulkEditLink>
          <BulkEditLink listingId={listing.id}>Edit tags in Bulk Edit →</BulkEditLink>
          <BulkEditLink listingId={listing.id}>Edit price in Bulk Edit →</BulkEditLink>
          <BulkEditLink listingId={listing.id}>Edit quantity in Bulk Edit →</BulkEditLink>
          <Link href="/listing-health" className="text-xs font-medium text-indigo-600 hover:text-indigo-800 hover:underline">
            Open Listing Health →
          </Link>
          {listing.url && (
            <a href={listing.url} target="_blank" rel="noopener noreferrer"
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 hover:underline">
              View on Etsy →
            </a>
          )}
        </div>
      </Card>
    </main>
  );
}
