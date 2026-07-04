// Content for dedicated SEO feature landing pages (/features/[slug]).
// Every claim here must match real, shipped behavior — see the code
// references in each entry's `_verifiedAgainst` comment trail during
// review. No invented ratings, reviews, testimonials, or usage stats.

export type FeaturePage = {
  slug: string;
  metaTitle: string;
  metaDescription: string;
  h1: string;
  intro: string;
  howItWorks: string[];
  boundaries?: string[]; // what it explicitly does NOT do — keeps claims honest
  safetyNote?: string;
  related: string[]; // slugs
};

export const FEATURE_PAGES: FeaturePage[] = [
  {
    slug: "product-video-generator",
    metaTitle: "Product Video Generator for Etsy Listings — Bulk-Edit",
    metaDescription:
      "Generate real MP4 product videos from your Etsy listing photos. Preview and download instantly — no Etsy auto-upload, you stay in control.",
    h1: "Product Video Generator",
    intro:
      "Turn a set of listing photos into a short, real MP4 product video — rendered with ffmpeg, not a mockup. Preview it, download it, and use it however you like.",
    howItWorks: [
      "Select a template and the listing photos you want to include.",
      "Choose an aspect ratio (9:16, 1:1, 4:5, or 16:9) sized to Etsy's video specs.",
      "Bulk-Edit renders a real MP4 slideshow video in the background.",
      "Preview the finished video and download it directly.",
    ],
    boundaries: [
      "Etsy auto-upload is not supported — you download the file and add it to your listing yourself through Etsy's own editor.",
      "Bulk video replace/delete directly on Etsy listings is not supported.",
    ],
    related: ["photo-bulk-editing", "social-promote"],
  },
  {
    slug: "shop-insights",
    metaTitle: "Shop Insights for Etsy Sellers — Bulk-Edit",
    metaDescription:
      "See real data from your connected, synced Etsy shop: listing counts, status breakdown, tag and photo coverage gaps, and price range.",
    h1: "Shop Insights",
    intro:
      "Shop Insights summarizes what's actually known about your connected Etsy shop, computed directly from your synced listing data — not invented analytics.",
    howItWorks: [
      "Connect your Etsy shop and let Bulk-Edit sync your listings.",
      "Open Shop Insights to see total listings and a breakdown by status (active, draft, and so on).",
      "See how many listings are missing tags or have low photo counts.",
      "See your price range (minimum, maximum, average) and when your shop last synced.",
    ],
    boundaries: [
      "Revenue, views, and favourites trend data are not shown — Etsy doesn't expose reliable trend data through this app's connection, and we won't fake it.",
    ],
    related: ["listing-health-score", "profit-calculator"],
  },
  {
    slug: "magic-revert",
    metaTitle: "Magic Revert — Undo Bulk Etsy Listing Changes — Bulk-Edit",
    metaDescription:
      "Restore any Etsy listing to its exact pre-edit state with one click. Every bulk edit is backed by an automatic snapshot before it's applied.",
    h1: "Magic Revert",
    intro:
      "Made a mistake in a bulk edit? Magic Revert restores any listing to its exact state from before the change — using the automatic backup snapshot created at apply time.",
    howItWorks: [
      "Every bulk edit apply automatically creates a pre-write snapshot of each affected listing.",
      "If a change doesn't look right, open the listing's change history.",
      "Choose Magic Revert to restore the listing to its pre-edit snapshot.",
      "Revert only works where a snapshot/change history exists for that listing.",
    ],
    safetyNote: "This is the core safety net behind every bulk edit — you're never locked into a change.",
    related: ["backup-snapshots", "safe-preview-engine"],
  },
  {
    slug: "photo-bulk-editing",
    metaTitle: "Bulk Edit Etsy Listing Photos — Bulk-Edit",
    metaDescription:
      "Add, replace, or delete Etsy listing photos in bulk, with a preview before anything is published.",
    h1: "Photo Bulk Editor",
    intro:
      "Update listing photos across many Etsy listings at once — add new photos, replace existing ones, or remove photos you no longer want, all previewed before publishing.",
    howItWorks: [
      "Select the listings whose photos you want to update.",
      "Choose to add, replace, or delete a photo.",
      "Preview the change before it's applied.",
      "Confirm to apply — a backup snapshot is taken first.",
    ],
    boundaries: [
      "Photo reorder is not supported — Etsy's API has no atomic reorder endpoint, and a delete-and-reupload workaround would be too destructive.",
      "Etsy video upload/replace/delete is not supported through this feature.",
    ],
    related: ["product-video-generator", "bulk-listing-editor"],
  },
  {
    slug: "etsy-csv-import-export",
    metaTitle: "Etsy CSV Import & Export — Bulk-Edit",
    metaDescription:
      "Export your Etsy listings to CSV, edit them in any spreadsheet tool, and import changes back as a draft bulk edit session with full preview.",
    h1: "Etsy CSV Import / Export",
    intro:
      "Prefer working in a spreadsheet? Export your listings to CSV, make your changes there, and bring them back into Bulk-Edit safely.",
    howItWorks: [
      "Export your listings to a CSV file.",
      "Edit titles, tags, prices, or descriptions in any spreadsheet tool.",
      "Import the edited CSV back into Bulk-Edit.",
      "The import creates a draft bulk edit session — reviewed and previewed like any other bulk edit before you apply it.",
    ],
    related: ["bulk-listing-editor", "safe-preview-engine"],
  },
  {
    slug: "ai-listing-optimization",
    metaTitle: "AI Listing Optimization for Etsy — Bulk-Edit",
    metaDescription:
      "Generate AI-powered title, description, tag, and alt text suggestions for your Etsy listings. Review every suggestion before it's applied.",
    h1: "AI Listing Optimization",
    intro:
      "Get AI-generated suggestions for listing titles, descriptions, tags, and photo alt text — then decide which ones to use.",
    howItWorks: [
      "Start an AI session on the listings you want to improve.",
      "Bulk-Edit generates suggestions for title, description, tags, and alt text.",
      "Review each suggestion individually — accept or reject.",
      "Accepted suggestions convert into a draft bulk edit session, previewed and confirmed like any other change.",
    ],
    boundaries: ["Nothing is published automatically — every suggestion goes through the same preview-and-confirm workflow as a manual edit."],
    related: ["listing-health-score", "bulk-listing-editor"],
  },
  {
    slug: "listing-health-score",
    metaTitle: "Etsy Listing Health Score — Bulk-Edit",
    metaDescription:
      "Score every Etsy listing 0–100 and find missing tags, weak titles, thin descriptions, and low photo counts before they cost you sales.",
    h1: "Listing Health Score",
    intro:
      "A rule-based health score for every listing — surfacing the specific, fixable issues that are most likely holding a listing back.",
    howItWorks: [
      "Bulk-Edit scores each listing from 0–100 based on title length, tag count, description depth, and photo count.",
      "Listings are graded (excellent, good, needs work, critical) and given a priority.",
      "Each issue lists a specific, recommended fix.",
      "Fix issues manually, or route them into a bulk edit / AI optimization session.",
    ],
    boundaries: ["This is a rule-based internal score, not a guarantee of Etsy or Google search ranking."],
    related: ["ai-listing-optimization", "bulk-listing-editor"],
  },
  {
    slug: "profit-calculator",
    metaTitle: "Etsy Profit & Cost Calculator — Bulk-Edit",
    metaDescription:
      "Track product cost, Etsy fees, shipping, and ad costs to see real net profit and margin per listing.",
    h1: "Profit & Cost Calculator",
    intro:
      "See what a listing actually earns after Etsy's transaction and payment fees, shipping, and optional ad costs — not just its sticker price.",
    howItWorks: [
      "Enter your product cost and any shipping cost for a listing.",
      "Bulk-Edit calculates Etsy's transaction fee, payment processing fee, listing fee, and optional Offsite Ads fee.",
      "See gross revenue, net profit, margin percentage, and a recommended minimum price.",
      "Save cost profiles to reuse across similar listings.",
    ],
    boundaries: ["This is a cost/margin estimate tool, not accounting, bookkeeping, or tax advice."],
    related: ["dynamic-pricing", "shop-insights"],
  },
  {
    slug: "dynamic-pricing",
    metaTitle: "Dynamic Pricing Rules for Etsy — Bulk-Edit",
    metaDescription:
      "Build rule-based Etsy price recommendations. Review and approve every recommendation before any price changes — nothing is automatic.",
    h1: "Dynamic Pricing",
    intro:
      "Define pricing rules once, and let Bulk-Edit generate price recommendations across matching listings — you decide which ones to apply.",
    howItWorks: [
      "Build a pricing rule (percentage adjustment, fixed amount, set price, or reference price) with margin/price floors and rounding.",
      "Bulk-Edit generates a recommendation for each matching listing.",
      "Review each recommendation individually — accept or reject.",
      "Accepted recommendations convert into a draft bulk edit session for preview and confirmation.",
    ],
    boundaries: ["Prices never change automatically — every recommendation requires your explicit approval."],
    related: ["profit-calculator", "bulk-listing-editor"],
  },
  {
    slug: "bulk-tag-editor",
    metaTitle: "Bulk Edit Etsy Listing Tags — Bulk-Edit",
    metaDescription:
      "Add, remove, or replace Etsy listing tags in bulk, with full preview and one-click revert.",
    h1: "Bulk Tag Editor",
    intro:
      "Update tags across many Etsy listings at once — part of the same safe bulk edit engine used for titles, prices, and descriptions.",
    howItWorks: [
      "Select the listings whose tags you want to update.",
      "Add, remove, or replace tags across all selected listings in one operation.",
      "Preview the exact tag changes per listing before anything is applied.",
      "Confirm to apply — a backup snapshot is taken first, so you can revert with Magic Revert if needed.",
    ],
    related: ["bulk-listing-editor", "magic-revert"],
  },
  {
    slug: "bulk-listing-editor",
    metaTitle: "Bulk Listing Editor for Etsy Sellers — Bulk-Edit",
    metaDescription:
      "Update titles, tags, prices, descriptions, and more across hundreds of Etsy listings in one operation, with full preview before anything is applied.",
    h1: "Bulk Listing Editor",
    intro:
      "The core of Bulk-Edit: select listings, define a change once, and apply it across your whole shop — titles, tags, prices, descriptions, and more.",
    howItWorks: [
      "Select the listings you want to update — by search, filter, or from Listing Health.",
      "Define your bulk change: title, tags, price, description, or other supported fields.",
      "Review a full before/after diff for every affected listing.",
      "Confirm to apply — snapshots are taken automatically before any Etsy write.",
    ],
    related: ["safe-preview-engine", "backup-snapshots", "bulk-tag-editor"],
  },
  {
    slug: "variation-editor",
    metaTitle: "Bulk Edit Etsy Listing Variations — Bulk-Edit",
    metaDescription:
      "Bulk-adjust prices, quantities, and SKUs across Etsy listing variations, with per-variation preview before applying.",
    h1: "Variation Editor",
    intro:
      "Update prices, quantities, and SKUs across variation listings in bulk — with a per-variation diff so you can see exactly what changes.",
    howItWorks: [
      "Select variation listings you want to update.",
      "Define your change — price, quantity, or SKU adjustments.",
      "Review a per-variation preview showing exactly what will change.",
      "Confirm to apply — backup snapshots are taken first.",
    ],
    related: ["bulk-listing-editor", "safe-preview-engine"],
  },
  {
    slug: "safe-preview-engine",
    metaTitle: "Safe Preview Engine — Preview Etsy Bulk Edits — Bulk-Edit",
    metaDescription:
      "Every bulk edit is previewed with a full before/after diff before anything touches your Etsy shop.",
    h1: "Safe Preview Engine",
    intro:
      "No blind writes. Every bulk edit — no matter which feature created it — goes through the same preview step before it's ever sent to Etsy.",
    howItWorks: [
      "Build a bulk edit from any Bulk-Edit feature (listing editor, AI suggestions, CSV import, dynamic pricing).",
      "Bulk-Edit generates a full before/after diff for every affected listing.",
      "Review the diff listing by listing, field by field.",
      "Only after you confirm does anything get written to Etsy.",
    ],
    related: ["bulk-listing-editor", "backup-snapshots", "magic-revert"],
  },
  {
    slug: "backup-snapshots",
    metaTitle: "Automatic Backup Snapshots for Etsy Listings — Bulk-Edit",
    metaDescription:
      "Every bulk edit apply creates an automatic pre-write snapshot of each listing, powering safe restore and revert.",
    h1: "Backup Snapshots",
    intro:
      "Before any bulk edit touches your Etsy shop, Bulk-Edit captures the full pre-change state of each affected listing.",
    howItWorks: [
      "When you confirm a bulk edit apply, Bulk-Edit takes a snapshot of each listing first.",
      "The snapshot captures the listing's full state before the change.",
      "Snapshots are never deleted — they remain available for Magic Revert.",
      "If a change doesn't work out, restore from the snapshot with one click.",
    ],
    related: ["magic-revert", "safe-preview-engine"],
  },
  {
    slug: "social-promote",
    metaTitle: "Social Promote — Pinterest & Instagram Captions for Etsy — Bulk-Edit",
    metaDescription:
      "Generate Pinterest and Instagram captions and images from your Etsy listings. Copy, download, or share when ready — never posted automatically.",
    h1: "Social Promote",
    intro:
      "Turn a listing into a ready-to-share social post — Bulk-Edit prepares the caption and image, you decide when and where to post it.",
    howItWorks: [
      "Connect your Pinterest or Instagram account.",
      "Choose a listing to promote.",
      "Bulk-Edit generates a caption and prepares the image.",
      "Copy the caption, download the image, or share when you're ready.",
    ],
    boundaries: ["Nothing is posted automatically to Pinterest or Instagram — every share is a deliberate, manual action."],
    related: ["product-video-generator"],
  },
  {
    slug: "scheduled-jobs",
    metaTitle: "Scheduled Sync & Draft Jobs for Etsy — Bulk-Edit",
    metaDescription:
      "Schedule safe Etsy syncs and draft creation jobs. Jobs never auto-publish to Etsy — your approval is always required.",
    h1: "Scheduled Jobs",
    intro:
      "Automate the safe parts of your workflow — syncing listing data and preparing drafts — without ever giving up control over what gets published.",
    howItWorks: [
      "Schedule a sync job to keep your listing data up to date automatically.",
      "Schedule draft-creation jobs from CSV imports, AI sessions, or dynamic pricing rules.",
      "Jobs run on schedule and prepare draft bulk edit sessions.",
      "Every draft still goes through the standard preview-and-confirm flow before anything reaches Etsy.",
    ],
    boundaries: ["Scheduled jobs never write to Etsy directly — they only sync data or prepare drafts for your review."],
    related: ["etsy-csv-import-export", "safe-preview-engine"],
  },
];

export function getFeaturePage(slug: string): FeaturePage | undefined {
  return FEATURE_PAGES.find((f) => f.slug === slug);
}
