"use client";

import React from "react";
import { Boxes, Plus, RefreshCw, Search, Sun, Moon, Laptop } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface HeaderProps {
  activeTab: string;
  onRefresh: () => void;
  onLoadSamples: () => void;
  onAddOpen: () => void;
  onOpenSearch: () => void;
  theme: "light" | "dark" | "system";
  onThemeChange: (theme: "light" | "dark" | "system") => void;
}

export function Header({
  activeTab,
  onRefresh,
  onLoadSamples,
  onAddOpen,
  onOpenSearch,
  theme,
  onThemeChange,
}: HeaderProps) {
  const getTabTitle = (tab: string) => {
    switch (tab) {
      case "overview":
        return "Flight Control Overview";
      case "applications":
        return "Registered Applications";
      case "logs":
        return "Process Stream Logs";
      case "activity":
        return "System Activity Log";
      case "settings":
        return "Control Panel Settings";
      default:
        return "Dashboard";
    }
  };

  return (
    <header className="flex flex-col gap-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[var(--shadow-sm)] md:flex-row md:items-center md:justify-between">
      {/* Title & Breadcrumbs */}
      <div>
        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[var(--accent)] font-semibold font-mono">
          <span>MACHINE ROOM</span>
          <span className="text-[var(--text-muted)]">/</span>
          <span className="capitalize text-[var(--text-muted)]">{activeTab}</span>
        </div>
        <h1 className="mt-1 text-2xl md:text-3xl font-black tracking-[-0.03em] text-[var(--text)] font-display">
          {getTabTitle(activeTab)}
        </h1>
      </div>

      {/* Action Toolbar */}
      <div className="flex flex-wrap items-center gap-2.5">
        {/* Quick Search / Command Palette Trigger */}
        <button
          type="button"
          onClick={onOpenSearch}
          className="flex items-center gap-2.5 rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text)] hover:border-[var(--accent)] transition-all min-h-[38px]"
          title="Search projects and actions (Ctrl+K)"
          aria-label="Search and command palette"
        >
          <Search className="h-3.5 w-3.5 text-[var(--accent)]" />
          <span className="hidden sm:inline">Search...</span>
          <kbd className="rounded border border-[var(--border)] bg-[var(--surface)] px-1.5 py-0.5 text-[10px] font-mono text-[var(--text-muted)]">
            Ctrl+K
          </kbd>
        </button>

        {/* Refresh */}
        <Button
          variant="secondary"
          size="sm"
          icon={<RefreshCw className="h-3.5 w-3.5" />}
          onClick={onRefresh}
          title="Refresh dashboard state"
        >
          <span className="hidden lg:inline">Refresh</span>
        </Button>

        {/* Load Samples */}
        <Button
          variant="secondary"
          size="sm"
          icon={<Boxes className="h-3.5 w-3.5" />}
          onClick={onLoadSamples}
          title="Load built-in demo applications"
        >
          <span className="hidden sm:inline">Load samples</span>
        </Button>

        {/* Add Application Primary */}
        <Button
          variant="primary"
          size="sm"
          icon={<Plus className="h-4 w-4" />}
          onClick={onAddOpen}
        >
          Add application
        </Button>

        {/* Theme Toggle Group */}
        <div className="flex items-center rounded-xl border border-[var(--border)] bg-[var(--surface-2)] p-1 ml-1">
          <button
            type="button"
            onClick={() => onThemeChange("light")}
            className={`p-1.5 rounded-lg transition-colors ${
              theme === "light"
                ? "bg-[var(--surface)] text-[var(--text)] shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text)]"
            }`}
            title="Light theme"
            aria-label="Switch to light theme"
          >
            <Sun className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={() => onThemeChange("dark")}
            className={`p-1.5 rounded-lg transition-colors ${
              theme === "dark"
                ? "bg-[var(--surface)] text-[var(--text)] shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text)]"
            }`}
            title="Dark theme"
            aria-label="Switch to dark theme"
          >
            <Moon className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={() => onThemeChange("system")}
            className={`p-1.5 rounded-lg transition-colors ${
              theme === "system"
                ? "bg-[var(--surface)] text-[var(--text)] shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text)]"
            }`}
            title="Follow system theme"
            aria-label="Follow system theme"
          >
            <Laptop className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
}

