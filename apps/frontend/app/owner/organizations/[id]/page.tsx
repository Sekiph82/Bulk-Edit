"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  adminGetOrganizationDetail,
  adminChangePlan,
  adminGrantComp,
  adminRevokeComp,
  adminTriggerSync,
  type AdminOrganizationDetail,
  ApiError,
} from "@/lib/api";
import { PageHeader, Card, Badge, StatCard, fmt, useOwnerBase } from "@/components/owner/OwnerUI";

const PLAN_OPTIONS = ["free", "basic_monthly", "basic_yearly", "pro_monthly", "pro_yearly"];

export default function OwnerOrganizationDetailPage() {
  const params = useParams();
  const orgId = String(params.id);
  const base = useOwnerBase();

  const [org, setOrg] = useState<AdminOrganizationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<string | null>(null);

  const [planTarget, setPlanTarget] = useState("");
  const [planReason, setPlanReason] = useState("");
  const [planBusy, setPlanBusy] = useState(false);
  const [planError, setPlanError] = useState<string | null>(null);
  const [showPlanConfirm, setShowPlanConfirm] = useState(false);

  const [compPlan, setCompPlan] = useState("");
  const [compReason, setCompReason] = useState("");
  const [compEndsAt, setCompEndsAt] = useState("");
  const [compBusy, setCompBusy] = useState(false);
  const [compError, setCompError] = useState<string | null>(null);

  const [syncBusy, setSyncBusy] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [showSyncConfirm, setShowSyncConfirm] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    adminGetOrganizationDetail(orgId)
      .then((d) => {
        setOrg(d);
        setPlanTarget(d.plan ?? "free");
      })
      .catch((e) => setError(e instanceof ApiError && e.status === 404 ? "Organization not found." : "Failed to load organization."))
      .finally(() => setLoading(false));
  }, [orgId]);

  useEffect(() => { load(); }, [load]);

  function flash(m: string) {
    setMsg(m);
    setTimeout(() => setMsg(null), 4000);
  }

  async function confirmChangePlan() {
    if (!planReason.trim()) {
      setPlanError("A reason is required.");
      return;
    }
    setPlanBusy(true);
    setPlanError(null);
    try {
      const result = await adminChangePlan(orgId, planTarget, planReason.trim());
      flash(result.message);
      setShowPlanConfirm(false);
      setPlanReason("");
      load();
    } catch (e) {
      setPlanError(e instanceof ApiError ? e.message : "Plan change failed.");
    } finally {
      setPlanBusy(false);
    }
  }

  async function submitCompGrant() {
    if (!compPlan || !compReason.trim()) {
      setCompError("Plan and reason are required.");
      return;
    }
    setCompBusy(true);
    setCompError(null);
    try {
      await adminGrantComp(orgId, compPlan, compReason.trim(), compEndsAt || null);
      flash("Comp access granted.");
      setCompPlan("");
      setCompReason("");
      setCompEndsAt("");
      load();
    } catch (e) {
      setCompError(e instanceof ApiError ? e.message : "Grant failed.");
    } finally {
      setCompBusy(false);
    }
  }

  async function revokeComp() {
    setCompBusy(true);
    setCompError(null);
    try {
      await adminRevokeComp(orgId);
      flash("Comp access revoked.");
      load();
    } catch (e) {
      setCompError(e instanceof ApiError ? e.message : "Revoke failed.");
    } finally {
      setCompBusy(false);
    }
  }

  async function confirmSync() {
    setSyncBusy(true);
    setSyncError(null);
    try {
      const result = await adminTriggerSync(orgId, null, "Manual sync triggered from owner console");
      flash(result.message);
      setShowSyncConfirm(false);
      load();
    } catch (e) {
      setSyncError(e instanceof ApiError ? e.message : "Sync failed.");
    } finally {
      setSyncBusy(false);
    }
  }

  const hasRisk = org && (org.risk.etsy_disconnected || org.risk.billing_issue || org.risk.failed_bulk_edit_count > 0 || org.risk.failed_ai_count > 0 || org.risk.failed_scheduled_runs_count > 0);

  return (
    <main className="max-w-6xl mx-auto px-6 py-8">
      <div className="mb-4">
        <Link href={`${base}/organizations`} className="text-sm text-indigo-600 hover:underline">← Back to Organizations</Link>
      </div>

      {loading && <p className="text-sm text-gray-400 py-8 text-center">Loading…</p>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}
      {msg && <div className="mb-4 bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm px-4 py-2 rounded-lg">{msg}</div>}

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

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <Card>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Plan &amp; access</h2>
              <dl className="space-y-2 text-sm mb-4">
                <div className="flex justify-between"><dt className="text-gray-400">Effective plan</dt><dd className="font-medium text-gray-800">{org.effective_access.effective_plan}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-400">Stripe-managed</dt><dd className="text-gray-800">{org.effective_access.stripe_managed ? "Yes" : "No"}</dd></div>
                {org.effective_access.comp && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg px-3 py-2 mt-2">
                    <p className="text-xs font-medium text-purple-800">Active comp grant: {org.effective_access.comp.comp_plan}</p>
                    <p className="text-[11px] text-purple-600 mt-0.5">{org.effective_access.comp.reason}</p>
                    <p className="text-[11px] text-purple-500 mt-0.5">
                      Since {fmt(org.effective_access.comp.starts_at)}{org.effective_access.comp.ends_at ? ` · ends ${fmt(org.effective_access.comp.ends_at)}` : " · no end date"}
                    </p>
                    <button
                      type="button"
                      onClick={revokeComp}
                      disabled={compBusy}
                      className="mt-2 text-xs font-medium text-red-600 hover:underline disabled:opacity-50"
                    >
                      Revoke comp access
                    </button>
                  </div>
                )}
              </dl>

              <div className="border-t border-gray-100 pt-3 mb-4">
                <p className="text-xs font-semibold text-gray-600 mb-2">Change plan directly</p>
                {org.effective_access.stripe_managed ? (
                  <p className="text-xs text-gray-400">
                    This organization has an active Stripe-managed subscription — change the plan via the Stripe dashboard or the customer billing portal.
                  </p>
                ) : (
                  <>
                    <div className="flex gap-2 mb-2">
                      <select
                        className="flex-1 border border-gray-200 rounded-lg px-2 py-1.5 text-sm"
                        value={planTarget}
                        onChange={(e) => setPlanTarget(e.target.value)}
                      >
                        {PLAN_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
                      </select>
                      <button
                        type="button"
                        onClick={() => setShowPlanConfirm(true)}
                        className="text-xs font-medium text-white bg-indigo-600 rounded-lg px-3 py-1.5 hover:bg-indigo-700"
                      >
                        Change
                      </button>
                    </div>
                    {showPlanConfirm && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                        <p className="text-xs text-gray-600 mb-2">Set plan to <strong>{planTarget}</strong>. This directly edits the local subscription record.</p>
                        <textarea
                          placeholder="Reason (required)"
                          className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm mb-2"
                          rows={2}
                          value={planReason}
                          onChange={(e) => setPlanReason(e.target.value)}
                        />
                        {planError && <p className="text-xs text-red-600 mb-2">{planError}</p>}
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={confirmChangePlan}
                            disabled={planBusy}
                            className="text-xs font-medium text-white bg-indigo-600 rounded-lg px-3 py-1.5 hover:bg-indigo-700 disabled:opacity-50"
                          >
                            {planBusy ? "Saving…" : "Confirm"}
                          </button>
                          <button
                            type="button"
                            onClick={() => { setShowPlanConfirm(false); setPlanError(null); }}
                            className="text-xs font-medium text-gray-500 px-3 py-1.5 hover:bg-gray-100 rounded-lg"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>

              <div className="border-t border-gray-100 pt-3">
                <p className="text-xs font-semibold text-gray-600 mb-2">Grant comp access</p>
                <div className="flex gap-2 mb-2">
                  <select
                    className="flex-1 border border-gray-200 rounded-lg px-2 py-1.5 text-sm"
                    value={compPlan}
                    onChange={(e) => setCompPlan(e.target.value)}
                  >
                    <option value="">Choose plan…</option>
                    {PLAN_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                  <input
                    type="date"
                    className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm"
                    value={compEndsAt}
                    onChange={(e) => setCompEndsAt(e.target.value)}
                    title="Ends at (optional — leave blank for indefinite)"
                  />
                </div>
                <textarea
                  placeholder="Reason (required)"
                  className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm mb-2"
                  rows={2}
                  value={compReason}
                  onChange={(e) => setCompReason(e.target.value)}
                />
                {compError && <p className="text-xs text-red-600 mb-2">{compError}</p>}
                <button
                  type="button"
                  onClick={submitCompGrant}
                  disabled={compBusy}
                  className="text-xs font-medium text-white bg-purple-600 rounded-lg px-3 py-1.5 hover:bg-purple-700 disabled:opacity-50"
                >
                  {compBusy ? "Granting…" : "Grant comp access"}
                </button>
                <p className="text-[11px] text-gray-400 mt-2">
                  Comp access is tracked and audited here but does not yet change runtime feature limits — that enforcement wiring is a follow-up.
                </p>
              </div>
            </Card>

            <Card>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Etsy sync</h2>
              {org.shops.length === 0 ? (
                <p className="text-sm text-gray-400 mb-4">No shops connected — nothing to sync.</p>
              ) : (
                <ul className="space-y-1.5 mb-4">
                  {org.shops.map((s) => (
                    <li key={s.id} className="text-sm flex items-center justify-between">
                      <span className="text-gray-700 truncate">{s.shop_name}</span>
                      <span className="flex items-center gap-2">
                        <Badge status={String(s.is_connected)} />
                        <span className="text-xs text-gray-400">{fmt(s.last_synced_at)}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              )}

              {syncError && <p className="text-xs text-red-600 mb-2">{syncError}</p>}

              {!showSyncConfirm ? (
                <button
                  type="button"
                  onClick={() => setShowSyncConfirm(true)}
                  disabled={org.shops.filter((s) => s.is_connected).length === 0}
                  className="text-xs font-medium text-indigo-600 border border-indigo-200 rounded-lg px-3 py-1.5 hover:bg-indigo-50 disabled:opacity-40"
                >
                  Trigger manual sync
                </button>
              ) : (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-xs text-gray-600 mb-2">
                    This runs synchronously and blocks until it finishes — this codebase has no background job queue yet.
                  </p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={confirmSync}
                      disabled={syncBusy}
                      className="text-xs font-medium text-white bg-indigo-600 rounded-lg px-3 py-1.5 hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {syncBusy ? "Syncing…" : "Confirm sync"}
                    </button>
                    <button
                      type="button"
                      onClick={() => { setShowSyncConfirm(false); setSyncError(null); }}
                      className="text-xs font-medium text-gray-500 px-3 py-1.5 hover:bg-gray-100 rounded-lg"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </Card>
          </div>

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
