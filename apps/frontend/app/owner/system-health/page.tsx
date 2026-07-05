"use client";

import { useEffect, useState } from "react";
import { adminGetSystemHealth, type AdminSystemHealth } from "@/lib/api";
import { PageHeader, StatCard } from "@/components/owner/OwnerUI";

export default function OwnerSystemHealthPage() {
  const [health, setHealth] = useState<AdminSystemHealth | null>(null);

  useEffect(() => {
    adminGetSystemHealth().then(setHealth).catch(() => {});
  }, []);

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="System Health" sub="Live platform status — superuser only" />
      {health && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <StatCard label="Database" value={health.database_status.toUpperCase()} sub="PostgreSQL connection" />
          <StatCard label="Redis" value={health.redis_status} />
          <StatCard label="Rate Limiting" value={health.rate_limit_enabled ? "Enabled" : "Disabled"} sub={health.rate_limit_backend} />
          <StatCard label="Total Users" value={health.total_users} />
          <StatCard label="Organizations" value={health.total_organizations} />
          <StatCard label="Audit Events" value={health.total_audit_events} />
          <StatCard label="Failed Scheduled Runs" value={health.recent_failed_scheduled_runs} sub="All time" />
          <StatCard label="Failed AI Sessions" value={health.recent_failed_ai_sessions} sub="All time" />
          <StatCard label="Sentry" value={health.sentry_configured ? "Configured" : "Not configured"} />
        </div>
      )}
    </main>
  );
}
