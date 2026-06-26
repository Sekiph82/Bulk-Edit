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
} from "@/lib/api";
// (type imports above)

type Section = "users" | "organizations" | "subscriptions" | "shops" | "scheduled-jobs" | "events";

function fmt(dt: string | null | undefined): string {
  if (!dt) return "—";
  return new Date(dt).toLocaleString();
}

function Badge({ status }: { status: string }) {
  const color: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    inactive: "bg-gray-100 text-gray-600",
    free: "bg-gray-100 text-gray-600",
    paused: "bg-yellow-100 text-yellow-800",
    completed: "bg-blue-100 text-blue-800",
    failed: "bg-red-100 text-red-800",
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

function OverviewCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-3xl font-bold text-gray-900">{value.toLocaleString()}</p>
    </div>
  );
}

function SectionHeader({ title, total, onRefresh }: { title: string; total: number; onRefresh: () => void }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h2 className="text-base font-semibold text-gray-800">
        {title} <span className="text-gray-400 font-normal text-sm">({total})</span>
      </h2>
      <button onClick={onRefresh} className="text-xs text-indigo-600 hover:underline">
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
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
        className="px-2 py-1 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
      >
        ←
      </button>
      <span className="text-gray-500">
        {page} / {pages}
      </span>
      <button
        disabled={page >= pages}
        onClick={() => onPage(page + 1)}
        className="px-2 py-1 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
      >
        →
      </button>
    </div>
  );
}

