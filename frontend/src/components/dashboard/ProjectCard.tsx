"use client";

import React from "react";
import {
  Code,
  ExternalLink,
  FolderOpen,
  Play,
  RotateCw,
  Square,
  Trash2,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PowerSwitch } from "@/components/ui/PowerSwitch";
import { Application } from "@/lib/types";

interface ProjectCardProps {
  app: Application;
  onToggleComponent: (componentId: string, nextState: boolean) => void;
  onRestartComponent: (componentId: string) => void;
  onStartApp: (appId: string) => void;
  onStopApp: (appId: string) => void;
  onOpenFolder: (appId: string) => void;
  onOpenEditor: (appId: string) => void;
  onRemoveProject: (app: Application) => void;
}

export function ProjectCard({
  app,
  onToggleComponent,
  onRestartComponent,
  onStartApp,
  onStopApp,
  onOpenFolder,
  onOpenEditor,
  onRemoveProject,
}: ProjectCardProps) {
  return (
    <Card className="p-5 overflow-hidden transition-all border-[var(--border)] bg-[var(--surface)] hover:border-[var(--accent)]/40 shadow-[var(--shadow-sm)]">
      {/* Bay Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-[var(--border)]">
        <div className="flex items-center gap-3.5 min-w-0">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--surface-2)] text-xl shadow-[var(--shadow-sm)]">
            {app.icon === "ScrollText" ? "📜" : "📦"}
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-bold text-base md:text-lg text-[var(--text)] truncate font-display">
                {app.name}
              </h3>
              <StatusBadge status={app.status as any} size="sm" />
            </div>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="text-xs text-[var(--text-muted)] font-mono truncate max-w-xs sm:max-w-md">
                {app.path}
              </span>
              {(app.tags || []).map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-[var(--border)] bg-[var(--surface-2)] px-2 py-0.2 text-[10px] text-[var(--text-muted)] font-mono"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Project Toolbar */}
        <div className="flex flex-wrap items-center gap-1.5 shrink-0">
          <Button
            variant="secondary"
            size="sm"
            icon={<FolderOpen className="h-3.5 w-3.5" />}
            onClick={() => onOpenFolder(app.id)}
            title="Open folder in File Explorer"
          >
            <span className="hidden xl:inline">Folder</span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
            icon={<Code className="h-3.5 w-3.5" />}
            onClick={() => onOpenEditor(app.id)}
            title="Open project in Editor"
          >
            <span className="hidden xl:inline">Editor</span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
            icon={<Play className="h-3.5 w-3.5" />}
            onClick={() => onStartApp(app.id)}
            title="Start all components in order"
          >
            Start
          </Button>

          <Button
            variant="secondary"
            size="sm"
            icon={<Square className="h-3.5 w-3.5" />}
            onClick={() => onStopApp(app.id)}
            title="Stop all components"
          >
            Stop
          </Button>

          {/* Remove Project Button */}
          <Button
            variant="danger"
            size="sm"
            icon={<Trash2 className="h-3.5 w-3.5" />}
            onClick={() => onRemoveProject(app)}
            title="Remove this project from Hangar"
          >
            Remove
          </Button>
        </div>
      </div>

      {/* Component Rows */}
      <div className="mt-3.5 space-y-2">
        {(app.components || []).map((comp) => (
          <div
            key={comp.id}
            className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl bg-[var(--surface-2)]/60 border border-[var(--border)] hover:bg-[var(--surface-2)] transition-colors"
          >
            {/* Component Status & Identity */}
            <div className="flex items-center gap-3 min-w-0">
              <PowerSwitch
                status={comp.status}
                label={`Toggle ${comp.name}`}
                onToggle={(nextState) => onToggleComponent(comp.id, nextState)}
              />

              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-sm text-[var(--text)] truncate">
                    {comp.name}
                  </span>
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded border border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)]">
                    {comp.kind}
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)] font-mono">
                    Tier {comp.tier}
                  </span>
                </div>

                <div className="text-xs text-[var(--text-muted)] font-mono mt-0.5 truncate max-w-sm sm:max-w-lg">
                  {comp.start_cmd}
                  {comp.port ? ` • :${comp.port}` : ""}
                  {comp.cpu_pct ? ` • ${comp.cpu_pct}% CPU` : ""}
                </div>
              </div>
            </div>

            {/* Component Quick Controls */}
            <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
              <StatusBadge status={comp.status as any} size="sm" />

              {comp.url && (
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<ExternalLink className="h-3.5 w-3.5" />}
                  onClick={() => window.open(comp.url || `http://localhost:${comp.port}`, "_blank")}
                  title={`Open http://localhost:${comp.port} in browser`}
                >
                  Open
                </Button>
              )}

              <Button
                variant="secondary"
                size="sm"
                icon={<RotateCw className="h-3.5 w-3.5" />}
                onClick={() => onRestartComponent(comp.id)}
                title="Restart this component"
              >
                Restart
              </Button>
            </div>
          </div>
        ))}

        {app.components.length === 0 && (
          <div className="p-4 text-center text-xs text-[var(--text-muted)] border border-dashed border-[var(--border)] rounded-xl">
            No components configured for this application yet.
          </div>
        )}
      </div>
    </Card>
  );
}

