"use client";

import Link from "next/link";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import ConversionCTA from "@/components/marketing/ConversionCTA";
import FadeUp from "@/components/marketing/FadeUp";
import type { BlogPost } from "@/lib/blogPosts";
import { getRelatedPosts } from "@/lib/blogPosts";

function slugifyHeading(heading: string): string {
  return heading
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
}

export default function BlogArticleContent({ post }: { post: BlogPost }) {
  const related = getRelatedPosts(post);

  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />

      {/* Breadcrumb */}
      <div className="max-w-3xl mx-auto px-6 sm:px-8 pt-6 text-sm text-gray-400">
        <Link href="/" className="hover:text-gray-600">Home</Link>
        <span className="mx-2">/</span>
        <Link href="/blog" className="hover:text-gray-600">Blog</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-600">{post.title}</span>
      </div>

      {/* Header */}
      <header className="max-w-3xl mx-auto px-6 sm:px-8 pt-6 pb-10">
        <FadeUp>
          <span className="inline-block text-xs font-semibold text-indigo-600 uppercase tracking-wide mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
            {post.category}
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight leading-tight mb-4">
            {post.title}
          </h1>
          <p className="text-lg text-gray-500 leading-relaxed mb-5">{post.description}</p>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-400">
            <span>By {post.author}</span>
            <span>·</span>
            <span>Published {formatDate(post.publishedAt)}</span>
            {post.updatedAt && (
              <>
                <span>·</span>
                <span>Updated {formatDate(post.updatedAt)}</span>
              </>
            )}
            <span>·</span>
            <span>{post.readingTime}</span>
          </div>
        </FadeUp>
      </header>

      {/* Table of contents */}
      <section className="max-w-3xl mx-auto px-6 sm:px-8 pb-10">
        <FadeUp>
          <nav aria-label="Table of contents" className="be-card p-5">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">In this guide</p>
            <ol className="space-y-1.5">
              {post.sections.map((section, i) => (
                <li key={section.heading} className="text-sm">
                  <a href={`#${slugifyHeading(section.heading)}`} className="text-indigo-600 hover:underline">
                    {i + 1}. {section.heading}
                  </a>
                </li>
              ))}
            </ol>
          </nav>
        </FadeUp>
      </section>

      {/* Intro + body */}
      <article className="max-w-3xl mx-auto px-6 sm:px-8 pb-4">
        <FadeUp>
          <p className="text-base text-gray-700 leading-relaxed mb-10">{post.intro}</p>
        </FadeUp>

        {post.sections.map((section) => (
          <section key={section.heading} id={slugifyHeading(section.heading)} className="mb-10 scroll-mt-24">
            <FadeUp>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">{section.heading}</h2>
              <div className="space-y-3">
                {section.paragraphs.map((p, i) => (
                  <p key={i} className="text-base text-gray-700 leading-relaxed">{p}</p>
                ))}
              </div>
              {section.list && (
                <ul className="mt-4 space-y-2">
                  {section.list.map((item) => (
                    <li key={item} className="flex items-start gap-3 text-sm text-gray-700">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              )}
            </FadeUp>
          </section>
        ))}

        {post.comparisonTable && (
          <FadeUp>
            <div className="mb-10 overflow-x-auto">
              <table className="w-full text-sm border border-gray-200 rounded-xl overflow-hidden">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide">
                    <th className="p-3">Aspect</th>
                    <th className="p-3">Bulk Edit App</th>
                    <th className="p-3">Vela</th>
                    <th className="p-3">eRank</th>
                  </tr>
                </thead>
                <tbody>
                  {post.comparisonTable.map((row) => (
                    <tr key={row.aspect} className="border-t border-gray-100 align-top">
                      <td className="p-3 font-medium text-gray-800">{row.aspect}</td>
                      <td className="p-3 text-gray-600">{row.bulkEditApp}</td>
                      <td className="p-3 text-gray-600">{row.vela}</td>
                      <td className="p-3 text-gray-600">{row.erank}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </FadeUp>
        )}

        {post.checklist && (
          <FadeUp>
            <div className="mb-10 be-card p-6 bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-100">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Quick checklist</h2>
              <ul className="space-y-2.5">
                {post.checklist.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-gray-700">
                    <span className="mt-0.5 w-5 h-5 rounded-full bg-white border border-indigo-200 flex items-center justify-center flex-shrink-0">
                      <svg className="w-3 h-3 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    </span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </FadeUp>
        )}

        {post.disclaimer && (
          <FadeUp>
            <p className="mb-10 text-xs text-gray-500 leading-relaxed border-l-2 border-gray-200 pl-4">
              {post.disclaimer}
            </p>
          </FadeUp>
        )}
      </article>

      <ConversionCTA
        title={post.ctaTitle}
        subtitle={post.ctaBody}
        primaryLabel="Try Bulk Edit App"
        secondaryLabel={post.secondaryCtaLabel ?? "View pricing"}
        secondaryHref={post.secondaryCtaHref ?? "/pricing"}
      />

      {related.length > 0 && (
        <section className="py-16 px-6 sm:px-8 bg-white border-t border-gray-100">
          <div className="max-w-3xl mx-auto">
            <FadeUp>
              <h2 className="text-lg font-bold text-gray-900 mb-6">Related guides</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {related.map((rp) => (
                  <Link key={rp.slug} href={`/blog/${rp.slug}`} className="be-card p-5 block hover:no-underline">
                    <h3 className="font-semibold text-gray-900 text-sm mb-1">{rp.title}</h3>
                    <p className="text-xs text-gray-500">{rp.description}</p>
                  </Link>
                ))}
              </div>
            </FadeUp>
          </div>
        </section>
      )}

      <section className="max-w-3xl mx-auto px-6 sm:px-8 py-8 text-center">
        <p className="text-xs text-gray-400">
          Bulk Edit App is an independent tool and is not endorsed by Etsy, Inc. Etsy is a trademark of Etsy, Inc.
        </p>
      </section>

      <MarketingFooter />
    </div>
  );
}
