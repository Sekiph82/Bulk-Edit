"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type {
  AdminOverview,
  AdminUser,
  AdminOrganization,
  AdminSubscription,
  AdminShop,
  AdminScheduledJobSummary,
  AdminAuditEvent,
  AdminPage,
  AdminBillingSummary,
  AdminStripeSummary,
  AdminProductUsage,
  AdminSystemHealth,
  AdminUsageSummary,
} from "@/lib/api";
import {
  ApiError,
  adminGetOverview,
  adminListUsers,
  adminListOrganizations,
  adminListSubscriptions,
  adminListShops,
  adminListScheduledJobs,
  adminListEvents,
  adminDisableUser,
  adminEnableUser,
  adminPauseScheduledJob,
  adminResumeScheduledJob,
  adminGetBillingSummary,
  adminGetStripeSummary,
  adminGetProductUsage,
  adminGetSystemHealth,
  adminListAuditLog,
  adminListUsage,
} from "@/lib/api";

type Tab = "overview" | "users" | "billing" | "etsy" | "usage" | "system";

function fmt(dt: string | null | undefined): string {
  if (!dt) return "—";
  return new Date(dt).toLocaleString();
}

function currency(n: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 }).format(n);
}

function Badge({ status }: { status: string }) {
  const color: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    inactive: "bg-gray-100 text-gray-600",
    free: "bg-gray-100 text-gray-600",
    paused: "bg-yellow-100 text-yellow-800",
    completed: "bg-blue-100 text-blue-800",
    failed: "bg-red-100 text-red-800",
    canceled: "bg-red-100 text-red-700",
    ok: "bg-green-100 text-green-800",
    superuser: "bg-purple-100 text-purple-800",
    true: "bg-green-100 text-green-800",
    false: "bg-gray-100 text-gray-600",
  };
  const cls = color[status] ?? "bg-indigo-100 text-indigo-800";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{typeof value === "number" ? value.toLocaleString() : value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

function SectionHeader({ title, total, onRefresh }: { title: string; total?: number; onRefresh: () => void }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h2 className="text-base font-semibold text-gray-800">
        {title}{total !== undefined && <span className="text-gray-400 font-normal text-sm ml-1">({total})</span>}
      </h2>
      <button type="button" onClick={onRefresh} className="text-xs text-indigo-600 hover:underline">
        Refresh
      </button>
    </div>
  );
}

