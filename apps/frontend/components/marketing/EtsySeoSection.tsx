"use client";

import Link from "next/link";
import FadeUp from "./FadeUp";
import AnimatedTagCloud from "./AnimatedTagCloud";
import HealthScoreGauge from "./HealthScoreGauge";

export default function EtsySeoSection() {
  return (
    <section className="py-20 px-6 sm:px-8 be-section-accent">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-14 items-center">
        <FadeUp>
          <div>
            <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
              Etsy SEO, at scale
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
              Fix the titles, tags, and descriptions holding your listings back
            </h2>
            <p className="text-gray-500 leading-relaxed mb-5">
              Listing Health Score finds the specific, fixable issues — weak titles, missing tags,
              thin descriptions, low photo counts — and grades every listing 0–100. AI Listing
              Optimization then generates title, description, tag, and alt text suggestions you
              review and approve before anything changes.
            </p>
            <ul className="space-y-2 text-sm text-gray-600 mb-6">
              <li>• Score every listing 0–100 with specific, prioritized fixes</li>
              <li>• AI-generated title, tag, and description suggestions</li>
              <li>• Bulk-apply cleanup across your whole catalog at once</li>
              <li>• Every suggestion previewed and approved — nothing automatic</li>
            </ul>
            <div className="flex flex-wrap gap-3">
              <Link href="/features/listing-health-score" className="text-sm font-medium text-indigo-600 hover:underline">
                Listing Health Score →
              </Link>
              <Link href="/features/ai-listing-optimization" className="text-sm font-medium text-indigo-600 hover:underline">
                AI Listing Optimization →
              </Link>
            </div>
          </div>
        </FadeUp>
        <FadeUp delay={0.1}>
          <div className="be-card p-8 flex flex-col items-center gap-8">
            <div className="flex gap-6">
              <HealthScoreGauge score={92} label="Excellent listing" />
              <HealthScoreGauge score={54} label="Needs work" />
            </div>
            <AnimatedTagCloud />
          </div>
        </FadeUp>
      </div>
    </section>
  );
}
