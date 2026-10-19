import React from "react";
import { RotateCw } from "lucide-react";

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  "aria-label": string;
  variant?: "secondary" | "ghost" | "danger" | "primary";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  "aria-label": ariaLabel,
  variant = "ghost",
  size = "md",
  loading = false,
  className = "",
  disabled,
  title,
  ...props
}) => {
  const sizeClasses = {
    sm: "w-8 h-8 min-w-[36px] min-h-[36px]",
    md: "w-9 h-9 min-w-[44px] min-h-[44px]",
    lg: "w-11 h-11 min-w-[44px] min-h-[44px]",
  }[size];

  const variantClasses = {
    primary: "bg-[var(--primary)] text-[var(--primary-text)] hover:opacity-90",
    secondary: "bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] hover:bg-[var(--surface-hover)]",
    ghost: "bg-transparent text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] border border-transparent",
    danger: "bg-transparent text-[var(--status-stopped)] hover:bg-[var(--status-stopped)]/10 border border-transparent",
  }[variant];

  return (
    <button
      type="button"
      aria-label={ariaLabel}
      title={title || ariaLabel}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center rounded-xl transition-all outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] disabled:opacity-40 disabled:cursor-not-allowed ${sizeClasses} ${variantClasses} ${className}`}
      {...props}
    >
      {loading ? <RotateCw className="w-4 h-4 animate-spin" /> : icon}
    </button>
  );
};
