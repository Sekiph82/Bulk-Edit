"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  adminListPayments,
  adminRefundPayment,
  type AdminPaymentItem,
  type AdminPage as AdminPageType,
  type AdminPaymentFilters,
  ApiError,
} from "@/lib/api";
import { PageHeader, SectionHeader, PaginationBar, Badge, Card, fmt, currency, useOwnerBase, downloadCsv, todayStamp } from "@/components/owner/OwnerUI";

const CSV_COLUMNS = [
  "id", "organization_name", "owner_email", "plan", "subscription_status",
  "event_type", "status", "amount", "currency", "stripe_customer_id", "created_at",
];

export default function OwnerPaymentsPage() {
  const base = useOwnerBase();
  const [payments, setPayments] = useState<AdminPageType<AdminPaymentItem> | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const [q, setQ] = useState("");
  const [plan, setPlan] = useState("");
  const [subscriptionStatus, setSubscriptionStatus] = useState("");
  const [createdFrom, setCreatedFrom] = useState("");
  const [createdTo, setCreatedTo] = useState("");

  const [refundTarget, setRefundTarget] = useState<AdminPaymentItem | null>(null);
  const [refundReason, setRefundReason] = useState("");
  const [refundAmount, setRefundAmount] = useState("");
  const [refundBusy, setRefundBusy] = useState(false);
  const [refundError, setRefundError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);

  const filters: AdminPaymentFilters = {
    q: q || undefined,
    plan: plan || undefined,
    subscription_status: subscriptionStatus || undefined,
    created_from: createdFrom || undefined,
    created_to: createdTo || undefined,
  };

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    adminListPayments(page, 25, filters)
      .then(setPayments)
      .catch(() => setError("Failed to load payments."))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, q, plan, subscriptionStatus, createdFrom, createdTo]);

  useEffect(() => { load(); }, [load]);

  function showFlash(m: string) {
    setFlash(m);
    setTimeout(() => setFlash(null), 4000);
  }

  async function handleExport() {
    setExporting(true);
    try {
      const rows: AdminPaymentItem[] = [];
      let p = 1;
      for (let i = 0; i < 5; i++) {
        const pg = await adminListPayments(p, 100, filters);
        rows.push(...pg.items);
        if (rows.length >= pg.total || pg.items.length === 0) break;
        p += 1;
      }
      const csvRows = rows.map((p) => ({
        id: p.id,
        organization_name: p.organization_name ?? "",
        owner_email: p.owner_email ?? "",
        plan: p.plan ?? "",
        subscription_status: p.subscription_status ?? "",
        event_type: p.event_type,
        status: p.status,
        amount: p.amount ?? "",
        currency: p.currency ?? "",
        stripe_customer_id: p.stripe_customer_id ?? "",
        created_at: p.created_at,
      }));
      downloadCsv(`owner-payments-${todayStamp()}.csv`, csvRows, CSV_COLUMNS);
    } catch {
      setError("Export failed.");
    } finally {
      setExporting(false);
    }
  }

  function openRefund(item: AdminPaymentItem) {
    setRefundTarget(item);
    setRefundReason("");
    setRefundAmount(item.amount !== null ? String(item.amount) : "");
    setRefundError(null);
  }

  async function confirmRefund() {
    if (!refundTarget || !refundReason.trim()) {
      setRefundError("A reason is required.");
      return;
    }
    setRefundBusy(true);
    setRefundError(null);
    try {
      const amount = refundAmount.trim() ? Number(refundAmount) : null;
      const result = await adminRefundPayment(refundTarget.id, refundReason.trim(), amount);
      showFlash(result.message);
      setRefundTarget(null);
      load();
    } catch (e) {
      setRefundError(e instanceof ApiError ? e.message : "Refund failed.");
    } finally {
      setRefundBusy(false);
    }
  }

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Payments" sub="Payments derived from Stripe billing events — superuser only" />
      {error && <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg">{error}</div>}
      {flash && <div className="mb-4 bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm px-4 py-2 rounded-lg">{flash}</div>}

      <Card>
        <div className="flex flex-col lg:flex-row lg:items-end gap-3 mb-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Search</label>
            <input
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              placeholder="Org name, org id, or owner email"
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

        <SectionHeader title="Payments" total={payments?.total} onRefresh={load} />

        {loading && !payments && <p className="text-sm text-gray-400 py-8 text-center">Loading…</p>}

        {payments && (
          <>
            {payments.items.length === 0 ? (
              <p className="text-sm text-gray-400 py-8 text-center">No payment events match these filters.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                      <th className="pb-2 pr-4">Organization</th>
                      <th className="pb-2 pr-4">Plan</th>
                      <th className="pb-2 pr-4">Event</th>
                      <th className="pb-2 pr-4">Status</th>
                      <th className="pb-2 pr-4">Amount</th>
                      <th className="pb-2 pr-4">Stripe ref</th>
                      <th className="pb-2 pr-4">When</th>
                      <th className="pb-2">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.items.map((p) => (
                      <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 pr-4">
                          {p.organization_id ? (
                            <Link href={`${base}/organizations/${p.organization_id}`} className="font-medium text-indigo-600 hover:underline">
                              {p.organization_name ?? p.organization_id}
                            </Link>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                          <p className="text-xs text-gray-400">{p.owner_email ?? ""}</p>
                        </td>
                        <td className="py-2 pr-4 text-gray-500">{p.plan ?? "—"}</td>
                        <td className="py-2 pr-4 text-gray-600 font-mono text-xs">{p.event_type}</td>
                        <td className="py-2 pr-4"><Badge status={p.status} /></td>
                        <td className="py-2 pr-4 text-gray-800">{p.amount !== null ? currency(p.amount) : "—"}</td>
                        <td className="py-2 pr-4 font-mono text-xs text-gray-500">{p.refundable_ref ?? "—"}</td>
                        <td className="py-2 pr-4 text-gray-400">{fmt(p.created_at)}</td>
                        <td className="py-2">
                          {p.refundable_ref && p.status === "succeeded" ? (
                            <button
                              type="button"
                              onClick={() => openRefund(p)}
                              className="text-xs font-medium text-red-600 border border-red-200 rounded-lg px-2.5 py-1 hover:bg-red-50"
                            >
                              Refund
                            </button>
                          ) : (
                            <span className="text-xs text-gray-300">
                              {p.status === "succeeded" ? "Refund via Stripe dashboard" : "—"}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <PaginationBar page={page} total={payments.total} pageSize={25} onPage={setPage} />
          </>
        )}
      </Card>

      {refundTarget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Refund payment</h3>
            <p className="text-sm text-gray-500 mb-4">
              {refundTarget.organization_name ?? refundTarget.organization_id} — {refundTarget.refundable_ref}
            </p>
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-800 mb-4">
              This calls the Stripe API directly and cannot be undone from here. Confirm the amount before continuing.
            </div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Reason (required)</label>
            <textarea
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              rows={2}
              value={refundReason}
              onChange={(e) => setRefundReason(e.target.value)}
            />
            <label className="block text-xs font-medium text-gray-500 mb-1">Amount (USD, leave as-is for full refund)</label>
            <input
              type="number"
              step="0.01"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              value={refundAmount}
              onChange={(e) => setRefundAmount(e.target.value)}
            />
            {refundError && <p className="text-sm text-red-600 mb-3">{refundError}</p>}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setRefundTarget(null)}
                disabled={refundBusy}
                className="text-sm font-medium text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmRefund}
                disabled={refundBusy}
                className="text-sm font-medium text-white bg-red-600 px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {refundBusy ? "Refunding…" : "Confirm refund"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
