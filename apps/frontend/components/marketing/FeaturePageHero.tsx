"use client";

import Link from "next/link";
import FadeUp from "./FadeUp";

export default function FeaturePageHero({
  h1,
  intro,
  bestFor,
}: {
  h1: string;
  intro: string;
  bestFor?: string;
}) {
  return (
    <section className="be-hero-bg pt-8 pb-16 px-6 sm:px-8">
      <div className="max-w-4xl mx-auto">
        <FadeUp>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight leading-tight mb-5">
            {h1}
          </h1>
        </FadeUp>
        <FadeUp delay={0.08}>
          <p className="text-lg text-gray-500 leading-relaxed max-w-2xl mb-6">{intro}</p>
        </FadeUp>
        {bestFor && (
          <FadeUp delay={0.12}>
            <p className="text-sm text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg px-4 py-2.5 max-w-2xl mb-8">
              <span className="font-semibold">Best for:</span> {bestFor}
            </p>
          </FadeUp>
        )}
        <FadeUp delay={0.18}>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link href="/register" className="be-btn-primary px-8 py-3 text-base">
              Try Bulk Edit App
            </Link>
            <Link href="/features" className="be-btn-secondary px-8 py-3 text-base">
              Explore all Etsy seller tools
            </Link>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}
