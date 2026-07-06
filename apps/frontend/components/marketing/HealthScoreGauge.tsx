"use client";

import { motion, useReducedMotion } from "motion/react";

// Decorative SVG gauge — illustrates the real Listing Health Score feature
// (0-100 rule-based score). Not a live data widget on marketing pages.
export default function HealthScoreGauge({
  score,
  label,
  size = 120,
}: {
  score: number;
  label: string;
  size?: number;
}) {
  const reduced = useReducedMotion();
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  const color = score >= 80 ? "#16a34a" : score >= 50 ? "#d97706" : "#dc2626";

  return (
    <div className="flex flex-col items-center gap-2" role="img" aria-label={`${label}: ${score} out of 100`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#e5e7eb" strokeWidth={10} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={circumference}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          initial={reduced ? { strokeDashoffset: offset } : { strokeDashoffset: circumference }}
          whileInView={{ strokeDashoffset: offset }}
          viewport={{ once: true }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
        <text x="50%" y="52%" textAnchor="middle" fontSize={size * 0.24} fontWeight={800} fill="#111827">
          {score}
        </text>
      </svg>
      <p className="text-xs text-gray-500 text-center max-w-[140px]">{label}</p>
    </div>
  );
}
