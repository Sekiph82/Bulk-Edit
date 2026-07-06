import type { Metadata } from "next";
import FaqContent from "@/components/marketing/FaqContent";

export const metadata: Metadata = {
  title: "FAQ — Bulk Edit App",
  description:
    "Answers about Etsy account safety, previewing changes, undoing bulk edits, billing, and AI tools in Bulk Edit App.",
  alternates: { canonical: "https://bulkeditapp.com/faq" },
  openGraph: {
    title: "FAQ — Bulk Edit App",
    description: "Common questions about safety, billing, AI tools, and Etsy connection.",
    url: "https://bulkeditapp.com/faq",
    siteName: "Bulk Edit App",
    type: "website",
  },
};

export default function Page() {
  return <FaqContent />;
}
