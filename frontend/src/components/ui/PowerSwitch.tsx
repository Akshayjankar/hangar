import React from "react";
import { RotateCw, OctagonAlert } from "lucide-react";
import { ComponentStatusType } from "@/lib/types";
import { Lamp } from "./Lamp";

interface PowerSwitchProps {
  status: ComponentStatusType;
  label: string;
  onToggle: (nextState: boolean) => void;
  disabled?: boolean;
}

export const PowerSwitch: React.FC<PowerSwitchProps> = ({
  status,
  label,
  onToggle,
  disabled = false,
}) => {
  const isTransitioning = status === "starting" || status === "stopping";
  const isOn = status === "running" || status === "unhealthy" || status === "starting";

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (disabled || isTransitioning) return;
    onToggle(!isOn);
  };

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        role="switch"
        aria-checked={isOn}
        aria-label={label}
        disabled={disabled || isTransitioning}
        onClick={handleClick}
        title={isTransitioning ? `Please wait, ${status}...` : isOn ? "Stop component" : "Start component"}
        className={`relative inline-flex items-center h-[26px] w-[46px] min-h-[44px] min-w-[44px] shrink-0 cursor-pointer rounded-pill p-1 transition-colors duration-200 outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${
          disabled ? "opacity-50 cursor-not-allowed" : ""
        }`}
      >
        {/* Switch track */}
        <div
          className={`absolute left-0 top-[9px] w-[46px] h-[26px] rounded-pill border border-line transition-colors duration-200 ${
            isOn ? "bg-surface-2" : "bg-surface"
          }`}
        />

        {/* Switch Thumb */}
        <span
          className={`relative z-10 inline-flex items-center justify-center w-5 h-5 rounded-pill bg-primary border border-line shadow-sm transition-transform duration-[180ms] ease-out ${
            isOn ? "translate-x-[20px]" : "translate-x-0"
          }`}
        >
          {status === "starting" || status === "stopping" ? (
            <RotateCw className="w-3 h-3 text-primary-text animate-spin" />
          ) : status === "crashed" ? (
            <OctagonAlert className="w-3 h-3 text-err" />
          ) : (
            <span
              className={`w-2 h-2 rounded-pill ${
                status === "running"
                  ? "bg-run"
                  : status === "unhealthy"
                  ? "bg-warn"
                  : "bg-off"
              }`}
            />
          )}
        </span>
      </button>

      {/* Accompanying Status Lamp */}
      <Lamp status={status} size="md" />
    </div>
  );
};

