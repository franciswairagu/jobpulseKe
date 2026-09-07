import React, { useState, useMemo } from "react";
import {
  Search,
  SlidersHorizontal,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  ChevronDown,
} from "lucide-react";

const NAVY = "#0B1F3A";
const DEEP_BLUE = "#123B63";
const LIGHT_BLUE = "#EAF3FA";
const PAGE_BG = "#F7F9FC";
const TEXT_DARK = "#172033";
const TEXT_SECONDARY = "#667085";
const SUCCESS = "#16A34A";
const WARNING = "#F59E0B";
const ERROR = "#DC2626";

const skills = [
  { skill: "SQL", demand: 72, growth: 18, jobs: 4820, role: "Data Analyst", status: "Growing" },
  { skill: "Python", demand: 68, growth: 12, jobs: 4350, role: "Data Scientist", status: "Growing" },
  { skill: "Excel", demand: 61, growth: 2, jobs: 3960, role: "Business Analyst", status: "Stable" },
  { skill: "Power BI", demand: 55, growth: 21, jobs: 3210, role: "BI Analyst", status: "Growing" },
  { skill: "AWS", demand: 49, growth: 25, jobs: 2890, role: "Cloud Engineer", status: "Growing" },
  { skill: "JavaScript", demand: 46, growth: 4, jobs: 2640, role: "Frontend Developer", status: "Stable" },
  { skill: "Tableau", demand: 39, growth: -3, jobs: 2015, role: "Data Analyst", status: "Declining" },
  { skill: "Machine Learning", demand: 35, growth: 15, jobs: 1840, role: "ML Engineer", status: "Growing" },
  { skill: "Docker", demand: 33, growth: 19, jobs: 1710, role: "DevOps Engineer", status: "Growing" },
  { skill: "R", demand: 21, growth: -6, jobs: 980, role: "Data Analyst", status: "Declining" },
];

const statusStyle = {
  Growing: { bg: "rgba(22,163,74,0.1)", fg: SUCCESS, Icon: ArrowUpRight },
  Stable: { bg: "rgba(102,112,133,0.1)", fg: TEXT_SECONDARY, Icon: Minus },
  Declining: { bg: "rgba(220,38,38,0.1)", fg: ERROR, Icon: ArrowDownRight },
};

const filterGroups = [
  { label: "Country", options: ["All countries", "Kenya", "Nigeria", "South Africa", "Ghana"] },
  { label: "Industry", options: ["All industries", "Fintech", "E-commerce", "Health Tech", "Agritech"] },
  { label: "Job role", options: ["All roles", "Data Analyst", "Data Scientist", "Cloud Engineer"] },
  { label: "Experience level", options: ["Any level", "Entry", "Mid", "Senior"] },
  { label: "Time period", options: ["Last 6 months", "Last 30 days", "Last 3 months", "Last year"] },
];

function FilterDropdown({ label, options }) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(options[0]);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium"
        style={{ borderColor: "#E4E9F2", color: TEXT_DARK, background: "#fff" }}
      >
        <span style={{ color: TEXT_SECONDARY }}>{label}:</span>
        {value}
        <ChevronDown size={13} style={{ color: TEXT_SECONDARY }} />
      </button>
      {open && (
        <div
          className="absolute left-0 z-20 mt-1 w-48 overflow-hidden rounded-lg border bg-white shadow-lg"
          style={{ borderColor: "#E4E9F2" }}
        >
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => {
                setValue(opt);
                setOpen(false);
              }}
              className="block w-full px-3 py-2 text-left text-xs hover:bg-[#F7F9FC]"
              style={{
                color: opt === value ? DEEP_BLUE : TEXT_DARK,
                fontWeight: opt === value ? 600 : 400,
              }}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function DemandBar({ value }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full" style={{ background: "#EEF2F7" }}>
        <div
          className="h-full rounded-full"
          style={{ width: `${value}%`, background: NAVY }}
        />
      </div>
      <span className="text-xs font-semibold" style={{ color: TEXT_DARK }}>
        {value}%
      </span>
    </div>
  );
}

