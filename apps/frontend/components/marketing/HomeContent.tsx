"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import AnimatedProductDemo from "@/components/AnimatedProductDemo";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import FadeUp from "@/components/marketing/FadeUp";
import SellerPainGrid from "@/components/marketing/SellerPainGrid";
import SafeEditingEngine from "@/components/marketing/SafeEditingEngine";
import FeatureShowcase from "@/components/marketing/FeatureShowcase";
import SafetyPreviewPanel from "@/components/marketing/SafetyPreviewPanel";
import ProductScreenshotsSection from "@/components/marketing/ProductScreenshotsSection";
import DemoVideoSection from "@/components/marketing/DemoVideoSection";
import TrustSection from "@/components/marketing/TrustSection";
import ComparisonSection from "@/components/marketing/ComparisonSection";
import EtsySeoSection from "@/components/marketing/EtsySeoSection";
import VideoInsightsSection from "@/components/marketing/VideoInsightsSection";
import ExplainerBlocks from "@/components/marketing/ExplainerBlocks";
import ConversionCTA from "@/components/marketing/ConversionCTA";
import SEOFAQ, { type FaqItem } from "@/components/marketing/SEOFAQ";
import { PLAN_PRICE_DISPLAY, HOMEPAGE_PLAN_SUMMARIES } from "@/lib/pricingPlans";

const TRUST_ITEMS = [
  "Preview every change",
  "Backup snapshots",
  "Magic Revert",
  "Built for Etsy sellers",
];

// Capability stats, not invented usage/customer numbers — every figure here
// maps directly to a real, shipped feature (see /features for the full list).
const STAT_ITEMS = [
  { value: "17+", label: "bulk edit & shop tools" },
  { value: "100%", label: "changes previewed before apply" },
  { value: "1-click", label: "Magic Revert on any listing" },
  { value: "6-step", label: "safe editing engine" },
];

// SEO-rich FAQ targeting buyer-intent search terms. Every answer is truthful
// and matches real shipped behavior — no invented capabilities.
const FAQ_ITEMS: FaqItem[] = [
  {
    q: "What is an Etsy bulk edit tool?",
    a: "An Etsy bulk edit tool lets you change titles, tags, prices, descriptions, photos, or variations across many Etsy listings at once instead of editing each listing individually through Etsy's own editor.",
  },
  {
    q: "Can I bulk edit Etsy titles and tags?",
    a: "Yes. Bulk Edit App lets you update titles and tags across many listings in one operation, with a full preview before anything is applied.",
  },
  {
    q: "Can I preview changes before applying them?",
    a: "Always. Every bulk edit — from any feature — shows a full before/after diff, listing by listing, before anything is sent to Etsy.",
  },
  {
    q: "Can I undo bulk edits on Etsy listings?",
    a: "Yes. Magic Revert restores any listing to its exact pre-edit snapshot with one click, using the automatic backup created before the edit was applied.",
  },
  {
    q: "Can I bulk edit Etsy listing photos?",
    a: "Yes — add, replace, or delete photos across many listings at once, previewed before publishing. Photo reorder isn't supported, since Etsy's API has no atomic reorder endpoint.",
  },
  {
    q: "Does Bulk Edit App upload videos directly to Etsy?",
    a: "No. The Product Video Generator creates a real MP4 video from your listing photos that you preview and download — you add it to your listing yourself through Etsy's own editor.",
  },
  {
    q: "Is Bulk Edit App useful for large Etsy shops?",
    a: "Yes — it's built specifically for sellers with more listings than they can reasonably manage one at a time, including variation-heavy shops and shops with hundreds of listings.",
  },
  {
    q: "Does it support Etsy CSV import and export?",
    a: "Yes. Export your listings to CSV, edit them in any spreadsheet tool, and import changes back as a draft bulk edit session with the same preview-and-confirm safety flow.",
  },
  {
    q: "Is my Etsy account safe?",
    a: "Yes. Bulk Edit App connects via Etsy's official OAuth2 login — we never see your Etsy password, and every write is gated behind preview and confirmation.",
  },
  {
    q: "Is this endorsed by Etsy?",
    a: "No. The term “Etsy” is a trademark of Etsy, Inc. This application uses the Etsy API but is not endorsed or certified by Etsy, Inc.",
  },
];

