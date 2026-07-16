import type { Metadata } from "next";
import PricingContent from "@/components/marketing/PricingContent";

export const metadata: Metadata = {
  title: "Pricing — Bulk Edit App",
  description:
    "Simple, transparent pricing for Etsy sellers. Start free, upgrade to Basic or Pro for more bulk edits, advanced workflows, and automation.",
  alternates: { canonical: "https://bulkeditapp.com/pricing" },
  openGraph: {
    title: "Pricing — Bulk Edit App",
    description: "Simple, transparent pricing for Etsy sellers.",
    url: "https://bulkeditapp.com/pricing",
    siteName: "Bulk Edit App",
    type: "website",
  },
};

export default function Page() {
  return <PricingContent />;
}
