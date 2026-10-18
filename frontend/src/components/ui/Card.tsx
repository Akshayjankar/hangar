"use client";

import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: "default" | "elevated" | "interactive";
  className?: string;
}

export function Card({
  children,
  variant = "default",
  className = "",
  ...props
}: CardProps) {
  const baseStyles = "rounded-2xl border border-[var(--border)] transition-all";
  
  const variantStyles = {
    default: "bg-[var(--surface)] shadow-[var(--shadow-sm)]",
    elevated: "bg-[var(--bg-elevated)] shadow-[var(--shadow-md)]",
    interactive: "bg-[var(--surface)] hover:bg-[var(--surface-hover)] hover:border-[var(--accent)] hover:shadow-[var(--shadow-md)] hover:-translate-y-0.5 cursor-pointer",
  }[variant];

  return (
    <div className={`${baseStyles} ${variantStyles} ${className}`} {...props}>
      {children}
    </div>
  );
}

