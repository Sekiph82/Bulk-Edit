"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import ThemeToggle from "@/components/theme/ThemeToggle";
import { useTheme } from "@/components/theme/ThemeProvider";

const NAV_BASE = [
  {
    section: "Workspace",
    items: [
      { href: "/dashboard",      label: "Dashboard",      icon: <GridIcon /> },
      { href: "/listings",       label: "Listings",        icon: <ListIcon /> },
      { href: "/bulk-edit",      label: "Bulk Edit",       icon: <PencilIcon /> },
      { href: "/media",          label: "Media",           icon: <ImageIcon /> },
      { href: "/variations",     label: "Variations",      icon: <LayersIcon /> },
    ],
  },
  {
    section: "Tools",
    items: [
      { href: "/ai",             label: "AI Tools",        icon: <SparkleIcon /> },
      { href: "/csv",            label: "CSV Import/Export",icon: <TableIcon /> },
      { href: "/pricing-rules",  label: "Dynamic Pricing", icon: <ChartIcon /> },
    ],
  },
  {
    section: "System",
    items: [
      { href: "/scheduled",      label: "Scheduled Jobs",  icon: <ClockIcon /> },
      { href: "/billing",        label: "Billing",         icon: <CardIcon /> },
    ],
  },
];

const ADMIN_NAV_ITEM = { href: "/admin", label: "Admin", icon: <ShieldIcon /> };

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

interface AppShellProps { children: React.ReactNode; }

