"use client";

import Link from "next/link";
import FadeUp from "./FadeUp";

type ToolCard = { title: string; href: string; copy: string; icon: string };

// Every claim here matches lib/featurePages.ts exactly — no unsupported
// claims (no direct Etsy video upload as a public promise, no auto-posting,
// no revenue/views/favorites analytics).
const TOOLS: ToolCard[] = [
  { title: "Product Video Generator", href: "/features/product-video-generator", copy: "Generate MP4 product videos from listing photos, preview and download.", icon: "🎬" },
  { title: "Shop Insights", href: "/features/shop-insights", copy: "Review connected, synced listing data — status, tag/photo coverage, and price ranges.", icon: "📊" },
  { title: "Magic Revert", href: "/features/magic-revert", copy: "Roll back supported bulk changes using automatic change history.", icon: "↩️" },
  { title: "Photo Bulk Editing", href: "/features/photo-bulk-editing", copy: "Bulk add, replace, and delete listing photos through the preview-first workflow.", icon: "🖼️" },
  { title: "Etsy CSV Import/Export", href: "/features/etsy-csv-import-export", copy: "Export listings to CSV, edit offline, import changes back as a draft bulk edit.", icon: "📋" },
  { title: "AI Listing Optimization", href: "/features/ai-listing-optimization", copy: "AI-generated title, description, tag, and alt text suggestions — you approve each one.", icon: "✨" },
  { title: "Listing Health Score", href: "/features/listing-health-score", copy: "Score every listing 0–100 and find the specific issues most likely costing you sales.", icon: "🩺" },
  { title: "Profit Calculator", href: "/features/profit-calculator", copy: "See true net profit after Etsy fees, shipping, and ad costs.", icon: "💰" },
  { title: "Dynamic Pricing", href: "/features/dynamic-pricing", copy: "Rule-based price recommendations you review and approve before anything changes.", icon: "📈" },
  { title: "Bulk Tag Editor", href: "/features/bulk-tag-editor", copy: "Add, remove, or replace tags across listings in one operation, fully previewed.", icon: "🏷️" },
  { title: "Bulk Listing Editor", href: "/features/bulk-listing-editor", copy: "Update titles, tags, prices, and descriptions across hundreds of listings at once.", icon: "⚡" },
  { title: "Variation Editor", href: "/features/variation-editor", copy: "Bulk-adjust prices, quantities, and SKUs across listing variations.", icon: "🔀" },
  { title: "Safe Preview Engine", href: "/features/safe-preview-engine", copy: "Every bulk edit shows a full before/after diff before anything touches Etsy.", icon: "🔍" },
  { title: "Backup Snapshots", href: "/features/backup-snapshots", copy: "Automatic pre-write snapshots capture each listing's state before any change.", icon: "🛡️" },
  { title: "Social Promote", href: "/features/social-promote", copy: "Generate Pinterest and Instagram captions and images from your listings — you decide when to post.", icon: "📣" },
  { title: "Scheduled Jobs", href: "/features/scheduled-jobs", copy: "Schedule safe syncs and draft creation — nothing publishes without your approval.", icon: "⏰" },
];

export default function AllToolsControlRoom() {
  return (
    <section className="py-20 px-6 sm:px-8 bg-white">
      <div className="max-w-7xl mx-auto">
        <FadeUp className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            All Etsy seller tools in one control room
          </h2>
          <p className="text-gray-500 max-w-xl mx-auto">
            Sixteen tools, one safe editing engine underneath every one of them.
          </p>
        </FadeUp>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {TOOLS.map((tool, i) => (
            <FadeUp key={tool.href} delay={i * 0.02}>
              <Link
                href={tool.href}
                className="be-card p-5 h-full flex flex-col hover:border-indigo-300 transition-colors block hover:no-underline"
              >
                <div className="text-2xl mb-2" role="img" aria-label={tool.title}>{tool.icon}</div>
                <h3 className="font-semibold text-gray-900 text-sm mb-1.5">{tool.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed flex-1">{tool.copy}</p>
                <span className="text-xs font-medium text-indigo-600 mt-3">
                  See {tool.title} →
                </span>
              </Link>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  );
}
