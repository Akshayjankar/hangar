import React from "react";
import { ComponentStatusType } from "@/lib/types";

interface LampProps {
  status: ComponentStatusType;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const Lamp: React.FC<LampProps> = ({ status, size = "md", className = "" }) => {
  const sizeClasses = {
    sm: "w-2 h-2",
    md: "w-2.5 h-2.5",
    lg: "w-3 h-3",
  }[size];

  // Map status to token background & glow
  const colorClasses = {
    running: "bg-run shadow-[var(--lamp-glow-run)] ring-1 ring-run/30",
    starting: "bg-start shadow-[var(--lamp-glow-start)] animate-pulse ring-1 ring-start/30",
    stopped: "bg-off ring-1 ring-off/20",
    stopping: "bg-off animate-pulse ring-1 ring-off/20",
    unhealthy: "bg-warn shadow-[var(--lamp-glow-warn)] ring-1 ring-warn/30",
    crashed: "bg-err shadow-[var(--lamp-glow-err)] ring-1 ring-err/30",
    failed: "bg-err shadow-[var(--lamp-glow-err)] ring-1 ring-err/30",
    external: "bg-mint shadow-[var(--lamp-glow-run)] ring-1 ring-mint/30",
  }[status] || "bg-off";

  return (
    <span
      className={`inline-block rounded-pill transition-all duration-200 shrink-0 ${sizeClasses} ${colorClasses} ${className}`}
      aria-hidden="true"
    />
  );
};

