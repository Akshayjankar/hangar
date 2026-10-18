"use client";

import React from "react";

interface LogoProps {
  variant?: "mark" | "full" | "mono";
  size?: number | string;
  className?: string;
}

export function Logo({ variant = "mark", size = 32, className = "" }: LogoProps) {
  if (variant === "full") {
    return (
      <svg
        viewBox="0 0 240 54"
        width={typeof size === "number" ? size * 4.4 : size}
        height={size}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={`inline-block shrink-0 ${className}`}
        aria-label="Hangar Machine Room Dashboard"
      >
        <title>Hangar</title>
        {/* Airplane mark */}
        <g transform="translate(2, 3)">
          <path d="M24 6L28 28H20L24 6Z" fill="currentColor" stroke="currentColor" strokeWidth="1" strokeLinejoin="round" />
          <path d="M24 20L42 32L38 34L24 26L10 34L6 32L24 20Z" fill="var(--accent)" stroke="var(--accent)" strokeWidth="0.5" strokeLinejoin="round" />
          <path d="M24 28L32 38L28 38L24 32L20 38L16 38L24 28Z" fill="currentColor" stroke="currentColor" strokeWidth="0.5" strokeLinejoin="round" />
          <circle cx="24" cy="6" r="1.5" fill="var(--accent)" />
        </g>
        <text x="64" y="29" fill="currentColor" fontFamily="inherit" fontSize="22" fontWeight="900" letterSpacing="1.5">
          HANGAR
        </text>
        <text x="65" y="44" fill="var(--accent)" fontFamily="inherit" fontSize="7.5" fontWeight="700" letterSpacing="2">
          MACHINE ROOM DASHBOARD
        </text>
      </svg>
    );
  }

  if (variant === "mono") {
    return (
      <svg
        viewBox="0 0 48 48"
        width={size}
        height={size}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={`inline-block shrink-0 ${className}`}
        aria-label="Hangar Logo"
      >
        <title>Hangar</title>
        <path d="M24 6L28 28H20L24 6Z" fill="currentColor" stroke="currentColor" strokeWidth="1" strokeLinejoin="round" />
        <path d="M24 20L42 32L38 34L24 26L10 34L6 32L24 20Z" fill="currentColor" stroke="currentColor" strokeWidth="0.5" strokeLinejoin="round" />
        <path d="M24 28L32 38L28 38L24 32L20 38L16 38L24 28Z" fill="currentColor" stroke="currentColor" strokeWidth="0.5" strokeLinejoin="round" />
        <circle cx="24" cy="6" r="1.5" fill="currentColor" />
      </svg>
    );
  }

  // Default: Mark — classic upward-pointing airplane
  return (
    <svg
      viewBox="0 0 48 48"
      width={size}
      height={size}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`inline-block shrink-0 ${className}`}
      aria-label="Hangar Logo"
    >
      <title>Hangar</title>
      {/* Fuselage */}
      <path
        d="M24 6L28 28H20L24 6Z"
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="1"
        strokeLinejoin="round"
      />
      {/* Main swept wings */}
      <path
        d="M24 20L42 32L38 34L24 26L10 34L6 32L24 20Z"
        fill="var(--accent)"
        stroke="var(--accent)"
        strokeWidth="0.5"
        strokeLinejoin="round"
      />
      {/* Tail fins */}
      <path
        d="M24 28L32 38L28 38L24 32L20 38L16 38L24 28Z"
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="0.5"
        strokeLinejoin="round"
      />
      {/* Nose tip accent */}
      <circle cx="24" cy="6" r="1.5" fill="var(--accent)" />
    </svg>
  );
}
