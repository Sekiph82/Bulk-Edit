"use client";

import Link from "next/link";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import ConversionCTA from "@/components/marketing/ConversionCTA";
import FadeUp from "@/components/marketing/FadeUp";
import SEOFAQ from "@/components/marketing/SEOFAQ";
import type { ComparisonPage } from "@/lib/comparisonPages";

export default function ComparisonPageContent({ page }: { page: ComparisonPage }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />

      {/* Breadcrumb */}
      <div className="max-w-4xl mx-auto px-6 sm:px-8 pt-6 text-sm text-gray-400">
        <Link href="/" className="hover:text-gray-600">Home</Link>
        <span className="mx-2">/</span>
        <Link href="/compare" className="hover:text-gray-600">Compare</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-600">{page.h1}</span>
      </div>

      {/* Header */}
      <header className="max-w-4xl mx-auto px-6 sm:px-8 pt-6 pb-12">
        <FadeUp>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight leading-tight mb-4">
            {page.h1}
          </h1>
          <p className="text-lg text-gray-500 leading-relaxed">{page.metaDescription}</p>
        </FadeUp>
      </header>

      <article className="max-w-4xl mx-auto px-6 sm:px-8">
        <section className="mb-12">
          <FadeUp>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">{page.introHeading}</h2>
            {page.introParagraphs.map((p, i) => (
              <p key={i} className="text-base text-gray-700 leading-relaxed mb-3">{p}</p>
            ))}
          </FadeUp>
        </section>

        <section className="mb-12">
          <FadeUp>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">{page.whenToLookHeading}</h2>
            {page.whenToLookParagraphs.map((p, i) => (
              <p key={i} className="text-base text-gray-700 leading-relaxed mb-3">{p}</p>
            ))}
          </FadeUp>
        </section>

        <section className="mb-12">
          <FadeUp>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">{page.whereBulkEditFocusesHeading}</h2>
            {page.whereBulkEditFocusesParagraphs.map((p, i) => (
              <p key={i} className="text-base text-gray-700 leading-relaxed mb-3">{p}</p>
            ))}
          </FadeUp>
        </section>

        {page.featureSections.map((section) => (
          <section key={section.heading} className="mb-12">
            <FadeUp>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">{section.heading}</h2>
              {section.paragraphs.map((p, i) => (
                <p key={i} className="text-base text-gray-700 leading-relaxed mb-3">{p}</p>
              ))}
            </FadeUp>
          </section>
        ))}

        {/* Comparison table */}
        <section className="mb-12">
          <FadeUp>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Workflow comparison</h2>
            <div className="be-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[640px]">
                  <thead>
                    <tr className="bg-gray-100 border-b border-gray-200">
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                        Workflow need
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                        Bulk Edit App approach
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                        Other tool considerations
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {page.table.map((row, i) => (
                      <tr key={row.need} className={i % 2 === 1 ? "bg-gray-50" : "bg-white"}>
                        <td className="px-4 py-3 font-semibold text-gray-900 border-b border-gray-200 last:border-b-0">
                          {row.need}
                        </td>
                        <td className="px-4 py-3 text-indigo-700 font-medium border-b border-gray-200 last:border-b-0">
                          {row.bulkEditApproach}
                        </td>
                        <td className="px-4 py-3 text-gray-700 border-b border-gray-200 last:border-b-0">
                          {row.otherConsiderations}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </FadeUp>
        </section>

        {/* Questions to ask */}
        <section className="mb-12">
          <FadeUp>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Questions to ask before choosing</h2>
            <ul className="space-y-2.5">
              {page.questionsToAsk.map((q) => (
                <li key={q} className="flex items-start gap-3 text-sm text-gray-700">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0" />
                  {q}
                </li>
              ))}
            </ul>
          </FadeUp>
        </section>

        <FadeUp>
          <p className="mb-12 text-xs text-gray-500 leading-relaxed border-l-2 border-gray-200 pl-4">
            {page.disclaimer}
          </p>
        </FadeUp>
      </article>

      <SEOFAQ items={page.faq} title={`${page.h1} — frequently asked questions`} columns={1} />

      <ConversionCTA
        title="See how Bulk Edit App's preview-first workflow fits your shop"
        subtitle="Free plan available. No credit card required to start."
        primaryLabel="Try Bulk Edit App"
        secondaryLabel="View pricing"
        secondaryHref="/pricing"
        variant="hero"
      />

      <section className="max-w-4xl mx-auto px-6 sm:px-8 py-8 text-center">
        <p className="text-xs text-gray-400">
          The term &quot;Etsy&quot; is a trademark of Etsy, Inc. This application uses the Etsy API but is not endorsed or certified by Etsy, Inc.
        </p>
      </section>

      <MarketingFooter />
    </div>
  );
}