export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { resolved } = useTheme();
  const isDark = resolved === "dark";

  const [email, setEmail] = useState<string | null>(null);
  const [isSuperuser, setIsSuperuser] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : null)
      .then((d) => {
        if (d?.user?.email) setEmail(d.user.email);
        if (d?.user?.is_superuser === true) setIsSuperuser(true);
      })
      .catch(() => {});
  }, []);

  const NAV = NAV_BASE.map((group) =>
    group.section === "System"
      ? {
          ...group,
          items: isSuperuser
            ? [...group.items, ADMIN_NAV_ITEM]
            : group.items,
        }
      : group
  );

  async function handleLogout() {
    const rt = localStorage.getItem("refresh_token");
    if (rt) {
      fetch(`${BACKEND_URL}/api/v1/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: rt }),
      }).catch(() => {});
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    router.push("/login");
  }

  const sidebarBg = isDark
    ? "bg-[#020c18] border-r border-blue-400/12"
    : "bg-white border-r border-gray-200";

  const topbarBg = isDark
    ? "bg-[#020c18]/90 border-b border-blue-400/12 backdrop-blur-md"
    : "bg-white border-b border-gray-200";

  const mainBg = isDark ? "bg-transparent" : "bg-gray-50";

  return (
    <div className={`flex h-screen overflow-hidden ${isDark ? "bg-[#020817]" : "bg-gray-50"}`}>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-30 w-60 flex flex-col
          transition-transform duration-200 ease-out
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
          lg:static lg:translate-x-0
          ${sidebarBg}
        `}
      >
        {/* Logo */}
        <div className={`h-14 flex items-center px-4 flex-shrink-0 border-b ${isDark ? "border-blue-400/12" : "border-gray-200"}`}>
          <Link
            href="/dashboard"
            className="flex items-center gap-2 group"
            onClick={() => setSidebarOpen(false)}
          >
            <span
              className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold text-white flex-shrink-0
                ${isDark
                  ? "bg-gradient-to-br from-blue-500 to-violet-600 shadow-[0_0_12px_rgba(59,130,246,0.55)]"
                  : "bg-gradient-to-br from-indigo-600 to-violet-600 shadow-md"}`}
            >
              BE
            </span>
            <span
              className={`text-sm font-semibold tracking-tight
                ${isDark
                  ? "text-slate-100 group-hover:text-white sidebar-text-glow"
                  : "text-gray-800 group-hover:text-indigo-600 transition-colors"}`}
            >
              Bulk‑Edit
            </span>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
          {NAV.map((group) => (
            <div key={group.section}>
              <p
                className={`px-2 mb-1 text-[10px] font-semibold uppercase tracking-widest
                  ${isDark ? "text-blue-400/50" : "text-gray-400"}`}
              >
                {group.section}
              </p>
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const active = pathname === item.href || pathname.startsWith(item.href + "/");
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={() => setSidebarOpen(false)}
                        className={`
                          flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm font-medium
                          transition-all duration-150
                          ${isDark
                            ? active
                              ? "bg-blue-500/15 text-white border-l-2 border-blue-400 shadow-[inset_2px_0_8px_rgba(59,130,246,0.20)] pl-[9px] sidebar-text-glow active"
                              : "text-slate-400 hover:text-white hover:bg-white/6 sidebar-text-glow border-l-2 border-transparent pl-[9px]"
                            : active
                              ? "bg-indigo-50 text-indigo-700 border-l-2 border-indigo-500 pl-[9px]"
                              : "text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-l-2 border-transparent pl-[9px]"}
                        `}
                        aria-current={active ? "page" : undefined}
                      >
                        <span className={`flex-shrink-0 w-4 h-4 ${isDark && active ? "text-blue-300" : ""}`}>
                          {item.icon}
                        </span>
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Bottom: user */}
        <div className={`p-3 border-t flex-shrink-0 ${isDark ? "border-blue-400/12" : "border-gray-200"}`}>
          {email && (
            <div className={`flex items-center gap-2 px-2 py-1.5 rounded-lg mb-2 ${isDark ? "bg-white/4" : "bg-gray-50"}`}>
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0
                  ${isDark
                    ? "bg-gradient-to-br from-blue-500 to-violet-600 shadow-[0_0_8px_rgba(59,130,246,0.40)]"
                    : "bg-gradient-to-br from-indigo-500 to-violet-500"}`}
              >
                {email[0].toUpperCase()}
              </div>
              <span className={`text-xs truncate ${isDark ? "text-slate-300" : "text-gray-700"}`}>
                {email}
              </span>
            </div>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className={`w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-sm transition-all duration-150
              ${isDark
                ? "text-slate-500 hover:text-red-400 hover:bg-red-500/8"
                : "text-gray-500 hover:text-red-600 hover:bg-red-50"}`}
          >
            <LogoutIcon />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className={`h-14 flex items-center justify-between px-4 gap-3 flex-shrink-0 ${topbarBg}`}>
          {/* Mobile hamburger */}
          <button
            type="button"
            className={`lg:hidden p-1.5 rounded-lg transition-colors
              ${isDark
                ? "text-slate-400 hover:text-white hover:bg-white/8"
                : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"}`}
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
          >
            <HamburgerIcon />
          </button>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Right actions */}
          <div className="flex items-center gap-1.5">
            <ThemeToggle />
          </div>
        </header>

        {/* Page content — pages own their <main> landmark */}
        <div className={`flex-1 overflow-y-auto ${mainBg}`}>
          {children}
        </div>
      </div>
    </div>
  );
}

/* ── Icons ────────────────────────────────────────────────────────────────── */
function GridIcon()     { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>; }
function ListIcon()     { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" /></svg>; }
function PencilIcon()   { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>; }
function ImageIcon()    { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" /></svg>; }
function LayersIcon()   { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" /></svg>; }
function SparkleIcon()  { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" /></svg>; }
function TableIcon()    { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path fillRule="evenodd" d="M5 4a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3V7a3 3 0 00-3-3H5zm-1 9v-1h5v2H5a1 1 0 01-1-1zm7 1h4a1 1 0 001-1v-1h-5v2zm0-4h5V8h-5v2zM9 8H4v2h5V8z" clipRule="evenodd" /></svg>; }
function ChartIcon()    { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" /></svg>; }
function ClockIcon()    { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" /></svg>; }
function CardIcon()     { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" /><path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" /></svg>; }
function ShieldIcon()   { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>; }
function LogoutIcon()   { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd" /></svg>; }
function HamburgerIcon(){ return <svg viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5"><path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" /></svg>; }
