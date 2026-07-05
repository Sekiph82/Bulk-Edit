import type { Metadata } from "next";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";

// NOTE: Starter legal content only. Have a lawyer review this page before
// full public launch — it is not a substitute for professional legal advice
// and makes no certification, compliance, or legal-guarantee claims.

export const metadata: Metadata = {
  title: "Terms of Service — Bulk Edit App",
  description: "The terms governing use of the Bulk Edit App service.",
  alternates: { canonical: "https://bulkeditapp.com/terms" },
  robots: { index: true, follow: true },
};

const LAST_UPDATED = "2026-07-04";
const SUPPORT_EMAIL = "support@bulk-edit.com"; // placeholder — replace with final support address before launch

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />
      <main className="py-16 px-6 sm:px-8">
        <div className="max-w-3xl mx-auto prose prose-slate">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-2">Terms of Service</h1>
          <p className="text-sm text-gray-400 mb-10">Last updated: {LAST_UPDATED}</p>

          <div className="space-y-8 text-gray-700 leading-relaxed">
            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">1. Acceptance of terms</h2>
              <p>
                By creating an account or using Bulk Edit App, you agree to these Terms of Service.
                If you do not agree, do not use the service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">2. The service</h2>
              <p>
                Bulk Edit App is a third-party tool that connects to your Etsy shop via the official
                Etsy API to help you bulk-edit listings, preview changes, and revert them. Bulk Edit App
                is not affiliated with, endorsed by, or certified by Etsy, Inc. &ldquo;Etsy&rdquo;
                is a trademark of Etsy, Inc.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">3. Your responsibilities</h2>
              <p>
                You are responsible for the accuracy of the listing content you choose to bulk
                edit and for reviewing every preview before confirming an apply. Bulk Edit App shows
                you a full diff before any write to Etsy, but the decision to apply is always
                yours.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">4. Billing</h2>
              <p>
                Paid plans are billed via Stripe on a recurring basis as described on the{" "}
                <a href="/pricing" className="text-indigo-600 hover:underline">pricing page</a>.
                You may cancel at any time; your plan remains active until the end of the current
                billing period.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">5. No warranty</h2>
              <p>
                Bulk Edit App is provided &ldquo;as is&rdquo; without warranties of any kind, express
                or implied. We do not guarantee uninterrupted or error-free operation, or that
                use of the service will increase sales or shop performance.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">6. Limitation of liability</h2>
              <p>
                To the maximum extent permitted by law, Bulk Edit App and its operators are not
                liable for indirect, incidental, or consequential damages arising from use of the
                service, including changes made to your Etsy shop that you confirmed and applied.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">7. Termination</h2>
              <p>
                You may stop using Bulk Edit App and disconnect your Etsy shop at any time. We may
                suspend or terminate accounts that violate these terms or misuse the service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">8. Contact</h2>
              <p>
                Questions about these terms can be sent to{" "}
                <a href={`mailto:${SUPPORT_EMAIL}`} className="text-indigo-600 hover:underline">
                  {SUPPORT_EMAIL}
                </a>
                .
              </p>
            </section>
          </div>
        </div>
      </main>
      <MarketingFooter />
    </div>
  );
}
