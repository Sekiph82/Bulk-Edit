"use client";

import { useCallback, useEffect, useState } from "react";
import { adminListAuditLog, type AdminAuditEvent, type AdminPage as AdminPageType } from "@/lib/api";
import { PageHeader, SectionHeader, PaginationBar, Card, fmt } from "@/components/owner/OwnerUI";

export default function OwnerAuditLogsPage() {
  const [log, setLog] = useState<AdminPageType<AdminAuditEvent> | null>(null);
  const [page, setPage] = useState(1);

  const load = useCallback(() => {
    adminListAuditLog(page).then(setLog).catch(() => {});
  }, [page]);

  useEffect(() => { load(); }, [load]);

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Audit Logs" sub="Real, persisted platform events across all organizations — superuser only" />
      <Card>
        <SectionHeader title="Audit Log" total={log?.total} onRefresh={load} />
        {log && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                    <th className="pb-2 pr-4">Event Type</th>
                    <th className="pb-2 pr-4">Entity</th>
                    <th className="pb-2 pr-4">Message</th>
                    <th className="pb-2">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {log.items.map((e) => (
                    <tr key={e.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-4 font-mono text-xs text-indigo-700">{e.event_type}</td>
                      <td className="py-2 pr-4 text-gray-400 text-xs">
                        {e.entity_type ?? "—"}{e.entity_id ? ` / ${e.entity_id.slice(0, 8)}…` : ""}
                      </td>
                      <td className="py-2 pr-4 text-gray-500 max-w-xs truncate">{e.message ?? "—"}</td>
                      <td className="py-2 text-gray-400">{fmt(e.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <PaginationBar page={page} total={log.total} pageSize={25} onPage={setPage} />
          </>
        )}
      </Card>
    </main>
  );
}
