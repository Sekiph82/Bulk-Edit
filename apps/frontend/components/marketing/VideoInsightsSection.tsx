"use client";

import Link from "next/link";
import FadeUp from "./FadeUp";

export default function VideoInsightsSection() {
  return (
    <section className="py-20 px-6 sm:px-8 bg-white">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
        <FadeUp>
          <div className="be-card p-7 h-full flex flex-col">
            <div className="text-3xl mb-3" role="img" aria-label="Product Video Generator">🎬</div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Product Video Generator</h3>
            <p className="text-sm text-gray-600 leading-relaxed mb-4 flex-1">
              Generate a real MP4 product video from your listing photos, sized to Etsy&apos;s
              video specs (9:16, 1:1, 4:5, 16:9). Preview it, then download it directly.
            </p>
            <p className="text-xs text-gray-400 mb-4">
              You add the downloaded video to your listing yourself through Etsy&apos;s own editor —
              there&apos;s no automatic Etsy video upload.
            </p>
            <Link href="/features/product-video-generator" className="text-sm font-medium text-indigo-600 hover:underline">
              See Product Video Generator →
            </Link>
          </div>
        </FadeUp>
        <FadeUp delay={0.08}>
          <div className="be-card p-7 h-full flex flex-col">
            <div className="text-3xl mb-3" role="img" aria-label="Shop Insights">📊</div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Shop Insights</h3>
            <p className="text-sm text-gray-600 leading-relaxed mb-4 flex-1">
              See real numbers from your connected, synced shop: total listings, status breakdown,
              how many listings are missing tags or photos, and your price range.
            </p>
            <p className="text-xs text-gray-400 mb-4">
              Based only on your synced listing data — no revenue, views, or favourites analytics.
            </p>
            <Link href="/features/shop-insights" className="text-sm font-medium text-indigo-600 hover:underline">
              See Shop Insights →
            </Link>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}
