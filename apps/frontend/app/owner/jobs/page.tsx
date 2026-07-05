"use client";

import { useCallback, useEffect, useState } from "react";
import {
  adminListScheduledJobs,
  adminPauseScheduledJob,
  adminResumeScheduledJob,
  type AdminScheduledJobSummary,
  type AdminPage as AdminPageType,
} from "@/lib/api";
import { PageHeader, SectionHeader, PaginationBar, Badge, Card, fmt } from "@/components/owner/OwnerUI";

export default function OwnerJobsPage() {
  const [jobs, setJobs] = useState<AdminPageType<AdminScheduledJobSummary> | null>(null);
  const [page, setPage] = useState(1);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    adminListScheduledJobs(page).then(setJobs).catch(() => {});
  }, [page]);

  useEffect(() => { load(); }, [load]);

  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(null), 3000); };

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Jobs" sub="Scheduled sync, draft, and pricing jobs across all organizations — superuser only" />
      {msg && <div className="mb-4 bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm px-4 py-2 rounded-lg">{msg}</div>}
      <Card>
        <SectionHeader title="Scheduled Jobs" total={jobs?.total} onRefresh={load} />
        {jobs && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                    <th className="pb-2 pr-4">Name</th>
                    <th className="pb-2 pr-4">Type</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2 pr-4">Runs</th>
                    <th className="pb-2 pr-4">Next Run</th>
                    <th className="pb-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.items.map((j) => (
                    <tr key={j.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-4 font-medium text-gray-800">{j.name}</td>
                      <td className="py-2 pr-4 text-gray-500">{j.job_type}</td>
                      <td className="py-2 pr-4"><Badge status={j.status} /></td>
                      <td className="py-2 pr-4 text-gray-500">{j.run_count}</td>
                      <td className="py-2 pr-4 text-gray-400">{fmt(j.next_run_at)}</td>
                      <td className="py-2 flex gap-2">
                        {(j.status === "active" || j.status === "idle") && (
                          <button
                            type="button"
                            onClick={() => adminPauseScheduledJob(j.id).then((r) => { flash(r.message); load(); })}
                            className="text-xs text-yellow-600 hover:underline"
                          >
                            Pause
                          </button>
                        )}
                        {j.status === "paused" && (
                          <button
                            type="button"
                            onClick={() => adminResumeScheduledJob(j.id).then((r) => { flash(r.message); load(); })}
                            className="text-xs text-green-600 hover:underline"
                          >
                            Resume
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <PaginationBar page={page} total={jobs.total} pageSize={25} onPage={setPage} />
          </>
        )}
      </Card>
    </main>
  );
}
