"use client";

import Link from "next/link";
import FadeUp from "./FadeUp";
import type { FeaturePage } from "@/lib/featurePages";

export default function RelatedFeatureLinks({ pages }: { pages: FeaturePage[] }) {
  if (pages.length === 0) return null;
  return (
    <section className="py-16 px-6 sm:px-8 bg-white border-t border-gray-100">
      <div className="max-w-4xl mx-auto">
        <FadeUp>
          <h2 className="text-lg font-bold text-gray-900 mb-6">Related features</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {pages.map((rp) => (
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
  );
}
