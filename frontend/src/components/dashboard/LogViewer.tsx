"use client";

import React, { useState, useEffect, useRef } from "react";
import { ArrowDown, Copy, Download, Trash2, Check } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { stripAnsi } from "@/lib/format";

interface LogViewerProps {
  logs: string[];
  selectedComponent: string;
  componentOptions: Array<{ id: string; name: string; appName: string }>;
  onSelectComponent: (id: string) => void;
  onClearLogs: () => void;
}

export function LogViewer({
  logs,
  selectedComponent,
  componentOptions,
  onSelectComponent,
  onClearLogs,
}: LogViewerProps) {
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleCopy = () => {
    const raw = (logs || []).map(stripAnsi).join("\n");
    navigator.clipboard.writeText(raw);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const raw = (logs || []).map(stripAnsi).join("\n");
    const blob = new Blob([raw], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hangar-log-${selectedComponent}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="p-5 border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-sm)]">
      {/* Log Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-[var(--border)]">
        <div>
          <h2 className="text-lg font-bold text-[var(--text)] font-display">
            Process Output Logs
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            Tailed directly from disk (stdout & stderr merged per run)
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Component Selector */}
          <select
            value={selectedComponent}
            onChange={(e) => onSelectComponent(e.target.value)}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-1.5 text-xs font-semibold text-[var(--text)] outline-none min-h-[36px]"
          >
            {componentOptions.map((c) => (
              <option key={c.id} value={c.id}>
                {c.appName} • {c.name}
              </option>
            ))}
          </select>

          {/* Follow / Auto-Scroll Toggle */}
          <button
            type="button"
            onClick={() => setAutoScroll(!autoScroll)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition-colors min-h-[36px] ${
              autoScroll
                ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]"
                : "border-[var(--border)] bg-[var(--surface-2)] text-[var(--text-muted)]"
            }`}
          >
            <ArrowDown className="h-3.5 w-3.5" />
            <span>Follow</span>
          </button>

          {/* Copy */}
          <Button
            variant="secondary"
            size="sm"
            icon={copied ? <Check className="h-3.5 w-3.5 text-[var(--status-running)]" /> : <Copy className="h-3.5 w-3.5" />}
            onClick={handleCopy}
            title="Copy logs to clipboard"
          >
            {copied ? "Copied" : "Copy"}
          </Button>

          {/* Download */}
          <Button
            variant="secondary"
            size="sm"
            icon={<Download className="h-3.5 w-3.5" />}
            onClick={handleDownload}
            title="Download log file"
          >
            Download
          </Button>

          {/* Clear */}
          <Button
            variant="secondary"
            size="sm"
            icon={<Trash2 className="h-3.5 w-3.5" />}
            onClick={onClearLogs}
            title="Clear component logs"
          >
            Clear
          </Button>
        </div>
      </div>

      {/* Terminal Display */}
      <div
        ref={logContainerRef}
        className="max-h-[620px] min-h-[380px] overflow-auto rounded-xl border border-[var(--border)] bg-[#040C14] p-4 font-mono text-xs text-slate-200 shadow-inner"
      >
        {(logs || []).length > 0 ? (
          (logs || []).map((line, idx) => {
            const cleanLine = stripAnsi(line);
            const isError = cleanLine.includes("ERROR") || cleanLine.includes("Traceback") || cleanLine.includes("Exception");
            const isWarn = cleanLine.includes("WARN") || cleanLine.includes("WARNING");
            const isSystem = cleanLine.includes("[hangar]");

            return (
              <div
                key={`${idx}-${cleanLine.slice(0, 10)}`}
                className={`whitespace-pre-wrap break-words leading-5 flex items-start gap-3 py-0.5 px-1 rounded ${
                  isError
                    ? "bg-red-500/10 text-red-300"
                    : isWarn
                    ? "bg-amber-500/10 text-amber-200"
                    : isSystem
                    ? "text-[var(--accent)] font-semibold"
                    : "text-slate-300"
                }`}
              >
                <span className="text-slate-600 select-none w-8 text-right shrink-0 text-[10px] pt-0.5">
                  {idx + 1}
                </span>
                <span className="flex-1">{cleanLine}</span>
              </div>
            );
          })
        ) : (
          <div className="text-[var(--text-muted)] flex flex-col items-center justify-center h-64 gap-2">
            <span className="text-sm font-semibold">No active stream for this component</span>
            <span className="text-xs">Start the component to see live process stdout & stderr</span>
          </div>
        )}
      </div>
    </Card>
  );
}

