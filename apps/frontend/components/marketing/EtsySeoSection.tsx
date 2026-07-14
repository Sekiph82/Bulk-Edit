"use client";

import FadeUp from "./FadeUp";
import AnimatedTagCloud from "./AnimatedTagCloud";

// Listing Health Score and AI Listing Optimization are real, shipped,
// in-app features (post-login only) — but public marketing claims about
// Etsy-derived scoring/AI-suggestion features are paused pending Etsy's
// written confirmation that they're permitted. See ETSY_SUPPORT_QUESTIONS.md
// Q1/Q2. This section only promotes the bulk-editing mechanics, which do
// not require that clarification.
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
              Edit titles, tags, and descriptions across your whole catalog at once, with a full
              before/after preview and explicit confirmation before anything reaches Etsy.
            </p>
            <ul className="space-y-2 text-sm text-gray-600 mb-6">
              <li>• Bulk-edit titles, tags, and descriptions across many listings at once</li>
              <li>• Bulk-apply cleanup across your whole catalog at once</li>
              <li>• Every change previewed and confirmed — nothing automatic</li>
            </ul>
          </div>
        </FadeUp>
        <FadeUp delay={0.1}>
          <div className="be-card p-8 flex flex-col items-center gap-8">
            <AnimatedTagCloud />
          </div>
        </FadeUp>
      </div>
    </section>
  );
}
