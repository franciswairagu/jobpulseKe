import React from "react";
import { AlertTriangle, SearchX, FileX } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";

const ICONS = {
  empty: SearchX,
  error: AlertTriangle,
  noData: FileX,
};

export default function EmptyState({ title, description, tone = "empty", action }) {
  const isError = tone === "error";
  const Icon = ICONS[tone] || ICONS.empty;

  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded-2xl border px-6 py-16 text-center animate-fade-in"
      style={{
        borderColor: isError ? "rgba(239,68,68,0.15)" : COLORS.border,
        background: isError ? "rgba(239,68,68,0.02)" : "#fff",
      }}
    >
      <div
        className="flex h-14 w-14 items-center justify-center rounded-2xl"
        style={{
          background: isError ? "rgba(239,68,68,0.08)" : COLORS.lightBlue,
        }}
      >
        <Icon
          size={24}
          style={{ color: isError ? COLORS.error : COLORS.accent }}
        />
      </div>
      <div>
        <p
          className="text-base font-semibold"
          style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
        >
          {title}
        </p>
        {description && (
          <p
            className="mt-1.5 max-w-sm text-sm leading-relaxed"
            style={{ color: COLORS.textSecondary }}
          >
            {description}
          </p>
        )}
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
