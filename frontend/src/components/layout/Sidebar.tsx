"use client";

import React from "react";
import {
  Activity,
  Boxes,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  ScrollText,
  Settings,
} from "lucide-react";
import { Logo } from "@/components/brand/Logo";

export const navItems = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "applications", label: "Applications", icon: Boxes },
  { id: "logs", label: "Logs", icon: ScrollText },
  { id: "activity", label: "Activity", icon: Activity },
  { id: "settings", label: "Settings", icon: Settings },
] as const;

export type TabId = (typeof navItems)[number]["id"];

interface SidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  wsConnected: boolean;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function Sidebar({
  activeTab,
  onTabChange,
  wsConnected,
  collapsed = false,
  onToggleCollapse,
}: SidebarProps) {
  return (
    <aside
      className={`hidden md:flex flex-col shrink-0 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-3 transition-all duration-200 ${
        collapsed ? "w-[76px]" : "w-[220px]"
      }`}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between pb-4 mb-2 border-b border-[var(--border)] px-1">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--surface-2)] text-[var(--accent)] shadow-[var(--shadow-sm)]">
            <Logo variant="mark" size={26} />
          </div>
          {!collapsed && (
            <div className="flex flex-col min-w-0">
              <span className="font-display font-black text-sm tracking-wide text-[var(--text)] truncate">
                HANGAR
              </span>
              <span className="text-[10px] uppercase tracking-wider text-[var(--accent)] font-mono font-semibold truncate">
                Control Room
              </span>
            </div>
          )}
        </div>

        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="hidden lg:flex h-7 w-7 items-center justify-center rounded-lg text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1.5 flex-1">
        {navItems.map(({ id, label, icon: Icon }) => {
          const isActive = activeTab === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onTabChange(id)}
              title={collapsed ? label : undefined}
              aria-label={label}
              className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-xs font-medium transition-all ${
                isActive
                  ? "bg-[var(--surface-2)] text-[var(--text)] font-semibold shadow-[var(--shadow-sm)]"
                  : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]"
              } ${collapsed ? "justify-center" : ""}`}
            >
              {/* Active accent beacon bar */}
              {isActive && (
                <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-[var(--accent)] shadow-[var(--accent-glow)]" />
              )}
              <Icon
                className={`h-4.5 w-4.5 shrink-0 transition-colors ${
                  isActive ? "text-[var(--accent)]" : "text-[var(--text-muted)] group-hover:text-[var(--text)]"
                }`}
                strokeWidth={isActive ? 2.25 : 1.75}
              />
              {!collapsed && <span className="truncate">{label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Dock Footer: Connection Status Pill */}
      <div className="pt-3 mt-auto border-t border-[var(--border)]">
        <div
          className={`flex items-center gap-2 rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-2.5 py-1.5 text-[11px] text-[var(--text-muted)] ${
            collapsed ? "justify-center px-1" : ""
          }`}
          title={wsConnected ? "WebSocket live: real-time streaming" : "Polling fallback active"}
        >
          <span
            className={`h-2 w-2 rounded-full shrink-0 ${
              wsConnected
                ? "bg-[var(--status-running)] shadow-[var(--lamp-glow-run)]"
                : "bg-[var(--status-starting)] animate-pulse"
            }`}
          />
          {!collapsed && (
            <span className="font-mono text-[10px] uppercase tracking-wider font-semibold text-[var(--text)] truncate">
              {wsConnected ? "System Live" : "Polling"}
            </span>
          )}
        </div>
      </div>
    </aside>
  );
}

