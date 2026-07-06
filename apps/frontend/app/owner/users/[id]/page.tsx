"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  adminGetUserDetail,
  adminDisableUser,
  adminEnableUser,
  type AdminUserDetail,
  ApiError,
} from "@/lib/api";
import { PageHeader, Card, Badge, StatCard, fmt, useOwnerBase } from "@/components/owner/OwnerUI";

export default function OwnerUserDetailPage() {
  const params = useParams();
  const userId = String(params.id);
  const base = useOwnerBase();

  const [user, setUser] = useState<AdminUserDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    adminGetUserDetail(userId)
      .then(setUser)
      .catch((e) => setError(e instanceof ApiError && e.status === 404 ? "User not found." : "Failed to load user."))
      .finally(() => setLoading(false));
  }, [userId]);

  useEffect(() => { load(); }, [load]);

  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(null), 3000); };

  return (
    <main className="max-w-5xl mx-auto px-6 py-8">
      <div className="mb-4">
        <Link href={`${base}/users`} className="text-sm text-indigo-600 hover:underline">← Back to Users</Link>
      </div>

      {loading && <p className="text-sm text-gray-400 py-8 text-center">Loading…</p>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}
      {msg && <div className="mb-4 bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm px-4 py-2 rounded-lg">{msg}</div>}

      {user && (
        <>
          <PageHeader title={user.full_name || user.email} sub={user.email} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <Card>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Identity</h2>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between"><dt className="text-gray-400">User ID</dt><dd className="font-mono text-xs text-gray-700">{user.id}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Email</dt><dd className="text-gray-800">{user.email}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Name</dt><dd className="text-gray-800">{user.full_name ?? "—"}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Status</dt><dd><Badge status={String(user.is_active)} /></dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Role</dt><dd>{user.is_superuser ? <Badge status="superuser" /> : <span className="text-xs text-gray-500">user</span>}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Verified</dt><dd>{user.is_verified ? "Yes" : "No"}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Created</dt><dd className="text-gray-600">{fmt(user.created_at)}</dd></div>
              </dl>
              <div className="mt-4 pt-4 border-t border-gray-100">
                {user.is_active ? (
                  <button
                    type="button"
                    onClick={() => adminDisableUser(user.id).then((r) => { flash(r.message); load(); })}
                    className="text-xs font-medium text-red-600 border border-red-200 rounded-lg px-3 py-1.5 hover:bg-red-50"
                  >
                    Disable user
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => adminEnableUser(user.id).then((r) => { flash(r.message); load(); })}
                    className="text-xs font-medium text-green-600 border border-green-200 rounded-lg px-3 py-1.5 hover:bg-green-50"
                  >
                    Enable user
                  </button>
                )}
              </div>
            </Card>

            <Card>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Organizations</h2>
              {user.organizations.length === 0 ? (
                <p className="text-sm text-gray-400">No organization membership.</p>
              ) : (
                <ul className="space-y-2">
                  {user.organizations.map((m) => (
                    <li key={m.organization_id} className="flex items-center justify-between text-sm">
                      <Link href={`${base}/organizations/${m.organization_id}`} className="text-indigo-600 hover:underline">
                        {m.organization_name}
                      </Link>
                      <span className="text-xs text-gray-400">{m.role}</span>
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-4 pt-4 border-t border-gray-100 text-sm">
                <div className="flex justify-between"><span className="text-gray-400">Plan</span><span className="text-gray-800">{user.plan ?? "—"}</span></div>
              </div>
            </Card>

            <Card>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Usage</h2>
              <div className="grid grid-cols-2 gap-3">
                <StatCard label="Bulk Edit Sessions" value={user.usage.bulk_edit_sessions_count} />
                <StatCard label="AI Sessions" value={user.usage.ai_sessions_count} />
                <StatCard label="CSV Jobs" value={user.usage.csv_jobs_count} />
                <StatCard label="Media Jobs" value={user.usage.media_jobs_count} />
              </div>
              <p className="text-[11px] text-gray-400 mt-3">
                Dynamic pricing jobs: {user.usage.dynamic_pricing_jobs_count}
              </p>
            </Card>
          </div>

          <Card>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Recent Activity</h2>
            {user.recent_events.length === 0 ? (
              <p className="text-sm text-gray-400">No recent activity.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                      <th className="pb-2 pr-4">Event</th>
                      <th className="pb-2 pr-4">Entity</th>
                      <th className="pb-2 pr-4">Message</th>
                      <th className="pb-2">When</th>
                    </tr>
                  </thead>
                  <tbody>
                    {user.recent_events.map((e) => (
                      <tr key={e.id} className="border-b border-gray-50">
                        <td className="py-2 pr-4 font-medium text-gray-700">{e.event_type}</td>
                        <td className="py-2 pr-4 text-gray-500">{e.entity_type ?? "—"}</td>
                        <td className="py-2 pr-4 text-gray-500 truncate max-w-xs">{e.message ?? "—"}</td>
                        <td className="py-2 text-gray-400">{fmt(e.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </main>
  );
}
