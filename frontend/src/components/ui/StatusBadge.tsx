"use client";

import React from "react";
import { StatusDot, SystemStatus } from "./StatusDot";

interface StatusBadgeProps {
  status: SystemStatus;
  label?: string;
  size?: "sm" | "md";
  className?: string;
}

export function StatusBadge({
  status,
  label,
  size = "md",
  className = "",
}: StatusBadgeProps) {
  const displayLabel =
    label ||
    {
      running: "Running",
      starting: "Starting...",
      stopped: "Stopped",
      idle: "Idle",
      unhealthy: "Unhealthy",
      crashed: "Crashed",
      external: "External",
    }[status] ||
    "Unknown";

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[11px]",
    md: "px-2.5 py-1 text-xs",
  }[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--surface-2)] font-medium text-[var(--text)] ${sizeStyles} ${className}`}
    >
      <StatusDot status={status} size={size === "sm" ? "sm" : "md"} />
      <span className="capitalize">{displayLabel}</span>
    </span>
  );
}

