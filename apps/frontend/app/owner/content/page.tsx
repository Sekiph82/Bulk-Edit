"use client";

import { PageHeader, Card } from "@/components/owner/OwnerUI";

// Placeholder only. There is no CMS/blog backend yet — do not build a fake
// one. When a real blog exists, public posts belong at bulkeditapp.com/blog
// and management belongs here.
export default function OwnerContentPage() {
  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Content" sub="Blog / CMS management — superuser only" />
      <Card>
        <p className="text-sm text-gray-700 font-medium mb-2">Not built yet.</p>
        <p className="text-sm text-gray-500">
          There is no blog or CMS backend in this app. This page is a placeholder for a future
          content-management surface — when a public blog is added at{" "}
          <code className="bg-gray-100 px-1 rounded">bulkeditapp.com/blog</code>, its management UI belongs here,
          not on the public site.
        </p>
      </Card>
    </main>
  );
}
