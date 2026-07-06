"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  adminListOrganizations,
  type AdminOrganization,
  type AdminPage as AdminPageType,
  type AdminOrganizationFilters,
} from "@/lib/api";
import { PageHeader, SectionHeader, PaginationBar, Badge, Card, fmt, useOwnerBase, downloadCsv, todayStamp } from "@/components/owner/OwnerUI";

const CSV_COLUMNS = [
  "organization_id", "name", "owner_email", "plan", "subscription_status",
  "etsy_connected", "users_count", "created_at",
];

export default function OwnerOrganizationsPage() {
  const base = useOwnerBase();
  const [orgs, setOrgs] = useState<AdminPageType<AdminOrganization> | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const [q, setQ] = useState("");
  const [plan, setPlan] = useState("");
  const [subscriptionStatus, setSubscriptionStatus] = useState("");
  const [etsyConnected, setEtsyConnected] = useState("");
  const [createdFrom, setCreatedFrom] = useState("");
  const [createdTo, setCreatedTo] = useState("");

  const filters: AdminOrganizationFilters = {
    q: q || undefined,
    plan: plan || undefined,
    subscription_status: subscriptionStatus || undefined,
    etsy_connected: etsyConnected === "" ? undefined : etsyConnected === "true",
    created_from: createdFrom || undefined,
    created_to: createdTo || undefined,
  };

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    adminListOrganizations(page, 25, filters)
      .then(setOrgs)
      .catch(() => setError("Failed to load organizations."))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, q, plan, subscriptionStatus, etsyConnected, createdFrom, createdTo]);

  useEffect(() => { load(); }, [load]);

  async function handleExport() {
    setExporting(true);
    try {
      const rows: AdminOrganization[] = [];
      let p = 1;
      for (let i = 0; i < 5; i++) {
        const pg = await adminListOrganizations(p, 100, filters);
        rows.push(...pg.items);
        if (rows.length >= pg.total || pg.items.length === 0) break;
        p += 1;
      }
      const csvRows = rows.map((o) => ({
        organization_id: o.id,
        name: o.name,
        owner_email: o.owner_email ?? "",
        plan: o.plan ?? "",
        subscription_status: o.subscription_status ?? "",
        etsy_connected: o.etsy_connected,
        users_count: o.users_count,
        created_at: o.created_at,
      }));
      downloadCsv(`owner-organizations-${todayStamp()}.csv`, csvRows, CSV_COLUMNS);
    } catch {
      setError("Export failed.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Organizations" sub="Platform-wide organizations — superuser only" />
      {error && <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg">{error}</div>}

      <Card>
        <div className="flex flex-col lg:flex-row lg:items-end gap-3 mb-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Search</label>
            <input
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              placeholder="Name, org id, or owner email"
              value={q}
              onChange={(e) => { setPage(1); setQ(e.target.value); }}
            />
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
            <label className="block text-xs font-medium text-gray-500 mb-1">Subscription</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              value={subscriptionStatus}
              onChange={(e) => { setPage(1); setSubscriptionStatus(e.target.value); }}
            >
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="trialing">Trialing</option>
              <option value="canceled">Canceled</option>
              <option value="free">Free</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Etsy connected</label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              value={etsyConnected}
              onChange={(e) => { setPage(1); setEtsyConnected(e.target.value); }}
            >
              <option value="">All</option>
              <option value="true">Connected</option>
              <option value="false">Not connected</option>
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

        <SectionHeader title="Organizations" total={orgs?.total} onRefresh={load} />

        {loading && !orgs && <p className="text-sm text-gray-400 py-8 text-center">Loading…</p>}

        {orgs && (
          <>
            {orgs.items.length === 0 ? (
              <p className="text-sm text-gray-400 py-8 text-center">No organizations match these filters.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                      <th className="pb-2 pr-4">Name</th>
                      <th className="pb-2 pr-4">Owner</th>
                      <th className="pb-2 pr-4">Plan</th>
                      <th className="pb-2 pr-4">Subscription</th>
                      <th className="pb-2 pr-4">Etsy</th>
                      <th className="pb-2 pr-4">Users</th>
                      <th className="pb-2">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orgs.items.map((o) => (
                      <tr key={o.id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 pr-4 font-medium text-gray-800">
                          <Link href={`${base}/organizations/${o.id}`} className="hover:text-indigo-600 hover:underline">
                            {o.name}
                          </Link>
                        </td>
                        <td className="py-2 pr-4 text-gray-500">{o.owner_email ?? "—"}</td>
                        <td className="py-2 pr-4 text-gray-500">{o.plan ?? "—"}</td>
                        <td className="py-2 pr-4">{o.subscription_status ? <Badge status={o.subscription_status} /> : "—"}</td>
                        <td className="py-2 pr-4"><Badge status={String(o.etsy_connected)} /></td>
                        <td className="py-2 pr-4 text-gray-500">{o.users_count}</td>
                        <td className="py-2 text-gray-400">{fmt(o.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <PaginationBar page={page} total={orgs.total} pageSize={25} onPage={setPage} />
          </>
        )}
      </Card>
    </main>
  );
}
