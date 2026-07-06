"use client";

import { useCallback, useEffect, useState } from "react";
import { adminListContactSubmissions, type AdminContactSubmission, type AdminPage as AdminPageType } from "@/lib/api";
import { PageHeader, SectionHeader, PaginationBar, Badge, Card, fmt } from "@/components/owner/OwnerUI";

export default function OwnerContactSubmissionsPage() {
  const [subs, setSubs] = useState<AdminPageType<AdminContactSubmission> | null>(null);
  const [page, setPage] = useState(1);

  const load = useCallback(() => {
    adminListContactSubmissions(page).then(setSubs).catch(() => {});
  }, [page]);

  useEffect(() => { load(); }, [load]);

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Contact Submissions" sub="Real submissions from the public contact form — superuser only" />
      <Card>
        <SectionHeader title="Submissions" total={subs?.total} onRefresh={load} />
        {subs && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                    <th className="pb-2 pr-4">From</th>
                    <th className="pb-2 pr-4">Subject</th>
                    <th className="pb-2 pr-4">Message</th>
                    <th className="pb-2 pr-4">Emailed</th>
                    <th className="pb-2">Received</th>
                  </tr>
                </thead>
                <tbody>
                  {subs.items.map((s) => (
                    <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50 align-top">
                      <td className="py-2 pr-4">
                        <div className="font-medium text-gray-800">{s.name}</div>
                        <div className="text-xs text-gray-400">{s.email}</div>
                      </td>
                      <td className="py-2 pr-4 text-gray-700">{s.subject}</td>
                      <td className="py-2 pr-4 text-gray-500 max-w-sm truncate" title={s.message}>{s.message}</td>
                      <td className="py-2 pr-4"><Badge status={s.email_delivered ? "true" : "false"} /></td>
                      <td className="py-2 text-gray-400">{fmt(s.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <PaginationBar page={page} total={subs.total} pageSize={25} onPage={setPage} />
          </>
        )}
      </Card>
    </main>
  );
}
