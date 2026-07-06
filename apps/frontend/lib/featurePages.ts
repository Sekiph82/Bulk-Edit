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
  benefits: string[]; // concrete, truthful "why this helps" bullets
  bestFor: string; // one line describing the ideal user of this feature
  boundaries?: string[]; // what it explicitly does NOT do — keeps claims honest
  safetyNote?: string;
  related: string[]; // slugs
};

export const FEATURE_PAGES: FeaturePage[] = [
  {
    slug: "product-video-generator",
    metaTitle: "Product Video Generator for Etsy Listings — Bulk Edit App",
    metaDescription:
      "Generate real MP4 product videos from your Etsy listing photos. Preview and download instantly — no Etsy auto-upload, you stay in control.",
    h1: "Product Video Generator",
    intro:
      "Turn a set of listing photos into a short, real MP4 product video — rendered with ffmpeg, not a mockup. Preview it, download it, and use it however you like.",
    howItWorks: [
      "Select a template and the listing photos you want to include.",
      "Choose an aspect ratio (9:16, 1:1, 4:5, or 16:9) sized to Etsy's video specs.",
      "Bulk Edit App renders a real MP4 slideshow video in the background.",
      "Preview the finished video and download it directly.",
    ],
    benefits: [
      "Turns existing listing photos into a video in minutes",
      "Etsy-spec aspect ratios (9:16, 1:1, 4:5, 16:9)",
      "Preview before you download — no surprises",
      "No video editing software required",
    ],
    bestFor: "Sellers who want Etsy-ready product videos without hiring a videographer or learning video editing software.",
    boundaries: [
      "Etsy auto-upload is not supported — you download the file and add it to your listing yourself through Etsy's own editor.",
      "Bulk video replace/delete directly on Etsy listings is not supported.",
    ],
    related: ["photo-bulk-editing", "social-promote"],
  },
  {
    slug: "shop-insights",
    metaTitle: "Shop Insights for Etsy Sellers — Bulk Edit App",
    metaDescription:
      "See real data from your connected, synced Etsy shop: listing counts, status breakdown, tag and photo coverage gaps, and price range.",
    h1: "Shop Insights",
    intro:
      "Shop Insights summarizes what's actually known about your connected Etsy shop, computed directly from your synced listing data — not invented analytics.",
    howItWorks: [
      "Connect your Etsy shop and let Bulk Edit App sync your listings.",
      "Open Shop Insights to see total listings and a breakdown by status (active, draft, and so on).",
      "See how many listings are missing tags or have low photo counts.",
      "See your price range (minimum, maximum, average) and when your shop last synced.",
    ],
    benefits: [
      "Real counts from your own synced listings — nothing invented",
      "Spot listings missing tags or with too few photos in seconds",
      "See your price range and last sync time at a glance",
      "No manual spreadsheet auditing needed",
    ],
    bestFor: "Sellers who want a fast, honest snapshot of shop health without digging through Etsy's own dashboard.",
    boundaries: [
      "Revenue, views, and favourites trend data are not shown — Etsy doesn't expose reliable trend data through this app's connection, and we won't fake it.",
    ],
    related: ["listing-health-score", "profit-calculator"],
  },
  {
    slug: "magic-revert",
    metaTitle: "Magic Revert — Undo Bulk Etsy Listing Changes — Bulk Edit App",
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
    benefits: [
      "One-click restore to the exact pre-edit state",
      "Automatic snapshot before every bulk apply — no setup required",
      "Removes the fear of trying a bulk change",
      "Works listing-by-listing, not just as an all-or-nothing rollback",
    ],
    bestFor: "Sellers who want to bulk edit with confidence, knowing every change can be undone.",
    safetyNote: "This is the core safety net behind every bulk edit — you're never locked into a change.",
    related: ["backup-snapshots", "safe-preview-engine"],
  },
  {
    slug: "photo-bulk-editing",
    metaTitle: "Bulk Edit Etsy Listing Photos — Bulk Edit App",
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
    benefits: [
      "Add, replace, or delete photos across many listings in one pass",
      "Full preview before anything publishes",
      "Backup snapshot taken automatically before applying",
      "Pairs with Magic Revert if a photo change needs undoing",
    ],
    bestFor: "Sellers refreshing product photography or swapping seasonal images across many listings at once.",
    boundaries: [
      "Photo reorder is not supported — Etsy's API has no atomic reorder endpoint, and a delete-and-reupload workaround would be too destructive.",
      "Etsy video upload/replace/delete is not supported through this feature.",
    ],
    related: ["product-video-generator", "bulk-listing-editor"],
  },
  {
    slug: "etsy-csv-import-export",
    metaTitle: "Etsy CSV Import & Export — Bulk Edit App",
    metaDescription:
      "Export your Etsy listings to CSV, edit them in any spreadsheet tool, and import changes back as a draft bulk edit session with full preview.",
    h1: "Etsy CSV Import / Export",
    intro:
      "Prefer working in a spreadsheet? Export your listings to CSV, make your changes there, and bring them back into Bulk Edit App safely.",
    howItWorks: [
      "Export your listings to a CSV file.",
      "Edit titles, tags, prices, or descriptions in any spreadsheet tool.",
      "Import the edited CSV back into Bulk Edit App.",
      "The import creates a draft bulk edit session — reviewed and previewed like any other bulk edit before you apply it.",
    ],
    benefits: [
      "Work in the spreadsheet tool you already know",
      "Bulk-edit titles, tags, prices, and descriptions offline",
      "Re-import goes through the same preview-and-confirm safety flow",
      "No new interface to learn for large batch edits",
    ],
    bestFor: "Sellers who prefer spreadsheets, or need to edit hundreds of listings faster than a UI allows.",
    related: ["bulk-listing-editor", "safe-preview-engine"],
  },
  {
    slug: "ai-listing-optimization",
    metaTitle: "AI Listing Optimization for Etsy — Bulk Edit App",
    metaDescription:
      "Generate AI-powered title, description, tag, and alt text suggestions for your Etsy listings. Review every suggestion before it's applied.",
    h1: "AI Listing Optimization",
    intro:
      "Get AI-generated suggestions for listing titles, descriptions, tags, and photo alt text — then decide which ones to use.",
    howItWorks: [
      "Start an AI session on the listings you want to improve.",
      "Bulk Edit App generates suggestions for title, description, tags, and alt text.",
      "Review each suggestion individually — accept or reject.",
      "Accepted suggestions convert into a draft bulk edit session, previewed and confirmed like any other change.",
    ],
    benefits: [
      "AI-generated title, description, tag, and alt text suggestions",
      "Accept or reject each suggestion individually",
      "Nothing publishes automatically — same preview-and-confirm flow",
      "Speeds up SEO cleanup across many listings at once",
    ],
    bestFor: "Sellers who know their listings need better titles, tags, or descriptions but don't have time to rewrite them one by one.",
    boundaries: ["Nothing is published automatically — every suggestion goes through the same preview-and-confirm workflow as a manual edit."],
    related: ["listing-health-score", "bulk-listing-editor"],
  },
  {
    slug: "listing-health-score",
    metaTitle: "Etsy Listing Health Score — Bulk Edit App",
    metaDescription:
      "Score every Etsy listing 0–100 and find missing tags, weak titles, thin descriptions, and low photo counts before they cost you sales.",
    h1: "Listing Health Score",
    intro:
      "A rule-based health score for every listing — surfacing the specific, fixable issues that are most likely holding a listing back.",
    howItWorks: [
      "Bulk Edit App scores each listing from 0–100 based on title length, tag count, description depth, and photo count.",
      "Listings are graded (excellent, good, needs work, critical) and given a priority.",
      "Each issue lists a specific, recommended fix.",
      "Fix issues manually, or route them into a bulk edit / AI optimization session.",
    ],
    benefits: [
      "Instant 0–100 score for every listing",
      "Specific, fixable issues — not vague advice",
      "Prioritized list so you fix what matters most first",
      "Routes straight into bulk edit or AI optimization",
    ],
    bestFor: "Sellers with a large catalog who need to know exactly which listings to fix first.",
    boundaries: ["This is a rule-based internal score, not a guarantee of Etsy or Google search ranking."],
    related: ["ai-listing-optimization", "bulk-listing-editor"],
  },
  {
    slug: "profit-calculator",
    metaTitle: "Etsy Profit & Cost Calculator — Bulk Edit App",
    metaDescription:
      "Track product cost, Etsy fees, shipping, and ad costs to see real net profit and margin per listing.",
    h1: "Profit & Cost Calculator",
    intro:
      "See what a listing actually earns after Etsy's transaction and payment fees, shipping, and optional ad costs — not just its sticker price.",
    howItWorks: [
      "Enter your product cost and any shipping cost for a listing.",
      "Bulk Edit App calculates Etsy's transaction fee, payment processing fee, listing fee, and optional Offsite Ads fee.",
      "See gross revenue, net profit, margin percentage, and a recommended minimum price.",
      "Save cost profiles to reuse across similar listings.",
    ],
    benefits: [
      "See true net profit after Etsy fees, shipping, and ad costs",
      "Recommended minimum price to protect margin",
      "Reusable cost profiles for similar products",
      "No spreadsheet formulas to maintain",
    ],
    bestFor: "Sellers who suspect some listings are barely profitable — or losing money — after fees.",
    boundaries: ["This is a cost/margin estimate tool, not accounting, bookkeeping, or tax advice."],
    related: ["dynamic-pricing", "shop-insights"],
  },
  {
    slug: "dynamic-pricing",
    metaTitle: "Dynamic Pricing Rules for Etsy — Bulk Edit App",
    metaDescription:
      "Build rule-based Etsy price recommendations. Review and approve every recommendation before any price changes — nothing is automatic.",
    h1: "Dynamic Pricing",
    intro:
      "Define pricing rules once, and let Bulk Edit App generate price recommendations across matching listings — you decide which ones to apply.",
    howItWorks: [
      "Build a pricing rule (percentage adjustment, fixed amount, set price, or reference price) with margin/price floors and rounding.",
      "Bulk Edit App generates a recommendation for each matching listing.",
      "Review each recommendation individually — accept or reject.",
      "Accepted recommendations convert into a draft bulk edit session for preview and confirmation.",
    ],
    benefits: [
      "Rule-based price recommendations across matching listings",
      "Margin and price floors prevent underpricing",
      "Every recommendation reviewed individually before applying",
      "Saves hours versus manually repricing listing by listing",
    ],
    bestFor: "Sellers who want consistent, rule-based pricing without giving up manual approval.",
    boundaries: ["Prices never change automatically — every recommendation requires your explicit approval."],
    related: ["profit-calculator", "bulk-listing-editor"],
  },
  {
    slug: "bulk-tag-editor",
    metaTitle: "Bulk Edit Etsy Listing Tags — Bulk Edit App",
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
    benefits: [
      "Add, remove, or replace tags across listings in one operation",
      "Full per-listing preview before anything changes",
      "Backed by the same snapshot + Magic Revert safety net",
      "Faster than opening each listing's edit screen one at a time",
    ],
    bestFor: "Sellers standardizing seasonal tags, keywords, or SEO cleanup across their catalog.",
    related: ["bulk-listing-editor", "magic-revert"],
  },
  {
    slug: "bulk-listing-editor",
    metaTitle: "Bulk Listing Editor for Etsy Sellers — Bulk Edit App",
    metaDescription:
      "Update titles, tags, prices, descriptions, and more across hundreds of Etsy listings in one operation, with full preview before anything is applied.",
    h1: "Bulk Listing Editor",
    intro:
      "The core of Bulk Edit App: select listings, define a change once, and apply it across your whole shop — titles, tags, prices, descriptions, and more.",
    howItWorks: [
      "Select the listings you want to update — by search, filter, or from Listing Health.",
      "Define your bulk change: title, tags, price, description, or other supported fields.",
      "Review a full before/after diff for every affected listing.",
      "Confirm to apply — snapshots are taken automatically before any Etsy write.",
    ],
    benefits: [
      "One change, applied across hundreds of listings",
      "Full before/after diff for every affected listing",
      "Automatic snapshot before any Etsy write",
      "The same safe engine every other bulk tool in the app is built on",
    ],
    bestFor: "Sellers managing more listings than they can reasonably edit one at a time.",
    related: ["safe-preview-engine", "backup-snapshots", "bulk-tag-editor"],
  },
  {
    slug: "variation-editor",
    metaTitle: "Bulk Edit Etsy Listing Variations — Bulk Edit App",
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
    benefits: [
      "Bulk-adjust price, quantity, and SKU across variations",
      "Per-variation preview, not just per-listing",
      "Snapshot-backed, so mistakes are recoverable",
      "Handles variation complexity manual editing struggles with",
    ],
    bestFor: "Sellers with variation-heavy listings (size, color, material) who need consistent bulk updates.",
    related: ["bulk-listing-editor", "safe-preview-engine"],
  },
  {
    slug: "safe-preview-engine",
    metaTitle: "Safe Preview Engine — Preview Etsy Bulk Edits — Bulk Edit App",
    metaDescription:
      "Every bulk edit is previewed with a full before/after diff before anything touches your Etsy shop.",
    h1: "Safe Preview Engine",
    intro:
      "No blind writes. Every bulk edit — no matter which feature created it — goes through the same preview step before it's ever sent to Etsy.",
    howItWorks: [
      "Build a bulk edit from any Bulk Edit App feature (listing editor, AI suggestions, CSV import, dynamic pricing).",
      "Bulk Edit App generates a full before/after diff for every affected listing.",
      "Review the diff listing by listing, field by field.",
      "Only after you confirm does anything get written to Etsy.",
    ],
    benefits: [
      "Every bulk edit — from every feature — goes through one safety gate",
      "Full before/after diff, field by field",
      "No blind writes to Etsy, ever",
      "Confirms exactly what will change before it happens",
    ],
    bestFor: "Sellers who want the confidence of a safety net on every kind of bulk change, not just some.",
    related: ["bulk-listing-editor", "backup-snapshots", "magic-revert"],
  },
  {
    slug: "backup-snapshots",
    metaTitle: "Automatic Backup Snapshots for Etsy Listings — Bulk Edit App",
    metaDescription:
      "Every bulk edit apply creates an automatic pre-write snapshot of each listing, powering safe restore and revert.",
    h1: "Backup Snapshots",
    intro:
      "Before any bulk edit touches your Etsy shop, Bulk Edit App captures the full pre-change state of each affected listing.",
    howItWorks: [
      "When you confirm a bulk edit apply, Bulk Edit App takes a snapshot of each listing first.",
      "The snapshot captures the listing's full state before the change.",
      "Snapshots are never deleted — they remain available for Magic Revert.",
      "If a change doesn't work out, restore from the snapshot with one click.",
    ],
    benefits: [
      "Automatic — no setup or manual backup step required",
      "Captures full pre-change listing state",
      "Snapshots are never deleted",
      "Powers one-click Magic Revert",
    ],
    bestFor: "Sellers who want a safety net running quietly in the background on every bulk edit.",
    related: ["magic-revert", "safe-preview-engine"],
  },
  {
    slug: "social-promote",
    metaTitle: "Social Promote — Pinterest & Instagram Captions for Etsy — Bulk Edit App",
    metaDescription:
      "Generate Pinterest and Instagram captions and images from your Etsy listings. Copy, download, or share when ready — never posted automatically.",
    h1: "Social Promote",
    intro:
      "Turn a listing into a ready-to-share social post — Bulk Edit App prepares the caption and image, you decide when and where to post it.",
    howItWorks: [
      "Connect your Pinterest or Instagram account.",
      "Choose a listing to promote.",
      "Bulk Edit App generates a caption and prepares the image.",
      "Copy the caption, download the image, or share when you're ready.",
    ],
    benefits: [
      "AI-prepared captions and images from your listings",
      "Works for Pinterest and Instagram",
      "You control exactly when and where it's shared",
      "Saves time writing captions from scratch",
    ],
    bestFor: "Sellers who want to promote listings on social media without writing captions manually every time.",
    boundaries: ["Nothing is posted automatically to Pinterest or Instagram — every share is a deliberate, manual action."],
    related: ["product-video-generator"],
  },
  {
    slug: "scheduled-jobs",
    metaTitle: "Scheduled Sync & Draft Jobs for Etsy — Bulk Edit App",
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
    benefits: [
      "Keeps listing data automatically in sync",
      "Prepares drafts from CSV, AI, or pricing rules on a schedule",
      "Every draft still requires your explicit approval",
      "Removes manual, repetitive sync work",
    ],
    bestFor: "Sellers who want routine syncing and draft prep automated, without losing control over what gets published.",
    boundaries: ["Scheduled jobs never write to Etsy directly — they only sync data or prepare drafts for your review."],
    related: ["etsy-csv-import-export", "safe-preview-engine"],
  },
];

