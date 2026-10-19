import React from "react";
import { Button } from "./Button";

export interface EmptyStateAction {
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  variant?: "primary" | "secondary";
}

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actions?: EmptyStateAction[];
  actionLabel?: string;
  actionIcon?: React.ReactNode;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actions,
  actionLabel,
  actionIcon,
  onAction,
  className = "",
}) => {
  const mergedActions: EmptyStateAction[] = actions || [];
  if (actionLabel && onAction) {
    mergedActions.push({
      label: actionLabel,
      icon: actionIcon,
      onClick: onAction,
      variant: "primary",
    });
  }

  return (
    <div
      className={`flex flex-col items-center justify-center p-8 md:p-12 text-center rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface)]/40 ${className}`}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--surface-2)] text-[var(--accent)] border border-[var(--border)] mb-4 shadow-[var(--shadow-sm)]">
        {icon || (
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
            <path d="M3 21V9C3 5.68629 5.68629 3 9 3H15C18.3137 3 21 5.68629 21 9V21" />
            <path d="M3 21H21" />
            <path d="M12 11L15 17L12 15L9 17L12 11Z" />
          </svg>
        )}
      </div>

      <h3 className="text-base font-bold text-[var(--text)] mb-1 font-display">
        {title}
      </h3>
      <p className="text-xs text-[var(--text-muted)] max-w-md mb-5 leading-relaxed">
        {description}
      </p>

      {mergedActions.length > 0 && (
        <div className="flex flex-wrap items-center justify-center gap-3">
          {mergedActions.map((act, idx) => (
            <Button
              key={`${act.label}-${idx}`}
              variant={act.variant || (idx === 0 ? "primary" : "secondary")}
              size="sm"
              icon={act.icon}
              onClick={act.onClick}
            >
              {act.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
};
