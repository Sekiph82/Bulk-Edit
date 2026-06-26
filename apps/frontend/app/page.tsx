"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import AnimatedProductDemo from "../components/AnimatedProductDemo";
import MarketingNav from "../components/marketing/MarketingNav";
import MarketingFooter from "../components/marketing/MarketingFooter";

const TRUST_ITEMS = [
  "Preview every change",
  "Backup snapshots",
  "Magic Revert",
  "Built for Etsy sellers",
];

const WORKFLOW_STEPS = ["Connect", "Sync", "Edit", "Preview", "Apply", "Revert"];

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
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.25, 0.1, 0.25, 1] }}
    >
      {children}
    </motion.div>
  );
}

export default function HomePage() {
  const reduced = useReducedMotion();

  return (
    <main className="min-h-screen bg-gray-50">
      <MarketingNav />

      {/* Hero */}
      <section className="be-hero-bg">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 pt-14 pb-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left column */}
            <div className="space-y-8 max-w-xl">
              <div className="space-y-4">
                <FadeUp>
                  <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-gray-900 leading-tight">
                    Bulk editing for Etsy sellers,{" "}
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                      without the chaos.
                    </span>
                  </h1>
                </FadeUp>
                <FadeUp delay={0.08}>
                  <p className="text-lg text-gray-500 leading-relaxed">
                    Connect your Etsy shop, update listings in bulk, preview every change, publish safely, and revert when needed.
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

              {/* Trust strip */}
              <FadeUp delay={0.2}>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                  {TRUST_ITEMS.map((item) => (
                    <div key={item} className="flex items-center gap-2 text-sm text-gray-600">
                      <svg
                        className="w-4 h-4 text-green-500 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {item}
                    </div>
                  ))}
                </div>
              </FadeUp>
            </div>

            {/* Right column — animated demo */}
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

      {/* Workflow strip */}
      <section className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 py-8">
          <div className="flex items-center justify-center gap-2 flex-wrap">
            {WORKFLOW_STEPS.map((step, i) => (
              <div key={step} className="flex items-center gap-2">
                <span className="be-step">{step}</span>
                {i < WORKFLOW_STEPS.length - 1 && (
                  <svg
                    className="w-4 h-4 text-gray-400 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature tease */}
      <section className="py-16 px-6 sm:px-8 be-section-accent">
        <div className="max-w-4xl mx-auto text-center">
          <motion.h2
            className="text-2xl font-bold text-gray-900 mb-3"
            initial={reduced ? false : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.45 }}
          >
            Everything you need to manage your Etsy shop at scale
          </motion.h2>
          <motion.p
            className="text-gray-500 mb-8"
            initial={reduced ? false : { opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.45, delay: 0.07 }}
          >
            AI optimization, CSV import/export, variation editing, photo bulk edit, dynamic pricing, and more.
          </motion.p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/features" className="be-btn-primary px-7 py-3">
              View all features
            </Link>
            <Link href="/pricing" className="be-btn-secondary px-7 py-3">
              See pricing
            </Link>
          </div>
        </div>
      </section>

      {/* Footer disclaimer */}
      <div className="bg-indigo-50 border-t border-indigo-100 px-6 sm:px-8 py-5 text-center">
        <p className="text-xs text-indigo-700">
          The term &ldquo;Etsy&rdquo; is a trademark of Etsy, Inc. Bulk-Edit uses the Etsy API but
          is not endorsed or certified by Etsy, Inc.
        </p>
      </div>

      <MarketingFooter />
    </main>
  );
}
