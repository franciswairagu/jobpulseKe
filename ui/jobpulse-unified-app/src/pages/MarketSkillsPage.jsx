import React, { useState, useCallback } from "react";
import { Search, SlidersHorizontal, ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import { COLORS, FONTS, AFRICAN_COUNTRIES } from "../lib/theme";
import Dropdown from "../components/shared/Dropdown";
import LoadingState from "../components/shared/LoadingState";
import EmptyState from "../components/shared/EmptyState";
import { getMarketSkills } from "../api/client";
import { useAsync } from "../hooks/useAsync";

const STATUS_STYLE = {
  Growing: { bg: "rgba(22,163,74,0.1)", fg: COLORS.success, Icon: ArrowUpRight },
  Stable: { bg: "rgba(102,112,133,0.1)", fg: COLORS.textSecondary, Icon: Minus },
  Declining: { bg: "rgba(220,38,38,0.1)", fg: COLORS.error, Icon: ArrowDownRight },
};

function DemandBar({ value }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full" style={{ background: COLORS.rowBorder }}>
        <div className="h-full rounded-full" style={{ width: `${value}%`, background: COLORS.navy }} />
      </div>
      <span className="text-xs font-semibold" style={{ color: COLORS.textDark }}>{value}%</span>
    </div>
  );
}

export default function MarketSkillsPage() {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState("demand");
  const [country, setCountry] = useState("All countries");
  const [showFilters, setShowFilters] = useState(false);

  const fetcher = useCallback(() => getMarketSkills({ query, sortKey, country }), [query, sortKey, country]);
  const { status, data, error, refetch } = useAsync(fetcher, [query, sortKey, country]);

  return (
    <div>
      <h1 className="text-2xl font-semibold sm:text-[28px]" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>African tech skills intelligence</h1>
      <p className="mt-1.5 max-w-lg text-sm" style={{ color: COLORS.textSecondary }}>Discover the skills employers are demanding across Africa.</p>

      <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex flex-1 items-center gap-2 rounded-lg border px-3.5 py-2.5" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <Search size={16} style={{ color: COLORS.textSecondary }} />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search a skill..." className="w-full bg-transparent text-sm outline-none" style={{ color: COLORS.textDark }} />
        </div>
        <button onClick={() => setShowFilters((s) => !s)} className="flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium" style={{ borderColor: showFilters ? COLORS.deepBlue : COLORS.border, color: showFilters ? COLORS.deepBlue : COLORS.textDark, background: "#fff" }}>
          <SlidersHorizontal size={15} /> Filters
        </button>
      </div>

      {showFilters && (
        <div className="mt-3 flex flex-wrap gap-2">
          <Dropdown label="Country" value={country} options={["All countries", ...AFRICAN_COUNTRIES]} onChange={setCountry} />
        </div>
      )}

      <div className="mt-7">
        {status === "loading" && <LoadingState label="Loading skill demand data..." />}
        {status === "error" && (
          <EmptyState tone="error" title="Couldn't load skills data" description={error?.message} action={<button onClick={refetch} className="mt-2 rounded-lg px-4 py-2 text-xs font-semibold text-white" style={{ background: COLORS.navy }}>Retry</button>} />
        )}
        {status === "success" && (
          <div className="overflow-hidden rounded-2xl border" style={{ borderColor: COLORS.border, background: "#fff" }}>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead>
                  <tr style={{ background: COLORS.pageBg }}>
                    <th className="px-5 py-3 text-xs font-medium" style={{ color: COLORS.textSecondary }}>Skill</th>
                    <th className="cursor-pointer px-5 py-3 text-xs font-medium" style={{ color: COLORS.textSecondary }} onClick={() => setSortKey("demand")}>Demand {sortKey === "demand" && "\u2193"}</th>
                    <th className="cursor-pointer px-5 py-3 text-xs font-medium" style={{ color: COLORS.textSecondary }} onClick={() => setSortKey("growth")}>Growth {sortKey === "growth" && "\u2193"}</th>
                    <th className="cursor-pointer px-5 py-3 text-xs font-medium" style={{ color: COLORS.textSecondary }} onClick={() => setSortKey("jobs")}>Jobs {sortKey === "jobs" && "\u2193"}</th>
                    <th className="cursor-pointer px-5 py-3 text-xs font-medium" style={{ color: COLORS.textSecondary }} onClick={() => setSortKey("avgSalary")}>Avg salary {sortKey === "avgSalary" && "\u2193"}</th>
                    <th className="px-5 py-3 text-xs font-medium" style={{ color: COLORS.textSecondary }}>Popular role</th>
                    <th className="px-5 py-3 text-xs font-medium" style={{ color: COLORS.textSecondary }}>Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {data.skills.map((row, i) => {
                    const { bg, fg, Icon } = STATUS_STYLE[row.status];
                    return (
                      <tr key={row.skill} style={{ borderTop: `1px solid ${COLORS.rowBorder}`, background: i % 2 === 1 ? "#FBFCFE" : "#fff" }}>
                        <td className="px-5 py-4 font-semibold" style={{ color: COLORS.textDark }}>{row.skill}</td>
                        <td className="px-5 py-4"><DemandBar value={row.demand} /></td>
                        <td className="px-5 py-4">
                          <span className="flex items-center gap-1 text-xs font-semibold" style={{ color: row.growth >= 0 ? COLORS.success : COLORS.error }}>
                            {row.growth >= 0 ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
                            {row.growth >= 0 ? "+" : ""}{row.growth}%
                          </span>
                        </td>
                        <td className="px-5 py-4" style={{ color: COLORS.textDark }}>{row.jobs.toLocaleString()}</td>
                        <td className="px-5 py-4" style={{ color: COLORS.textDark }}>${row.avgSalary.toLocaleString()}</td>
                        <td className="px-5 py-4" style={{ color: COLORS.textSecondary }}>{row.role}</td>
                        <td className="px-5 py-4">
                          <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium" style={{ background: bg, color: fg }}>
                            <Icon size={11} /> {row.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                  {data.skills.length === 0 && (
                    <tr><td colSpan={7} className="px-5 py-10 text-center text-sm" style={{ color: COLORS.textSecondary }}>No skills match "{query}".</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {status === "success" && (
          <p className="mt-3 text-xs" style={{ color: COLORS.textSecondary }}>
            Showing {data.skills.length} tracked skills · updated {data.dataSource.collectedAt}
          </p>
        )}
      </div>
    </div>
  );
}
