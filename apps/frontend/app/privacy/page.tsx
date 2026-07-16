import type { Metadata } from "next";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";

// NOTE: Starter legal content only. Must be reviewed by a qualified lawyer
// before production launch — it is not a substitute for professional legal
// advice and makes no certification, compliance, or legal-guarantee claims.

export const metadata: Metadata = {
  title: "Privacy Policy — Bulk Edit App",
  description: "How Bulk Edit App collects, uses, and protects Etsy seller data.",
  alternates: { canonical: "https://bulkeditapp.com/privacy" },
  robots: { index: true, follow: true },
};

const LAST_UPDATED = "2026-07-16";
const SUPPORT_EMAIL = "support@bulkeditapp.com";

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
                Bulk Edit App (&ldquo;we&rdquo;, &ldquo;us&rdquo;) is a software-as-a-service tool
                that helps Etsy sellers bulk-edit listings, sync shop data, apply AI-assisted
                optimizations, manage media, and control billing. This policy explains what data
                we collect, why, and how it is handled.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">2. Account data</h2>
              <p>
                When you create an account we collect your email address, name, and organization
                or shop details you provide. If you sign in with a password, we store only a
                salted hash of it — never the plain-text password.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">3. Etsy OAuth / API connection</h2>
              <p>
                When you connect your Etsy shop, Bulk Edit App uses Etsy&rsquo;s official OAuth2
                authorization flow. We never see or store your Etsy password — only a
                time-limited, revocable access token (and a refresh token, stored securely) used
                to read your shop data and, only after you preview and confirm a change, write
                updates to your listings on your behalf. Disconnecting your Etsy shop deletes our
                stored access and refresh tokens for that shop immediately. The term
                &ldquo;Etsy&rdquo; is a trademark of Etsy, Inc. This application uses the Etsy API
                but is not endorsed or certified by Etsy, Inc.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">4. Etsy shop &amp; listing data</h2>
              <p>
                To provide the service, we sync and store the shop and listing data needed to
                display and bulk-edit your shop: listing titles, descriptions, tags, prices,
                quantities, variations, images/media metadata, and listing/shop status. This data
                is used only to power the features you use and is scoped to your organization.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">5. Bulk edit &amp; media data</h2>
              <p>
                When you run a bulk edit or media job, we store the preview/diff, a backup
                snapshot of the affected listings taken before any write, the change history of
                what was applied, and — if you use the Product Video Generator — records of
                generated video renders. Backups exist so Magic Revert can restore a listing to
                its pre-edit state.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">6. AI features</h2>
              <p>
                Bulk Edit App includes optional, authenticated AI-assisted suggestion tools (for
                example, title, description, tag, and alt-text suggestions). Suggestions are shown
                to you for review only and are never applied to Etsy automatically — you decide
                which ones to accept.
              </p>
              <p>
                While we await Etsy&rsquo;s written confirmation on how AI processing of
                Etsy-derived listing data may be used, sending your Etsy listing content to an
                external, third-party AI provider is disabled by default in production. In this
                default state, suggestions are generated without processing live Etsy listing data
                through an external AI service. This is a conservative choice we have made while
                guidance is pending — it is not a statement that Etsy has prohibited or restricted
                AI use, and it is not a claim that Etsy has approved, certified, or endorsed any AI
                feature.
              </p>
              <p>
                We make no guarantee that using AI suggestions will improve sales, search ranking,
                or shop performance — you are responsible for reviewing any suggestion before
                applying it.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">7. Billing (Stripe)</h2>
              <p>
                Subscription billing is processed by Stripe. Bulk Edit App does not store your
                full card number — Stripe handles payment data directly under its own security
                and privacy standards. We store billing identifiers and subscription/plan status
                needed to manage your account.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">8. Email</h2>
              <p>
                We send account and security emails (e.g. password reset) and reply to messages
                sent through our contact form. We do not send marketing email you haven&rsquo;t
                asked for.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">9. Analytics &amp; logging</h2>
              <p>
                We may use privacy-conscious analytics and application logging to understand
                product usage and diagnose errors. Where analytics is enabled, we aim to minimize
                personal data collection and will document the specific provider and data
                collected separately as it is introduced — we do not name a provider here unless
                one is actually integrated.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">10. Data retention</h2>
              <p>
                We retain account and shop data while your account is active. Backup snapshots
                created before a bulk edit, media, or variation write (used to power Magic Revert)
                and CSV import/export job records are retained for a maximum of 30 days by default
                — after that window, they are automatically deleted by a daily automated retention
                cleanup process, and that specific change can no longer be reverted through the
                app. This 30-day window is Bulk Edit App&rsquo;s own conservative, configurable
                default; it is not a number mandated by Etsy. The first scheduled cleanup run
                completed successfully on 2026-07-15.
              </p>
              <p>
                Live synced listing and shop data may continue to be stored while you keep your
                Etsy shop connected, since this data is needed to display and bulk-edit your shop.
                Synced listing data is treated as stale after 6 hours and is refreshed, or you are
                shown a freshness warning, before it is relied on for a new write. Disconnecting an
                Etsy shop deletes its stored access/refresh tokens immediately and pauses any
                scheduled jobs tied to that shop.
              </p>
              <p>
                You can delete your account and its associated data at any time from within Bulk
                Edit App&rsquo;s billing settings, after re-confirming your password. Account
                deletion is blocked while any organization you own has an active or billable
                Stripe subscription — that subscription must be canceled or resolved first.
                Account deletion does not automatically cancel your Stripe subscription or delete
                your Stripe customer/subscription records; those remain in Stripe per Stripe&rsquo;s
                own retention practices and our accounting/legal requirements. Once the billing
                check passes, deleting your account removes your organization(s) and associated app
                data (shops, tokens, listings, bulk edit history, snapshots, subscriptions, and so
                on) from Bulk Edit App. You can also contact support (see below) with any deletion
                or data question.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">11. Security</h2>
              <p>
                We use reasonable technical and organizational safeguards to protect your data,
                including encrypted storage of Etsy tokens and hashed passwords. No method of
                storage or transmission is 100% secure, and we cannot guarantee absolute security.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">12. Your rights &amp; contact</h2>
              <p>
                To request access to, correction of, or deletion of your data, or to ask any
                question about this policy, contact us at{" "}
                <a href={`mailto:${SUPPORT_EMAIL}`} className="text-indigo-600 hover:underline">
                  {SUPPORT_EMAIL}
                </a>
                . We will respond and process requests within a reasonable timeframe.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">13. Children</h2>
              <p>
                Bulk Edit App is a business tool intended for adult Etsy sellers and is not
                directed to, or intended for use by, children.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-2">14. Changes to this policy</h2>
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
