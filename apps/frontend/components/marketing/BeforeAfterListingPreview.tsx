"use client";

import { motion, useReducedMotion } from "motion/react";

// Static-but-animated illustration of a bulk-edit before/after diff.
// Purely decorative marketing visual — not a live data widget.
export default function BeforeAfterListingPreview() {
  const reduced = useReducedMotion();
  const rows = [
    { before: "Ceramic Mug", after: "Ceramic Mug — 2026 Gift-Ready" },
    { before: "$28.00", after: "$30.80" },
    { before: "handmade, gift", after: "handmade, gift, holiday gift" },
  ];

  return (
    <div className="rounded-2xl border border-gray-200 shadow-xl bg-white overflow-hidden max-w-md" role="img" aria-label="Example before and after listing edit preview">
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 flex items-center justify-between">
        <span className="text-[11px] font-semibold text-amber-800 uppercase tracking-wide">Preview — before you apply</span>
        <span className="text-[11px] text-amber-700">1 listing</span>
      </div>
      <div className="divide-y divide-gray-100">
        {rows.map((r, i) => (
          <motion.div
            key={r.before}
            className="px-4 py-3 flex items-center gap-3 text-xs"
            initial={reduced ? false : { opacity: 0, x: -8 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.35, delay: i * 0.1 }}
          >
            <span className="text-gray-400 line-through flex-1 truncate">{r.before}</span>
            <span className="text-amber-500 flex-shrink-0">→</span>
            <span className="text-gray-900 font-medium flex-1 truncate">{r.after}</span>
          </motion.div>
        ))}
      </div>
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 flex items-center gap-2">
        <span className="w-4 h-4 rounded-full bg-green-100 border border-green-300 flex items-center justify-center flex-shrink-0">
          <svg className="w-2.5 h-2.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </span>
        <span className="text-[11px] text-gray-500">Backup snapshot will be created before this applies</span>
      </div>
    </div>
  );
}
