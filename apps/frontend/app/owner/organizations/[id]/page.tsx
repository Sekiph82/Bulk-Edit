"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  adminGetOrganizationDetail,
  type AdminOrganizationDetail,
  ApiError,
} from "@/lib/api";
import { PageHeader, Card, Badge, StatCard, fmt, useOwnerBase } from "@/components/owner/OwnerUI";

export default function OwnerOrganizationDetailPage() {
  const params = useParams();
  const orgId = String(params.id);
  const base = useOwnerBase();

  const [org, setOrg] = useState<AdminOrganizationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    adminGetOrganizationDetail(orgId)
      .then(setOrg)
      .catch((e) => setError(e instanceof ApiError && e.status === 404 ? "Organization not found." : "Failed to load organization."))
      .finally(() => setLoading(false));
  }, [orgId]);

  useEffect(() => { load(); }, [load]);

  const hasRisk = org && (org.risk.etsy_disconnected || org.risk.billing_issue || org.risk.failed_bulk_edit_count > 0 || org.risk.failed_ai_count > 0 || org.risk.failed_scheduled_runs_count > 0);

  return (
    <main className="max-w-6xl mx-auto px-6 py-8">
      <div className="mb-4">
        <Link href={`${base}/organizations`} className="text-sm text-indigo-600 hover:underline">← Back to Organizations</Link>
      </div>

      {loading && <p className="text-sm text-gray-400 py-8 text-center">Loading…</p>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}

      {org && (
        <>
          <PageHeader title={org.name} sub={`Organization ID: ${org.id}`} />

          {hasRisk && (
            <div className="mb-6 bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-amber-800 mb-1">Risk indicators</p>
              <ul className="text-xs text-amber-700 space-y-0.5">
                {org.risk.etsy_disconnected && <li>• Etsy shop disconnected</li>}
                {org.risk.billing_issue && <li>• Billing issue on subscription</li>}
                {org.risk.failed_bulk_edit_count > 0 && <li>• {org.risk.failed_bulk_edit_count} failed bulk edit session(s)</li>}
                {org.risk.failed_ai_count > 0 && <li>• {org.risk.failed_ai_count} failed AI session(s)</li>}
                {org.risk.failed_scheduled_runs_count > 0 && <li>• {org.risk.failed_scheduled_runs_count} failed scheduled run(s)</li>}
              </ul>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <Card>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Identity</h2>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between"><dt className="text-gray-400">Org ID</dt><dd className="font-mono text-xs text-gray-700">{org.id}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Name</dt><dd className="text-gray-800">{org.name}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Owner</dt><dd className="text-gray-800">{org.owner_email ?? "—"}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Users</dt><dd className="text-gray-800">{org.users_count}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Created</dt><dd className="text-gray-600">{fmt(org.created_at)}</dd></div>
              </dl>
            </Card>

            <Card>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Billing</h2>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between"><dt className="text-gray-400">Plan</dt><dd className="text-gray-800">{org.plan ?? "—"}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Status</dt><dd>{org.subscription_status ? <Badge status={org.subscription_status} /> : "—"}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Stripe customer</dt><dd className="font-mono text-xs text-gray-500">{org.subscription?.stripe_customer_id ?? "—"}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Cancels at period end</dt><dd className="text-gray-800">{org.subscription?.cancel_at_period_end ? "Yes" : "No"}</dd></div>
              </dl>
            </Card>

            <Card>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Etsy Shops</h2>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-400">Connected</span>
                <Badge status={String(org.etsy_connected)} />
              </div>
              {org.shops.length === 0 ? (
                <p className="text-sm text-gray-400">No shops connected.</p>
              ) : (
                <ul className="space-y-1.5">
                  {org.shops.map((s) => (
                    <li key={s.id} className="text-sm flex items-center justify-between">
                      <span className="text-gray-700 truncate">{s.shop_name}</span>
                      <Badge status={String(s.is_connected)} />
                    </li>
                  ))}
                </ul>
              )}
              <p className="text-xs text-gray-400 mt-2">Listings synced: {org.listing_count}</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <Card>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Usage</h2>
              <div className="grid grid-cols-2 gap-3">
                <StatCard label="Bulk Edit Sessions" value={org.usage.bulk_edit_sessions_count} />
                <StatCard label="AI Sessions" value={org.usage.ai_sessions_count} />
                <StatCard label="CSV Jobs" value={org.usage.csv_jobs_count} />
                <StatCard label="Media Jobs" value={org.usage.media_jobs_count} />
                <StatCard label="Video Renders" value={org.usage.video_renders_count} />
                <StatCard label="Sync Jobs" value={org.usage.sync_jobs_count} />
              </div>
              <p className="text-[11px] text-gray-400 mt-3">
                Dynamic pricing jobs: {org.usage.dynamic_pricing_jobs_count}
              </p>
            </Card>

            <Card>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Members</h2>
              {org.members.length === 0 ? (
                <p className="text-sm text-gray-400">No members.</p>
              ) : (
                <ul className="space-y-2">
                  {org.members.map((m) => (
                    <li key={m.user_id} className="flex items-center justify-between text-sm">
                      <Link href={`${base}/users/${m.user_id}`} className="text-indigo-600 hover:underline truncate">
                        {m.email}
                      </Link>
                      <span className="text-xs text-gray-400">{m.role}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>

          <Card>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Recent Activity</h2>
            {org.recent_events.length === 0 ? (
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
                    {org.recent_events.map((e) => (
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
