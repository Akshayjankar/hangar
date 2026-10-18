import React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "secondary",
  size = "md",
  icon,
  className = "",
  disabled,
  ...props
}) => {
  const baseClasses =
    "inline-flex items-center justify-center font-medium rounded-input border transition-colors outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 select-none disabled:opacity-50 disabled:cursor-not-allowed";

  const sizeClasses = {
    sm: "h-8 px-2.5 text-xs gap-1.5 min-h-[36px]",
    md: "h-9 px-3.5 text-sm gap-2 min-h-[44px]",
    lg: "h-11 px-5 text-base gap-2.5 min-h-[44px]",
  }[size];

  const variantClasses = {
    primary:
      "bg-primary text-primary-text border-primary hover:opacity-90 active:opacity-95 font-semibold",
    secondary:
      "bg-surface text-text border-line hover:bg-surface-2 active:bg-surface-2",
    danger:
      "bg-surface text-err border-err/40 hover:bg-err/10 active:bg-err/20",
    ghost:
      "bg-transparent text-text border-transparent hover:bg-surface-2 active:bg-surface-2",
  }[variant];

  return (
    <button
      className={`${baseClasses} ${sizeClasses} ${variantClasses} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children && <span>{children}</span>}
    </button>
  );
};

