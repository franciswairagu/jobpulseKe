import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, Check } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";

export default function Dropdown({ label, value, options, onChange, align = "left" }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-xl border px-3.5 py-2 text-xs font-medium transition-all duration-200 hover:border-accent/30 hover:shadow-sm"
        style={{
          borderColor: open ? COLORS.accent : COLORS.border,
          color: COLORS.textDark,
          background: "#fff",
          fontFamily: FONTS.body,
          boxShadow: open ? "0 0 0 3px rgba(250,81,15,0.1)" : "none",
        }}
      >
        {label && <span style={{ color: COLORS.textMuted }}>{label}:</span>}
        <span className="font-semibold">{value}</span>
        <ChevronDown
          size={14}
          className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          style={{ color: COLORS.textMuted }}
        />
      </button>

      {open && (
        <div
          className={`absolute ${align === "right" ? "right-0" : "left-0"} z-30 mt-2 w-52 overflow-hidden rounded-xl border py-1.5 animate-fade-in-down`}
          style={{
            borderColor: COLORS.border,
            background: "#fff",
            boxShadow: "0 12px 40px rgba(16,31,60,0.12), 0 4px 12px rgba(16,31,60,0.06)",
          }}
        >
          {options.map((opt) => {
            const isSelected = opt === value;
            return (
              <button
                key={opt}
                onClick={() => {
                  onChange(opt);
                  setOpen(false);
                }}
                className="flex w-full items-center justify-between px-3.5 py-2.5 text-left text-xs transition-colors duration-150 hover:bg-surface-tertiary"
                style={{
                  color: isSelected ? COLORS.accent : COLORS.textDark,
                  fontWeight: isSelected ? 600 : 400,
                  background: isSelected ? "rgba(250,81,15,0.05)" : "transparent",
                }}
              >
                <span>{opt}</span>
                {isSelected && <Check size={14} className="text-accent" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
