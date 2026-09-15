import React from "react";
import { COLORS, FONTS } from "../../lib/theme";

function SkeletonBar({ width = "100%", height = "16px", className = "" }) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{ width, height, borderRadius: "8px" }}
    />
  );
}

export default function LoadingState({ label = "Loading...", variant = "default" }) {
  if (variant === "skeleton") {
    return (
      <div className="space-y-4 animate-fade-in">
        <div className="flex items-center gap-4">
          <SkeletonBar width="48px" height="48px" className="rounded-xl" />
          <div className="flex-1 space-y-2">
            <SkeletonBar width="60%" height="14px" />
            <SkeletonBar width="40%" height="12px" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="rounded-2xl border border-border p-5 space-y-3">
              <SkeletonBar width="70%" height="16px" />
              <SkeletonBar width="100%" height="12px" />
              <SkeletonBar width="80%" height="12px" />
              <div className="flex gap-2 pt-2">
                <SkeletonBar width="60px" height="24px" className="rounded-full" />
                <SkeletonBar width="40px" height="24px" className="rounded-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex flex-col items-center justify-center rounded-2xl border px-6 py-16 animate-fade-in"
      style={{ borderColor: COLORS.border, background: "#fff" }}
    >
      <div className="relative mb-4">
        <div
          className="h-12 w-12 rounded-full"
          style={{
            border: `3px solid ${COLORS.border}`,
            borderTopColor: COLORS.accent,
            animation: "spin 1s linear infinite",
          }}
        />
        <div
          className="absolute inset-0 h-12 w-12 rounded-full"
          style={{
            border: `3px solid transparent`,
            borderTopColor: "rgba(250,81,15,0.3)",
            animation: "spin 1.5s linear infinite reverse",
          }}
        />
      </div>
      <p
        className="text-sm font-medium"
        style={{ color: COLORS.textSecondary, fontFamily: FONTS.body }}
      >
        {label}
      </p>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