export default function HomeContent() {
  const reduced = useReducedMotion();

  return (
    <main className="min-h-screen bg-gray-50">
      <MarketingNav />

      {/* Hero */}
      <section className="be-hero-bg">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 pt-14 pb-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <div className="space-y-8 max-w-xl">
              <div className="space-y-4">
                <FadeUp>
                  <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-gray-900 leading-tight">
                    Bulk edit Etsy listings{" "}
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                      faster, safer, and smarter.
                    </span>
                  </h1>
                </FadeUp>
                <FadeUp delay={0.08}>
                  <p className="text-lg text-gray-500 leading-relaxed">
                    Titles, tags, prices, photos, variations, and CSV workflows — update them
                    across your whole Etsy shop with one safe engine: preview every change, apply
                    with confidence, revert instantly if something looks wrong.
                  </p>
                </FadeUp>
              </div>

              <FadeUp delay={0.14}>
                <div className="flex flex-col sm:flex-row gap-3">
                  <Link href="/register" className="be-btn-primary px-8 py-3 text-base">
                    Start editing your Etsy listings
                  </Link>
                  <Link href="/features" className="be-btn-secondary px-8 py-3 text-base">
                    Explore features
                  </Link>
                </div>
              </FadeUp>

              <FadeUp delay={0.2}>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                  {TRUST_ITEMS.map((item) => (
                    <div key={item} className="flex items-center gap-2 text-sm text-gray-600">
                      <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {item}
                    </div>
                  ))}
                </div>
              </FadeUp>
            </div>

            <motion.div
              className="w-full lg:max-w-lg lg:justify-self-end"
              initial={reduced ? false : { opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.25, ease: [0.25, 0.1, 0.25, 1] }}
            >
              <AnimatedProductDemo />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Primary positioning statement — plain, factual, no beta/launch framing */}
      <section className="border-t border-gray-200 bg-white">
        <div className="max-w-4xl mx-auto px-6 sm:px-8 py-8 text-center">
          <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
            Bulk Edit App is a seller-authorized listing management utility that helps Etsy sellers
            synchronize their own listings, prepare bulk changes, review exact before-and-after
            differences, and explicitly confirm changes before submission through Etsy&rsquo;s
            documented API. Bulk Edit App complements Etsy&rsquo;s seller tools — orders, checkout,
            payments, and core shop management remain within Etsy.
          </p>
        </div>
      </section>

      {/* Stat strip — capability stats only, no invented usage numbers */}
      <section className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 py-10">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
            {STAT_ITEMS.map((s) => (
              <div key={s.label}>
                <p className="text-2xl sm:text-3xl font-extrabold text-gray-900">{s.value}</p>
                <p className="text-xs sm:text-sm text-gray-500 mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Product workflow preview — mock UI, sample data only */}
      <ProductScreenshotsSection />

      {/* Problem */}
      <SellerPainGrid />

      {/* Solution — safe editing engine (rich timeline, not plain pills) */}
      <SafeEditingEngine />

      <ConversionCTA
        eyebrow="Preview-first bulk editing"
        title="Too many listings for manual edits? Bulk Edit App handles the bulk changes safely."
        subtitle="Connect your shop and see exactly what a bulk edit would change — before anything happens. Orders, checkout, and core shop management stay in Etsy."
        primaryLabel="Try Bulk Edit App"
        secondaryLabel="See all features"
        secondaryHref="/features"
        variant="white"
      />

      {/* Feature clusters */}
      <FeatureShowcase />

      {/* 60-second demo — real video if present, honest placeholder otherwise */}
      <DemoVideoSection />

      {/* Fake-free trust building — no testimonials, ratings, or invented counts */}
      <TrustSection />

      {/* Careful, non-attack competitor positioning */}
      <ComparisonSection />

      {/* Trust and safety */}
      <SafetyPreviewPanel />

      {/* Etsy SEO */}
      <EtsySeoSection />

      {/* Product Video Generator + Shop Insights */}
      <VideoInsightsSection />

      {/* AI-search-friendly explainer blocks */}
      <ExplainerBlocks />

      {/* Positioning — honest, no fake testimonials or customer counts */}
      <section className="py-20 px-6 sm:px-8 be-section-accent">
        <div className="max-w-5xl mx-auto">
          <FadeUp className="text-center mb-10">
            <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
              Built for Etsy sellers
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">
              Built for Etsy sellers who need safer bulk updates
            </h2>
            <p className="text-gray-500 max-w-2xl mx-auto">
              Bulk Edit App focuses on one job: changing many listings at once, safely. Tools like
              eRank, Marmalead, or Alura focus on keyword and SEO research; Bulk Edit App focuses on
              the bulk editing and shop-management workflow itself — the two are complementary,
              not competing.
            </p>
          </FadeUp>
          <FadeUp delay={0.1}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 max-w-3xl mx-auto">
              <div className="be-card p-6">
                <h3 className="font-semibold text-gray-900 mb-2">SEO research tools</h3>
                <p className="text-sm text-gray-600">
                  Help you decide what keywords and tags to use, based on search data.
                </p>
              </div>
              <div className="be-card p-6">
                <h3 className="font-semibold text-gray-900 mb-2">Bulk Edit App</h3>
                <p className="text-sm text-gray-600">
                  Helps you apply those decisions across your whole shop at once — safely,
                  with preview and revert built in.
                </p>
              </div>
            </div>
          </FadeUp>
        </div>
      </section>

      {/* SEO-rich FAQ with FAQPage schema */}
      <SEOFAQ items={FAQ_ITEMS} />
      <div className="text-center -mt-12 pb-8 relative z-10">
        <Link href="/faq" className="text-sm font-medium text-indigo-600 hover:underline">
          Read the full FAQ →
        </Link>
      </div>

      {/* Pricing preview — same plan names/prices as /pricing (lib/pricingPlans.ts) */}
      <section className="py-20 px-6 sm:px-8 bg-white border-t border-gray-100">
        <div className="max-w-5xl mx-auto">
          <FadeUp className="text-center mb-10">
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              Start free. Upgrade when you need more.
            </h2>
            <p className="text-gray-500">
              A free plan to get started, plus Basic and Pro tiers for growing shops that need
              more bulk edits, advanced workflows, and automation.
            </p>
          </FadeUp>

          <FadeUp delay={0.1}>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-10">
              {HOMEPAGE_PLAN_SUMMARIES.map(({ key, highlights }) => {
                const display = PLAN_PRICE_DISPLAY[key];
                const isFree = key === "free";
                return (
                  <div
                    key={key}
                    className={`relative bg-white rounded-2xl border p-6 flex flex-col gap-4 ${
                      key === "pro_monthly" ? "border-indigo-400 ring-2 ring-indigo-200" : "border-gray-200"
                    }`}
                  >
                    {display.badge && (
                      <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                        {display.badge}
                      </span>
                    )}
                    <div>
                      <h3 className="font-bold text-gray-900 text-lg">{display.label}</h3>
                      <p className="text-indigo-600 font-semibold mt-1">{display.price}</p>
                    </div>
                    <ul className="space-y-1.5 flex-1 text-left">
                      {highlights.map((h) => (
                        <li key={h} className="flex items-start gap-2 text-sm text-gray-600">
                          <svg className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          {h}
                        </li>
                      ))}
                    </ul>
                    {isFree ? (
                      <Link href="/register" className="be-btn-secondary w-full text-center py-2.5 text-sm">
                        Start for free
                      </Link>
                    ) : (
                      <Link href="/pricing" className="be-btn-primary w-full text-center py-2.5 text-sm">
                        See full pricing
                      </Link>
                    )}
                  </div>
                );
              })}
            </div>
          </FadeUp>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/pricing" className="be-btn-primary px-8 py-3">
              See full pricing
            </Link>
            <Link href="/register" className="be-btn-secondary px-8 py-3">
              Start for free
            </Link>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <ConversionCTA
        title="Ready to edit your Etsy shop safely, at scale?"
        subtitle="Free plan available. No credit card required to start."
        primaryLabel="Try Bulk Edit App"
        secondaryLabel="Sign In"
        secondaryHref="/login"
        variant="hero"
      />

      <MarketingFooter />
    </main>
  );
}
