"use client";

import FadeUp from "./FadeUp";
import BeforeAfterListingPreview from "./BeforeAfterListingPreview";

const SAFETY_POINTS = [
  "Every Etsy write requires your explicit confirmation",
  "A backup snapshot is created before every apply",
  "Preview-first — no blind writes, ever",
  "Magic Revert restores any listing instantly, if needed",
];

export default function SafetyPreviewPanel() {
  return (
    <section className="py-20 px-6 sm:px-8 be-section-accent">
      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <FadeUp>
          <div>
            <span className="inline-block text-xs font-semibold text-green-600 tracking-widest uppercase mb-4 bg-green-50 px-3 py-1 rounded-full border border-green-100">
              Safety first
            </span>
            <h2 className="text-3xl font-bold text-gray-900 mb-5">No blind writes. Ever.</h2>
            <p className="text-gray-500 leading-relaxed mb-6">
              Every path to Etsy is gated by preview, explicit confirmation, and an automatic
              backup snapshot. You decide what gets applied — Bulk Edit App just makes it faster.
            </p>
            <ul className="space-y-3">
              {SAFETY_POINTS.map((item) => (
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
          </div>
        </FadeUp>
        <FadeUp delay={0.1} className="flex justify-center lg:justify-end">
          <BeforeAfterListingPreview />
        </FadeUp>
      </div>
    </section>
  );
}
