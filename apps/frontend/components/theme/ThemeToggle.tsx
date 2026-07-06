"use client";

import { useState, useRef, useEffect } from "react";
import { useTheme, type ThemePref } from "./ThemeProvider";

const OPTIONS: { value: ThemePref; label: string; desc: string; icon: string }[] = [
  { value: "system", label: "System preference", desc: "Follows your device setting automatically.", icon: "💻" },
  { value: "light",  label: "Light mode",        desc: "Always use the light Bulk Edit App theme.",    icon: "☀️" },
  { value: "dark",   label: "Dark mode",          desc: "Always use the dark Bulk Edit App theme.",     icon: "🌙" },
];

function ThemeIcon({ resolved, pref }: { resolved: "light" | "dark"; pref: ThemePref }) {
  if (pref === "system") {
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    );
  }
  if (resolved === "dark") {
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
      </svg>
    );
  }
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  );
}

export default function ThemeToggle({ className = "" }: { className?: string }) {
  const { pref, resolved, setPref } = useTheme();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Escape") setOpen(false);
  }

  const isDark = resolved === "dark";
  const buttonBase = isDark
    ? "h-8 w-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-blue-300 hover:bg-white/10 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
    : "h-8 w-8 rounded-lg flex items-center justify-center text-gray-500 hover:text-indigo-600 hover:bg-gray-100 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400";

  const dropdownBase = isDark
    ? "absolute right-0 top-full mt-2 w-64 rounded-xl border border-blue-400/20 bg-[#071426]/95 backdrop-blur-xl shadow-[0_0_40px_rgba(59,130,246,0.20)] z-50 overflow-hidden"
    : "absolute right-0 top-full mt-2 w-64 rounded-xl border border-gray-200 bg-white shadow-lg z-50 overflow-hidden";

  return (
    <div ref={ref} className={`relative ${className}`} onKeyDown={handleKey}>
      <button
        type="button"
        className={buttonBase}
        aria-label={`Theme: ${pref} (${resolved})`}
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => setOpen((o) => !o)}
      >
        <ThemeIcon resolved={resolved} pref={pref} />
      </button>

      {open && (
        <div className={dropdownBase} role="listbox" aria-label="Select theme">
          <div className={`px-3 pt-3 pb-2 ${isDark ? "border-b border-blue-400/15" : "border-b border-gray-100"}`}>
            <p className={`text-[11px] font-semibold uppercase tracking-widest ${isDark ? "text-blue-400/70" : "text-gray-400"}`}>
              Appearance
            </p>
          </div>

          {OPTIONS.map((opt) => {
            const active = pref === opt.value;
            const itemBase = isDark
              ? `flex items-start gap-3 px-3 py-2.5 cursor-pointer transition-colors ${active ? "bg-blue-500/15" : "hover:bg-white/5"}`
              : `flex items-start gap-3 px-3 py-2.5 cursor-pointer transition-colors ${active ? "bg-indigo-50" : "hover:bg-gray-50"}`;

            return (
              <button
                key={opt.value}
                type="button"
                role="option"
                aria-selected={active}
                className={`${itemBase} w-full text-left`}
                onClick={() => { setPref(opt.value); setOpen(false); }}
              >
                <span className="text-base mt-0.5 flex-shrink-0">{opt.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className={`flex items-center gap-2`}>
                    <span className={`text-sm font-medium ${isDark ? (active ? "text-blue-300" : "text-slate-200") : (active ? "text-indigo-700" : "text-gray-800")}`}>
                      {opt.label}
                    </span>
                    {active && (
                      <svg className={`w-3.5 h-3.5 flex-shrink-0 ${isDark ? "text-blue-400" : "text-indigo-500"}`} fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <p className={`text-xs mt-0.5 leading-snug ${isDark ? "text-slate-400" : "text-gray-500"}`}>
                    {opt.desc}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
