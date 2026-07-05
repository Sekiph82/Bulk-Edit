"use client";

import { useCallback, useEffect, useState } from "react";
import { adminListShops, type AdminShop, type AdminPage as AdminPageType } from "@/lib/api";
import { PageHeader, SectionHeader, PaginationBar, Badge, Card, fmt } from "@/components/owner/OwnerUI";

export default function OwnerShopsPage() {
  const [shops, setShops] = useState<AdminPageType<AdminShop> | null>(null);
  const [page, setPage] = useState(1);

  const load = useCallback(() => {
    adminListShops(page).then(setShops).catch(() => {});
  }, [page]);

  useEffect(() => { load(); }, [load]);

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <PageHeader title="Shops" sub="Connected Etsy shops across all organizations — superuser only" />
      <Card>
        <SectionHeader title="Connected Shops" total={shops?.total} onRefresh={load} />
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
            <PaginationBar page={page} total={shops.total} pageSize={25} onPage={setPage} />
          </>
        )}
      </Card>
    </main>
  );
}
