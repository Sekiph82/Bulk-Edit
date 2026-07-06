import type { Metadata } from "next";
import { getComparisonPage } from "@/lib/comparisonPages";
import ComparisonPageContent from "@/components/marketing/ComparisonPageContent";

const page = getComparisonPage("bulk-edit-app-vs-evlista")!;
const url = "https://bulkeditapp.com/compare/bulk-edit-app-vs-evlista";

export const metadata: Metadata = {
  title: page.metaTitle,
  description: page.metaDescription,
  keywords: page.targetKeywords,
  alternates: { canonical: url },
  openGraph: {
    title: page.metaTitle,
    description: page.metaDescription,
    url,
    siteName: "Bulk Edit App",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: page.metaTitle,
    description: page.metaDescription,
  },
};

const WEBPAGE_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebPage",
  name: page.h1,
  description: page.metaDescription,
  url,
};

const BREADCRUMB_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    { "@type": "ListItem", position: 1, name: "Home", item: "https://bulkeditapp.com/" },
    { "@type": "ListItem", position: 2, name: "Compare", item: "https://bulkeditapp.com/compare" },
    { "@type": "ListItem", position: 3, name: page.h1, item: url },
  ],
};

export default function Page() {
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(WEBPAGE_JSON_LD) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(BREADCRUMB_JSON_LD) }} />
      <ComparisonPageContent page={page} />
    </>
  );
}