export default function MarketSkills() {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState("demand");
  const [showFilters, setShowFilters] = useState(false);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const rows = q ? skills.filter((s) => s.skill.toLowerCase().includes(q)) : skills;
    return [...rows].sort((a, b) => b[sortKey] - a[sortKey]);
  }, [query, sortKey]);

  return (
    <div className="min-h-screen w-full" style={{ background: PAGE_BG, fontFamily: "Inter, sans-serif" }}>
      <div className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
        <h1
          className="text-2xl font-semibold sm:text-[28px]"
          style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
        >
          African tech skills intelligence
        </h1>
        <p className="mt-1.5 max-w-lg text-sm" style={{ color: TEXT_SECONDARY }}>
          Discover the skills employers are demanding across Africa.
        </p>

        {/* Search + filter toggle */}
        <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
          <div
            className="flex flex-1 items-center gap-2 rounded-lg border px-3.5 py-2.5"
            style={{ borderColor: "#E4E9F2", background: "#fff" }}
          >
            <Search size={16} style={{ color: TEXT_SECONDARY }} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search a skill..."
              className="w-full bg-transparent text-sm outline-none"
              style={{ color: TEXT_DARK }}
            />
          </div>
          <button
            onClick={() => setShowFilters((s) => !s)}
            className="flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium"
            style={{
              borderColor: showFilters ? DEEP_BLUE : "#E4E9F2",
              color: showFilters ? DEEP_BLUE : TEXT_DARK,
              background: "#fff",
            }}
          >
            <SlidersHorizontal size={15} />
            Filters
          </button>
        </div>

        {showFilters && (
          <div className="mt-3 flex flex-wrap gap-2">
            {filterGroups.map((g) => (
              <FilterDropdown key={g.label} label={g.label} options={g.options} />
            ))}
          </div>
        )}

        {/* Table */}
        <div
          className="mt-7 overflow-hidden rounded-2xl border"
          style={{ borderColor: "#E4E9F2", background: "#fff" }}
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr style={{ background: PAGE_BG }}>
                  <th className="px-5 py-3 text-xs font-medium" style={{ color: TEXT_SECONDARY }}>
                    Skill
                  </th>
                  <th
                    className="cursor-pointer px-5 py-3 text-xs font-medium"
                    style={{ color: TEXT_SECONDARY }}
                    onClick={() => setSortKey("demand")}
                  >
                    Demand {sortKey === "demand" && "↓"}
                  </th>
                  <th
                    className="cursor-pointer px-5 py-3 text-xs font-medium"
                    style={{ color: TEXT_SECONDARY }}
                    onClick={() => setSortKey("growth")}
                  >
                    Growth {sortKey === "growth" && "↓"}
                  </th>
                  <th
                    className="cursor-pointer px-5 py-3 text-xs font-medium"
                    style={{ color: TEXT_SECONDARY }}
                    onClick={() => setSortKey("jobs")}
                  >
                    Jobs {sortKey === "jobs" && "↓"}
                  </th>
                  <th className="px-5 py-3 text-xs font-medium" style={{ color: TEXT_SECONDARY }}>
                    Popular role
                  </th>
                  <th className="px-5 py-3 text-xs font-medium" style={{ color: TEXT_SECONDARY }}>
                    Trend
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, i) => {
                  const { bg, fg, Icon } = statusStyle[row.status];
                  return (
                    <tr
                      key={row.skill}
                      style={{
                        borderTop: "1px solid #EEF2F7",
                        background: i % 2 === 1 ? "#FBFCFE" : "#fff",
                      }}
                    >
                      <td className="px-5 py-4 font-semibold" style={{ color: TEXT_DARK }}>
                        {row.skill}
                      </td>
                      <td className="px-5 py-4">
                        <DemandBar value={row.demand} />
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className="flex items-center gap-1 text-xs font-semibold"
                          style={{ color: row.growth >= 0 ? SUCCESS : ERROR }}
                        >
                          {row.growth >= 0 ? (
                            <ArrowUpRight size={13} />
                          ) : (
                            <ArrowDownRight size={13} />
                          )}
                          {row.growth >= 0 ? "+" : ""}
                          {row.growth}%
                        </span>
                      </td>
                      <td className="px-5 py-4" style={{ color: TEXT_DARK }}>
                        {row.jobs.toLocaleString()}
                      </td>
                      <td className="px-5 py-4" style={{ color: TEXT_SECONDARY }}>
                        {row.role}
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium"
                          style={{ background: bg, color: fg }}
                        >
                          <Icon size={11} />
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-5 py-10 text-center text-sm" style={{ color: TEXT_SECONDARY }}>
                      No skills match "{query}".
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <p className="mt-3 text-xs" style={{ color: TEXT_SECONDARY }}>
          Showing {filtered.length} of {skills.length} tracked skills
        </p>
      </div>
    </div>
  );
}
