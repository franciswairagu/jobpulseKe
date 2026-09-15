import React, { useState, useCallback, useEffect } from "react";
import { Search, SlidersHorizontal, ArrowUpRight, ArrowDownRight, Minus, X } from "lucide-react";
import { COLORS, FONTS, AFRICAN_COUNTRIES } from "../lib/theme";
import Dropdown from "../components/shared/Dropdown";
import LoadingState from "../components/shared/LoadingState";
import EmptyState from "../components/shared/EmptyState";
import { getMarketSkills } from "../api/client";
import { useAsync } from "../hooks/useAsync";

const STATUS_STYLE = {
  Growing: { bg: "rgba(16,185,129,0.1)", fg: "#059669", Icon: ArrowUpRight },
  Stable: { bg: "rgba(100,116,139,0.1)", fg: COLORS.textSecondary, Icon: Minus },
  Declining: { bg: "rgba(239,68,68,0.1)", fg: COLORS.error, Icon: ArrowDownRight },
};

function DemandBar({ value }) {
  const color = value >= 60 ? "#FA510F" : value >= 30 ? "#FF7A3D" : "#93C5FD";
  return (
    <div className="flex items-center gap-2.5">
      <div className="h-2 w-20 overflow-hidden rounded-full" style={{ background: COLORS.surfaceTertiary }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${value}%`,
            background: `linear-gradient(90deg, ${color}cc, ${color})`,
          }}
        />
      </div>
      <span className="text-xs font-bold" style={{ color: COLORS.textDark }}>{value}%</span>
    </div>
  );
}

export default function MarketSkillsPage({ initialQuery = "" }) {
  const [query, setQuery] = useState(initialQuery);
  const [sortKey, setSortKey] = useState("demand");
  const [country, setCountry] = useState("All countries");
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery);
    }
  }, [initialQuery]);

  const fetcher = useCallback(() => getMarketSkills({ query, sortKey, country }), [query, sortKey, country]);
  const { status, data, error, refetch } = useAsync(fetcher, [query, sortKey, country]);

  return (
    <div>
      <div className="mb-7">
        <h1
          className="text-2xl font-bold sm:text-3xl"
          style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
        >
          African tech skills intelligence
        </h1>
        <p className="mt-2 max-w-lg text-sm" style={{ color: COLORS.textSecondary }}>
          Discover the skills employers are demanding across Africa.
        </p>
      </div>

      {/* Search & filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div
          className="flex flex-1 items-center gap-3 rounded-xl border px-4 py-3 transition-all duration-200 focus-within:border-accent focus-within:shadow-glow-blue"
          style={{ borderColor: COLORS.border, background: "#fff" }}
        >
          <Search size={16} style={{ color: COLORS.textMuted }} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search a skill..."
            className="w-full bg-transparent text-sm outline-none placeholder:text-textMuted"
            style={{ color: COLORS.textDark }}
          />
          {query && (
            <button onClick={() => setQuery("")} className="rounded-md p-1 hover:bg-surface-tertiary">
              <X size={14} style={{ color: COLORS.textMuted }} />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowFilters((s) => !s)}
          className="flex items-center justify-center gap-2 rounded-xl border px-4 py-3 text-sm font-medium transition-all duration-200"
          style={{
            borderColor: showFilters ? COLORS.accent : COLORS.border,
            color: showFilters ? COLORS.accent : COLORS.textDark,
            background: showFilters ? "rgba(250,81,15,0.05)" : "#fff",
          }}
        >
          <SlidersHorizontal size={15} /> Filters
        </button>
      </div>

      {showFilters && (
        <div className="mt-3 flex flex-wrap gap-2 animate-fade-in-down">
          <Dropdown label="Country" value={country} options={["All countries", ...AFRICAN_COUNTRIES]} onChange={setCountry} />
        </div>
      )}

      {/* Table */}
      <div className="mt-6">
        {status === "loading" && <LoadingState label="Loading skill demand data..." />}
        {status === "error" && (
          <EmptyState
            tone="error"
            title="Couldn't load skills data"
            description={error?.message}
            action={
              <button
                onClick={refetch}
                className="mt-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white"
                style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
              >
                Retry
              </button>
            }
          />
        )}
        {status === "success" && (
          <div
            className="overflow-hidden rounded-2xl border animate-fade-in"
            style={{ borderColor: COLORS.border, background: "#fff" }}
          >
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead>
                  <tr style={{ background: COLORS.pageBg }}>
                    {[
                      { key: "skill", label: "Skill" },
                      { key: "demand", label: "Demand", sortable: true },
                      { key: "growth", label: "Growth", sortable: true },
                      { key: "jobs", label: "Jobs", sortable: true },
                      { key: "role", label: "Popular role" },
                      { key: "status", label: "Trend" },
                    ].map((col) => (
                      <th
                        key={col.key}
                        className={`px-5 py-3.5 text-xs font-semibold uppercase tracking-wider ${col.sortable ? "cursor-pointer hover:text-accent" : ""}`}
                        style={{ color: COLORS.textMuted }}
                        onClick={col.sortable ? () => setSortKey(col.key) : undefined}
                      >
                        {col.label}
                        {col.sortable && sortKey === col.key && (
                          <span className="ml-1 text-accent">↓</span>
                        )}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.skills.map((row, i) => {
                    const { bg, fg, Icon } = STATUS_STYLE[row.status];
                    return (
                      <tr
                        key={row.skill}
                        className="transition-colors hover:bg-surface-secondary"
                        style={{
                          borderTop: `1px solid ${COLORS.borderLight}`,
                        }}
                      >
                        <td className="px-5 py-4 font-semibold" style={{ color: COLORS.textDark }}>
                          {row.skill}
                        </td>
                        <td className="px-5 py-4">
                          <DemandBar value={row.demand} />
                        </td>
                        <td className="px-5 py-4">
                          <span
                            className="flex items-center gap-1 text-xs font-bold"
                            style={{ color: row.growth >= 0 ? "#059669" : COLORS.error }}
                          >
                            {row.growth >= 0 ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
                            {row.growth >= 0 ? "+" : ""}{row.growth}%
                          </span>
                        </td>
                        <td className="px-5 py-4 font-medium" style={{ color: COLORS.textDark }}>
                          {row.jobs.toLocaleString()}
                        </td>
                        <td className="px-5 py-4" style={{ color: COLORS.textSecondary }}>
                          {row.role}
                        </td>
                        <td className="px-5 py-4">
                          <span
                            className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium"
                            style={{ background: bg, color: fg }}
                          >
                            <Icon size={11} /> {row.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                  {data.skills.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-5 py-12 text-center text-sm" style={{ color: COLORS.textSecondary }}>
                        No skills match "{query}".
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {status === "success" && (
          <p className="mt-3 text-xs" style={{ color: COLORS.textMuted }}>
            Showing {data.skills.length} tracked skills · updated {data.dataSource.collectedAt}
          </p>
        )}
      </div>
    </div>
  );
}
