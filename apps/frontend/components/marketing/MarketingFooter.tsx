import Link from "next/link";

const FOOTER_LINKS = {
  Product: [
    { href: "/features", label: "Features" },
    { href: "/pricing", label: "Pricing" },
    { href: "/tools", label: "Free Tools" },
    { href: "/compare", label: "Compare" },
  ],
  Support: [
    { href: "/contact-us", label: "Contact Us" },
    { href: "/faq", label: "Help Center" },
    { href: "/faq", label: "FAQ" },
    { href: "/blog", label: "Blog" },
  ],
  Account: [
    { href: "/login", label: "Sign In" },
    { href: "/register", label: "Get Started" },
  ],
  Legal: [
    { href: "/privacy", label: "Privacy" },
    { href: "/terms", label: "Terms" },
  ],
};

// Dashboard/Admin are intentionally never linked here — they are private,
// authenticated-only app routes, not public marketing pages.

export default function MarketingFooter() {
  return (
    <footer className="border-t border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 py-14">
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-8 mb-10">
          {/* Brand column */}
          <div className="col-span-2 sm:col-span-1">
            <Link
              href="/"
              className="text-lg font-extrabold text-gray-900 hover:text-indigo-600 transition-colors"
            >
              Bulk Edit App
            </Link>
            <p className="mt-3 text-sm text-gray-500 leading-relaxed max-w-xs">
              Bulk editing for Etsy sellers. Preview every change. Apply safely. Revert when needed.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(FOOTER_LINKS).map(([section, links]) => (
            <div key={section}>
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                {section}
              </h4>
              <ul className="space-y-2">
                {links.map(({ href, label }) => (
                  <li key={label}>
                    <Link
                      href={href}
                      className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
                    >
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Legal */}
        <div className="border-t border-gray-100 pt-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-gray-400">© 2026 Bulk Edit App LLC. All rights reserved.</p>
          <p className="text-xs text-gray-400 text-center sm:text-right max-w-md">
            The term &ldquo;Etsy&rdquo; is a trademark of Etsy, Inc. This application uses the Etsy
            API but is not endorsed or certified by Etsy, Inc.
          </p>
        </div>
      </div>
    </footer>
  );
}
