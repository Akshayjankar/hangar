import React from "react";
import {
  Play,
  RotateCw,
  Square,
  OctagonAlert,
  TriangleAlert,
  Globe,
} from "lucide-react";
import { ComponentStatusType, ApplicationStatusType } from "@/lib/types";
import { Lamp } from "./Lamp";

interface StatusPillProps {
  status: ComponentStatusType | ApplicationStatusType;
  className?: string;
  showIcon?: boolean;
}

export const StatusPill: React.FC<StatusPillProps> = ({
  status,
  className = "",
  showIcon = true,
}) => {
  const getIcon = () => {
    switch (status) {
      case "running":
        return <Play className="w-3 h-3 text-run" strokeWidth={2.5} />;
      case "starting":
        return <RotateCw className="w-3 h-3 text-start animate-spin" strokeWidth={2.5} />;
      case "stopped":
        return <Square className="w-3 h-3 text-off" strokeWidth={2.5} />;
      case "stopping":
        return <RotateCw className="w-3 h-3 text-off animate-spin" strokeWidth={2.5} />;
      case "unhealthy":
      case "degraded":
        return <TriangleAlert className="w-3 h-3 text-warn" strokeWidth={2.5} />;
      case "crashed":
      case "failed":
      case "problem":
        return <OctagonAlert className="w-3 h-3 text-err" strokeWidth={2.5} />;
      case "external":
        return <Globe className="w-3 h-3 text-mint" strokeWidth={2.5} />;
      case "partial":
        return <Play className="w-3 h-3 text-start" strokeWidth={2.5} />;
      default:
        return null;
    }
  };

  const getLabel = () => {
    switch (status) {
      case "running":
        return "Running";
      case "starting":
        return "Starting";
      case "stopped":
        return "Stopped";
      case "stopping":
        return "Stopping";
      case "unhealthy":
        return "Unhealthy";
      case "crashed":
        return "Crashed";
      case "failed":
        return "Failed";
      case "external":
        return "External";
      case "degraded":
        return "Degraded";
      case "problem":
        return "Problem";
      case "partial":
        return "Partial";
      default:
        return status;
    }
  };

  const getTextColor = () => {
    switch (status) {
      case "running":
        return "text-run";
      case "starting":
        return "text-start";
      case "stopped":
      case "stopping":
        return "text-off";
      case "unhealthy":
      case "degraded":
        return "text-warn";
      case "crashed":
      case "failed":
      case "problem":
        return "text-err";
      default:
        return "text-muted";
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-pill border border-line bg-surface text-xs font-medium ${className}`}
    >
      <Lamp status={status as ComponentStatusType} size="sm" />
      {showIcon && getIcon()}
      <span className={getTextColor()}>{getLabel()}</span>
    </span>
  );
};

