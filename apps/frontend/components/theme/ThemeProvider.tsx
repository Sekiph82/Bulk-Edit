"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

export type ThemePref = "system" | "light" | "dark";
export type ResolvedTheme = "light" | "dark";

interface ThemeCtx {
  pref: ThemePref;
  resolved: ResolvedTheme;
  setPref: (p: ThemePref) => void;
}

const ThemeContext = createContext<ThemeCtx>({
  pref: "system",
  resolved: "light",
  setPref: () => {},
});

export function useTheme() {
  return useContext(ThemeContext);
}

function resolveTheme(pref: ThemePref): ResolvedTheme {
  if (pref === "dark") return "dark";
  if (pref === "light") return "light";
  if (typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

function applyTheme(theme: ResolvedTheme) {
  document.documentElement.setAttribute("data-theme", theme);
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [pref, setPrefState] = useState<ThemePref>("system");
  const [resolved, setResolved] = useState<ResolvedTheme>("light");

  useEffect(() => {
    const stored = (localStorage.getItem("bulk-edit-theme") as ThemePref) || "system";
    const r = resolveTheme(stored);
    setPrefState(stored);
    setResolved(r);
    applyTheme(r);

    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const curr = (localStorage.getItem("bulk-edit-theme") as ThemePref) || "system";
      if (curr === "system") {
        const nr = resolveTheme("system");
        setResolved(nr);
        applyTheme(nr);
      }
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const setPref = useCallback((p: ThemePref) => {
    localStorage.setItem("bulk-edit-theme", p);
    const r = resolveTheme(p);
    setPrefState(p);
    setResolved(r);
    applyTheme(r);
  }, []);

  return (
    <ThemeContext.Provider value={{ pref, resolved, setPref }}>
      {children}
    </ThemeContext.Provider>
  );
}