export function getFeaturePage(slug: string): FeaturePage | undefined {
  return FEATURE_PAGES.find((f) => f.slug === slug);
}

// Feature-cluster grouping used on the homepage and /features index —
// purely organizational, every slug here must exist in FEATURE_PAGES.
export const FEATURE_CLUSTERS: { title: string; description: string; slugs: string[] }[] = [
  {
    title: "Bulk Listing Control",
    description: "Update titles, tags, prices, descriptions, photos, and variations across your whole shop at once.",
    slugs: ["bulk-listing-editor", "bulk-tag-editor", "variation-editor", "etsy-csv-import-export"],
  },
  {
    title: "SEO & AI Optimization",
    description: "Find weak listings and generate better titles, tags, and descriptions — you approve every change.",
    slugs: ["listing-health-score", "ai-listing-optimization"],
  },
  {
    title: "Photo & Video Tools",
    description: "Refresh listing photos in bulk and generate real MP4 product videos from your existing images.",
    slugs: ["photo-bulk-editing", "product-video-generator", "social-promote"],
  },
  {
    title: "Pricing & Profit",
    description: "See true profit after fees and build rule-based pricing recommendations you control.",
    slugs: ["profit-calculator", "dynamic-pricing"],
  },
  {
    title: "Safety & Revert",
    description: "Every bulk edit is previewed, snapshotted, and reversible — nothing writes to Etsy blind.",
    slugs: ["safe-preview-engine", "backup-snapshots", "magic-revert"],
  },
  {
    title: "Shop Insights & Automation",
    description: "See real shop health from synced data, and schedule safe syncs and draft prep on autopilot.",
    slugs: ["shop-insights", "scheduled-jobs"],
  },
];
