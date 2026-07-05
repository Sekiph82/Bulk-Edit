"use client";

import FadeUp from "./FadeUp";

const PAINS = [
  { icon: "🔁", title: "One-by-one editing", desc: "Opening the same edit form hundreds of times to change a tag, a price, a title." },
  { icon: "🏷️", title: "Inconsistent tags & titles", desc: "SEO drifts over time as different fixes get applied to different listings." },
  { icon: "💲", title: "Pricing mistakes", desc: "Fee changes or cost increases mean margins quietly erode across the shop." },
  { icon: "🖼️", title: "Photo cleanup", desc: "Seasonal photo refreshes mean touching every listing, one at a time." },
  { icon: "🧵", title: "Variation chaos", desc: "Size, color, and material variations multiply the number of fields to manage." },
  { icon: "⚠️", title: "Fear of irreversible changes", desc: "One bad bulk change with no undo can mean hours of manual repair." },
];

export default function SellerPainGrid() {
  return (
    <section className="py-20 px-6 sm:px-8 be-section-accent">
      <div className="max-w-5xl mx-auto">
        <FadeUp className="text-center mb-12">
          <span className="inline-block text-xs font-semibold text-red-600 tracking-widest uppercase mb-4 bg-red-50 px-3 py-1 rounded-full border border-red-100">
            The problem
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">
            Editing Etsy listings one by one doesn&apos;t scale
          </h2>
          <p className="text-gray-500 max-w-xl mx-auto">
            The more your shop grows, the more these small frictions cost you every week.
          </p>
        </FadeUp>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {PAINS.map((p, i) => (
            <FadeUp key={p.title} delay={i * 0.05}>
              <div className="be-card p-6 h-full">
                <div className="text-2xl mb-3" role="img" aria-label={p.title}>{p.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{p.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{p.desc}</p>
              </div>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  );
}
