import React from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";
import Dropdown from "../shared/Dropdown";

const SORT_OPTIONS = [
  { key: "match", label: "Best matches" },
  { key: "recent", label: "Most recent" },
  { key: "fewestGaps", label: "Fewest skill gaps" },
];

export default function JobFilters({
  query,
  onQueryChange,
  country,
  onCountryChange,
  remoteOnly,
  onRemoteChange,
  sortBy,
  onSortChange,
  showFilters,
  onToggleFilters,
  personalized,
}) {
  return (
    <div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div
          className="flex flex-1 items-center gap-3 rounded-xl border px-4 py-3 transition-all duration-200 focus-within:border-accent focus-within:shadow-glow-blue"
          style={{ borderColor: COLORS.border, background: "#fff" }}
        >
          <Search size={16} style={{ color: COLORS.textMuted }} />
          <input
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Search jobs by title, skill or company"
            className="w-full bg-transparent text-sm outline-none placeholder:text-textMuted"
            style={{ color: COLORS.textDark }}
          />
          {query && (
            <button
              onClick={() => onQueryChange("")}
              className="rounded-md p-1 hover:bg-surface-tertiary"
            >
              <X size={14} style={{ color: COLORS.textMuted }} />
            </button>
          )}
        </div>
        <button
          onClick={onToggleFilters}
          className="flex items-center justify-center gap-2 rounded-xl border px-4 py-3 text-sm font-medium transition-all duration-200"
          style={{
            borderColor: showFilters ? COLORS.accent : COLORS.border,
            color: showFilters ? COLORS.accent : COLORS.textDark,
            background: showFilters ? "rgba(250,81,15,0.05)" : "#fff",
            boxShadow: showFilters ? "0 0 0 3px rgba(250,81,15,0.1)" : "none",
          }}
        >
          <SlidersHorizontal size={15} /> Filters
        </button>
      </div>

      {showFilters && (
        <div className="mt-3 flex flex-wrap gap-2 animate-fade-in-down">
          <Dropdown label="Country" value={country} options={["All countries", ...["Kenya", "Nigeria", "South Africa", "Ghana", "Uganda", "Rwanda", "Egypt"]]} onChange={onCountryChange} />
          <Dropdown label="Remote" value={remoteOnly ? "Remote only" : "All types"} options={["All types", "Remote only"]} onChange={(v) => onRemoteChange(v === "Remote only")} />
          {personalized && (
            <Dropdown label="Sort" value={SORT_OPTIONS.find((o) => o.key === sortBy)?.label} options={SORT_OPTIONS.map((o) => o.label)} onChange={(label) => onSortChange(SORT_OPTIONS.find((o) => o.label === label).key)} />
          )}
        </div>
      )}
    </div>
  );
}
