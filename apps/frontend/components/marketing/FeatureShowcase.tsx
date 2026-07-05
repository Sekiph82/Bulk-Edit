"use client";

import Link from "next/link";
import FadeUp from "./FadeUp";
import { FEATURE_CLUSTERS, getFeaturePage } from "@/lib/featurePages";

export default function FeatureShowcase() {
  return (
    <section className="py-20 px-6 sm:px-8 bg-white">
      <div className="max-w-7xl mx-auto">
        <FadeUp className="text-center mb-14">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            Everything you need to manage your Etsy shop at scale
          </h2>
          <p className="text-gray-500 max-w-xl mx-auto">
            Six tool groups, one safe editing engine underneath every one of them.
          </p>
        </FadeUp>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {FEATURE_CLUSTERS.map((cluster, ci) => (
            <FadeUp key={cluster.title} delay={ci * 0.05}>
              <div className="be-card p-6 h-full">
                <h3 className="font-bold text-gray-900 mb-1.5">{cluster.title}</h3>
                <p className="text-sm text-gray-500 mb-4 leading-relaxed">{cluster.description}</p>
                <ul className="space-y-1.5">
                  {cluster.slugs.map((slug) => {
                    const fp = getFeaturePage(slug);
                    if (!fp) return null;
                    return (
                      <li key={slug}>
                        <Link
                          href={`/features/${slug}`}
                          className="text-sm text-indigo-600 hover:text-indigo-800 hover:underline inline-flex items-center gap-1.5"
                        >
                          <span aria-hidden="true">→</span> {fp.h1}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
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
  );
}
