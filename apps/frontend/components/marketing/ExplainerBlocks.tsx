"use client";

import FadeUp from "./FadeUp";

// Concise, direct-answer blocks written for both human skimmers and AI
// search/answer engines, which tend to extract short structured answers
// rather than long marketing prose. Every claim here must stay truthful.
const BLOCKS = [
  {
    title: "What Bulk Edit App does",
    body: "Bulk Edit App lets Etsy sellers update titles, tags, descriptions, prices, photos, and variations across many listings at once — with a full preview before anything is applied.",
  },
  {
    title: "Who it is for",
    body: "Etsy shop owners and listing managers with more than a handful of listings — handmade, vintage, and digital product sellers who are spending too much time editing listings one at a time.",
  },
  {
    title: "What you can bulk edit",
    body: "Titles, tags, descriptions, prices, photos, and variation prices/quantities/SKUs — plus CSV import/export, AI-generated suggestions, and rule-based pricing recommendations.",
  },
  {
    title: "What stays under your control",
    body: "Every bulk change is previewed before it's applied, requires your explicit confirmation, and is backed by an automatic snapshot you can revert with Magic Revert.",
  },
  {
    title: "What Bulk Edit App does not do",
    body: "It does not auto-post to social media, upload videos directly to Etsy, or publish any change without your confirmation. It does not show revenue, views, or favourites analytics.",
  },
];

export default function ExplainerBlocks() {
  return (
    <section className="py-16 px-6 sm:px-8 bg-white border-t border-gray-100">
      <div className="max-w-4xl mx-auto">
        <FadeUp>
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            Bulk Edit App, in plain terms
          </h2>
        </FadeUp>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {BLOCKS.map((b, i) => (
            <FadeUp key={b.title} delay={i * 0.05} className={i === BLOCKS.length - 1 ? "sm:col-span-2" : ""}>
              <div className="be-card p-5 h-full">
                <h3 className="font-semibold text-gray-900 mb-2 text-sm">{b.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{b.body}</p>
              </div>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  );
}
