import type { Metadata } from "next";
import Link from "next/link";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import ConversionCTA from "@/components/marketing/ConversionCTA";
import SEOFAQ from "@/components/marketing/SEOFAQ";
import EtsyFeeCalculator from "@/components/marketing/EtsyFeeCalculator";
import { getFreeTool } from "@/lib/freeTools";

const tool = getFreeTool("etsy-fee-calculator")!;
const url = "https://bulkeditapp.com/tools/etsy-fee-calculator";

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
  name: "Etsy Fee Calculator",
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
    { "@type": "ListItem", position: 3, name: "Etsy Fee Calculator", item: url },
  ],
};

const FAQ_ITEMS = [
  {
    q: "Is this an official Etsy fee calculator?",
    a: "No. This is an independent estimate tool built by Bulk Edit App, not an official Etsy product. Always verify current fees in your own Etsy account and Etsy's official documentation.",
  },
  {
    q: "Why are the fee rates editable?",
    a: "Etsy's transaction, payment processing, and ad fees can vary by country, currency, and account, and can change over time. Editable defaults let you match the estimate to your own situation instead of relying on one fixed number.",
  },
  {
    q: "Does this include Etsy Ads or Offsite Ads?",
    a: "There's an optional, editable Offsite Ads percentage field. Etsy Ads spend isn't modeled separately since it varies per campaign rather than per sale — factor it in using the \"Other costs\" field if relevant.",
  },
  {
    q: "Can I use this before bulk price updates?",
    a: "Yes — that's the intended use. Check a few representative listings here before applying a price rule across many listings at once, since cost structure often varies more than sellers expect.",
  },
  {
    q: "Does Bulk Edit App change my prices automatically from this calculator?",
    a: "No. This calculator only estimates numbers in your browser — it doesn't connect to your Etsy shop or change any listing. Price changes in Bulk Edit App always go through a separate preview-and-confirm bulk edit workflow.",
  },
];

export default function EtsyFeeCalculatorPage() {
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
          <span className="text-gray-600">Etsy Fee Calculator</span>
        </div>

        <header className="max-w-4xl mx-auto px-6 sm:px-8 pt-6 pb-10 text-center">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight leading-tight mb-4">
            Etsy Fee Calculator
          </h1>
          <p className="text-lg text-gray-500 leading-relaxed max-w-2xl mx-auto">
            Estimate Etsy seller fees, costs, and profit before making pricing updates across your listings.
          </p>
        </header>

        <section className="max-w-4xl mx-auto px-6 sm:px-8 pb-16">
          <EtsyFeeCalculator />
        </section>

        <section className="max-w-3xl mx-auto px-6 sm:px-8 pb-16 text-center">
          <p className="text-sm text-gray-600 mb-4">Preview price updates before applying them in bulk.</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/blog/how-to-calculate-real-profit-on-etsy" className="be-btn-secondary px-6 py-2.5 text-sm">
              Read the profit guide
            </Link>
            <Link href="/pricing" className="be-btn-secondary px-6 py-2.5 text-sm">
              View pricing
            </Link>
          </div>
        </section>

        <SEOFAQ items={FAQ_ITEMS} title="Etsy Fee Calculator — frequently asked questions" columns={1} />

        <ConversionCTA
          title="Ready to review and apply pricing changes safely?"
          subtitle="Bulk Edit App previews every price change before it touches Etsy, with automatic backups behind every apply."
          primaryLabel="Try Bulk Edit App"
          secondaryLabel="View pricing"
          secondaryHref="/pricing"
        />

        <MarketingFooter />
      </div>
    </>
  );
}
