import type { Metadata } from "next";
import FaqContent from "@/components/marketing/FaqContent";

export const metadata: Metadata = {
  title: "FAQ — Bulk-Edit",
  description:
    "Answers about Etsy account safety, previewing changes, undoing bulk edits, billing, and AI tools in Bulk-Edit.",
  alternates: { canonical: "https://bulkeditapp.com/faq" },
  openGraph: {
    title: "FAQ — Bulk-Edit",
    description: "Common questions about safety, billing, AI tools, and Etsy connection.",
    url: "https://bulkeditapp.com/faq",
    siteName: "Bulk-Edit",
    type: "website",
  },
};

export default function Page() {
  return <FaqContent />;
}
