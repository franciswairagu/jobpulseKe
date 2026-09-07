import React from "react";
import { AlertTriangle } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";

// Section 27: never leave the user staring at a blank page. Used for both
// "no results" and "request failed" states, with a slightly different tone.
export default function EmptyState({ title, description, tone = "empty", action }) {
  const isError = tone === "error";
  return (
    <div
      className="flex flex-col items-center justify-center gap-2 rounded-2xl border px-6 py-14 text-center"
      style={{ borderColor: COLORS.border, background: isError ? "rgba(220,38,38,0.03)" : "#fff" }}
    >
      {isError && <AlertTriangle size={20} style={{ color: COLORS.error }} />}
      <p className="text-sm font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
        {title}
      </p>
      {description && (
        <p className="max-w-sm text-xs" style={{ color: COLORS.textSecondary }}>
          {description}
        </p>
      )}
      {action}
    </div>
  );
}
