"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import AnimatedProductDemo from "@/components/AnimatedProductDemo";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";

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
  { value: "6-step", label: "safe apply workflow" },
];

const FEATURE_GRID = [
  { icon: "⚡", title: "Bulk Title & Tag Editing", desc: "Update titles, tags, and descriptions across hundreds of listings in one pass." },
  { icon: "💲", title: "Bulk Price & Variation Editing", desc: "Adjust prices, quantities, and SKUs across listings and variations together." },
  { icon: "📊", title: "CSV Import / Export", desc: "Export listings to CSV, edit offline, and import changes back as a draft." },
  { icon: "🖼️", title: "Photo Bulk Editing", desc: "Add, replace, or reorder listing photos in bulk, previewed before publish." },
  { icon: "🤖", title: "AI Listing Optimization", desc: "AI-generated title, tag, and description suggestions — you approve every one." },
  { icon: "🩺", title: "Listing Health Score", desc: "Score every listing 0–100 and find weak titles, thin tags, and low photo counts." },
  { icon: "📈", title: "Profit & Cost Calculator", desc: "See real net profit per listing after Etsy fees, shipping, and ad spend." },
  { icon: "💰", title: "Dynamic Pricing Rules", desc: "Build rule-based price recommendations you review before anything changes." },
];

const FAQ_TEASER = [
  {
    q: "Is my Etsy account safe?",
    a: "Yes. Bulk-Edit connects via Etsy's official OAuth2 login — we never see your Etsy password, and every write is gated behind preview and confirmation.",
  },
  {
    q: "Can I preview changes before applying them?",
    a: "Always. Every bulk edit shows a full before/after diff, listing by listing, before anything is sent to Etsy.",
  },
  {
    q: "Can I undo a bulk edit?",
    a: "Yes — Magic Revert restores any listing to its exact pre-edit snapshot with one click.",
  },
  {
    q: "Does Bulk-Edit replace Etsy?",
    a: "No. Bulk-Edit is a management layer on top of your existing Etsy shop — your listings still live and sell on Etsy.",
  },
  {
    q: "Is this endorsed by Etsy?",
    a: "No. Bulk-Edit is an independent tool that uses the official Etsy API. “Etsy” is a trademark of Etsy, Inc.",
  },
  {
    q: "Do I need technical skills?",
    a: "No. Bulk-Edit is built for sellers, not developers — connect your shop and start editing with no code or CSV knowledge required (though CSV import/export is there if you want it).",
  },
];

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
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay, ease: [0.25, 0.1, 0.25, 1] }}
    >
      {children}
    </motion.div>
  );
}

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
                    The Etsy bulk edit tool for sellers,{" "}
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                      without the chaos.
                    </span>
                  </h1>
                </FadeUp>
                <FadeUp delay={0.08}>
                  <p className="text-lg text-gray-500 leading-relaxed">
                    Connect your Etsy shop, update listings in bulk, preview every change, apply
                    safely, and revert instantly if something looks wrong. Nothing reaches Etsy
                    without your confirmation.
                  </p>
                </FadeUp>
              </div>

              <FadeUp delay={0.14}>
                <div className="flex flex-col sm:flex-row gap-3">
                  <Link href="/register" className="be-btn-primary px-8 py-3 text-base">
                    Get Started Free
                  </Link>
                  <Link href="/features" className="be-btn-secondary px-8 py-3 text-base">
                    See features
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

      {/* Problem / solution */}
      <section className="py-20 px-6 sm:px-8 be-section-accent">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
          <FadeUp>
            <div>
              <span className="inline-block text-xs font-semibold text-red-600 tracking-widest uppercase mb-4 bg-red-50 px-3 py-1 rounded-full border border-red-100">
                The problem
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
                Editing listings one by one doesn&apos;t scale.
              </h2>
              <p className="text-gray-500 leading-relaxed">
                Etsy sellers with more than a handful of listings lose hours every week clicking
                through the same edit form — updating a tag here, a price there — with no way to
                change many listings at once or safely undo a mistake.
              </p>
            </div>
          </FadeUp>
          <FadeUp delay={0.1}>
            <div>
              <span className="inline-block text-xs font-semibold text-green-600 tracking-widest uppercase mb-4 bg-green-50 px-3 py-1 rounded-full border border-green-100">
                The solution
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
                Preview, apply, and revert — across your whole shop.
              </h2>
              <p className="text-gray-500 leading-relaxed">
                Bulk-Edit lets you select listings, define a change once, and review a full
                before/after diff before anything is written to Etsy. If a change doesn&apos;t
                look right, Magic Revert restores the exact prior state in one click.
              </p>
            </div>
          </FadeUp>
        </div>
      </section>

      {/* Feature grid — replaces the old 2-card teaser */}
      <section className="py-20 px-6 sm:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <FadeUp className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">
              Everything you need to manage your Etsy shop at scale
            </h2>
            <p className="text-gray-500 max-w-xl mx-auto">
              AI optimization, CSV import/export, variation editing, photo bulk edit, dynamic
              pricing, listing health scoring, and profit tracking — all in one place.
            </p>
          </FadeUp>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {FEATURE_GRID.map((f, i) => (
              <FadeUp key={f.title} delay={i * 0.04}>
                <motion.div
                  className="be-card p-6 h-full border flex flex-col"
                  whileHover={reduced ? {} : { y: -4 }}
                  transition={{ duration: 0.18 }}
                >
                  <div className="text-3xl mb-3" role="img" aria-label={f.title}>
                    {f.icon}
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed flex-1">{f.desc}</p>
                </motion.div>
              </FadeUp>
            ))}
          </div>

          <div className="text-center mt-10">
            <Link href="/features" className="be-btn-primary px-7 py-3">
              View all features
            </Link>
          </div>
        </div>
      </section>

      {/* Safety / revert */}
      <section className="py-20 px-6 sm:px-8 be-section-accent">
        <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <FadeUp>
            <div>
              <span className="inline-block text-xs font-semibold text-green-600 tracking-widest uppercase mb-4 bg-green-50 px-3 py-1 rounded-full border border-green-100">
                Safety first
              </span>
              <h2 className="text-3xl font-bold text-gray-900 mb-5">No blind writes. Ever.</h2>
              <p className="text-gray-500 leading-relaxed">
                Every path to Etsy is gated by preview, explicit confirmation, and an automatic
                backup snapshot. You decide what gets applied — Bulk-Edit just makes it faster.
              </p>
            </div>
          </FadeUp>
          <FadeUp delay={0.1}>
            <ul className="space-y-3">
              {[
                "Every Etsy write requires explicit user confirmation",
                "Backup snapshots created before every apply",
                "Preview-first — no blind writes, ever",
                "Magic Revert restores any listing instantly",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <span className="mt-0.5 w-5 h-5 rounded-full bg-green-100 border border-green-200 flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  </span>
                  <span className="text-sm text-gray-700">{item}</span>
                </li>
              ))}
            </ul>
          </FadeUp>
        </div>
      </section>

      {/* Positioning / comparison — honest, no fake testimonials or customer counts */}
      <section className="py-20 px-6 sm:px-8 bg-white">
        <div className="max-w-5xl mx-auto">
          <FadeUp className="text-center mb-10">
            <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
              Built for Etsy sellers
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">
              Built for Etsy sellers who need safer bulk updates
            </h2>
            <p className="text-gray-500 max-w-2xl mx-auto">
              Bulk-Edit focuses on one job: changing many listings at once, safely. Tools like
              eRank, Marmalead, or Alura focus on keyword and SEO research; Bulk-Edit focuses on
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
                <h3 className="font-semibold text-gray-900 mb-2">Bulk-Edit</h3>
                <p className="text-sm text-gray-600">
                  Helps you apply those decisions across your whole shop at once — safely,
                  with preview and revert built in.
                </p>
              </div>
            </div>
          </FadeUp>
        </div>
      </section>

      {/* FAQ teaser */}
      <section className="py-20 px-6 sm:px-8 be-section-accent">
        <div className="max-w-4xl mx-auto">
          <FadeUp className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Common questions</h2>
          </FadeUp>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {FAQ_TEASER.map((item, i) => (
              <FadeUp key={item.q} delay={i * 0.05}>
                <div className="be-card p-5">
                  <h3 className="font-semibold text-gray-900 mb-2 text-sm">{item.q}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{item.a}</p>
                </div>
              </FadeUp>
            ))}
          </div>
          <div className="text-center mt-8">
            <Link href="/faq" className="text-sm font-medium text-indigo-600 hover:underline">
              Read the full FAQ →
            </Link>
          </div>
        </div>
      </section>

      {/* Pricing preview */}
      <section className="py-20 px-6 sm:px-8 bg-white border-t border-gray-100">
        <div className="max-w-3xl mx-auto text-center">
          <FadeUp>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              Start free. Upgrade when you need more.
            </h2>
            <p className="text-gray-500 mb-8">
              A free plan to get started, plus Basic and Pro tiers for growing shops that need
              more bulk edits, AI credits, and automation.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/pricing" className="be-btn-primary px-8 py-3">
                See full pricing
              </Link>
              <Link href="/register" className="be-btn-secondary px-8 py-3">
                Start for free
              </Link>
            </div>
          </FadeUp>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-6 sm:px-8 be-hero-bg">
        <FadeUp>
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Ready to edit your Etsy shop safely, at scale?
            </h2>
            <p className="text-gray-500 mb-8">
              Free plan available. No credit card required to start.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/register" className="be-btn-primary px-8 py-3 text-base">
                Get Started Free
              </Link>
              <Link href="/login" className="be-btn-secondary px-8 py-3 text-base">
                Sign In
              </Link>
            </div>
          </div>
        </FadeUp>
      </section>

      <MarketingFooter />
    </main>
  );
}
