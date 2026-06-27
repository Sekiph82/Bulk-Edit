"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";

const FEATURES = [
  {
    icon: "⚡",
    title: "Bulk Listing Editor",
    desc: "Update titles, tags, prices, descriptions, and more across hundreds of listings in one operation.",
    color: "from-indigo-50 to-blue-50 border-indigo-200",
  },
  {
    icon: "🔍",
    title: "Safe Preview Engine",
    desc: "Every change is previewed before anything touches Etsy. See exactly what will change — listing by listing.",
    color: "from-violet-50 to-purple-50 border-violet-200",
  },
  {
    icon: "🛡️",
    title: "Backup Snapshots",
    desc: "Automatic pre-write snapshots capture the full state of each listing before any change is applied.",
    color: "from-emerald-50 to-teal-50 border-emerald-200",
  },
  {
    icon: "↩️",
    title: "Magic Revert",
    desc: "Made a mistake? Restore any listing to its exact pre-edit state with one click. No data lost.",
    color: "from-rose-50 to-pink-50 border-rose-200",
  },
  {
    icon: "🖼️",
    title: "Photo & Video Editor",
    desc: "Add, replace, or remove listing photos and videos in bulk. Visualize the result before publishing.",
    color: "from-amber-50 to-orange-50 border-amber-200",
  },
  {
    icon: "🔀",
    title: "Variation Editor",
    desc: "Bulk-adjust prices, quantities, and SKUs across variation listings. Preview per-variation diffs.",
    color: "from-cyan-50 to-sky-50 border-cyan-200",
  },
  {
    icon: "🤖",
    title: "AI Listing Optimizer",
    desc: "Generate AI-powered title, description, tag, and alt text suggestions. Review every suggestion before accepting.",
    color: "from-indigo-50 to-violet-50 border-indigo-200",
  },
  {
    icon: "📊",
    title: "CSV Import / Export",
    desc: "Export your listings to CSV for external editing. Import changes back as a draft bulk edit session.",
    color: "from-green-50 to-emerald-50 border-green-200",
  },
  {
    icon: "💰",
    title: "Dynamic Pricing",
    desc: "Build rule-based price recommendations. Review and approve per-listing before any price changes.",
    color: "from-yellow-50 to-amber-50 border-yellow-200",
  },
  {
    icon: "⏰",
    title: "Scheduled Jobs",
    desc: "Schedule safe syncs and draft creations. Jobs never auto-publish to Etsy — your approval is always required.",
    color: "from-blue-50 to-indigo-50 border-blue-200",
  },
  {
    icon: "🏢",
    title: "Admin Visibility",
    desc: "Platform operators get a secure admin panel with paginated views of all entities. No secrets exposed.",
    color: "from-slate-50 to-gray-50 border-slate-200",
  },
  {
    icon: "🩺",
    title: "Listing Health Score",
    desc: "Score every listing 0–100. Detect missing tags, weak titles, thin descriptions, and low photo counts before they cost you sales.",
    color: "from-green-50 to-teal-50 border-green-200",
    href: "/listing-health",
  },
  {
    icon: "📈",
    title: "Profit & Cost Calculator",
    desc: "Track product cost, POD base cost, Etsy fees, shipping, and ad costs to estimate net profit and margin per listing.",
    color: "from-violet-50 to-indigo-50 border-violet-200",
    href: "/profit",
  },
];

const WORKFLOW = [
  { step: "1", label: "Connect Etsy Shop", desc: "OAuth2 PKCE connection in under a minute." },
  { step: "2", label: "Sync Listings", desc: "Pull all your listings into Bulk-Edit securely." },
  { step: "3", label: "Build Your Edits", desc: "Select listings and define bulk changes." },
  { step: "4", label: "Preview Changes", desc: "Review a full diff before anything is written." },
  { step: "5", label: "Apply Safely", desc: "Confirm once. Snapshots auto-created. Etsy updated." },
  { step: "6", label: "Revert if Needed", desc: "Restore any listing from its snapshot instantly." },
];

