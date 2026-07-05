"use client";

import Link from "next/link";
import FadeUp from "./FadeUp";

export default function ConversionCTA({
  eyebrow,
  title,
  subtitle,
  primaryLabel = "Try Bulk Edit App",
  primaryHref = "/register",
  secondaryLabel,
  secondaryHref,
  variant = "accent",
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  primaryLabel?: string;
  primaryHref?: string;
  secondaryLabel?: string;
  secondaryHref?: string;
  variant?: "accent" | "hero" | "white";
}) {
  const bg =
    variant === "hero" ? "be-hero-bg" : variant === "white" ? "bg-white border-t border-gray-100" : "be-section-accent";

  return (
    <section className={`py-20 px-6 sm:px-8 ${bg}`}>
      <FadeUp>
        <div className="max-w-2xl mx-auto text-center">
          {eyebrow && (
            <span className="inline-block text-xs font-semibold text-indigo-600 tracking-widest uppercase mb-4 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
              {eyebrow}
            </span>
          )}
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">{title}</h2>
          {subtitle && <p className="text-gray-500 mb-8 leading-relaxed">{subtitle}</p>}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href={primaryHref} className="be-btn-primary px-8 py-3 text-base">
              {primaryLabel}
            </Link>
            {secondaryLabel && secondaryHref && (
              <Link href={secondaryHref} className="be-btn-secondary px-8 py-3 text-base">
                {secondaryLabel}
              </Link>
            )}
          </div>
        </div>
      </FadeUp>
    </section>
  );
}
