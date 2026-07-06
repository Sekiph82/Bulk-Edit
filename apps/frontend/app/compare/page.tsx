import type { Metadata } from "next";
import Link from "next/link";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import ConversionCTA from "@/components/marketing/ConversionCTA";
import { COMPARISON_PAGES } from "@/lib/comparisonPages";

export const metadata: Metadata = {
  title: "Compare Etsy Seller Tools — Bulk Edit App",
  description:
    "Compare Bulk Edit App with other Etsy seller tools from a workflow perspective, including bulk editing, previews, listing cleanup, and safer updates.",
  alternates: { canonical: "https://bulkeditapp.com/compare" },
  openGraph: {
    title: "Compare Etsy Seller Tools — Bulk Edit App",
    description:
      "Compare Bulk Edit App with other Etsy seller tools from a workflow perspective, including bulk editing, previews, listing cleanup, and safer updates.",
    url: "https://bulkeditapp.com/compare",
    siteName: "Bulk Edit App",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Compare Etsy Seller Tools — Bulk Edit App",
    description:
      "Compare Bulk Edit App with other Etsy seller tools from a workflow perspective, including bulk editing, previews, listing cleanup, and safer updates.",
  },
};

const COLLECTION_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  name: "Compare Etsy Seller Tools",
  url: "https://bulkeditapp.com/compare",
  description:
    "Compare common Etsy seller workflows for bulk editing, listing cleanup, previews, and safer update management.",
};

const BREADCRUMB_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    { "@type": "ListItem", position: 1, name: "Home", item: "https://bulkeditapp.com/" },
    { "@type": "ListItem", position: 2, name: "Compare", item: "https://bulkeditapp.com/compare" },
  ],
};

export default function ComparePage() {
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(COLLECTION_JSON_LD) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(BREADCRUMB_JSON_LD) }} />
      <div className="min-h-screen bg-gray-50">
        <MarketingNav />

        <section className="be-hero-bg pt-16 pb-14 px-6 sm:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
              Tool Comparisons
            </span>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight leading-tight mt-2 mb-5">
              Compare Etsy seller tools
            </h1>
            <p className="text-lg text-gray-500 leading-relaxed max-w-2xl mx-auto">
              Compare common Etsy seller workflows for bulk editing, listing cleanup, previews, and
              safer update management.
            </p>
          </div>
        </section>

        <section className="py-16 px-6 sm:px-8 bg-white">
          <div className="max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-6">
            {COMPARISON_PAGES.map((page) => (
              <Link key={page.slug} href={`/compare/${page.slug}`} className="be-card p-6 block hover:no-underline">
                <h2 className="font-semibold text-gray-900 mb-2">{page.h1}</h2>
                <p className="text-sm text-gray-500 leading-relaxed">{page.metaDescription}</p>
                <span className="mt-3 inline-block text-xs font-medium text-indigo-600">Read comparison →</span>
              </Link>
            ))}
          </div>
        </section>

        <ConversionCTA
          title="See how Bulk Edit App's preview-first workflow fits your shop"
          subtitle="Free plan available. No credit card required to start."
          primaryLabel="Try Bulk Edit App"
          secondaryLabel="View pricing"
          secondaryHref="/pricing"
          variant="hero"
        />

        <MarketingFooter />
      </div>
    </>
  );
}
