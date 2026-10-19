"use client";

import React from "react";

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  count?: number;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  className = "",
}) => {
  return (
    <div
      role="tablist"
      className={`flex items-center gap-1 border-b border-line overflow-x-auto ${className}`}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={`flex items-center gap-2 px-3.5 py-2 text-sm font-medium border-b-2 -mb-[1px] transition-colors whitespace-nowrap min-h-[44px] ${
              isActive
                ? "border-primary text-text font-semibold bg-surface-2/40"
                : "border-transparent text-muted hover:text-text hover:bg-surface-2/20"
            }`}
          >
            {tab.icon && <span className="shrink-0">{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span className="ml-1 px-1.5 py-0.2 rounded-pill text-[10px] bg-surface-2 text-muted border border-line">
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};

