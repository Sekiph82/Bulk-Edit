"use client";

import { useState } from "react";
import Link from "next/link";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import ConversionCTA from "@/components/marketing/ConversionCTA";
import FadeUp from "@/components/marketing/FadeUp";
import { BLOG_POSTS, BLOG_CATEGORIES } from "@/lib/blogPosts";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
}

export default function BlogIndexContent() {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const posts = activeCategory
    ? BLOG_POSTS.filter((p) => p.category === activeCategory)
    : BLOG_POSTS;

  const sorted = [...posts].sort(
    (a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />

      {/* Hero */}
      <section className="be-hero-bg pt-16 pb-14 px-6 sm:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <FadeUp>
            <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
              Etsy Seller Guides
            </span>
          </FadeUp>
          <FadeUp delay={0.08}>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight leading-tight mt-2 mb-5">
              Etsy seller guides for safer bulk editing
            </h1>
          </FadeUp>
          <FadeUp delay={0.14}>
            <p className="text-lg text-gray-500 leading-relaxed max-w-2xl mx-auto">
              Practical guides on bulk editing, listing cleanup, Etsy SEO, pricing, and safer update
              workflows — written for sellers managing more than a handful of listings.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* Category chips */}
      <section className="px-6 sm:px-8 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto py-5 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setActiveCategory(null)}
            className={`text-xs font-medium px-3.5 py-1.5 rounded-full border transition-colors ${
              activeCategory === null
                ? "bg-indigo-600 text-white border-indigo-600"
                : "text-gray-600 border-gray-200 hover:bg-gray-50"
            }`}
          >
            All guides
          </button>
          {BLOG_CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setActiveCategory(cat)}
              className={`text-xs font-medium px-3.5 py-1.5 rounded-full border transition-colors ${
                activeCategory === cat
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "text-gray-600 border-gray-200 hover:bg-gray-50"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </section>

      {/* Post grid */}
      <section className="py-16 px-6 sm:px-8 bg-white">
        <div className="max-w-6xl mx-auto">
          {sorted.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-12">No guides in this category yet.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {sorted.map((post, i) => (
                <FadeUp key={post.slug} delay={Math.min(i, 6) * 0.04}>
                  <Link
                    href={`/blog/${post.slug}`}
                    className="be-card p-6 h-full flex flex-col hover:no-underline"
                  >
                    <span className="inline-block text-[11px] font-semibold text-indigo-600 uppercase tracking-wide mb-3">
                      {post.category}
                    </span>
                    <h2 className="font-semibold text-gray-900 mb-2 leading-snug">{post.title}</h2>
                    <p className="text-sm text-gray-500 leading-relaxed flex-1">{post.description}</p>
                    <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
                      <span>{formatDate(post.publishedAt)}</span>
                      <span>{post.readingTime}</span>
                    </div>
                  </Link>
                </FadeUp>
              ))}
            </div>
          )}
        </div>
      </section>

      <ConversionCTA
        title="Ready to clean up your listings faster?"
        subtitle="Bulk Edit App previews every change before it touches Etsy, with automatic backups behind every apply."
        primaryLabel="Try Bulk Edit App"
        secondaryLabel="View pricing"
        secondaryHref="/pricing"
        variant="hero"
      />

      <MarketingFooter />
    </div>
  );
}
