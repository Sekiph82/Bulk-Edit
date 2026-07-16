import type { Metadata } from "next";
import Link from "next/link";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";

export const metadata: Metadata = {
  title: "Account Access Temporarily Paused — Bulk Edit App",
  description: "New account sign-ups are temporarily paused while we complete a required Etsy verification step. Contact us for a status update.",
  robots: { index: false, follow: false },
  alternates: { canonical: "https://bulkeditapp.com/private-beta" },
};

export default function PrivateBetaPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />

      <section className="py-24 px-6 sm:px-8">
        <div className="max-w-xl mx-auto text-center">
          <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
            Temporary pause
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight leading-tight mb-5">
            New account access is temporarily paused
          </h1>
          <p className="text-lg text-gray-500 leading-relaxed mb-8">
            Bulk Edit App is a finished, production product — this pause is not a product-readiness
            issue. New account sign-ups are temporarily paused while we complete a required Etsy
            developer-account verification step. If you&rsquo;d like a status update, contact us
            at{" "}
            <a href="mailto:support@bulkeditapp.com" className="text-indigo-600 hover:underline">
              support@bulkeditapp.com
            </a>
            .
          </p>
          <Link href="/contact-us" className="be-btn-primary px-8 py-3 text-base">
            Contact us
          </Link>
        </div>
      </section>

      <MarketingFooter />
    </div>
  );
}
