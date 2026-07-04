"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import { FEATURE_PAGES, type FeaturePage } from "@/lib/featurePages";

function FadeUp({
  children,
  delay = 0,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduced ? false : { opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.45, delay, ease: [0.25, 0.1, 0.25, 1] }}
    >
      {children}
    </motion.div>
  );
}

export default function FeaturePageContent({ feature }: { feature: FeaturePage }) {
  const relatedPages = feature.related
    .map((slug) => FEATURE_PAGES.find((f) => f.slug === slug))
    .filter((f): f is FeaturePage => Boolean(f));

  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />

      {/* Breadcrumb */}
      <div className="max-w-4xl mx-auto px-6 sm:px-8 pt-6 text-sm text-gray-400">
        <Link href="/" className="hover:text-gray-600">Home</Link>
        <span className="mx-2">/</span>
        <Link href="/features" className="hover:text-gray-600">Features</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-600">{feature.h1}</span>
      </div>

      {/* Hero */}
      <section className="be-hero-bg pt-8 pb-16 px-6 sm:px-8">
        <div className="max-w-4xl mx-auto">
          <FadeUp>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight leading-tight mb-5">
              {feature.h1}
            </h1>
          </FadeUp>
          <FadeUp delay={0.08}>
            <p className="text-lg text-gray-500 leading-relaxed max-w-2xl mb-8">{feature.intro}</p>
          </FadeUp>
          <FadeUp delay={0.14}>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link href="/register" className="be-btn-primary px-8 py-3 text-base">
                Get Started Free
              </Link>
              <Link href="/pricing" className="be-btn-secondary px-8 py-3 text-base">
                See pricing
              </Link>
            </div>
          </FadeUp>
        </div>
      </section>

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

      {/* Boundaries / accurate claims */}
      {feature.boundaries && feature.boundaries.length > 0 && (
        <section className="py-12 px-6 sm:px-8 be-section-accent">
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

      {/* Related features */}
      {relatedPages.length > 0 && (
        <section className="py-16 px-6 sm:px-8 bg-white border-t border-gray-100">
          <div className="max-w-4xl mx-auto">
            <FadeUp>
              <h2 className="text-lg font-bold text-gray-900 mb-6">Related features</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {relatedPages.map((rp) => (
                  <Link
                    key={rp.slug}
                    href={`/features/${rp.slug}`}
                    className="be-card p-5 block hover:no-underline"
                  >
                    <h3 className="font-semibold text-gray-900 text-sm mb-1">{rp.h1}</h3>
                    <p className="text-xs text-gray-500">{rp.intro}</p>
                  </Link>
                ))}
              </div>
            </FadeUp>
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="py-16 px-6 sm:px-8 be-hero-bg">
        <FadeUp>
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              See all features
            </h2>
            <p className="text-gray-500 mb-8">
              {feature.h1} is one part of the full Bulk-Edit toolkit.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/features" className="be-btn-primary px-8 py-3 text-base">
                View all features
              </Link>
              <Link href="/register" className="be-btn-secondary px-8 py-3 text-base">
                Start for free
              </Link>
            </div>
          </div>
        </FadeUp>
      </section>

      <MarketingFooter />
    </div>
  );
}
