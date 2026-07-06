"use client";

import FadeUp from "./FadeUp";

// Mock/example UI built from generic sample data — not a real customer's
// shop, not a real Etsy seller's listings. Wording below deliberately says
// "example" / "sample" rather than "real screenshot".

const GRID_ROWS = [
  { title: "Wool blend scarf", tags: ["handmade", "winter"], price: "$32.00", status: "active" },
  { title: "Enamel pin set", tags: ["accessory", "gift"], price: "$14.00", status: "active" },
  { title: "Vintage postcard bundle", tags: ["vintage", "paper"], price: "$9.00", status: "active" },
];

const DIFF_ROWS = [
  { field: "Title", before: "Wool blend scarf", after: "Wool blend scarf — winter gift edition" },
  { field: "Price", before: "$32.00", after: "$35.20" },
  { field: "Tags", before: "handmade, winter", after: "handmade, winter, gift" },
];

const TIMELINE = [
  { label: "Backup snapshot created", detail: "Before any change reaches Etsy", tone: "neutral" },
  { label: "Bulk edit applied", detail: "3 listings updated", tone: "success" },
  { label: "Magic Revert available", detail: "Restore the snapshot anytime", tone: "info" },
];

export default function ProductScreenshotsSection() {
  return (
    <section className="py-20 px-6 sm:px-8 bg-white">
      <div className="max-w-6xl mx-auto">
        <FadeUp className="text-center mb-14">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            See every change before it touches your Etsy shop
          </h2>
          <p className="text-gray-500 max-w-2xl mx-auto">
            Bulk Edit App is built around a simple safety loop: select listings, preview changes,
            apply only when you&apos;re sure, and revert if needed.
          </p>
        </FadeUp>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 — Bulk edit grid */}
          <FadeUp>
            <div className="be-card p-5 h-full flex flex-col">
              <h3 className="font-bold text-gray-900 mb-1">Bulk edit grid</h3>
              <p className="text-xs text-gray-400 mb-4">Example bulk edit workflow — sample listing data</p>
              <div className="rounded-lg border border-gray-200 overflow-hidden text-xs flex-1">
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border-b border-gray-200 text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                  <div className="w-3.5 h-3.5 rounded border border-gray-300 flex-shrink-0" />
                  <div className="flex-1">Title</div>
                  <div className="w-14 text-right">Price</div>
                  <div className="w-12">Status</div>
                </div>
                {GRID_ROWS.map((row) => (
                  <div key={row.title} className="flex items-center gap-2 px-3 py-2 border-b border-gray-100 last:border-b-0 bg-indigo-50/60">
                    <div className="w-3.5 h-3.5 rounded bg-indigo-600 flex items-center justify-center flex-shrink-0">
                      <svg className="w-2 h-2 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-800 font-medium truncate">{row.title}</p>
                      <div className="flex gap-1 mt-0.5">
                        {row.tags.map((t) => (
                          <span key={t} className="text-[9px] bg-gray-100 text-gray-500 px-1 py-0.5 rounded">{t}</span>
                        ))}
                      </div>
                    </div>
                    <div className="w-14 text-right text-gray-700 flex-shrink-0">{row.price}</div>
                    <div className="w-12 flex-shrink-0">
                      <span className="text-[9px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium">{row.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </FadeUp>

          {/* Card 2 — Preview & diff */}
          <FadeUp delay={0.08}>
            <div className="be-card p-5 h-full flex flex-col">
              <h3 className="font-bold text-gray-900 mb-1">Preview &amp; diff</h3>
              <p className="text-xs text-gray-400 mb-4">Product workflow preview — sample listing data</p>
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 mb-3 flex-shrink-0">
                <p className="text-[10px] font-semibold text-amber-800 uppercase tracking-wide">Preview ready</p>
                <p className="text-[10px] text-amber-700 mt-0.5">3 changes on 1 listing</p>
              </div>
              <div className="space-y-2 flex-1">
                {DIFF_ROWS.map((d) => (
                  <div key={d.field} className="rounded-lg border border-gray-200 bg-gray-50 p-2.5">
                    <p className="text-[9px] font-semibold text-gray-400 uppercase tracking-wide mb-1">{d.field}</p>
                    <p className="text-[11px] text-gray-400 line-through truncate">{d.before}</p>
                    <p className="text-[11px] text-gray-800 font-medium truncate">{d.after}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 rounded-lg bg-indigo-600 text-white text-center text-[11px] font-semibold py-2">
                Confirm to apply
              </div>
            </div>
          </FadeUp>

          {/* Card 3 — Magic Revert / backups */}
          <FadeUp delay={0.16}>
            <div className="be-card p-5 h-full flex flex-col">
              <h3 className="font-bold text-gray-900 mb-1">Magic Revert &amp; backups</h3>
              <p className="text-xs text-gray-400 mb-4">Example bulk edit workflow — sample listing data</p>
              <ul className="space-y-3 flex-1">
                {TIMELINE.map((step, i) => (
                  <li key={step.label} className="flex items-start gap-2.5">
                    <span
                      className={`mt-0.5 w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                        step.tone === "success" ? "bg-green-500" : step.tone === "info" ? "bg-indigo-500" : "bg-gray-300"
                      }`}
                    />
                    <div className="min-w-0">
                      <p className="text-[11px] font-medium text-gray-800">{step.label}</p>
                      <p className="text-[10px] text-gray-400">{step.detail}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <div className="mt-3 rounded-lg border border-gray-200 text-center text-[11px] font-semibold text-gray-700 py-2">
                Restore this snapshot
              </div>
            </div>
          </FadeUp>
        </div>
      </div>
    </section>
  );
}
