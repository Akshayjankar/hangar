"use client";

import React from "react";
import { Card } from "./Card";

interface StatCardProps {
  label: string;
  value: string | number;
  hint?: string;
  icon?: React.ReactNode;
  trend?: string;
  accent?: boolean;
  className?: string;
}

export function StatCard({
  label,
  value,
  hint,
  icon,
  trend,
  accent = false,
  className = "",
}: StatCardProps) {
  return (
    <Card
      className={`p-5 relative overflow-hidden transition-all ${
        accent ? "border-[var(--accent)]/50 bg-[var(--surface)]" : ""
      } ${className}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs uppercase tracking-[0.16em] text-[var(--text-muted)] font-semibold">
            {label}
          </span>
          <div className="mt-2 text-3xl font-black tracking-[-0.03em] text-[var(--text)] font-display tabular-nums">
            {value}
          </div>
          {hint && (
            <p className="mt-1 text-xs text-[var(--text-muted)] leading-relaxed">
              {hint}
            </p>
          )}
          {trend && (
            <span className="mt-2 inline-flex items-center text-xs font-medium text-[var(--accent)] font-mono">
              {trend}
            </span>
          )}
        </div>

        {icon && (
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--surface-2)] text-[var(--accent)]">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}

