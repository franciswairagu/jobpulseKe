import React from "react";
import { Loader2 } from "lucide-react";
import { COLORS } from "../../lib/theme";

export default function LoadingState({ label = "Loading..." }) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-2xl border px-6 py-16"
      style={{ borderColor: COLORS.border, background: "#fff" }}
    >
      <Loader2 size={26} className="mb-3 animate-spin" style={{ color: COLORS.deepBlue }} />
      <p className="text-sm" style={{ color: COLORS.textSecondary }}>{label}</p>
    </div>
  );
}
