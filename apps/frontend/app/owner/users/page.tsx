"use client";

import { useCallback, useEffect, useState } from "react";
import {
  adminListUsers,
  adminDisableUser,
  adminEnableUser,
  type AdminUser,
  type AdminPage as AdminPageType,
} from "@/lib/api";
import { PageHeader, SectionHeader, PaginationBar, Badge, Card, fmt } from "@/components/owner/OwnerUI";

export default function OwnerUsersPage() {
  const [users, setUsers] = useState<AdminPageType<AdminUser> | null>(null);
  const [page, setPage] = useState(1);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    adminListUsers(page).then(setUsers).catch(() => {});
  }, [page]);

  useEffect(() => { load(); }, [load]);

  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(null), 3000); };

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Users" sub="Platform-wide user accounts — superuser only" />
      {msg && <div className="mb-4 bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm px-4 py-2 rounded-lg">{msg}</div>}
      <Card>
        <SectionHeader title="Users" total={users?.total} onRefresh={load} />
        {users && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                    <th className="pb-2 pr-4">Email</th>
                    <th className="pb-2 pr-4">Name</th>
                    <th className="pb-2 pr-4">Active</th>
                    <th className="pb-2 pr-4">Role</th>
                    <th className="pb-2 pr-4">Created</th>
                    <th className="pb-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.items.map((u) => (
                    <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-4 font-medium text-gray-800">{u.email}</td>
                      <td className="py-2 pr-4 text-gray-500">{u.full_name ?? "—"}</td>
                      <td className="py-2 pr-4"><Badge status={String(u.is_active)} /></td>
                      <td className="py-2 pr-4">
                        {u.is_superuser ? <Badge status="superuser" /> : <span className="text-xs text-gray-400">user</span>}
                      </td>
                      <td className="py-2 pr-4 text-gray-400">{fmt(u.created_at)}</td>
                      <td className="py-2">
                        {u.is_active ? (
                          <button
                            type="button"
                            onClick={() => adminDisableUser(u.id).then((r) => { flash(r.message); load(); })}
                            className="text-xs text-red-600 hover:underline"
                          >
                            Disable
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => adminEnableUser(u.id).then((r) => { flash(r.message); load(); })}
                            className="text-xs text-green-600 hover:underline"
                          >
                            Enable
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <PaginationBar page={page} total={users.total} pageSize={25} onPage={setPage} />
          </>
        )}
      </Card>
    </main>
  );
}
