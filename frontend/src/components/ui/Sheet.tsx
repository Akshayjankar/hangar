"use client";

import React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";

export const Sheet = DialogPrimitive.Root;
export const SheetTrigger = DialogPrimitive.Trigger;

export const SheetContent: React.FC<{
  children: React.ReactNode;
  title: string;
  description?: string;
  className?: string;
  isOpen?: boolean;
  onClose?: () => void;
}> = ({ children, title, description, className = "", onClose }) => {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm transition-opacity" />
      <DialogPrimitive.Content
        className={`fixed z-50 bg-surface border-line p-6 focus:outline-none transition-transform 
          bottom-0 left-0 right-0 max-h-[92dvh] rounded-t-panel border-t overflow-y-auto
          md:bottom-0 md:top-0 md:right-0 md:left-auto md:w-[600px] md:max-w-[90vw] md:max-h-full md:rounded-none md:border-l md:border-t-0 ${className}`}
      >
        <div className="flex items-center justify-between pb-3 border-b border-line mb-4">
          <div>
            <DialogPrimitive.Title className="text-xl font-bold text-text">
              {title}
            </DialogPrimitive.Title>
            {description && (
              <DialogPrimitive.Description className="text-xs text-muted mt-0.5">
                {description}
              </DialogPrimitive.Description>
            )}
          </div>
          <DialogPrimitive.Close asChild onClick={onClose}>
            <button
              className="p-1.5 rounded-input text-muted hover:text-text hover:bg-surface-2 transition-colors min-h-[44px] min-w-[44px] inline-flex items-center justify-center"
              aria-label="Close sheet"
            >
              <X className="w-5 h-5" />
            </button>
          </DialogPrimitive.Close>
        </div>
        <div className="pb-12 md:pb-6">{children}</div>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
};

