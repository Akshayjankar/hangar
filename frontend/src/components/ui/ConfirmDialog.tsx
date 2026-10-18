"use client";

import React from "react";
import { Dialog, DialogContent } from "./Dialog";
import { Button } from "./Button";
import { AlertTriangle, RotateCw } from "lucide-react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  body: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  children?: React.ReactNode;
}

export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger = false,
  loading = false,
  onConfirm,
  onCancel,
  children,
}: ConfirmDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!loading && !nextOpen) {
          onCancel();
        }
      }}
    >
      <DialogContent title={title} description="Action confirmation">
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            {danger && (
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-500/10 text-[var(--status-stopped)]">
                <AlertTriangle className="h-5 w-5" />
              </div>
            )}
            <div className="text-sm text-[var(--text)] leading-relaxed">
              {body}
            </div>
          </div>

          {children}

          <div className="flex justify-end gap-2 pt-2 border-t border-[var(--border)]">
            <Button
              variant="secondary"
              size="sm"
              onClick={onCancel}
              disabled={loading}
            >
              {cancelLabel}
            </Button>
            <Button
              variant={danger ? "danger" : "primary"}
              size="sm"
              icon={
                loading ? (
                  <RotateCw className="h-3.5 w-3.5 animate-spin" />
                ) : undefined
              }
              onClick={onConfirm}
              disabled={loading}
            >
              {loading ? "Processing..." : confirmLabel}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

