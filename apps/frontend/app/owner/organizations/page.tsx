"use client";

import { useCallback, useEffect, useState } from "react";
import { adminListOrganizations, type AdminOrganization, type AdminPage as AdminPageType } from "@/lib/api";
import { PageHeader, SectionHeader, PaginationBar, Card, fmt } from "@/components/owner/OwnerUI";

export default function OwnerOrganizationsPage() {
  const [orgs, setOrgs] = useState<AdminPageType<AdminOrganization> | null>(null);
  const [page, setPage] = useState(1);

  const load = useCallback(() => {
    adminListOrganizations(page).then(setOrgs).catch(() => {});
  }, [page]);

  useEffect(() => { load(); }, [load]);

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Organizations" sub="Platform-wide organizations — superuser only" />
      <Card>
        <SectionHeader title="Organizations" total={orgs?.total} onRefresh={load} />
        {orgs && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                    <th className="pb-2 pr-4">Name</th>
                    <th className="pb-2 pr-4">Owner ID</th>
                    <th className="pb-2">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {orgs.items.map((o) => (
                    <tr key={o.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-4 font-medium text-gray-800">{o.name}</td>
                      <td className="py-2 pr-4 text-gray-400 font-mono text-xs">{o.owner_id}</td>
                      <td className="py-2 text-gray-400">{fmt(o.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <PaginationBar page={page} total={orgs.total} pageSize={25} onPage={setPage} />
          </>
        )}
      </Card>
    </main>
  );
}
