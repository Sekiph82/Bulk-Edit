"use client";

import Link from "next/link";
import FadeUp from "./FadeUp";

// No fake ratings, testimonials, user counts, or press logos here on
// purpose — this section builds trust through what's actually true
// rather than inventing social proof.
const TRUST_POINTS = [
  "Built for shops with too many listings to edit one by one",
  "Every change is previewed and requires your explicit confirmation before it reaches Etsy",
  "Backup snapshots and Magic Revert on every bulk write",
  "No fake ratings. No inflated seller counts. Just a safer workflow for Etsy sellers.",
];

export default function TrustSection() {
  return (
    <section className="py-20 px-6 sm:px-8 bg-white">
      <div className="max-w-3xl mx-auto text-center">
        <FadeUp>
          <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
            Built for Etsy sellers
          </span>
          <h2 className="text-3xl font-bold text-gray-900 mb-5">
            A seller-authorized listing management utility
          </h2>
        </FadeUp>

        <FadeUp delay={0.04}>
          <p className="text-sm text-gray-600 leading-relaxed max-w-lg mx-auto mb-8">
            Bulk Edit App is a seller-authorized listing management utility that helps Etsy
            sellers synchronize their own listings, prepare bulk changes, review exact
            before-and-after differences and explicitly confirm changes before submission through
            Etsy&rsquo;s documented API. Bulk Edit App complements Etsy&rsquo;s seller tools.
            Orders, checkout, payments and core shop management remain within Etsy.
          </p>
        </FadeUp>

        <FadeUp delay={0.08}>
          <ul className="space-y-3 text-left max-w-lg mx-auto mb-10">
            {TRUST_POINTS.map((point) => (
              <li key={point} className="flex items-start gap-3">
                <span className="mt-0.5 w-5 h-5 rounded-full bg-indigo-100 border border-indigo-200 flex items-center justify-center flex-shrink-0">
                  <svg className="w-3 h-3 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                </span>
                <span className="text-sm text-gray-700">{point}</span>
              </li>
            ))}
          </ul>
        </FadeUp>

        <FadeUp delay={0.16}>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/register" className="be-btn-primary px-8 py-3 text-base">
              Create your account
            </Link>
            <Link href="/contact-us" className="be-btn-secondary px-8 py-3 text-base">
              Have questions? Contact us
            </Link>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}
