"use client";

import { motion, useReducedMotion } from "motion/react";

const TAGS = [
  "handmade gift", "boho decor", "personalized", "eco friendly", "minimalist",
  "wedding favor", "digital download", "vintage style", "custom name", "small batch",
];

// Decorative animated tag chips illustrating bulk tag/SEO editing. Purely
// visual — not a live listing widget.
export default function AnimatedTagCloud() {
  const reduced = useReducedMotion();

  return (
    <div className="flex flex-wrap gap-2 justify-center max-w-lg mx-auto" role="img" aria-label="Example Etsy listing tags">
      {TAGS.map((tag, i) => (
        <motion.span
          key={tag}
          className="text-xs font-medium px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100"
          initial={reduced ? false : { opacity: 0, y: 8, scale: 0.9 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.3, delay: i * 0.05 }}
        >
          {tag}
        </motion.span>
      ))}
    </div>
  );
}
