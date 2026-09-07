import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";

export default function Dropdown({ label, value, options, onChange, align = "left" }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium"
        style={{ borderColor: COLORS.border, color: COLORS.textDark, background: "#fff", fontFamily: FONTS.body }}
      >
        {label && <span style={{ color: COLORS.textSecondary }}>{label}:</span>}
        {value}
        <ChevronDown size={13} style={{ color: COLORS.textSecondary }} />
      </button>
      {open && (
        <div
          className={`absolute ${align === "right" ? "right-0" : "left-0"} z-20 mt-1 w-48 overflow-hidden rounded-lg border bg-white shadow-lg`}
          style={{ borderColor: COLORS.border }}
        >
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => {
                onChange(opt);
                setOpen(false);
              }}
              className="block w-full px-3 py-2 text-left text-xs hover:bg-[#F7F9FC]"
              style={{ color: opt === value ? COLORS.deepBlue : COLORS.textDark, fontWeight: opt === value ? 600 : 400 }}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
