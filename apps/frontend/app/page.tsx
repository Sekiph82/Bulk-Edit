import type { Metadata } from "next";
import HomeContent from "@/components/marketing/HomeContent";

export const metadata: Metadata = {
  title: "Bulk Edit App — Etsy Bulk Edit Tool | Preview, Apply, Revert Safely",
  description:
    "Bulk Edit App is the Etsy bulk edit tool for sellers who need to update titles, tags, prices, and photos across many listings at once — with full preview and one-click revert.",
  alternates: { canonical: "https://bulkeditapp.com/" },
  openGraph: {
    title: "Bulk Edit App — Etsy Bulk Edit Tool",
    description:
      "Update Etsy listings in bulk. Preview every change, apply safely, revert instantly.",
    url: "https://bulkeditapp.com/",
    siteName: "Bulk Edit App",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Bulk Edit App — Etsy Bulk Edit Tool",
    description:
      "Update Etsy listings in bulk. Preview every change, apply safely, revert instantly.",
  },
};

const ORGANIZATION_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "Bulk Edit App",
  url: "https://bulkeditapp.com/",
  description:
    "Bulk Edit App is a SaaS tool for Etsy sellers to bulk edit listings, preview changes, and revert safely.",
};

const SOFTWARE_APPLICATION_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Bulk Edit App",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "USD",
    description: "Free plan available",
  },
};

export default function Page() {
  return (
    <>
      {/* JSON-LD: accurate, no invented ratings/reviews/user counts */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(ORGANIZATION_JSON_LD) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(SOFTWARE_APPLICATION_JSON_LD) }}
      />
      <HomeContent />
    </>
  );
}
