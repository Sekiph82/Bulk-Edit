"use client";

import FadeUp from "./FadeUp";

// Careful, non-attack positioning only. No "better than X", no "only tool",
// no pricing comparisons, no claims about what competitors lack beyond
// "varies by tool" where we don't have verified public information, and no
// Etsy affiliation/certification claims for Bulk Edit App or anyone else.
const ROWS: { need: string; seo: string; bulkEdit: string }[] = [
  { need: "Keyword research", seo: "Strong focus", bulkEdit: "AI listing suggestions, not a dedicated keyword database" },
  { need: "Bulk apply changes", seo: "Varies by tool", bulkEdit: "Core focus" },
  { need: "Preview before applying", seo: "Varies by tool", bulkEdit: "Core safety flow" },
  { need: "Backup / revert", seo: "Varies by tool", bulkEdit: "Magic Revert snapshots" },
  { need: "Media workflows", seo: "Varies by tool", bulkEdit: "Media tools, Product Video Generator" },
];

export default function ComparisonSection() {
  return (
    <section className="py-20 px-6 sm:px-8 bg-white border-t border-gray-100">
      <div className="max-w-4xl mx-auto">
        <FadeUp className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Where Bulk Edit App fits alongside other Etsy seller tools
          </h2>
          <p className="text-gray-500 max-w-2xl mx-auto leading-relaxed">
            Tools such as eRank, Marmalead, and Alura are commonly associated with Etsy keyword
            research, SEO insights, or market research. Bulk Edit App focuses on the workflow of
            safely changing many listings at once — many sellers may use both kinds of tools
            together.
          </p>
          <p className="text-gray-500 max-w-2xl mx-auto leading-relaxed mt-3">
            Vela is known by many Etsy sellers for listing editing workflows. Bulk Edit App
            focuses on preview-first, backup-backed, reversible bulk changes across many
            listings at once.
          </p>
        </FadeUp>

        <FadeUp delay={0.1}>
          <div className="be-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[560px]">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Workflow need
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      SEO research tools
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Bulk Edit App
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {ROWS.map((row, i) => (
                    <tr key={row.need} className={i % 2 === 1 ? "bg-gray-50/60" : ""}>
                      <td className="px-4 py-3 font-medium text-gray-800 border-b border-gray-100 last:border-b-0">
                        {row.need}
                      </td>
                      <td className="px-4 py-3 text-gray-500 border-b border-gray-100 last:border-b-0">
                        {row.seo}
                      </td>
                      <td className="px-4 py-3 text-indigo-700 font-medium border-b border-gray-100 last:border-b-0">
                        {row.bulkEdit}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </FadeUp>

        <FadeUp delay={0.16}>
          <p className="text-xs text-gray-400 text-center max-w-2xl mx-auto mt-6 leading-relaxed">
            Competitor names are trademarks of their respective owners. This comparison is for
            general positioning only and is not an endorsement, affiliation, or certification.
          </p>
        </FadeUp>
      </div>
    </section>
  );
}
