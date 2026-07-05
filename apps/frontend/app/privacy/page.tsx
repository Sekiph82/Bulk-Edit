import type { Metadata } from "next";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";

// NOTE: Starter legal content only. Have a lawyer review this page before
// full public launch — it is not a substitute for professional legal advice
// and makes no certification, compliance, or legal-guarantee claims.

export const metadata: Metadata = {
  title: "Privacy Policy — Bulk Edit App",
  description: "How Bulk Edit App collects, uses, and protects your data.",
  alternates: { canonical: "https://bulkeditapp.com/privacy" },
  robots: { index: true, follow: true },
};

const LAST_UPDATED = "2026-07-04";
const SUPPORT_EMAIL = "support@bulk-edit.com"; // placeholder — replace with final support address before launch

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <MarketingNav />
      <main className="py-16 px-6 sm:px-8">
        <div className="max-w-3xl mx-auto prose prose-slate">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-2">Privacy Policy</h1>
          <p className="text-sm text-gray-400 mb-10">Last updated: {LAST_UPDATED}</p>

          <div className="space-y-8 text-gray-700 leading-relaxed">
            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">1. What Bulk Edit App is</h2>
              <p>
                Bulk Edit App (&ldquo;we&rdquo;, &ldquo;us&rdquo;) is a software-as-a-service tool that
                helps Etsy sellers manage and bulk-edit their Etsy shop listings. This policy
                explains what data we collect, why, and how it is handled.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">2. Account data</h2>
              <p>
                When you create an account we store your email address, hashed password, name,
                and organization details you provide. We never store your password in plain text.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">3. Etsy API connection</h2>
              <p>
                When you connect your Etsy shop, Bulk Edit App uses Etsy&rsquo;s official OAuth2
                authorization flow. We never receive or store your Etsy username or password —
                only a time-limited, revocable access token used to read and, with your
                confirmation, write listing data on your behalf. You can disconnect your shop at
                any time, which removes our access immediately. &ldquo;Etsy&rdquo; is a trademark
                of Etsy, Inc.; Bulk Edit App is an independent tool and is not endorsed or certified
                by Etsy, Inc.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">4. Billing</h2>
              <p>
                Subscription billing is processed by Stripe. Bulk Edit App does not store your full
                card number — Stripe handles payment data directly under its own security and
                privacy standards.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">5. Analytics &amp; logging</h2>
              <p>
                We may use privacy-conscious analytics and application logging to understand
                product usage and diagnose errors. Where analytics is enabled, we aim to minimize
                personal data collection and will document the specific provider and data
                collected separately as it is introduced.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">6. Data deletion &amp; contact</h2>
              <p>
                To request deletion of your account and associated data, or to ask any question
                about this policy, contact us at{" "}
                <a href={`mailto:${SUPPORT_EMAIL}`} className="text-indigo-600 hover:underline">
                  {SUPPORT_EMAIL}
                </a>
                . We will respond and process deletion requests within a reasonable timeframe.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">7. Changes to this policy</h2>
              <p>
                We may update this policy as the product evolves. Material changes will be
                reflected by updating the &ldquo;Last updated&rdquo; date above.
              </p>
            </section>
          </div>
        </div>
      </main>
      <MarketingFooter />
    </div>
  );
}
