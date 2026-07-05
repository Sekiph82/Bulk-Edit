"use client";

import { useEffect, useState } from "react";
import {
  adminGetOverview,
  adminGetBillingSummary,
  type AdminOverview,
  type AdminBillingSummary,
} from "@/lib/api";
import { PageHeader, StatCard, currency } from "@/components/owner/OwnerUI";

export default function OwnerDashboardPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [billing, setBilling] = useState<AdminBillingSummary | null>(null);

  useEffect(() => {
    adminGetOverview().then(setOverview).catch(() => {});
    adminGetBillingSummary().then(setBilling).catch(() => {});
  }, []);

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Owner Dashboard" sub="Platform-wide metrics — superuser only" />

      <div className="mb-6">
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
            <StatCard label="Projected MRR" value={currency(billing.estimated_monthly_revenue)} sub="Expected — not guaranteed cash" />
            <StatCard label="Active Subs" value={billing.active_count} />
            <StatCard
              label="Paid Plans"
              value={billing.basic_monthly_count + billing.basic_yearly_count + billing.pro_monthly_count + billing.pro_yearly_count}
            />
            <StatCard label="Canceling" value={billing.cancel_at_period_end_count} />
          </div>
        </div>
      )}
    </main>
  );
}
