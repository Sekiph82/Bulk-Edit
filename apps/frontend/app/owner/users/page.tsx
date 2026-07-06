"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  adminListUsers,
  adminDisableUser,
  adminEnableUser,
  type AdminUser,
  type AdminPage as AdminPageType,
  type AdminUserFilters,
} from "@/lib/api";
import { PageHeader, SectionHeader, PaginationBar, Badge, Card, fmt, useOwnerBase, downloadCsv, todayStamp } from "@/components/owner/OwnerUI";

const CSV_COLUMNS = [
  "user_id", "email", "name", "role", "status",
  "organization_id", "organization_name", "plan", "created_at",
];

export default function OwnerUsersPage() {
  const base = useOwnerBase();
  const [users, setUsers] = useState<AdminPageType<AdminUser> | null>(null);
  const [page, setPage] = useState(1);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const [q, setQ] = useState("");
  const [status, setStatus] = useState<AdminUserFilters["status"]>("all");
  const [role, setRole] = useState<AdminUserFilters["role"]>("all");
  const [plan, setPlan] = useState("");
  const [createdFrom, setCreatedFrom] = useState("");
  const [createdTo, setCreatedTo] = useState("");

  const filters: AdminUserFilters = {
    q: q || undefined,
    status,
    role,
    plan: plan || undefined,
    created_from: createdFrom || undefined,
    created_to: createdTo || undefined,
  };

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    adminListUsers(page, 25, filters)
      .then(setUsers)
      .catch(() => setError("Failed to load users."))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, q, status, role, plan, createdFrom, createdTo]);

  useEffect(() => { load(); }, [load]);

  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(null), 3000); };

  async function handleExport() {
    setExporting(true);
    try {
      const rows: AdminUser[] = [];
      let p = 1;
      // Manageable pre-launch dataset — fetch up to 500 filtered rows for export.
      for (let i = 0; i < 5; i++) {
        const pg = await adminListUsers(p, 100, filters);
        rows.push(...pg.items);
        if (rows.length >= pg.total || pg.items.length === 0) break;
        p += 1;
      }
      const csvRows = rows.map((u) => ({
        user_id: u.id,
        email: u.email,
        name: u.full_name ?? "",
        role: u.is_superuser ? "superuser" : "user",
        status: u.is_active ? "active" : "disabled",
        organization_id: u.organization_id ?? "",
        organization_name: u.organization_name ?? "",
        plan: u.plan ?? "",
        created_at: u.created_at,
      }));
      downloadCsv(`owner-users-${todayStamp()}.csv`, csvRows, CSV_COLUMNS);
    } catch {
      setError("Export failed.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Users" sub="Platform-wide user accounts — superuser only" />
      {msg && <div className="mb-4 bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm px-4 py-2 rounded-lg">{msg}</div>}
      {error && <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg">{error}</div>}

      <Card>
        <div className="flex flex-col lg:flex-row lg:items-end gap-3 mb-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Search</label>
            <input
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              placeholder="Name, email, or user id"
              value={q}
              onChange={(e) => { setPage(1); setQ(e.target.value); }}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              value={status}
              onChange={(e) => { setPage(1); setStatus(e.target.value as AdminUserFilters["status"]); }}
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="disabled">Disabled</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Role</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              value={role}
              onChange={(e) => { setPage(1); setRole(e.target.value as AdminUserFilters["role"]); }}
            >
              <option value="all">All</option>
              <option value="superuser">Superuser</option>
              <option value="user">User</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Plan</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              value={plan}
              onChange={(e) => { setPage(1); setPlan(e.target.value); }}
            >
              <option value="">All</option>
              <option value="free">Free</option>
              <option value="basic_monthly">Basic (Monthly)</option>
              <option value="basic_yearly">Basic (Yearly)</option>
              <option value="pro_monthly">Pro (Monthly)</option>
              <option value="pro_yearly">Pro (Yearly)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Created from</label>
            <input
              type="date"
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              value={createdFrom}
              onChange={(e) => { setPage(1); setCreatedFrom(e.target.value); }}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Created to</label>
            <input
              type="date"
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              value={createdTo}
              onChange={(e) => { setPage(1); setCreatedTo(e.target.value); }}
            />
          </div>
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting}
            className="text-xs font-medium text-indigo-600 border border-indigo-200 rounded-lg px-3 py-2 hover:bg-indigo-50 disabled:opacity-40 whitespace-nowrap"
          >
            {exporting ? "Exporting…" : "Export CSV"}
          </button>
        </div>

        <SectionHeader title="Users" total={users?.total} onRefresh={load} />

        {loading && !users && <p className="text-sm text-gray-400 py-8 text-center">Loading…</p>}

        {users && (
          <>
            {users.items.length === 0 ? (
              <p className="text-sm text-gray-400 py-8 text-center">No users match these filters.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                      <th className="pb-2 pr-4">Email</th>
                      <th className="pb-2 pr-4">Name</th>
                      <th className="pb-2 pr-4">Organization</th>
                      <th className="pb-2 pr-4">Plan</th>
                      <th className="pb-2 pr-4">Active</th>
                      <th className="pb-2 pr-4">Role</th>
                      <th className="pb-2 pr-4">Created</th>
                      <th className="pb-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.items.map((u) => (
                      <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 pr-4 font-medium text-gray-800">
                          <Link href={`${base}/users/${u.id}`} className="hover:text-indigo-600 hover:underline">
                            {u.email}
                          </Link>
                        </td>
                        <td className="py-2 pr-4 text-gray-500">{u.full_name ?? "—"}</td>
                        <td className="py-2 pr-4 text-gray-500">
                          {u.organization_id ? (
                            <Link href={`${base}/organizations/${u.organization_id}`} className="hover:text-indigo-600 hover:underline">
                              {u.organization_name}
                            </Link>
                          ) : "—"}
                        </td>
                        <td className="py-2 pr-4 text-gray-500">{u.plan ?? "—"}</td>
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
            )}
            <PaginationBar page={page} total={users.total} pageSize={25} onPage={setPage} />
          </>
        )}
      </Card>
    </main>
  );
}
