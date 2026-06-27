"use client";

import Link from "next/link";

type Step = {
  label: string;
  description: string;
  href: string;
  done: boolean;
};

type Props = {
  shopCount: number;
  listingCount: number;
};

export default function OnboardingChecklist({ shopCount, listingCount }: Props) {
  const steps: Step[] = [
    {
      label: "Connect your Etsy shop",
      description: "Link your Etsy account to start managing listings.",
      href: "/shops",
      done: shopCount > 0,
    },
    {
      label: "Sync your listings",
      description: "Pull your listings into Bulk Edit.",
      href: "/listings",
      done: listingCount > 0,
    },
    {
      label: "Try bulk edit",
      description: "Edit titles, tags, or prices across many listings at once.",
      href: "/bulk-edit",
      done: false,
    },
    {
      label: "Explore paid features",
      description: "Unlock AI optimization, CSV import, and dynamic pricing.",
      href: "/pricing",
      done: false,
    },
  ];

  const completedCount = steps.filter((s) => s.done).length;

  if (completedCount === steps.length) return null;

  const progressPct = Math.round((completedCount / steps.length) * 100);

  return (
    <div className="be-card mb-8 p-6" data-testid="onboarding-checklist">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-base text-gray-900 dark:text-gray-100">
          Get started
        </h2>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {completedCount} / {steps.length} complete
        </span>
      </div>

      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mb-5">
        <div
          className="bg-indigo-600 h-1.5 rounded-full transition-all"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      <ul className="space-y-3">
        {steps.map((step) => (
          <li key={step.label}>
            {step.done ? (
              <div className="flex items-start gap-3 opacity-60 cursor-default">
                <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 12 12">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 line-through">{step.label}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">{step.description}</p>
                </div>
              </div>
            ) : (
              <Link href={step.href} className="flex items-start gap-3 group">
                <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full border-2 border-indigo-400 group-hover:border-indigo-600 transition-colors" />
                <div>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 group-hover:text-indigo-600 transition-colors">
                    {step.label}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{step.description}</p>
                </div>
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
