import type { Metadata } from "next";
import ContactContent from "@/components/marketing/ContactContent";

export const metadata: Metadata = {
  title: "Contact Us — Bulk-Edit",
  description: "Get in touch with the Bulk-Edit team about billing, Etsy connection, or safety questions.",
  alternates: { canonical: "https://bulkeditapp.com/contact-us" },
  openGraph: {
    title: "Contact Us — Bulk-Edit",
    description: "Get in touch with the Bulk-Edit team.",
    url: "https://bulkeditapp.com/contact-us",
    siteName: "Bulk-Edit",
    type: "website",
  },
};

export default function Page() {
  return <ContactContent />;
}
