"use client";

import React, { useState } from "react";
import { Play, Square, Star, AlertTriangle } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ProgressRing } from "@/components/ui/ProgressRing";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { OverviewData } from "@/lib/types";

interface MasterControlProps {
  overview: OverviewData | null;
  onStartFavorites: () => void;
  onStartAll: () => void;
  onStopAll: () => void;
}

export function MasterControl({
  overview,
  onStartFavorites,
  onStartAll,
  onStopAll,
}: MasterControlProps) {
  const [stopAllConfirmOpen, setStopAllConfirmOpen] = useState(false);

  const totalComps = overview?.total_components ?? 0;
  const runningComps = overview?.running_components ?? 0;
  const machineCpu = overview?.machine_cpu_pct ?? 0;
  const machineMemory = overview?.machine_memory_pct ?? 0;

  return (
    <>
      <Card className="p-6 relative overflow-hidden bg-gradient-to-r from-[var(--surface)] via-[var(--surface)] to-[var(--bg-elevated)] border-[var(--border)] shadow-[var(--shadow-md)]">
        {/* Background Runway Line Accent */}
        <div className="absolute top-0 right-0 w-96 h-full opacity-10 pointer-events-none">
          <svg width="100%" height="100%" viewBox="0 0 400 200" fill="none">
            <line x1="0" y1="50" x2="400" y2="50" stroke="var(--accent)" strokeWidth="2" strokeDasharray="8 6" />
            <line x1="0" y1="100" x2="400" y2="100" stroke="var(--accent)" strokeWidth="3" />
            <line x1="0" y1="150" x2="400" y2="150" stroke="var(--accent)" strokeWidth="2" strokeDasharray="8 6" />
          </svg>
        </div>

        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          {/* Left: Overall Machine Room Status */}
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full border border-[var(--border)] bg-[var(--surface-2)] text-[10px] uppercase font-mono font-bold tracking-wider text-[var(--accent)]">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" />
              Machine Room Master Control
            </div>
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-[var(--text)] font-display">
              {runningComps} <span className="text-[var(--text-muted)] font-normal">of</span> {totalComps}{" "}
              <span className="text-xl sm:text-2xl font-bold text-[var(--text-muted)]">services active</span>
            </h2>
            <p className="text-xs text-[var(--text-muted)] max-w-lg leading-relaxed">
              Supervising local projects with zero-orphan tree termination and health check monitoring.
            </p>
          </div>

          {/* Right: Actions & Resource Rings */}
          <div className="flex flex-wrap items-center gap-6">
            {/* Live Machine Gauges */}
            <div className="flex items-center gap-4 py-1 px-3 rounded-2xl border border-[var(--border)] bg-[var(--surface-2)]/60">
              <ProgressRing value={machineCpu} label="CPU Load" size={54} strokeWidth={5} />
              <div className="h-8 w-px bg-[var(--border)]" />
              <ProgressRing value={machineMemory} label="RAM Usage" size={54} strokeWidth={5} />
            </div>

            {/* Batch Operation Buttons */}
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                icon={<Star className="h-3.5 w-3.5 text-[var(--accent)]" />}
                onClick={onStartFavorites}
                title="Start starred projects"
              >
                Start favorites
              </Button>
              <Button
                variant="primary"
                size="sm"
                icon={<Play className="h-3.5 w-3.5" />}
                onClick={onStartAll}
                title="Start all registered applications in order"
              >
                Start all
              </Button>
              <Button
                variant="danger"
                size="sm"
                icon={<Square className="h-3.5 w-3.5" />}
                onClick={() => setStopAllConfirmOpen(true)}
                title="Stop all running applications"
              >
                Stop all
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Stop All Confirmation Dialog */}
      <ConfirmDialog
        open={stopAllConfirmOpen}
        title="Stop all applications?"
        danger
        confirmLabel="Stop everything"
        onConfirm={() => {
          setStopAllConfirmOpen(false);
          onStopAll();
        }}
        onCancel={() => setStopAllConfirmOpen(false)}
        body={
          <p>
            This will terminate all running services across all registered projects in reverse tier order.
            Are you sure you want to proceed?
          </p>
        }
      />
    </>
  );
}

