"use client";

import Link from "next/link";
import FadeUp from "./FadeUp";

// Careful, non-attack positioning only. No "better than X", no unverified
// competitor feature claims, no pricing claims for competitors, and no
// Etsy/Vela/Evlista affiliation or endorsement claims for Bulk Edit App.
// One single table only — do not split into per-competitor tables.
const ROWS: { need: string; bulkEdit: string; vela: string; evlista: string }[] = [
  {
    need: "Bulk listing updates",
    bulkEdit: "Preview-first bulk updates across titles, tags, prices, and more",
    vela: "Check current plan and feature availability",
    evlista: "Check current plan and feature availability",
  },
  {
    need: "Preview before applying",
    bulkEdit: "Full before/after diff on every bulk edit",
    vela: "Verify preview and rollback workflow before bulk changes",
    evlista: "Verify preview and rollback workflow before bulk changes",
  },
  {
    need: "Revert / backup snapshots",
    bulkEdit: "Magic Revert restores any listing from an automatic pre-edit snapshot",
    vela: "Feature availability varies by tool and plan",
    evlista: "Feature availability varies by tool and plan",
  },
  {
    need: "Listing cleanup workflow",
    bulkEdit: "Listing health score and AI suggestions, reviewed before applying",
    vela: "Feature availability varies by tool and plan",
    evlista: "Feature availability varies by tool and plan",
  },
  {
    need: "Media and video operations",
    bulkEdit: "Add Video, Replace Video, and Delete Video, previewed before applying",
    vela: "Verify current media workflow support",
    evlista: "Verify current media workflow support",
  },
  {
    need: "Pricing transparency",
    bulkEdit: "Free $0, Basic $19/mo, Pro $49/mo — published on our pricing page",
    vela: "Verify current pricing on the provider's website",
    evlista: "Verify current pricing on the provider's website",
  },
  {
    need: "Safety-first workflow",
    bulkEdit: "No blind writes — every Etsy write requires preview, confirmation, and a backup snapshot",
    vela: "Verify preview and rollback workflow before bulk changes",
    evlista: "Verify preview and rollback workflow before bulk changes",
  },
];

export default function ComparisonSection() {
  return (
    <section className="py-20 px-6 sm:px-8 bg-white border-t border-gray-100">
      <div className="max-w-5xl mx-auto">
        <FadeUp className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Compare Bulk Edit App with Vela and Evlista
          </h2>
          <p className="text-gray-500 max-w-2xl mx-auto leading-relaxed">
            Different Etsy seller tools can fit different workflows. This comparison focuses on
            workflow fit: safer bulk editing, previewing changes, reversible updates, and listing
            cleanup.
          </p>
        </FadeUp>

        <FadeUp delay={0.1}>
          <div className="be-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[720px]">
                <thead>
                  <tr className="bg-gray-100 border-b border-gray-200">
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Workflow need
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Bulk Edit App
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Vela
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Evlista
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {ROWS.map((row, i) => (
                    <tr key={row.need} className={i % 2 === 1 ? "bg-gray-50" : "bg-white"}>
                      <td className="px-4 py-3 font-semibold text-gray-900 border-b border-gray-200 last:border-b-0">
                        {row.need}
                      </td>
                      <td className="px-4 py-3 text-indigo-700 font-medium border-b border-gray-200 last:border-b-0">
                        {row.bulkEdit}
                      </td>
                      <td className="px-4 py-3 text-gray-700 border-b border-gray-200 last:border-b-0">
                        {row.vela}
                      </td>
                      <td className="px-4 py-3 text-gray-700 border-b border-gray-200 last:border-b-0">
                        {row.evlista}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </FadeUp>

        <FadeUp delay={0.16}>
          <div className="flex flex-col sm:flex-row gap-3 justify-center mt-8">
            <Link href="/compare/bulk-edit-app-vs-vela" className="be-btn-secondary px-6 py-2.5 text-sm">
              Bulk Edit App vs Vela →
            </Link>
            <Link href="/compare/bulk-edit-app-vs-evlista" className="be-btn-secondary px-6 py-2.5 text-sm">
              Bulk Edit App vs Evlista →
            </Link>
          </div>
        </FadeUp>

        <FadeUp delay={0.2}>
          <p className="text-xs text-gray-500 text-center max-w-2xl mx-auto mt-6 leading-relaxed">
            Vela and Evlista are trademarks of their respective owners. Bulk Edit App is independent
            and is not affiliated with or endorsed by Etsy, Vela, or Evlista. Feature availability
            can change, so always verify current details with each provider.
          </p>
        </FadeUp>
      </div>
    </section>
  );
}
