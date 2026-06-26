"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { useTheme } from "@/components/theme/ThemeProvider";

const LISTINGS = [
  { id: 1, title: "Ceramic mug set", tags: ["handmade", "gift"], price: 28.0 },
  { id: 2, title: "Linen tote bag", tags: ["eco", "minimalist"], price: 34.0 },
  { id: 3, title: "Printable wall art", tags: ["digital", "instant"], price: 6.0 },
  { id: 4, title: "Handmade candle", tags: ["soy", "scented"], price: 18.0 },
];

const SELECTED = new Set([1, 2, 3]);

// Phase durations in ms
const DURATIONS = [1200, 2200, 2800, 2800, 4000];
// 0 = grid idle
// 1 = rows selected
// 2 = edit panel visible
// 3 = preview panel visible
// 4 = apply / safety strip visible

export default function AnimatedProductDemo() {
  const [phase, setPhase] = useState(0);
  const prefersReduced = useReducedMotion();
  const { resolved } = useTheme();
  const isDark = resolved === "dark";

  useEffect(() => {
    if (prefersReduced) {
      setPhase(4);
      return;
    }
    const timer = setTimeout(() => {
      setPhase((p) => (p >= 4 ? 0 : p + 1));
    }, DURATIONS[phase]);
    return () => clearTimeout(timer);
  }, [phase, prefersReduced]);

  const sel = (id: number) => phase >= 1 && SELECTED.has(id);
  const showPanel = phase >= 2;
  const showPreview = phase >= 3;
  const showSafety = phase >= 4;

  const easeOut = { duration: 0.35, ease: "easeOut" } as const;
  const easeOutSlow = { duration: 0.45, ease: "easeOut" } as const;

  return (
    <div
      className="w-full select-none"
      aria-hidden="true"
      role="presentation"
    >
      {/* Mock app shell */}
      <div className="rounded-2xl border border-gray-200 shadow-2xl bg-white overflow-hidden">

        {/* Title bar */}
        <div className="bg-gray-100 border-b border-gray-200 px-4 py-2.5 flex items-center gap-3">
          <div className="flex gap-1.5 flex-shrink-0">
            <div className="w-3 h-3 rounded-full bg-red-400" />
            <div className="w-3 h-3 rounded-full bg-yellow-400" />
            <div className="w-3 h-3 rounded-full bg-green-400" />
          </div>
          <span className="text-xs text-gray-500 font-medium flex-1 text-center">
            Bulk-Edit Workspace
          </span>
          <AnimatePresence>
            {phase >= 1 && (
              <motion.span
                key="sel-badge"
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.85 }}
                transition={easeOut}
                className="flex-shrink-0 text-[10px] bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-semibold"
              >
                3 selected
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Content area: table + sliding panel */}
        <div className="relative overflow-hidden" style={{ minHeight: 200 }}>

          {/* Listing table */}
          <div className="w-full">
            {/* Table header */}
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border-b border-gray-200">
              <div className="w-4 flex-shrink-0" />
              <div className="flex-1 text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Listing</div>
              <div className="w-14 text-right text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Price</div>
              <div className="w-12 text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Status</div>
            </div>

            {LISTINGS.map((listing, i) => {
              const selected = sel(listing.id);
              const changed = showPreview && selected;
              return (
                <motion.div
                  key={listing.id}
                  animate={{
                    backgroundColor: selected
                      ? (isDark ? "rgba(59,130,246,0.18)" : "#EEF2FF")
                      : (isDark ? "rgba(7,15,38,0.45)"    : "#FFFFFF"),
                  }}
                  transition={{ duration: 0.3, delay: i * 0.07 }}
                  className="flex items-center gap-2 px-3 py-2.5 border-b border-gray-100"
                >
                  {/* Checkbox */}
                  <motion.div
                    animate={{
                      borderColor: selected
                        ? "#6366F1"
                        : (isDark ? "rgba(96,165,250,0.40)" : "#D1D5DB"),
                      backgroundColor: selected
                        ? "#6366F1"
                        : (isDark ? "rgba(2,12,24,0.85)" : "#FFFFFF"),
                    }}
                    transition={{ duration: 0.2, delay: i * 0.07 }}
                    className="w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0"
                  >
                    <AnimatePresence>
                      {selected && (
                        <motion.svg
                          key="check"
                          initial={{ opacity: 0, scale: 0.4 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.4 }}
                          transition={{ duration: 0.15 }}
                          className="w-2.5 h-2.5 text-white"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </motion.svg>
                      )}
                    </AnimatePresence>
                  </motion.div>

                  {/* Title + tags */}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-800 truncate">{listing.title}</p>
                    <div className="flex flex-wrap gap-1 mt-0.5">
                      {listing.tags.map((tag) => (
                        <span
                          key={tag}
                          className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      <AnimatePresence>
                        {changed && (
                          <motion.span
                            key="new-tag"
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            transition={{ duration: 0.2, delay: 0.1 }}
                            className="text-[10px] bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded font-medium"
                          >
                            holiday gift
                          </motion.span>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>

                  {/* Price */}
                  <div className="w-14 text-right flex-shrink-0">
                    <AnimatePresence mode="wait">
                      {changed ? (
                        <motion.div
                          key="changed-price"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <p className="text-[10px] line-through text-gray-400">
                            ${listing.price.toFixed(2)}
                          </p>
                          <p className="text-xs font-semibold text-green-700">
                            ${(listing.price * 1.1).toFixed(2)}
                          </p>
                        </motion.div>
                      ) : (
                        <motion.span
                          key="price"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="text-xs text-gray-700"
                        >
                          ${listing.price.toFixed(2)}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Status */}
                  <div className="w-12 flex-shrink-0">
                    <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium">
                      active
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Edit panel — slides in from right */}
          <AnimatePresence>
            {showPanel && (
              <motion.div
                key="edit-panel"
                initial={{ x: "100%", opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: "100%", opacity: 0 }}
                transition={easeOutSlow}
                className="absolute top-0 right-0 bottom-0 w-44 border-l border-gray-200 bg-white shadow-xl overflow-y-auto"
              >
                <div className="p-3 space-y-3">
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
                    Edit — 3 listings
                  </p>

                  <div className="space-y-2">
                    <div className="rounded-lg border border-gray-200 bg-gray-50 p-2.5">
                      <p className="text-[10px] text-gray-400 font-medium mb-1">Title — Append</p>
                      <p className="text-[11px] text-gray-800 font-semibold leading-snug">
                        &ldquo;— 2026 gift-ready&rdquo;
                      </p>
                    </div>

                    <div className="rounded-lg border border-gray-200 bg-gray-50 p-2.5">
                      <p className="text-[10px] text-gray-400 font-medium mb-1">Tags — Add</p>
                      <span className="inline-block text-[10px] bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded font-medium">
                        holiday gift
                      </span>
                    </div>

                    <div className="rounded-lg border border-gray-200 bg-gray-50 p-2.5">
                      <p className="text-[10px] text-gray-400 font-medium mb-1">Price — Increase</p>
                      <p className="text-[11px] text-gray-800 font-semibold">+10%</p>
                    </div>
                  </div>

                  <AnimatePresence>
                    {showPreview && (
                      <motion.div
                        key="preview-ready"
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 6 }}
                        transition={easeOut}
                        className="rounded-lg border border-amber-200 bg-amber-50 p-2.5"
                      >
                        <p className="text-[10px] font-semibold text-amber-800">Preview ready</p>
                        <p className="text-[10px] text-amber-700 mt-0.5">9 changes across 3 listings</p>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <AnimatePresence>
                    {showSafety && (
                      <motion.button
                        key="apply-btn"
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 6 }}
                        transition={{ ...easeOut, delay: 0.1 }}
                        className="w-full text-[11px] bg-indigo-600 text-white font-semibold py-2 rounded-lg"
                      >
                        Apply safely
                      </motion.button>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Preview summary bar */}
        <AnimatePresence>
          {showPreview && (
            <motion.div
              key="preview-bar"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 6 }}
              transition={easeOut}
              className="border-t border-amber-200 bg-amber-50 px-4 py-2.5"
            >
              <div className="flex items-center justify-between mb-1.5">
                <p className="text-[10px] font-semibold text-amber-800 uppercase tracking-wide">
                  Preview — 9 changes
                </p>
                <span className="text-[10px] text-amber-700">3 listings</span>
              </div>
              <div className="space-y-1">
                {["Ceramic mug set", "Linen tote bag", "Printable wall art"].map((title) => (
                  <div key={title} className="flex items-baseline gap-1.5 text-[10px]">
                    <span className="text-gray-400 line-through truncate max-w-[90px]">{title}</span>
                    <span className="text-amber-500 flex-shrink-0">→</span>
                    <span className="text-gray-800 font-medium truncate">{title} — 2026 gift-ready</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Safety strip */}
        <AnimatePresence>
          {showSafety && (
            <motion.div
              key="safety-strip"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 6 }}
              transition={easeOut}
              className="border-t border-gray-200 bg-white px-4 py-3 flex items-center justify-between gap-3"
            >
              <div className="flex items-center gap-2 flex-wrap">
                <motion.span
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ ...easeOut, delay: 0.15 }}
                  className="text-[10px] bg-green-100 text-green-700 px-2 py-1 rounded-full font-semibold"
                >
                  Backup snapshot created
                </motion.span>
                <motion.span
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ ...easeOut, delay: 0.3 }}
                  className="text-[10px] bg-gray-100 text-gray-600 px-2 py-1 rounded-full font-medium"
                >
                  Magic Revert ready
                </motion.span>
              </div>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ ...easeOut, delay: 0.1 }}
                className="flex-shrink-0 text-[10px] text-gray-400"
              >
                Safe preview mode
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