function PaginationBar({
  page,
  total,
  pageSize,
  onPage,
}: {
  page: number;
  total: number;
  pageSize: number;
  onPage: (p: number) => void;
}) {
  const pages = Math.ceil(total / pageSize);
  if (pages <= 1) return null;
  return (
    <div className="flex gap-2 items-center justify-end mt-3 text-sm">
      <button
        type="button"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
        className="px-2 py-1 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
      >
        ←
      </button>
      <span className="text-gray-500">{page} / {pages}</span>
      <button
        type="button"
        disabled={page >= pages}
        onClick={() => onPage(page + 1)}
        className="px-2 py-1 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
      >
        →
      </button>
    </div>
  );
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const [forbidden, setForbidden] = useState(false);
  const [tab, setTab] = useState<Tab>("overview");
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  // Overview tab
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [billing, setBilling] = useState<AdminBillingSummary | null>(null);

  // Users tab
  const [users, setUsers] = useState<AdminPage<AdminUser> | null>(null);
  const [userPage, setUserPage] = useState(1);
  const [orgs, setOrgs] = useState<AdminPage<AdminOrganization> | null>(null);
  const [orgPage, setOrgPage] = useState(1);

  // Billing tab
  const [stripeSummary, setStripeSummary] = useState<AdminStripeSummary | null>(null);
  const [subs, setSubs] = useState<AdminPage<AdminSubscription> | null>(null);
  const [subPage, setSubPage] = useState(1);

  // Etsy tab
  const [shops, setShops] = useState<AdminPage<AdminShop> | null>(null);
  const [shopPage, setShopPage] = useState(1);
  const [schedJobs, setSchedJobs] = useState<AdminPage<AdminScheduledJobSummary> | null>(null);
  const [schedPage, setSchedPage] = useState(1);

  // Usage tab
  const [productUsage, setProductUsage] = useState<AdminProductUsage | null>(null);
  const [usageCounters, setUsageCounters] = useState<AdminPage<AdminUsageSummary> | null>(null);
  const [usagePage, setUsagePage] = useState(1);

  // System tab
  const [systemHealth, setSystemHealth] = useState<AdminSystemHealth | null>(null);
  const [auditLog, setAuditLog] = useState<AdminPage<AdminAuditEvent> | null>(null);
  const [auditPage, setAuditPage] = useState(1);

  const handleApiError = (e: unknown) => {
    if (e instanceof ApiError && e.status === 403) setForbidden(true);
  };

  // Load overview + billing summary on mount
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) { router.push("/login"); return; }
    adminGetOverview().then(setOverview).catch(handleApiError);
    adminGetBillingSummary().then(setBilling).catch(handleApiError);
  }, [router]);

  // Tab-specific loaders
  const loadUsers = useCallback(() => {
    adminListUsers(userPage).then(setUsers).catch(handleApiError);
  }, [userPage]);
  const loadOrgs = useCallback(() => {
    adminListOrganizations(orgPage).then(setOrgs).catch(handleApiError);
  }, [orgPage]);
  const loadStripeSummary = useCallback(() => {
    adminGetStripeSummary().then(setStripeSummary).catch(handleApiError);
  }, []);
  const loadSubs = useCallback(() => {
    adminListSubscriptions(subPage).then(setSubs).catch(handleApiError);
  }, [subPage]);
  const loadShops = useCallback(() => {
    adminListShops(shopPage).then(setShops).catch(handleApiError);
  }, [shopPage]);
  const loadSchedJobs = useCallback(() => {
    adminListScheduledJobs(schedPage).then(setSchedJobs).catch(handleApiError);
  }, [schedPage]);
  const loadProductUsage = useCallback(() => {
    adminGetProductUsage().then(setProductUsage).catch(handleApiError);
  }, []);
  const loadUsageCounters = useCallback(() => {
    adminListUsage(usagePage).then(setUsageCounters).catch(handleApiError);
  }, [usagePage]);
  const loadSystemHealth = useCallback(() => {
    adminGetSystemHealth().then(setSystemHealth).catch(handleApiError);
  }, []);
  const loadAuditLog = useCallback(() => {
    adminListAuditLog(auditPage).then(setAuditLog).catch(handleApiError);
  }, [auditPage]);

  useEffect(() => {
    if (tab === "users") { loadUsers(); loadOrgs(); }
  }, [tab, loadUsers, loadOrgs]);
  useEffect(() => {
    if (tab === "billing") { loadStripeSummary(); loadSubs(); }
  }, [tab, loadStripeSummary, loadSubs]);
  useEffect(() => {
    if (tab === "etsy") { loadShops(); loadSchedJobs(); }
  }, [tab, loadShops, loadSchedJobs]);
  useEffect(() => {
    if (tab === "usage") { loadProductUsage(); loadUsageCounters(); }
  }, [tab, loadProductUsage, loadUsageCounters]);
  useEffect(() => {
    if (tab === "system") { loadSystemHealth(); loadAuditLog(); }
  }, [tab, loadSystemHealth, loadAuditLog]);

  const flash = (msg: string) => {
    setActionMsg(msg);
    setTimeout(() => setActionMsg(null), 3500);
  };

  const handleDisable = async (userId: string) => {
    try { const r = await adminDisableUser(userId); flash(r.message); loadUsers(); }
    catch (e) { if (e instanceof ApiError) flash(e.message); }
  };
  const handleEnable = async (userId: string) => {
    try { const r = await adminEnableUser(userId); flash(r.message); loadUsers(); }
    catch (e) { if (e instanceof ApiError) flash(e.message); }
  };
  const handlePause = async (jobId: string) => {
    try { const r = await adminPauseScheduledJob(jobId); flash(r.message); loadSchedJobs(); }
    catch (e) { if (e instanceof ApiError) flash(e.message); }
  };
  const handleResume = async (jobId: string) => {
    try { const r = await adminResumeScheduledJob(jobId); flash(r.message); loadSchedJobs(); }
    catch (e) { if (e instanceof ApiError) flash(e.message); }
  };

  if (forbidden) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center" data-testid="admin-access-denied">
        <div className="bg-white border border-red-200 rounded-2xl p-10 text-center max-w-md shadow-sm">
          <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
          </div>
          <p className="text-xl font-bold text-gray-900 mb-2">Access Denied</p>
          <p className="text-gray-500 text-sm mb-6">This dashboard requires superuser access. Your account does not have the required permissions.</p>
          <Link href="/dashboard" className="inline-block bg-indigo-600 text-white text-sm font-medium px-5 py-2 rounded-lg hover:bg-indigo-700 transition-colors">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const TABS: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "users",    label: "Users" },
    { id: "billing",  label: "Billing" },
    { id: "etsy",     label: "Etsy" },
    { id: "usage",    label: "Usage" },
    { id: "system",   label: "System" },
  ];

  return (
    <main className="max-w-7xl mx-auto px-6 py-8" data-testid="admin-dashboard">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Admin Business Dashboard</h1>
        <p className="text-gray-400 text-sm mt-0.5">Internal platform metrics — superuser only — read-only + safe actions</p>
      </div>

      {actionMsg && (
        <div className="mb-4 bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm px-4 py-2 rounded-lg">
          {actionMsg}
        </div>
      )}

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 flex-wrap border-b border-gray-200 pb-0">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
              tab === t.id
                ? "border-indigo-600 text-indigo-700"
                : "border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Overview Tab ─────────────────────────────────────────────────────── */}
      {tab === "overview" && (
        <div className="space-y-6">
          <div>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Platform</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {overview && (
                <>
                  <StatCard label="Total Users" value={overview.total_users} />
                  <StatCard label="Organizations" value={overview.total_organizations} />
                  <StatCard label="Active Subscriptions" value={overview.active_subscriptions} />
                  <StatCard label="Paid Plans" value={overview.paid_subscriptions} />
                  <StatCard label="Total Listings" value={overview.total_listings} />
                  <StatCard label="Scheduled Jobs" value={overview.total_scheduled_jobs} />
                  <StatCard label="AI Sessions" value={overview.total_ai_sessions} />
                  <StatCard label="CSV Jobs" value={overview.total_csv_jobs} />
                </>
              )}
            </div>
          </div>

          {billing && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Revenue Snapshot</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard
                  label="Projected MRR"
                  value={currency(billing.estimated_monthly_revenue)}
                  sub="Expected — not guaranteed cash"
                />
                <StatCard label="Active Subs" value={billing.active_count} />
                <StatCard label="Paid Plans" value={
                  billing.basic_monthly_count + billing.basic_yearly_count +
                  billing.pro_monthly_count + billing.pro_yearly_count
                } />
                <StatCard label="Canceling" value={billing.cancel_at_period_end_count} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Users Tab ────────────────────────────────────────────────────────── */}
      {tab === "users" && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <SectionHeader title="Users" total={users?.total} onRefresh={loadUsers} />
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
                              <button type="button" onClick={() => handleDisable(u.id)} className="text-xs text-red-600 hover:underline">Disable</button>
                            ) : (
                              <button type="button" onClick={() => handleEnable(u.id)} className="text-xs text-green-600 hover:underline">Enable</button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <PaginationBar page={userPage} total={users.total} pageSize={25} onPage={setUserPage} />
              </>
            )}
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <SectionHeader title="Organizations" total={orgs?.total} onRefresh={loadOrgs} />
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
                <PaginationBar page={orgPage} total={orgs.total} pageSize={25} onPage={setOrgPage} />
              </>
            )}
          </div>
        </div>
      )}

      {/* ── Billing Tab ──────────────────────────────────────────────────────── */}
      {tab === "billing" && (
        <div className="space-y-6">
          {billing && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Plan Distribution</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
                <StatCard label="Free" value={billing.free_plan_count} />
                <StatCard label="Basic Monthly" value={billing.basic_monthly_count} />
                <StatCard label="Basic Yearly" value={billing.basic_yearly_count} />
                <StatCard label="Pro Monthly" value={billing.pro_monthly_count} />
                <StatCard label="Pro Yearly" value={billing.pro_yearly_count} />
                <StatCard label="Total Subs" value={billing.total_subscriptions} />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard label="Active" value={billing.active_count} />
                <StatCard label="Trialing" value={billing.trialing_count} />
                <StatCard label="Canceled" value={billing.canceled_count} />
                <StatCard
                  label="Projected MRR"
                  value={currency(billing.estimated_monthly_revenue)}
                  sub="Expected — not guaranteed cash"
                />
              </div>
            </div>
          )}

          {stripeSummary && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Stripe</h2>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <StatCard label="Stripe Customers" value={stripeSummary.total_stripe_customers} />
                <StatCard label="With Stripe Sub" value={stripeSummary.subscriptions_with_stripe_sub} />
                <StatCard label="Active Stripe" value={stripeSummary.active_stripe_subscriptions} />
                <StatCard label="Canceling" value={stripeSummary.canceling_at_period_end} />
                <StatCard label="Billing Events" value={stripeSummary.total_billing_events} />
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <SectionHeader title="Subscriptions" total={subs?.total} onRefresh={loadSubs} />
            {subs && (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                        <th className="pb-2 pr-4">Org ID</th>
                        <th className="pb-2 pr-4">Plan</th>
                        <th className="pb-2 pr-4">Status</th>
                        <th className="pb-2 pr-4">Stripe Customer</th>
                        <th className="pb-2">Period End</th>
                      </tr>
                    </thead>
                    <tbody>
                      {subs.items.map((s) => (
                        <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="py-2 pr-4 text-gray-400 font-mono text-xs">{s.organization_id}</td>
                          <td className="py-2 pr-4"><Badge status={s.plan} /></td>
                          <td className="py-2 pr-4"><Badge status={s.status} /></td>
                          <td className="py-2 pr-4 text-gray-400 font-mono text-xs">{s.stripe_customer_id ?? "—"}</td>
                          <td className="py-2 text-gray-400">{fmt(s.current_period_end)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <PaginationBar page={subPage} total={subs.total} pageSize={25} onPage={setSubPage} />
              </>
            )}
          </div>
        </div>
      )}

      {/* ── Etsy Tab ─────────────────────────────────────────────────────────── */}
      {tab === "etsy" && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <SectionHeader title="Connected Shops" total={shops?.total} onRefresh={loadShops} />
            {shops && (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                        <th className="pb-2 pr-4">Shop Name</th>
                        <th className="pb-2 pr-4">Etsy Shop ID</th>
                        <th className="pb-2 pr-4">Connected</th>
                        <th className="pb-2">Last Synced</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shops.items.map((s) => (
                        <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="py-2 pr-4 font-medium text-gray-800">{s.shop_name}</td>
                          <td className="py-2 pr-4 text-gray-400 font-mono text-xs">{s.etsy_shop_id}</td>
                          <td className="py-2 pr-4"><Badge status={s.is_connected ? "active" : "inactive"} /></td>
                          <td className="py-2 text-gray-400">{fmt(s.last_synced_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <PaginationBar page={shopPage} total={shops.total} pageSize={25} onPage={setShopPage} />
              </>
            )}
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <SectionHeader title="Scheduled Jobs" total={schedJobs?.total} onRefresh={loadSchedJobs} />
            {schedJobs && (
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
                      {schedJobs.items.map((j) => (
                        <tr key={j.id} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="py-2 pr-4 font-medium text-gray-800">{j.name}</td>
                          <td className="py-2 pr-4 text-gray-500">{j.job_type}</td>
                          <td className="py-2 pr-4"><Badge status={j.status} /></td>
                          <td className="py-2 pr-4 text-gray-500">{j.run_count}</td>
                          <td className="py-2 pr-4 text-gray-400">{fmt(j.next_run_at)}</td>
                          <td className="py-2 flex gap-2">
                            {(j.status === "active" || j.status === "idle") && (
                              <button type="button" onClick={() => handlePause(j.id)} className="text-xs text-yellow-600 hover:underline">Pause</button>
                            )}
                            {j.status === "paused" && (
                              <button type="button" onClick={() => handleResume(j.id)} className="text-xs text-green-600 hover:underline">Resume</button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <PaginationBar page={schedPage} total={schedJobs.total} pageSize={25} onPage={setSchedPage} />
              </>
            )}
          </div>
        </div>
      )}

      {/* ── Usage Tab ────────────────────────────────────────────────────────── */}
      {tab === "usage" && (
        <div className="space-y-6">
          {productUsage && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Product Usage (All Time)</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard label="Listings" value={productUsage.total_listings} />
                <StatCard label="Shops" value={productUsage.total_shops} />
                <StatCard label="Bulk Edit Sessions" value={productUsage.total_bulk_edit_sessions} />
                <StatCard label="AI Sessions" value={productUsage.total_ai_sessions} />
                <StatCard label="CSV Jobs" value={productUsage.total_csv_jobs} />
                <StatCard label="Dynamic Pricing Jobs" value={productUsage.total_dynamic_pricing_jobs} />
                <StatCard label="Sync Jobs" value={productUsage.total_sync_jobs} />
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <SectionHeader title="Usage Counters (per org/period)" total={usageCounters?.total} onRefresh={loadUsageCounters} />
            {usageCounters && (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                        <th className="pb-2 pr-4">Org ID</th>
                        <th className="pb-2 pr-4">Period</th>
                        <th className="pb-2 pr-4">Synced</th>
                        <th className="pb-2 pr-4">Bulk Edits</th>
                        <th className="pb-2 pr-4">AI Credits</th>
                        <th className="pb-2 pr-4">Media</th>
                        <th className="pb-2">DP Jobs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {usageCounters.items.map((u) => (
                        <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="py-2 pr-4 text-gray-400 font-mono text-xs">{u.organization_id.slice(0, 12)}…</td>
                          <td className="py-2 pr-4 text-gray-600 font-mono text-xs">{u.period_key}</td>
                          <td className="py-2 pr-4 text-gray-600">{u.listings_synced}</td>
                          <td className="py-2 pr-4 text-gray-600">{u.bulk_edits_used}</td>
                          <td className="py-2 pr-4 text-gray-600">{u.ai_credits_used}</td>
                          <td className="py-2 pr-4 text-gray-600">{u.media_assets_used}</td>
                          <td className="py-2 text-gray-600">{u.dynamic_pricing_jobs_used}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <PaginationBar page={usagePage} total={usageCounters.total} pageSize={25} onPage={setUsagePage} />
              </>
            )}
          </div>
        </div>
      )}

      {/* ── System Tab ───────────────────────────────────────────────────────── */}
      {tab === "system" && (
        <div className="space-y-6">
          {systemHealth && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">System Health</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <StatCard
                  label="Database"
                  value={systemHealth.database_status.toUpperCase()}
                  sub="PostgreSQL connection"
                />
                <StatCard label="Total Users" value={systemHealth.total_users} />
                <StatCard label="Organizations" value={systemHealth.total_organizations} />
                <StatCard label="Audit Events" value={systemHealth.total_audit_events} />
                <StatCard
                  label="Failed Scheduled Runs"
                  value={systemHealth.recent_failed_scheduled_runs}
                  sub="All time"
                />
                <StatCard
                  label="Failed AI Sessions"
                  value={systemHealth.recent_failed_ai_sessions}
                  sub="All time"
                />
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <SectionHeader title="Recent Audit Log" total={auditLog?.total} onRefresh={loadAuditLog} />
            {auditLog && (
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
                      {auditLog.items.map((e) => (
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
                <PaginationBar page={auditPage} total={auditLog.total} pageSize={25} onPage={setAuditPage} />
              </>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
