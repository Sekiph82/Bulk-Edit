"use client";

import { PageHeader, Card } from "@/components/owner/OwnerUI";

// Email delivery attempts (password reset, contact notifications) are not
// yet persisted anywhere — app/services/email.py only logs them, it never
// writes a row. Rather than fake a history here, this page states that
// plainly and points at the real place delivery failures currently surface.
export default function OwnerEmailsPage() {
  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Emails" sub="Outbound email delivery — superuser only" />
      <Card>
        <p className="text-sm text-gray-700 mb-2 font-medium">No send history is persisted yet.</p>
        <p className="text-sm text-gray-500">
          Password-reset and contact-notification emails go through <code className="bg-gray-100 px-1 rounded">app/services/email.py</code>,
          which logs each attempt (provider, recipient domain/count, sent/error) but does not write to a database
          table. Building a real <code className="bg-gray-100 px-1 rounded">email_events</code> table is a follow-up —
          not implemented here to avoid faking history this page can&apos;t actually show yet.
        </p>
        <p className="text-sm text-gray-500 mt-3">
          Until then, check backend logs (<code className="bg-gray-100 px-1 rounded">doctl apps logs &lt;app-id&gt; api --type run</code>)
          for delivery outcomes, or the Contact Submissions page for real per-submission delivery status.
        </p>
      </Card>
    </main>
  );
}
