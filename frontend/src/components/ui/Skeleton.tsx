import React from "react";

export const Skeleton: React.FC<{ className?: string }> = ({ className = "" }) => {
  return (
    <div
      className={`animate-pulse rounded-input bg-surface-2/60 border border-line/30 ${className}`}
      aria-hidden="true"
    />
  );
};

