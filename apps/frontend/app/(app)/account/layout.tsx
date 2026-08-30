"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ACCOUNT_NAV = [
  { href: "/account", label: "Overview" },
  { href: "/account/profile", label: "Profile" },
  { href: "/account/billing", label: "Plan & Billing" },
  { href: "/account/usage", label: "Usage" },
  { href: "/account/credits", label: "Credits" },
  { href: "/account/connected-shops", label: "Connected Shops" },
  { href: "/account/team", label: "Team / Users" },
  { href: "/account/security", label: "Security" },
  { href: "/account/notifications", label: "Notifications" },
  { href: "/account/activity", label: "Activity & Audit" },
  { href: "/account/data-privacy", label: "Data & Privacy" },
  { href: "/account/support", label: "Support" },
];

export default function AccountLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <main className="max-w-5xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Account</h1>
      <div className="flex flex-col md:flex-row gap-6">
        <nav className="md:w-52 shrink-0">
          <ul className="flex md:flex-col gap-1 overflow-x-auto md:overflow-visible pb-2 md:pb-0">
            {ACCOUNT_NAV.map((item) => {
              const active = pathname === item.href;
              return (
                <li key={item.href} className="shrink-0">
                  <Link
                    href={item.href}
                    className={`block px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                      active
                        ? "bg-indigo-50 text-indigo-700"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    }`}
                    aria-current={active ? "page" : undefined}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="flex-1 min-w-0">{children}</div>
      </div>
    </main>
  );
}
