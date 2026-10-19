"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  Activity,
  Boxes,
  LayoutDashboard,
  Play,
  RotateCw,
  ScrollText,
  Search,
  Settings,
  Square,
  X,
} from "lucide-react";
import { Application } from "@/lib/types";

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  applications: Application[];
  onNavigateTab: (tab: any) => void;
  onStartAll: () => void;
  onStopAll: () => void;
}

export function CommandPalette({
  open,
  onClose,
  applications,
  onNavigateTab,
  onStartAll,
  onStopAll,
}: CommandPaletteProps) {
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        if (open) onClose();
        else setQuery("");
      }
      if (e.key === "Escape" && open) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  const navCommands = useMemo(
    () => [
      { id: "overview", label: "Jump to Overview", icon: LayoutDashboard, category: "Navigation" },
      { id: "applications", label: "Jump to Applications", icon: Boxes, category: "Navigation" },
      { id: "logs", label: "Jump to Logs", icon: ScrollText, category: "Navigation" },
      { id: "activity", label: "Jump to Activity", icon: Activity, category: "Navigation" },
      { id: "settings", label: "Jump to Settings", icon: Settings, category: "Navigation" },
    ],
    []
  );

  const filteredCommands = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return navCommands;
    return navCommands.filter((c) => c.label.toLowerCase().includes(q));
  }, [query, navCommands]);

  const filteredApps = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return applications;
    return applications.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        a.components.some((c) => c.name.toLowerCase().includes(q)) ||
        a.tags.some((t) => t.toLowerCase().includes(q))
    );
  }, [query, applications]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="w-full max-w-xl rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-lg)] overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Command search palette"
      >
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border)] bg-[var(--surface-2)]">
          <Search className="h-4 w-4 text-[var(--accent)] shrink-0" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search applications..."
            className="w-full bg-transparent text-sm text-[var(--text)] outline-none placeholder:text-[var(--text-muted)] font-medium"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="text-[var(--text-muted)] hover:text-[var(--text)]"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
          <kbd className="rounded border border-[var(--border)] bg-[var(--surface)] px-1.5 py-0.5 text-[10px] font-mono text-[var(--text-muted)] shrink-0">
            Esc
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-[380px] overflow-y-auto p-2 space-y-3">
          {/* Quick Actions */}
          <div>
            <div className="px-2 py-1 text-[10px] font-mono font-bold uppercase tracking-wider text-[var(--accent)]">
              Quick Actions
            </div>
            <div className="space-y-0.5 mt-1">
              <button
                type="button"
                onClick={() => {
                  onStartAll();
                  onClose();
                }}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left text-xs font-medium text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
              >
                <Play className="h-3.5 w-3.5 text-[var(--status-running)]" />
                <span>Start all applications</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  onStopAll();
                  onClose();
                }}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left text-xs font-medium text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
              >
                <Square className="h-3.5 w-3.5 text-[var(--status-stopped)]" />
                <span>Stop all applications</span>
              </button>
            </div>
          </div>

          {/* Navigation */}
          {filteredCommands.length > 0 && (
            <div>
              <div className="px-2 py-1 text-[10px] font-mono font-bold uppercase tracking-wider text-[var(--accent)]">
                Navigation
              </div>
              <div className="space-y-0.5 mt-1">
                {filteredCommands.map((cmd) => {
                  const Icon = cmd.icon;
                  return (
                    <button
                      key={cmd.id}
                      type="button"
                      onClick={() => {
                        onNavigateTab(cmd.id);
                        onClose();
                      }}
                      className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left text-xs font-medium text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
                    >
                      <Icon className="h-3.5 w-3.5 text-[var(--accent)]" />
                      <span>{cmd.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Applications */}
          {filteredApps.length > 0 && (
            <div>
              <div className="px-2 py-1 text-[10px] font-mono font-bold uppercase tracking-wider text-[var(--accent)]">
                Projects ({filteredApps.length})
              </div>
              <div className="space-y-0.5 mt-1">
                {filteredApps.map((app) => (
                  <button
                    key={app.id}
                    type="button"
                    onClick={() => {
                      onNavigateTab("applications");
                      onClose();
                    }}
                    className="w-full flex items-center justify-between px-2.5 py-2 rounded-xl text-left text-xs font-medium text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Boxes className="h-3.5 w-3.5 text-[var(--accent)]" />
                      <span className="font-semibold">{app.name}</span>
                      <span className="text-[10px] text-[var(--text-muted)] font-mono">
                        {app.components.length} service(s)
                      </span>
                    </div>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded border border-[var(--border)] text-[var(--text-muted)]">
                      {app.status}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {filteredCommands.length === 0 && filteredApps.length === 0 && (
            <div className="p-6 text-center text-xs text-[var(--text-muted)]">
              No matching commands or projects found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

