"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { OctagonAlert, TriangleAlert, Info, X } from "lucide-react";

export interface ToastItem {
  id: string;
  level: "info" | "warn" | "error";
  title: string;
  reason?: string;
}

interface ToastContextType {
  addToast: (toast: Omit<ToastItem, "id">) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((toast: Omit<ToastItem, "id">) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev.slice(-4), { ...toast, id }]); // keep max 5 active
    // Auto dismiss after 6s
    setTimeout(() => {
      removeToast(id);
    }, 6000);
  }, [removeToast]);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      {/* Toast container with ARIA live region for screen readers */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none px-4"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-panel border shadow-lg transition-all duration-150 ${
              t.level === "error"
                ? "bg-surface border-err text-text"
                : t.level === "warn"
                ? "bg-surface border-warn text-text"
                : "bg-surface border-line text-text"
            }`}
          >
            <div className="shrink-0 mt-0.5">
              {t.level === "error" ? (
                <OctagonAlert className="w-4 h-4 text-err" />
              ) : t.level === "warn" ? (
                <TriangleAlert className="w-4 h-4 text-warn" />
              ) : (
                <Info className="w-4 h-4 text-start" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold truncate">{t.title}</div>
              {t.reason && <div className="text-xs text-muted mt-0.5 line-clamp-2">{t.reason}</div>}
            </div>
            <button
              onClick={() => removeToast(t.id)}
              className="p-1 text-muted hover:text-text rounded-input min-w-[32px] min-h-[32px] inline-flex items-center justify-center shrink-0"
              aria-label="Dismiss notification"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
};

