"use client";

import React from "react";

export type SystemStatus =
  | "running"
  | "starting"
  | "stopped"
  | "idle"
  | "unhealthy"
  | "crashed"
  | "external";

interface StatusDotProps {
  status: SystemStatus;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function StatusDot({ status, size = "md", className = "" }: StatusDotProps) {
  const sizeClasses = {
    sm: "w-2 h-2",
    md: "w-2.5 h-2.5",
    lg: "w-3 h-3",
  }[size];

  const statusConfig: Record<
    SystemStatus,
    { bg: string; glow: string; label: string; pulse: boolean }
  > = {
    running: {
      bg: "bg-[var(--status-running)]",
      glow: "shadow-[var(--lamp-glow-run)]",
      label: "Running",
      pulse: false,
    },
    starting: {
      bg: "bg-[var(--status-starting)]",
      glow: "shadow-[var(--lamp-glow-start)]",
      label: "Starting",
      pulse: true,
    },
    stopped: {
      bg: "bg-[var(--status-stopped)]",
      glow: "shadow-[var(--lamp-glow-err)]",
      label: "Stopped",
      pulse: false,
    },
    idle: {
      bg: "bg-[var(--status-idle)]",
      glow: "none",
      label: "Idle",
      pulse: false,
    },
    unhealthy: {
      bg: "bg-[var(--warn)]",
      glow: "shadow-[var(--lamp-glow-warn)]",
      label: "Unhealthy",
      pulse: true,
    },
    crashed: {
      bg: "bg-[var(--status-stopped)]",
      glow: "shadow-[var(--lamp-glow-err)]",
      label: "Crashed",
      pulse: false,
    },
    external: {
      bg: "bg-[var(--accent)]",
      glow: "none",
      label: "External process",
      pulse: false,
    },
  };

  const config = statusConfig[status] || statusConfig.idle;

  return (
    <span
      className="relative inline-flex items-center justify-center shrink-0"
      title={config.label}
      aria-label={config.label}
      role="status"
    >
      {config.pulse && (
        <span
          className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${config.bg}`}
        />
      )}
      <span
        className={`relative inline-flex rounded-full ${sizeClasses} ${config.bg} ${config.glow} ${className}`}
      />
    </span>
  );
}

