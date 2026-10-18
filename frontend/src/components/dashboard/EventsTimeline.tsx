"use client";

import React, { useState, useMemo } from "react";
import { CheckCheck, Filter } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusDot } from "@/components/ui/StatusDot";
import { EventItem } from "@/lib/types";
import { formatRelativeTime } from "@/lib/format";

interface EventsTimelineProps {
  events: EventItem[];
  onMarkAllRead: () => void;
  maxDisplay?: number;
}

export function EventsTimeline({
  events,
  onMarkAllRead,
  maxDisplay = 10,
}: EventsTimelineProps) {
  const [filter, setFilter] = useState<"all" | "error" | "warn" | "info">("all");

  const filteredEvents = useMemo(() => {
    const validEvents = (events || []).filter(
      (e): e is EventItem => Boolean(e && typeof e === "object" && e.id)
    );
    if (filter === "all") return validEvents;
    return validEvents.filter((e) => e.level === filter);
  }, [events, filter]);

  const displayedEvents = filteredEvents.slice(0, maxDisplay);

  return (
    <Card className="p-5 border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-sm)]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-[var(--border)]">
        <div>
          <h2 className="text-lg font-bold text-[var(--text)] font-display">
            System Activity Log
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            Chronological audit of processes, crashes, health states, and alerts
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Filter Chips */}
          <div className="flex items-center rounded-xl border border-[var(--border)] bg-[var(--surface-2)] p-0.5 text-xs">
            {(["all", "error", "warn", "info"] as const).map((lvl) => (
              <button
                key={lvl}
                type="button"
                onClick={() => setFilter(lvl)}
                className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors uppercase font-mono ${
                  filter === lvl
                    ? "bg-[var(--surface)] text-[var(--text)] font-bold shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text)]"
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          <Button
            variant="secondary"
            size="sm"
            icon={<CheckCheck className="h-3.5 w-3.5" />}
            onClick={onMarkAllRead}
            title="Mark all activity events as read"
          >
            <span className="hidden sm:inline">Mark all read</span>
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        {displayedEvents.map((event) => {
          if (!event || !event.id) return null;
          const statusType =
            event.level === "error"
              ? "crashed"
              : event.level === "warn"
              ? "unhealthy"
              : "running";

          return (
            <div
              key={event.id}
              className="flex items-start gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface-2)]/60 p-3 hover:bg-[var(--surface-2)] transition-colors"
            >
              <div className="mt-1">
                <StatusDot status={statusType} size="sm" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-xs text-[var(--text)] truncate">
                    {event.title || "System event"}
                  </span>
                  <span className="text-[11px] text-[var(--text-muted)] font-mono shrink-0">
                    {event.ts ? formatRelativeTime(event.ts) : ""}
                  </span>
                </div>
                {event.reason && (
                  <p className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-2">
                    {event.reason}
                  </p>
                )}
              </div>
            </div>
          );
        })}

        {displayedEvents.length === 0 && (
          <div className="p-8 text-center text-xs text-[var(--text-muted)] border border-dashed border-[var(--border)] rounded-xl">
            No system events match the selected filter.
          </div>
        )}
      </div>
    </Card>
  );
}

