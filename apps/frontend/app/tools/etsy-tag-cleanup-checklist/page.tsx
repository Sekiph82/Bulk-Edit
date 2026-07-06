import type { Metadata } from "next";
import Link from "next/link";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import ConversionCTA from "@/components/marketing/ConversionCTA";
import SEOFAQ from "@/components/marketing/SEOFAQ";
import EtsyTagCleanupChecklist from "@/components/marketing/EtsyTagCleanupChecklist";
import { getFreeTool } from "@/lib/freeTools";

const tool = getFreeTool("etsy-tag-cleanup-checklist")!;
const url = "https://bulkeditapp.com/tools/etsy-tag-cleanup-checklist";

export const metadata: Metadata = {
  title: tool.metaTitle,
  description: tool.metaDescription,
  keywords: tool.targetKeywords,
  alternates: { canonical: url },
  openGraph: {
    title: tool.metaTitle,
    description: tool.metaDescription,
    url,
    siteName: "Bulk Edit App",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: tool.metaTitle,
    description: tool.metaDescription,
  },
};

const APP_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "Etsy Tag Cleanup Checklist",
  url,
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  description: tool.metaDescription,
  offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
};

const BREADCRUMB_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    { "@type": "ListItem", position: 1, name: "Home", item: "https://bulkeditapp.com/" },
    { "@type": "ListItem", position: 2, name: "Tools", item: "https://bulkeditapp.com/tools" },
    { "@type": "ListItem", position: 3, name: "Etsy Tag Cleanup Checklist", item: url },
  ],
};

const FAQ_ITEMS = [
  {
    q: "Is this an official Etsy tag generator?",
    a: "No. This is an independent tag-idea and cleanup helper built by Bulk Edit App, not an official Etsy tool.",
  },
  {
    q: "Does it use Etsy search volume?",
    a: "No. Bulk Edit App does not claim official Etsy search volume data. Ideas here come from your own tags and attributes, not a keyword database.",
  },
  {
    q: "Should I apply every suggestion?",
    a: "No — review suggestions before applying them. Treat everything here as tag ideas, not guaranteed keywords, and check each one against the real product.",
  },
  {
    q: "Can I clean up tags across multiple listings?",
    a: "This tool reviews one tag list at a time. Once you know the pattern of issues across your shop, Bulk Edit App's bulk tag editor can apply a cleanup across many listings with a preview before anything changes.",
  },
  {
    q: "How does this connect to Bulk Edit App?",
    a: "It doesn't automatically — this checklist runs entirely in your browser and doesn't touch your Etsy shop. When your tag list is ready, use Bulk Edit App to preview and apply the update across your listings.",
  },
];

export default function EtsyTagCleanupChecklistPage() {
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(APP_JSON_LD) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(BREADCRUMB_JSON_LD) }} />
      <div className="min-h-screen bg-gray-50">
        <MarketingNav />

        <div className="max-w-4xl mx-auto px-6 sm:px-8 pt-6 text-sm text-gray-400">
          <Link href="/" className="hover:text-gray-600">Home</Link>
          <span className="mx-2">/</span>
          <Link href="/tools" className="hover:text-gray-600">Tools</Link>
          <span className="mx-2">/</span>
          <span className="text-gray-600">Etsy Tag Cleanup Checklist</span>
        </div>

        <header className="max-w-4xl mx-auto px-6 sm:px-8 pt-6 pb-10 text-center">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight leading-tight mb-4">
            Etsy Tag Cleanup Checklist
          </h1>
          <p className="text-lg text-gray-500 leading-relaxed max-w-2xl mx-auto">
            Review Etsy listing tags for duplicates, vague phrases, missing attributes, and bulk cleanup opportunities.
          </p>
        </header>

        <section className="max-w-4xl mx-auto px-6 sm:px-8 pb-16">
          <EtsyTagCleanupChecklist />
        </section>

        <section className="max-w-3xl mx-auto px-6 sm:px-8 pb-16 text-center">
          <p className="text-sm text-gray-600 mb-4">When your tag list is ready, preview bulk updates before applying them.</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/blog/etsy-tag-generator-guide" className="be-btn-secondary px-6 py-2.5 text-sm">
              Read the tag generator guide
            </Link>
            <Link href="/blog/etsy-seo-title-tag-optimization-checklist" className="be-btn-secondary px-6 py-2.5 text-sm">
              Read the SEO checklist
            </Link>
            <Link href="/pricing" className="be-btn-secondary px-6 py-2.5 text-sm">
              View pricing
            </Link>
          </div>
        </section>

        <SEOFAQ items={FAQ_ITEMS} title="Etsy Tag Cleanup Checklist — frequently asked questions" columns={1} />

        <ConversionCTA
          title="Ready to apply tag cleanup across your shop?"
          subtitle="Bulk Edit App previews every tag change before it touches Etsy, with automatic backups behind every apply."
          primaryLabel="Try Bulk Edit App"
          secondaryLabel="View pricing"
          secondaryHref="/pricing"
        />

        <MarketingFooter />
      </div>
    </>
  );
}