export default function AdminPage() {
  const router = useRouter();
  const [forbidden, setForbidden] = useState(false);
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [section, setSection] = useState<Section>("users");

  const [users, setUsers] = useState<AdminPage<AdminUser> | null>(null);
  const [userPage, setUserPage] = useState(1);

  const [orgs, setOrgs] = useState<AdminPage<AdminOrganization> | null>(null);
  const [orgPage, setOrgPage] = useState(1);

  const [subs, setSubs] = useState<AdminPage<AdminSubscription> | null>(null);
  const [subPage, setSubPage] = useState(1);

  const [shops, setShops] = useState<AdminPage<AdminShop> | null>(null);
  const [shopPage, setShopPage] = useState(1);

  const [jobs, setJobs] = useState<AdminPage<AdminScheduledJobSummary> | null>(null);
  const [jobPage, setJobPage] = useState(1);

  const [events, setEvents] = useState<AdminPage<AdminAuditEvent> | null>(null);
  const [eventPage, setEventPage] = useState(1);

  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const handleApiError = (e: unknown) => {
    if (e instanceof ApiError && e.status === 403) {
      setForbidden(true);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) { router.push("/login"); return; }
    adminGetOverview().then(setOverview).catch(handleApiError);
  }, [router]);

  const loadUsers = useCallback(() => {
    adminListUsers(userPage).then(setUsers).catch(handleApiError);
  }, [userPage]);

  const loadOrgs = useCallback(() => {
    adminListOrganizations(orgPage).then(setOrgs).catch(handleApiError);
  }, [orgPage]);

  const loadSubs = useCallback(() => {
    adminListSubscriptions(subPage).then(setSubs).catch(handleApiError);
  }, [subPage]);

  const loadShops = useCallback(() => {
    adminListShops(shopPage).then(setShops).catch(handleApiError);
  }, [shopPage]);

  const loadJobs = useCallback(() => {
    adminListScheduledJobs(jobPage).then(setJobs).catch(handleApiError);
  }, [jobPage]);

  const loadEvents = useCallback(() => {
    adminListEvents(eventPage).then(setEvents).catch(handleApiError);
  }, [eventPage]);

  useEffect(() => { if (section === "users") loadUsers(); }, [section, loadUsers]);
  useEffect(() => { if (section === "organizations") loadOrgs(); }, [section, loadOrgs]);
  useEffect(() => { if (section === "subscriptions") loadSubs(); }, [section, loadSubs]);
  useEffect(() => { if (section === "shops") loadShops(); }, [section, loadShops]);
  useEffect(() => { if (section === "scheduled-jobs") loadJobs(); }, [section, loadJobs]);
  useEffect(() => { if (section === "events") loadEvents(); }, [section, loadEvents]);

  const flash = (msg: string) => {
    setActionMsg(msg);
    setTimeout(() => setActionMsg(null), 3000);
  };

  const handleDisable = async (userId: string) => {
    try {
      const res = await adminDisableUser(userId);
      flash(res.message);
      loadUsers();
    } catch (e) { if (e instanceof ApiError) flash(e.message); }
  };

  const handleEnable = async (userId: string) => {
    try {
      const res = await adminEnableUser(userId);
      flash(res.message);
      loadUsers();
    } catch (e) { if (e instanceof ApiError) flash(e.message); }
  };

  const handlePause = async (jobId: string) => {
    try {
      const res = await adminPauseScheduledJob(jobId);
      flash(res.message);
      loadJobs();
    } catch (e) { if (e instanceof ApiError) flash(e.message); }
  };

  const handleResume = async (jobId: string) => {
    try {
      const res = await adminResumeScheduledJob(jobId);
      flash(res.message);
      loadJobs();
    } catch (e) { if (e instanceof ApiError) flash(e.message); }
  };

  if (forbidden) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white border border-red-200 rounded-2xl p-10 text-center max-w-md shadow-sm">
          <p className="text-2xl font-bold text-red-600 mb-2">Access Denied</p>
          <p className="text-gray-500 mb-6">This panel requires superuser access.</p>
          <Link href="/dashboard" className="text-indigo-600 hover:underline text-sm font-medium">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const SECTIONS: { id: Section; label: string }[] = [
    { id: "users", label: "Users" },
    { id: "organizations", label: "Organizations" },
    { id: "subscriptions", label: "Subscriptions" },
    { id: "shops", label: "Shops" },
    { id: "scheduled-jobs", label: "Scheduled Jobs" },
    { id: "events", label: "Audit Events" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <Link href="/" className="text-xl font-extrabold text-gray-900 hover:text-indigo-600 transition-colors">
          Bulk-Edit
        </Link>
        <div className="flex gap-4 items-center">
          <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded font-semibold">ADMIN</span>
          <Link href="/dashboard" className="text-sm text-gray-500 hover:underline">
            Dashboard
          </Link>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-8 py-10">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-400 text-sm mt-0.5">Platform-level visibility — read-only + safe actions only</p>
        </div>

        {actionMsg && (
          <div className="mb-4 bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm px-4 py-2 rounded-lg">
            {actionMsg}
          </div>
        )}

        {overview && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            <OverviewCard label="Total Users" value={overview.total_users} />
            <OverviewCard label="Organizations" value={overview.total_organizations} />
            <OverviewCard label="Active Subscriptions" value={overview.active_subscriptions} />
            <OverviewCard label="Paid Plans" value={overview.paid_subscriptions} />
            <OverviewCard label="Listings" value={overview.total_listings} />
            <OverviewCard label="Scheduled Jobs" value={overview.total_scheduled_jobs} />
            <OverviewCard label="AI Sessions" value={overview.total_ai_sessions} />
            <OverviewCard label="CSV Jobs" value={overview.total_csv_jobs} />
          </div>
        )}

        <div className="flex gap-1 mb-6 flex-wrap">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSection(s.id)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                section === s.id
                  ? "bg-indigo-600 text-white"
                  : "bg-white border border-gray-200 text-gray-600 hover:border-indigo-300"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
          {/* Users */}
          {section === "users" && users && (
            <>
              <SectionHeader title="Users" total={users.total} onRefresh={loadUsers} />
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                      <th className="pb-2 pr-4">Email</th>
                      <th className="pb-2 pr-4">Name</th>
                      <th className="pb-2 pr-4">Active</th>
                      <th className="pb-2 pr-4">Superuser</th>
                      <th className="pb-2 pr-4">Created</th>
                      <th className="pb-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.items.map((u) => (
                      <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 pr-4 font-medium text-gray-800">{u.email}</td>
                        <td className="py-2 pr-4 text-gray-500">{u.full_name ?? "—"}</td>
                        <td className="py-2 pr-4">
                          <Badge status={String(u.is_active)} />
                        </td>
                        <td className="py-2 pr-4">
                          {u.is_superuser && <Badge status="superuser" />}
                        </td>
                        <td className="py-2 pr-4 text-gray-400">{fmt(u.created_at)}</td>
                        <td className="py-2">
                          {u.is_active ? (
                            <button
                              onClick={() => handleDisable(u.id)}
                              className="text-xs text-red-600 hover:underline"
                            >
                              Disable
                            </button>
                          ) : (
                            <button
                              onClick={() => handleEnable(u.id)}
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
              <PaginationBar page={userPage} total={users.total} pageSize={25} onPage={setUserPage} />
            </>
          )}

          {/* Organizations */}
          {section === "organizations" && orgs && (
            <>
              <SectionHeader title="Organizations" total={orgs.total} onRefresh={loadOrgs} />
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

          {/* Subscriptions */}
          {section === "subscriptions" && subs && (
            <>
              <SectionHeader title="Subscriptions" total={subs.total} onRefresh={loadSubs} />
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
                        <td className="py-2 pr-4">
                          <Badge status={s.plan} />
                        </td>
                        <td className="py-2 pr-4">
                          <Badge status={s.status} />
                        </td>
                        <td className="py-2 pr-4 text-gray-400 font-mono text-xs">
                          {s.stripe_customer_id ?? "—"}
                        </td>
                        <td className="py-2 text-gray-400">{fmt(s.current_period_end)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <PaginationBar page={subPage} total={subs.total} pageSize={25} onPage={setSubPage} />
            </>
          )}

          {/* Shops */}
          {section === "shops" && shops && (
            <>
              <SectionHeader title="Etsy Shops" total={shops.total} onRefresh={loadShops} />
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
                        <td className="py-2 pr-4">
                          <Badge status={s.is_connected ? "active" : "inactive"} />
                        </td>
                        <td className="py-2 text-gray-400">{fmt(s.last_synced_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <PaginationBar page={shopPage} total={shops.total} pageSize={25} onPage={setShopPage} />
            </>
          )}

          {/* Scheduled Jobs */}
          {section === "scheduled-jobs" && jobs && (
            <>
              <SectionHeader title="Scheduled Jobs" total={jobs.total} onRefresh={loadJobs} />
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
                        <td className="py-2 pr-4">
                          <Badge status={j.status} />
                        </td>
                        <td className="py-2 pr-4 text-gray-500">{j.run_count}</td>
                        <td className="py-2 pr-4 text-gray-400">{fmt(j.next_run_at)}</td>
                        <td className="py-2 flex gap-2">
                          {(j.status === "active" || j.status === "idle") && (
                            <button
                              onClick={() => handlePause(j.id)}
                              className="text-xs text-yellow-600 hover:underline"
                            >
                              Pause
                            </button>
                          )}
                          {j.status === "paused" && (
                            <button
                              onClick={() => handleResume(j.id)}
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
              <PaginationBar page={jobPage} total={jobs.total} pageSize={25} onPage={setJobPage} />
            </>
          )}

          {/* Audit Events */}
          {section === "events" && events && (
            <>
              <SectionHeader title="Audit Events" total={events.total} onRefresh={loadEvents} />
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
                    {events.items.map((e) => (
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
              <PaginationBar page={eventPage} total={events.total} pageSize={25} onPage={setEventPage} />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
