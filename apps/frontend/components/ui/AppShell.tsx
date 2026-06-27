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
      { href: "/shops",          label: "Shops",           icon: <ShopIcon /> },
      { href: "/listings",       label: "Listings",        icon: <ListIcon /> },
      { href: "/listing-health", label: "Listing Health",  icon: <HeartIcon /> },
      { href: "/profit",         label: "Profit",          icon: <DollarIcon /> },
      { href: "/insights",       label: "Insights",        icon: <InsightsIcon /> },
      { href: "/bulk-edit",      label: "Bulk Edit",       icon: <PencilIcon /> },
      { href: "/bulk-create",    label: "Bulk Create",     icon: <CreateIcon /> },
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
      { href: "/promote",        label: "Promote",         icon: <PromoteIcon /> },
      { href: "/video-generator",label: "Video Generator", icon: <VideoIcon /> },
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
                        data-testid={item.href === "/admin" ? "admin-nav-link" : undefined}
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
            <SoundToggle isDark={isDark} />
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
function HeartIcon()    { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" /></svg>; }
function ShopIcon()     { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" /></svg>; }
function DollarIcon()   { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" /><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" /></svg>; }
function InsightsIcon() { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" /></svg>; }
function PromoteIcon()  { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" /></svg>; }
function VideoIcon()    { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" /></svg>; }
function CreateIcon()   { return <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" /></svg>; }

/* ── Sound Toggle ────────────────────────────────────────────────────────── */
function SoundToggle({ isDark }: { isDark: boolean }) {
  const [enabled, setEnabled] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setEnabled(localStorage.getItem("bulk-edit-sound-enabled") === "true");
  }, []);

  function toggle() {
    const next = !enabled;
    setEnabled(next);
    localStorage.setItem("bulk-edit-sound-enabled", String(next));
    if (next) {
      try {
        const a = new Audio("/sounds/cha-ching.mp3");
        a.play().catch(() => {});
      } catch {}
    }
  }

  if (!mounted) return null;

  return (
    <button
      onClick={toggle}
      title={enabled ? "Success chime on (click to mute)" : "Success chime off (click to enable)"}
      aria-pressed={enabled}
      className={`p-1.5 rounded-lg transition-colors ${
        isDark
          ? enabled ? "text-blue-300 hover:bg-white/8" : "text-slate-500 hover:bg-white/6"
          : enabled ? "text-indigo-600 hover:bg-indigo-50" : "text-gray-400 hover:bg-gray-100"
      }`}
    >
      {enabled ? (
        <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
          <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
        </svg>
      ) : (
        <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
          <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM12.293 7.293a1 1 0 011.414 0L15 8.586l1.293-1.293a1 1 0 111.414 1.414L16.414 10l1.293 1.293a1 1 0 01-1.414 1.414L15 11.414l-1.293 1.293a1 1 0 01-1.414-1.414L13.586 10l-1.293-1.293a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      )}
    </button>
  );
}
