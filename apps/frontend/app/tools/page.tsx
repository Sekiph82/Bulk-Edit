import type { Metadata } from "next";
import Link from "next/link";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import ConversionCTA from "@/components/marketing/ConversionCTA";
import { FREE_TOOLS } from "@/lib/freeTools";

export const metadata: Metadata = {
  title: "Free Etsy Seller Tools — Bulk Edit App",
  description:
    "Free Etsy seller tools for fee estimates, tag cleanup, listing reviews, and safer bulk editing workflows.",
  alternates: { canonical: "https://bulkeditapp.com/tools" },
  openGraph: {
    title: "Free Etsy Seller Tools — Bulk Edit App",
    description:
      "Free Etsy seller tools for fee estimates, tag cleanup, listing reviews, and safer bulk editing workflows.",
    url: "https://bulkeditapp.com/tools",
    siteName: "Bulk Edit App",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Free Etsy Seller Tools — Bulk Edit App",
    description:
      "Free Etsy seller tools for fee estimates, tag cleanup, listing reviews, and safer bulk editing workflows.",
  },
};

const COLLECTION_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  name: "Free Etsy Seller Tools",
  url: "https://bulkeditapp.com/tools",
  description:
    "Simple tools and checklists to help Etsy sellers review fees, tags, listing cleanup, and safer bulk update workflows.",
};

const BREADCRUMB_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    { "@type": "ListItem", position: 1, name: "Home", item: "https://bulkeditapp.com/" },
    { "@type": "ListItem", position: 2, name: "Tools", item: "https://bulkeditapp.com/tools" },
  ],
};

export default function ToolsPage() {
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(COLLECTION_JSON_LD) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(BREADCRUMB_JSON_LD) }} />
      <div className="min-h-screen bg-gray-50">
        <MarketingNav />

        <section className="be-hero-bg pt-16 pb-14 px-6 sm:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
              Free Tools
            </span>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight leading-tight mt-2 mb-5">
              Free Etsy seller tools
            </h1>
            <p className="text-lg text-gray-500 leading-relaxed max-w-2xl mx-auto">
              Simple tools and checklists to help Etsy sellers review fees, tags, listing cleanup,
              and safer bulk update workflows.
            </p>
          </div>
        </section>

        <section className="py-16 px-6 sm:px-8 bg-white">
          <div className="max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-6">
            {FREE_TOOLS.map((tool) => (
              <Link key={tool.slug} href={`/tools/${tool.slug}`} className="be-card p-6 block hover:no-underline">
                <h2 className="font-semibold text-gray-900 mb-2">{tool.title}</h2>
                <p className="text-sm text-gray-500 leading-relaxed">{tool.description}</p>
                <span className="mt-3 inline-block text-xs font-medium text-indigo-600">Open tool →</span>
              </Link>
            ))}
          </div>
        </section>

        <ConversionCTA
          title="Ready to update listings after reviewing them?"
          subtitle="Bulk Edit App previews every change before it touches Etsy, with automatic backups behind every apply."
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
