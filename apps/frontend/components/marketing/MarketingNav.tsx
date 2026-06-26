"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/features", label: "Features" },
  { href: "/faq", label: "FAQ" },
  { href: "/contact-us", label: "Contact" },
  { href: "/pricing", label: "Pricing" },
];

export default function MarketingNav() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-gray-100 shadow-sm">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 py-4 flex items-center justify-between">
        <Link
          href="/"
          className="text-xl font-extrabold tracking-tight text-gray-900 hover:text-indigo-600 transition-colors"
        >
          Bulk-Edit
        </Link>

        <div className="hidden sm:flex items-center gap-0.5">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`text-sm font-medium px-3.5 py-2 rounded-lg transition-colors ${
                pathname === href
                  ? "bg-indigo-50 text-indigo-700"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
              }`}
            >
              {label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="hidden sm:block text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            Sign in
          </Link>
          <Link href="/register" className="be-btn-primary">
            Get started
          </Link>
        </div>
      </div>
    </nav>
  );
}
