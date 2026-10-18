"use client";

import React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;

export const DialogContent: React.FC<{
  children: React.ReactNode;
  title: string;
  description?: string;
  className?: string;
}> = ({ children, title, description, className = "" }) => {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm transition-opacity" />
      <DialogPrimitive.Content
        className={`fixed left-[50%] top-[50%] z-50 w-full max-w-lg translate-x-[-50%] translate-y-[-50%] rounded-panel border border-line bg-surface p-6 shadow-2xl focus:outline-none ${className}`}
      >
        <div className="flex items-center justify-between pb-3 border-b border-line mb-4">
          <div>
            <DialogPrimitive.Title className="text-lg font-bold text-text">
              {title}
            </DialogPrimitive.Title>
            {description && (
              <DialogPrimitive.Description className="text-xs text-muted mt-0.5">
                {description}
              </DialogPrimitive.Description>
            )}
          </div>
          <DialogPrimitive.Close asChild>
            <button
              className="p-1 rounded-input text-muted hover:text-text hover:bg-surface-2 transition-colors min-h-[44px] min-w-[44px] inline-flex items-center justify-center"
              aria-label="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </DialogPrimitive.Close>
        </div>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
};

