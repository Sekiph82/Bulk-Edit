import type { Metadata } from "next";
import FeaturesContent from "@/components/marketing/FeaturesContent";

export const metadata: Metadata = {
  title: "Etsy Bulk Edit Features — Bulk-Edit",
  description:
    "Bulk title, tag, price, photo, and variation editing for Etsy sellers — with AI optimization, CSV import/export, dynamic pricing, listing health scoring, and Magic Revert.",
  alternates: { canonical: "https://bulkeditapp.com/features" },
  openGraph: {
    title: "Etsy Bulk Edit Features — Bulk-Edit",
    description: "Everything Etsy sellers need to edit listings in bulk, safely.",
    url: "https://bulkeditapp.com/features",
    siteName: "Bulk-Edit",
    type: "website",
  },
};

export default function Page() {
  return <FeaturesContent />;
}
