"use client";

import { useEffect, useState } from "react";
import { adminGetFeatureFlags, type AdminFeatureFlags } from "@/lib/api";
import { PageHeader, Card, Badge } from "@/components/owner/OwnerUI";

// Read-only by design: these mirror real env-driven config, there is no
// functional toggle backend yet. Do not add write actions here until a real
// admin-controlled flag store exists — a read-only mirror is honest; a fake
// switch that silently does nothing is not.
export default function OwnerFeatureFlagsPage() {
  const [flags, setFlags] = useState<AdminFeatureFlags | null>(null);

  useEffect(() => {
    adminGetFeatureFlags().then(setFlags).catch(() => {});
  }, []);

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Feature Flags" sub="Read-only view of current environment config — superuser only" />
      <Card>
        <p className="text-sm text-gray-500 mb-4">
          These reflect real deployed config. There is no functional toggle here yet — changing a flag
          still requires updating the platform env vars and redeploying.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                <th className="pb-2 pr-4">Flag</th>
                <th className="pb-2 pr-4">State</th>
                <th className="pb-2">Source</th>
              </tr>
            </thead>
            <tbody>
              {flags?.flags.map((f) => (
                <tr key={f.key} className="border-b border-gray-50">
                  <td className="py-2 pr-4 font-mono text-xs text-gray-700">{f.key}</td>
                  <td className="py-2 pr-4"><Badge status={f.enabled ? "true" : "false"} /></td>
                  <td className="py-2 text-gray-400 text-xs">{f.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </main>
  );
}
