import React from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { COLORS, AFRICAN_COUNTRIES } from "../../lib/theme";
import Dropdown from "../shared/Dropdown";

const SORT_OPTIONS = [
  { key: "match", label: "Best matches" },
  { key: "recent", label: "Most recent" },
  { key: "salary", label: "Highest salary" },
  { key: "fewestGaps", label: "Fewest skill gaps" },
];

export default function JobFilters({ query, onQueryChange, country, onCountryChange, remoteOnly, onRemoteChange, sortBy, onSortChange, showFilters, onToggleFilters, personalized }) {
  return (
    <div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex flex-1 items-center gap-2 rounded-lg border px-3.5 py-2.5" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <Search size={16} style={{ color: COLORS.textSecondary }} />
          <input
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Search jobs by title, skill or company"
            className="w-full bg-transparent text-sm outline-none"
            style={{ color: COLORS.textDark }}
          />
        </div>
        <button onClick={onToggleFilters} className="flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium" style={{ borderColor: showFilters ? COLORS.deepBlue : COLORS.border, color: showFilters ? COLORS.deepBlue : COLORS.textDark, background: "#fff" }}>
          <SlidersHorizontal size={15} /> Filters
        </button>
      </div>

      {showFilters && (
        <div className="mt-3 flex flex-wrap gap-2">
          <Dropdown label="Country" value={country} options={["All countries", ...AFRICAN_COUNTRIES]} onChange={onCountryChange} />
          <Dropdown label="Remote" value={remoteOnly ? "Remote only" : "All types"} options={["All types", "Remote only"]} onChange={(v) => onRemoteChange(v === "Remote only")} />
          {personalized && (
            <Dropdown label="Sort" value={SORT_OPTIONS.find((o) => o.key === sortBy)?.label} options={SORT_OPTIONS.map((o) => o.label)} onChange={(label) => onSortChange(SORT_OPTIONS.find((o) => o.label === label).key)} />
          )}
        </div>
      )}
    </div>
  );
}
