"use client";

import React, { useEffect, useState } from "react";
import { Sun, Moon, Laptop } from "lucide-react";
import { Theme, applyTheme, getStoredTheme } from "@/lib/theme";

export const ThemeSwitch: React.FC = () => {
  const [theme, setTheme] = useState<Theme>("system");

  useEffect(() => {
    setTheme(getStoredTheme());
    const handler = (e: any) => setTheme(e.detail);
    window.addEventListener("hangar-theme-change", handler);
    return () => window.removeEventListener("hangar-theme-change", handler);
  }, []);

  const cycleTheme = () => {
    let next: Theme = "dark";
    if (theme === "dark") next = "light";
    else if (theme === "light") next = "system";
    else next = "dark";
    applyTheme(next);
  };

  return (
    <button
      onClick={cycleTheme}
      type="button"
      className="p-2 rounded-input border border-line bg-surface text-muted hover:text-text hover:bg-surface-2 transition-colors min-w-[44px] min-h-[44px] inline-flex items-center justify-center"
      aria-label={`Switch theme, current: ${theme}`}
      title={`Theme: ${theme.toUpperCase()} (Click to change)`}
    >
      {theme === "dark" && <Moon className="w-4 h-4 text-start" />}
      {theme === "light" && <Sun className="w-4 h-4 text-warn" />}
      {theme === "system" && <Laptop className="w-4 h-4 text-muted" />}
    </button>
  );
};

