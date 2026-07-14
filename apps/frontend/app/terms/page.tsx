import type { Metadata } from "next";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";

// NOTE: Starter legal content only. Must be reviewed by a qualified lawyer
// before production launch — it is not a substitute for professional legal
// advice and makes no certification, compliance, or legal-guarantee claims.

export const metadata: Metadata = {
  title: "Terms of Service — Bulk Edit App",
  description: "Terms governing use of Bulk Edit App.",
  alternates: { canonical: "https://bulkeditapp.com/terms" },
  robots: { index: true, follow: true },
};

const LAST_UPDATED = "2026-07-13";
const SUPPORT_EMAIL = "support@bulkeditapp.com";
const LEGAL_ENTITY_NAME = process.env.NEXT_PUBLIC_LEGAL_ENTITY_NAME || "Bulk Edit App";

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
                By creating an account or using Bulk Edit App, you agree to these Terms of
                Service. If you do not agree, do not use the service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">2. The service</h2>
              <p>
                Bulk Edit App is a seller-authorized listing management utility that helps Etsy
                sellers synchronize their own listings, prepare bulk changes, review exact
                before-and-after differences, and explicitly confirm changes before submission
                through Etsy&rsquo;s documented API. Bulk Edit App complements Etsy&rsquo;s seller
                tools. Orders, checkout, payments, and core shop management remain within Etsy.
                The term &ldquo;Etsy&rdquo; is a trademark of Etsy, Inc. This application uses the
                Etsy API but is not endorsed or certified by Etsy, Inc.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">3. Your account responsibilities</h2>
              <p>
                You are responsible for providing accurate account information, protecting your
                login credentials, and all activity that takes place through your account.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">4. Your Etsy shop responsibility</h2>
              <p>
                You are responsible for the Etsy shop you connect and for the content of your
                listings. Bulk Edit App shows you a full preview before any write, but the
                decision to apply a change is always yours — you must review each preview before
                confirming, and you remain responsible for your listings&rsquo; compliance with
                Etsy&rsquo;s own policies and rules.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">5. Bulk edit risk &amp; preview</h2>
              <p>
                Bulk Edit App provides preview, backup snapshot, and Magic Revert tools designed
                to make bulk changes safe to apply and easy to undo. You must explicitly confirm
                before any write reaches Etsy. We cannot guarantee that every possible Etsy or
                third-party API issue can be undone or reversed.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">6. AI tools</h2>
              <p>
                AI-generated titles, descriptions, tags, and other suggestions are suggestions
                only. We make no guarantee of increased sales, search ranking, or shop
                performance from using them. You must review AI output before applying it to your
                listings.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">7. Media &amp; video tools</h2>
              <p>
                Generated media (including Product Video Generator output) must be reviewed by
                you before use. You are responsible for ensuring any media you upload or apply to
                a listing complies with applicable rights and Etsy&rsquo;s content policies.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">8. Billing</h2>
              <p>
                Paid plans are billed via Stripe on a recurring basis as described on the{" "}
                <a href="/pricing" className="text-indigo-600 hover:underline">pricing page</a>.
                Subscriptions renew automatically unless canceled before the next billing period.
                Plan limits apply as published. We do not yet have a formal refund policy in
                place; refund requests are handled case-by-case through support.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">9. Acceptable use</h2>
              <p>
                You may not use Bulk Edit App to abuse, scrape, or gain unauthorized access to
                any system, to send spam, or for any illegal activity.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">10. Service availability</h2>
              <p>
                We do not guarantee uninterrupted or error-free operation. Outages or changes to
                Etsy&rsquo;s API, Stripe, or other third-party services we depend on may affect
                the availability of features.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">11. Termination</h2>
              <p>
                You may stop using Bulk Edit App and disconnect your Etsy shop at any time. We
                may suspend or terminate accounts that violate these terms or misuse the service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">12. Disclaimers</h2>
              <p>
                Bulk Edit App is provided &ldquo;as is&rdquo; without warranties of any kind,
                express or implied. We do not guarantee any specific sales, search ranking, or
                revenue outcome from using the service.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">13. Limitation of liability</h2>
              <p>
                To the maximum extent permitted by law, Bulk Edit App and its operators are not
                liable for indirect, incidental, or consequential damages arising from use of the
                service, including changes made to your Etsy shop that you previewed, confirmed,
                and applied.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">14. Changes to these terms</h2>
              <p>
                We may update these terms as the product evolves. Material changes will be
                reflected by updating the &ldquo;Last updated&rdquo; date above.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">15. Etsy API developer disclaimer</h2>
              <p>
                This Application is solely provided by {LEGAL_ENTITY_NAME} (the &ldquo;Application
                Developer&rdquo;). You acknowledge that Etsy, Inc. and its affiliates are not the
                Application Developer, do not provide the Application service, and make no
                warranties of any kind with respect to the Application or data accessed through
                it. {LEGAL_ENTITY_NAME} represents that its use of the Etsy Open API v3 complies
                with Etsy&rsquo;s API Terms of Use as in effect at the time of use, and will
                promptly correct or remove any feature found to violate those terms upon notice
                from Etsy.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">16. Contact</h2>
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