const SAFETY_ITEMS = [
  "Every Etsy write requires explicit user confirmation",
  "Backup snapshots created before every apply",
  "Preview-first — no blind writes, ever",
  "Scheduled jobs create drafts, never auto-publish",
  "AI suggestions are reviewed before acceptance",
  "Dynamic Pricing creates recommendations, not auto-edits",
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
      initial={reduced ? false : { opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay, ease: [0.25, 0.1, 0.25, 1] }}
    >
      {children}
    </motion.div>
  );
}

export default function FeaturesPage() {
  const reduced = useReducedMotion();

  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="be-hero-bg pt-16 pb-24 px-6 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-3xl mx-auto text-center">
            <FadeUp>
              <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
                Full Feature Set
              </span>
            </FadeUp>

            <FadeUp delay={0.08}>
              <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight leading-tight mt-2 mb-5">
                Everything Etsy sellers need{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                  to edit smarter
                </span>
              </h1>
            </FadeUp>

            <FadeUp delay={0.14}>
              <p className="text-lg text-gray-500 leading-relaxed max-w-2xl mx-auto mb-8">
                Bulk-Edit gives you a complete toolkit for managing Etsy listings at scale — with
                safety gates, backups, and previews built into every workflow.
              </p>
            </FadeUp>

            <FadeUp delay={0.2}>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link href="/register" className="be-btn-primary px-8 py-3 text-base">
                  Start for free
                </Link>
                <Link href="/pricing" className="be-btn-secondary px-8 py-3 text-base">
                  View pricing
                </Link>
              </div>
            </FadeUp>
          </div>

          {/* Animated listing-to-preview visual */}
          <FadeUp delay={0.3} className="mt-16 max-w-2xl mx-auto">
            <AnimatedListingVisual reduced={!!reduced} />
          </FadeUp>
        </div>
      </section>

      {/* ── Feature grid ─────────────────────────────────────────────────── */}
      <section className="py-20 px-6 sm:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <FadeUp className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Built around your workflow</h2>
            <p className="text-gray-500 max-w-xl mx-auto">
              Thirteen tools that work together — from first sync to bulk apply, health scoring, profit tracking, and instant revert.
            </p>
          </FadeUp>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => (
              <FadeUp key={f.title} delay={i * 0.04}>
                <motion.div
                  className={`be-card p-6 h-full bg-gradient-to-br ${f.color} border flex flex-col`}
                  whileHover={reduced ? {} : { y: -4 }}
                  transition={{ duration: 0.18 }}
                >
                  <div className="text-3xl mb-3" role="img" aria-label={f.title}>
                    {f.icon}
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed flex-1">{f.desc}</p>
                  {"href" in f && f.href && (
                    <Link
                      href={f.href}
                      className="mt-3 text-xs font-medium text-indigo-600 hover:underline"
                    >
                      Open →
                    </Link>
                  )}
                </motion.div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ── Workflow ─────────────────────────────────────────────────────── */}
      <section className="py-20 px-6 sm:px-8 be-section-accent">
        <div className="max-w-7xl mx-auto">
          <FadeUp className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">How it works</h2>
            <p className="text-gray-500 max-w-xl mx-auto">
              A complete six-step workflow designed to keep you in control at every point.
            </p>
          </FadeUp>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {WORKFLOW.map((w, i) => (
              <FadeUp key={w.step} delay={i * 0.06}>
                <div className="be-card p-6 h-full">
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center text-sm font-bold mb-4 shadow-sm">
                    {w.step}
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{w.label}</h3>
                  <p className="text-sm text-gray-500">{w.desc}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ── Safety section ───────────────────────────────────────────────── */}
      <section className="py-20 px-6 sm:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <FadeUp>
              <div>
                <span className="inline-block text-xs font-semibold text-green-600 tracking-widest uppercase mb-4 bg-green-50 px-3 py-1 rounded-full border border-green-100">
                  Safety First
                </span>
                <h2 className="text-3xl font-bold text-gray-900 mb-5">
                  No blind writes. Ever.
                </h2>
                <p className="text-gray-500 leading-relaxed">
                  Every path to Etsy is gated by preview, confirmation, and snapshot backup. You decide
                  what gets applied — Bulk-Edit just makes it faster and safer.
                </p>
              </div>
            </FadeUp>

            <FadeUp delay={0.1}>
              <ul className="space-y-3">
                {SAFETY_ITEMS.map((item) => (
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
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────────────── */}
      <section className="py-20 px-6 sm:px-8 be-hero-bg">
        <FadeUp>
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Start editing smarter today
            </h2>
            <p className="text-gray-500 mb-8">
              Free plan available. No credit card required to start.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/register" className="be-btn-primary px-8 py-3 text-base">
                Try Bulk-Edit free
              </Link>
              <Link href="/pricing" className="be-btn-secondary px-8 py-3 text-base">
                See plans
              </Link>
            </div>
          </div>
        </FadeUp>
      </section>

      <MarketingFooter />
    </div>
  );
}

/* ── Animated listing → preview visual ──────────────────────────────────── */
function AnimatedListingVisual({ reduced }: { reduced: boolean }) {
  const listings = [
    { title: "Handmade ceramic mug", price: "$28", selected: true },
    { title: "Linen tote bag set", price: "$34", selected: true },
    { title: "Printable wall art", price: "$6", selected: false },
    { title: "Soy wax candle trio", price: "$18", selected: true },
  ];

  return (
    <div className="relative bg-white border border-gray-200 rounded-2xl shadow-lg overflow-hidden">
      {/* Header bar */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-5 py-3 flex items-center gap-2">
        <div className="w-2.5 h-2.5 rounded-full bg-white/30" />
        <div className="w-2.5 h-2.5 rounded-full bg-white/30" />
        <div className="w-2.5 h-2.5 rounded-full bg-white/30" />
        <span className="ml-2 text-xs text-white/80 font-medium">Bulk Edit — Preview</span>
      </div>

      {/* Listing rows */}
      <div className="p-4 space-y-2">
        {listings.map((l, i) => (
          <motion.div
            key={l.title}
            className={`flex items-center gap-3 p-3 rounded-lg border ${
              l.selected
                ? "border-indigo-200 bg-indigo-50"
                : "border-gray-100 bg-gray-50"
            }`}
            initial={reduced ? false : { opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: i * 0.1, ease: "easeOut" }}
          >
            <div
              className={`w-4 h-4 rounded flex items-center justify-center flex-shrink-0 ${
                l.selected
                  ? "bg-indigo-600"
                  : "border border-gray-300 bg-white"
              }`}
            >
              {l.selected && (
                <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
            <span className="text-sm text-gray-700 flex-1 font-medium">{l.title}</span>
            <span className="text-sm text-gray-500">{l.price}</span>
            {l.selected && (
              <motion.span
                className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full border border-green-200 font-medium"
                initial={reduced ? false : { scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.25, delay: 0.4 + i * 0.1 }}
              >
                +20%
              </motion.span>
            )}
          </motion.div>
        ))}
      </div>

      {/* Preview footer */}
      <motion.div
        className="border-t border-gray-100 bg-gradient-to-r from-indigo-50 to-purple-50 px-5 py-4 flex items-center justify-between"
        initial={reduced ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.7 }}
      >
        <span className="text-xs text-indigo-700 font-medium">3 listings selected · Preview ready</span>
        <div className="flex gap-2">
          <span className="text-xs bg-white border border-indigo-200 text-indigo-600 px-3 py-1 rounded-lg font-medium">
            Preview
          </span>
          <span className="text-xs bg-indigo-600 text-white px-3 py-1 rounded-lg font-medium">
            Apply →
          </span>
        </div>
      </motion.div>
    </div>
  );
}
