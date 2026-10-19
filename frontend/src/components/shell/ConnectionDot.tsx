"use client";

import React, { useEffect, useState } from "react";
import { wsClient } from "@/lib/ws";

export const ConnectionDot: React.FC = () => {
  const [status, setStatus] = useState<"connected" | "reconnecting" | "disconnected">("disconnected");

  useEffect(() => {
    wsClient.connect();
    const unsub = wsClient.onConnectionChange((st) => setStatus(st));
    return () => unsub();
  }, []);

  const getStatusText = () => {
    if (status === "connected") return "Live";
    if (status === "reconnecting") return "Reconnecting";
    return "Offline";
  };

  const getDotClass = () => {
    if (status === "connected") return "bg-run shadow-[var(--lamp-glow-run)]";
    if (status === "reconnecting") return "bg-warn animate-pulse";
    return "bg-off";
  };

  return (
    <div
      className="flex items-center gap-1.5 px-2 py-1 text-[11px] font-medium text-muted"
      title={`WebSocket: ${status}`}
    >
      <span className={`w-2 h-2 rounded-pill shrink-0 ${getDotClass()}`} />
      <span className="hidden md:inline">{getStatusText()}</span>
    </div>
  );
};

