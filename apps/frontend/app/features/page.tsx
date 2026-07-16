import type { Metadata } from "next";
import FeaturesContent from "@/components/marketing/FeaturesContent";

export const metadata: Metadata = {
  title: "Etsy Bulk Edit Features — Bulk Edit App",
  description:
    "Bulk title, tag, price, photo, CSV, variation, pricing, shop insights, and revert workflows for Etsy sellers.",
  alternates: { canonical: "https://bulkeditapp.com/features" },
  openGraph: {
    title: "Etsy Bulk Edit Features — Bulk Edit App",
    description: "Everything Etsy sellers need to edit listings in bulk, safely.",
    url: "https://bulkeditapp.com/features",
    siteName: "Bulk Edit App",
    type: "website",
  },
};

export default function Page() {
  return <FeaturesContent />;
}
