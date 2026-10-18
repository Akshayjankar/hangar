"use client";

import React from "react";

interface ProgressRingProps {
  value: number; // 0 to 100
  label: string;
  size?: number;
  strokeWidth?: number;
  unit?: string;
  className?: string;
}

export function ProgressRing({
  value,
  label,
  size = 72,
  strokeWidth = 6,
  unit = "%",
  className = "",
}: ProgressRingProps) {
  const clampedValue = Math.min(100, Math.max(0, value));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (clampedValue / 100) * circumference;

  // Color gradient depending on load: green -> amber -> red
  let strokeColor = "var(--status-running)";
  if (clampedValue >= 80) {
    strokeColor = "var(--status-stopped)";
  } else if (clampedValue >= 60) {
    strokeColor = "var(--status-starting)";
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="rotate-[-90deg]">
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--surface-2)"
            strokeWidth={strokeWidth}
          />
          {/* Active Progress Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-500 ease-out"
          />
        </svg>

        {/* Center Value */}
        <div className="absolute inset-0 flex items-center justify-center font-mono font-bold text-xs text-[var(--text)] tabular-nums">
          {Math.round(clampedValue)}
          <span className="text-[10px] text-[var(--text-muted)] font-normal">{unit}</span>
        </div>
      </div>

      <div>
        <div className="text-xs font-semibold text-[var(--text)]">{label}</div>
        <div className="text-[11px] text-[var(--text-muted)] font-mono">
          {clampedValue >= 80 ? "High load" : clampedValue >= 60 ? "Elevated" : "Nominal"}
        </div>
      </div>
    </div>
  );
}

