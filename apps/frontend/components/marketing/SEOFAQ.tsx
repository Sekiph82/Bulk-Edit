"use client";

import FadeUp from "./FadeUp";

export type FaqItem = { q: string; a: string };

// Renders an FAQ section AND its FAQPage JSON-LD from the same data, so the
// visible copy and the structured data can never drift apart. Only render
// this once per page — Google penalizes duplicate FAQPage schema.
export default function SEOFAQ({
  items,
  title = "Frequently asked questions",
  columns = 2,
}: {
  items: FaqItem[];
  title?: string;
  columns?: 1 | 2;
}) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.q,
      acceptedAnswer: { "@type": "Answer", text: item.a },
    })),
  };

  return (
    <section className="py-20 px-6 sm:px-8 be-section-accent">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <div className="max-w-4xl mx-auto">
        <FadeUp className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">{title}</h2>
        </FadeUp>
        <div className={`grid grid-cols-1 ${columns === 2 ? "sm:grid-cols-2" : ""} gap-5`}>
          {items.map((item, i) => (
            <FadeUp key={item.q} delay={i * 0.04}>
              <div className="be-card p-5">
                <h3 className="font-semibold text-gray-900 mb-2 text-sm">{item.q}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{item.a}</p>
              </div>
            </FadeUp>
          ))}
        </div>
      </div>
    </section>
  );
}
