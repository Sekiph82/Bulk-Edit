"use client";

import Link from "next/link";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import FadeUp from "@/components/marketing/FadeUp";
import FeaturePageHero from "@/components/marketing/FeaturePageHero";
import RelatedFeatureLinks from "@/components/marketing/RelatedFeatureLinks";
import ConversionCTA from "@/components/marketing/ConversionCTA";
import SEOFAQ, { type FaqItem } from "@/components/marketing/SEOFAQ";
import { FEATURE_PAGES, type FeaturePage } from "@/lib/featurePages";

// Generates 2-3 truthful, page-specific FAQ entries from data already
// verified against shipped behavior (intro/boundaries/safetyNote) — avoids
// hand-authoring 16 separate FAQ lists while keeping every answer accurate.
function buildFaq(feature: FeaturePage): FaqItem[] {
  const items: FaqItem[] = [
    {
      q: `Can I preview ${feature.h1.toLowerCase()} changes before they're applied?`,
      a: `Yes. ${feature.intro}`,
    },
  ];
  if (feature.boundaries) {
    for (const b of feature.boundaries) {
      items.push({ q: "What does this not do?", a: b });
    }
  }
  if (feature.safetyNote) {
    items.push({ q: "How does this stay safe?", a: feature.safetyNote });
  }
  items.push({
    q: `Who is ${feature.h1} best for?`,
    a: feature.bestFor,
  });
  return items;
}

export default function FeaturePageContent({ feature }: { feature: FeaturePage }) {
  const relatedPages = feature.related
    .map((slug) => FEATURE_PAGES.find((f) => f.slug === slug))
    .filter((f): f is FeaturePage => Boolean(f));

  const softwareApplicationJsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: `${feature.h1} — Bulk Edit App`,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    description: feature.metaDescription,
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
      description: "Free plan available",
    },
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareApplicationJsonLd) }}
      />
      <MarketingNav />

      {/* Breadcrumb */}
      <div className="max-w-4xl mx-auto px-6 sm:px-8 pt-6 text-sm text-gray-400">
        <Link href="/" className="hover:text-gray-600">Home</Link>
        <span className="mx-2">/</span>
        <Link href="/features" className="hover:text-gray-600">Features</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-600">{feature.h1}</span>
      </div>

      <FeaturePageHero h1={feature.h1} intro={feature.intro} bestFor={feature.bestFor} />

      {/* How it works */}
      <section className="py-16 px-6 sm:px-8 bg-white">
        <div className="max-w-4xl mx-auto">
          <FadeUp>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">How it works</h2>
          </FadeUp>
          <div className="space-y-4">
            {feature.howItWorks.map((step, i) => (
              <FadeUp key={step} delay={i * 0.05}>
                <div className="be-card p-5 flex items-start gap-4">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                    {i + 1}
                  </div>
                  <p className="text-sm text-gray-700 leading-relaxed pt-1">{step}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-16 px-6 sm:px-8 be-section-accent">
        <div className="max-w-4xl mx-auto">
          <FadeUp>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Why it helps</h2>
          </FadeUp>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {feature.benefits.map((b, i) => (
              <FadeUp key={b} delay={i * 0.05}>
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 w-5 h-5 rounded-full bg-green-100 border border-green-200 flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  </span>
                  <span className="text-sm text-gray-700 leading-relaxed">{b}</span>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* Boundaries / accurate claims */}
      {feature.boundaries && feature.boundaries.length > 0 && (
        <section className="py-12 px-6 sm:px-8 bg-white border-t border-gray-100">
          <div className="max-w-4xl mx-auto">
            <FadeUp>
              <h2 className="text-lg font-bold text-gray-900 mb-4">Good to know</h2>
              <ul className="space-y-2">
                {feature.boundaries.map((b) => (
                  <li key={b} className="flex items-start gap-3 text-sm text-gray-600">
                    <span className="mt-1 w-1.5 h-1.5 rounded-full bg-gray-400 flex-shrink-0" />
                    {b}
                  </li>
                ))}
              </ul>
            </FadeUp>
          </div>
        </section>
      )}

      {/* Safety note */}
      {feature.safetyNote && (
        <section className="py-12 px-6 sm:px-8 bg-white border-t border-gray-100">
          <div className="max-w-4xl mx-auto">
            <FadeUp>
              <div className="be-card p-6 bg-gradient-to-br from-green-50 to-teal-50 border border-green-200">
                <p className="text-sm text-gray-700">{feature.safetyNote}</p>
              </div>
            </FadeUp>
          </div>
        </section>
      )}

      <RelatedFeatureLinks pages={relatedPages} />

      <SEOFAQ items={buildFaq(feature)} title={`${feature.h1} — frequently asked questions`} columns={1} />

      <ConversionCTA
        title="See all Etsy seller tools"
        subtitle={`${feature.h1} is one part of the full Bulk Edit App toolkit.`}
        primaryLabel="Try Bulk Edit App"
        secondaryLabel="View all features"
        secondaryHref="/features"
        variant="hero"
      />

      <MarketingFooter />
    </div>
  );
}
