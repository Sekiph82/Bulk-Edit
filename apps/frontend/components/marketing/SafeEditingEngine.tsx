"use client";

import { motion, useReducedMotion } from "motion/react";
import FadeUp from "./FadeUp";

const STEPS = [
  { icon: "🔗", title: "Connect", desc: "Sign in to your Etsy shop with official OAuth2 — we never see your password." },
  { icon: "🔄", title: "Sync", desc: "Bulk Edit App pulls your listings so every edit works from current data." },
  { icon: "✏️", title: "Edit", desc: "Define a bulk change once — title, tags, price, photos, or variations." },
  { icon: "👁️", title: "Preview", desc: "See a full before/after diff for every affected listing." },
  { icon: "✅", title: "Apply", desc: "Confirm to write to Etsy — a backup snapshot is taken first." },
  { icon: "⏪", title: "Revert", desc: "Not right? Magic Revert restores the exact prior state, instantly." },
];

// Replaces the old flat "pill" workflow strip with a connected, animated
// timeline — same six-step concept, presented as a real visual system.
export default function SafeEditingEngine() {
  const reduced = useReducedMotion();

  return (
    <section className="py-20 px-6 sm:px-8 bg-white">
      <div className="max-w-6xl mx-auto">
        <FadeUp className="text-center mb-14">
          <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
            The safe editing engine
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">
            One engine powers every bulk edit
          </h2>
          <p className="text-gray-500 max-w-xl mx-auto">
            Connect, sync, edit, preview, apply, revert — the same six-step safety flow behind
            every feature in Bulk Edit App.
          </p>
        </FadeUp>

        <div className="relative">
          {/* Connecting line */}
          <div className="hidden lg:block absolute top-8 left-0 right-0 h-0.5 bg-gray-100" aria-hidden="true">
            <motion.div
              className="h-full bg-gradient-to-r from-indigo-400 via-purple-500 to-green-500"
              initial={reduced ? { width: "100%" } : { width: "0%" }}
              whileInView={{ width: "100%" }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 1.4, ease: "easeInOut" }}
            />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-6 lg:gap-4 relative">
            {STEPS.map((step, i) => (
              <motion.div
                key={step.title}
                className="flex flex-col items-center text-center"
                initial={reduced ? false : { opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
              >
                <div className="w-16 h-16 rounded-2xl bg-white border-2 border-indigo-100 shadow-sm flex items-center justify-center text-2xl mb-3 relative z-10">
                  <span role="img" aria-label={step.title}>{step.icon}</span>
                </div>
                <h3 className="text-sm font-semibold text-gray-900 mb-1">{step.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed max-w-[140px]">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
