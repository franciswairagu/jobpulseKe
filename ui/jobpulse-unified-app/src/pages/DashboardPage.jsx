import React, { useCallback } from "react";
import { ArrowUpRight, ChevronDown } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line, CartesianGrid } from "recharts";
import { COLORS, FONTS, AFRICAN_COUNTRIES, PERIODS } from "../lib/theme";
import Dropdown from "../components/shared/Dropdown";
import LoadingState from "../components/shared/LoadingState";
import EmptyState from "../components/shared/EmptyState";
import { getDashboard } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAppState, useFilters } from "../state/AppContext";

function PulseLine({ color = COLORS.deepBlue, opacity = 1, height = 20 }) {
  return (
    <svg viewBox="0 0 240 20" width="100%" height={height} preserveAspectRatio="none" style={{ opacity }}>
      <polyline points="0,10 40,10 52,2 64,18 76,10 100,10 112,4 124,16 136,10 240,10" fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

function CustomBarTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div style={{ background: COLORS.navy, color: "#fff", padding: "8px 12px", borderRadius: 8, fontSize: 13, fontFamily: FONTS.body }}>
      <div style={{ fontWeight: 600 }}>{label}</div>
      <div style={{ color: COLORS.lightBlue }}>{payload[0].value}% of postings</div>
    </div>
  );
}

function CircularReadiness({ percent = 0, size = 128 }) {
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (percent / 100) * c;
  return (
    <svg width={size} height={size} className="shrink-0">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={COLORS.lightBlue} strokeWidth={stroke} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={COLORS.navy} strokeWidth={stroke} strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round" transform={`rotate(-90 ${size / 2} ${size / 2})`} style={{ transition: "stroke-dashoffset 0.6s ease" }} />
      <text x="50%" y="47%" textAnchor="middle" dominantBaseline="middle" style={{ fontFamily: FONTS.display, fontSize: 30, fontWeight: 700, fill: COLORS.textDark }}>{percent}%</text>
      <text x="50%" y="66%" textAnchor="middle" dominantBaseline="middle" style={{ fontFamily: FONTS.body, fontSize: 11, fill: COLORS.textSecondary }}>match</text>
    </svg>
  );
}

export default function DashboardPage({ onNavigate }) {
  const { cvAnalysis } = useAppState();
  const { filters, setFilters } = useFilters();

  const fetcher = useCallback(() => getDashboard({ region: filters.region, period: filters.period }), [filters.region, filters.period]);
  const { status, data, error, refetch } = useAsync(fetcher, [filters.region, filters.period]);

  if (status === "loading") return <LoadingState label="Loading your market snapshot..." />;
  if (status === "error") {
    return (
      <EmptyState
        tone="error"
        title="Couldn't load dashboard data"
        description={error?.message || "The market data service didn't respond. Try again."}
        action={<button onClick={refetch} className="mt-2 rounded-lg px-4 py-2 text-xs font-semibold text-white" style={{ background: COLORS.navy }}>Retry</button>}
      />
    );
  }

  const { snapshot, trendingSkills, highlightSkillTrend, dataSource } = data;

  return (
    <div>
      {/* Welcome card */}
      <div className="relative mb-7 overflow-hidden rounded-2xl px-6 py-7 sm:px-8" style={{ background: COLORS.navy }}>
        <div className="relative z-10 max-w-lg">
          <h1 className="text-2xl font-semibold text-white sm:text-[28px]" style={{ fontFamily: FONTS.display, lineHeight: 1.2 }}>
            Your career intelligence dashboard
          </h1>
          <p className="mt-2 text-sm" style={{ color: "rgba(234,243,250,0.75)" }}>
            See how your skills compare with what African tech employers are looking for.
          </p>
          <button onClick={() => onNavigate("cv-analyzer")} className="mt-5 rounded-lg px-5 py-2.5 text-sm font-semibold transition-opacity hover:opacity-90" style={{ background: "#fff", color: COLORS.navy }}>
            {cvAnalysis ? "Re-analyze CV" : "Analyze CV"}
          </button>
        </div>
        <div className="pointer-events-none absolute inset-y-0 right-0 hidden w-64 items-center opacity-40 sm:flex">
          <PulseLine color={COLORS.lightBlue} height={90} />
        </div>
      </div>

      <p className="mb-3 text-xs" style={{ color: COLORS.textSecondary }}>
        Market data collected {dataSource.collectedAt} · {dataSource.sampleSize.toLocaleString()} postings tracked
      </p>

      {/* Market snapshot */}
      <div className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl p-5 sm:col-span-2 lg:col-span-1" style={{ background: COLORS.navy }}>
          <p className="text-xs font-medium" style={{ color: "rgba(234,243,250,0.6)" }}>Most demanded skill</p>
          <p className="mt-2 text-3xl font-semibold text-white" style={{ fontFamily: FONTS.display }}>{snapshot.mostDemandedSkill.name}</p>
          <p className="mt-1 text-xs" style={{ color: "rgba(234,243,250,0.6)" }}>{snapshot.mostDemandedSkill.detail}</p>
        </div>
        <div className="rounded-2xl border p-5" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <p className="text-xs font-medium" style={{ color: COLORS.textSecondary }}>Fastest growing skill</p>
          <p className="mt-2 text-2xl font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>{snapshot.fastestGrowingSkill.name}</p>
          <div className="mt-1.5 flex items-center gap-1 text-xs font-medium" style={{ color: COLORS.success }}>
            <ArrowUpRight size={13} /> +{snapshot.fastestGrowingSkill.growthRate}% this period
          </div>
        </div>
        <div className="rounded-2xl border p-5" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <p className="text-xs font-medium" style={{ color: COLORS.textSecondary }}>Average tech salary</p>
          <p className="mt-2 text-2xl font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
            ${snapshot.avgSalary.toLocaleString()}<span className="text-sm font-medium" style={{ color: COLORS.textSecondary }}>/mo</span>
          </p>
        </div>
        <div className="rounded-2xl border p-5" style={{ borderColor: COLORS.border, background: COLORS.lightBlue }}>
          <p className="text-xs font-medium" style={{ color: COLORS.deepBlue }}>Remote opportunities</p>
          <p className="mt-2 text-2xl font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>{snapshot.remotePct}%</p>
          <p className="mt-1.5 text-xs" style={{ color: COLORS.deepBlue }}>of tracked listings</p>
        </div>
      </div>

      {/* Trending skills + trend */}
      <div className="mb-7 grid grid-cols-1 gap-4 lg:grid-cols-5">
        <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-3" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <div className="mb-1 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>What employers want</h2>
              <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>Most frequently requested skills across African tech postings</p>
            </div>
            <div className="flex gap-2">
              <Dropdown value={filters.region} options={["All Africa", ...AFRICAN_COUNTRIES]} onChange={(region) => setFilters({ region })} />
              <Dropdown value={filters.period} options={PERIODS} onChange={(period) => setFilters({ period })} />
            </div>
          </div>
          <div className="mt-4 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendingSkills} layout="vertical" margin={{ top: 4, right: 24, left: 4, bottom: 4 }} barCategoryGap={14}>
                <XAxis type="number" domain={[0, 80]} hide />
                <YAxis type="category" dataKey="skill" width={110} tickLine={false} axisLine={false} tick={{ fontSize: 12.5, fill: COLORS.textDark, fontFamily: FONTS.body }} />
                <Tooltip cursor={{ fill: "rgba(11,31,58,0.04)" }} content={<CustomBarTooltip />} />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={16} fill={COLORS.deepBlue} onClick={() => onNavigate("skill-demand")} style={{ cursor: "pointer" }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-2" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <div className="mb-1 flex items-start justify-between">
            <div>
              <h2 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>{highlightSkillTrend.skill} demand</h2>
              <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>Demand over the selected period</p>
            </div>
            <button onClick={() => onNavigate("skill-demand")} className="flex items-center gap-1 text-xs font-medium" style={{ color: COLORS.deepBlue }}>
              View all skills <ChevronDown size={12} />
            </button>
          </div>
          <div className="mt-3 inline-flex items-baseline gap-2 rounded-lg px-3 py-1.5" style={{ background: COLORS.lightBlue }}>
            <span className="text-xl font-semibold" style={{ color: highlightSkillTrend.growthRate >= 0 ? COLORS.success : COLORS.error, fontFamily: FONTS.display }}>
              {highlightSkillTrend.growthRate >= 0 ? "+" : ""}{highlightSkillTrend.growthRate}%
            </span>
            <span className="text-xs" style={{ color: COLORS.deepBlue }}>demand change</span>
          </div>
          <div className="mt-4 h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={highlightSkillTrend.points} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke={COLORS.rowBorder} />
                <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fontSize: 11.5, fill: COLORS.textSecondary, fontFamily: FONTS.body }} />
                <YAxis hide domain={["dataMin - 10", "dataMax + 10"]} />
                <Tooltip content={<CustomBarTooltip />} />
                <Line type="monotone" dataKey="value" stroke={COLORS.navy} strokeWidth={2.5} dot={{ r: 3, fill: COLORS.navy }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Personalized readiness (real once CV analyzed, prompt otherwise) */}
      <div className="rounded-2xl border p-5 sm:p-6" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <h2 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Your market readiness</h2>

        {cvAnalysis ? (
          <>
            <div className="mt-4 flex flex-col gap-6 sm:flex-row sm:items-center">
              <div className="flex items-center gap-5">
                <CircularReadiness percent={cvAnalysis.overallMatch} />
                <p className="max-w-xs text-sm" style={{ color: COLORS.textSecondary }}>
                  Your current skill profile matches approximately{" "}
                  <span style={{ color: COLORS.textDark, fontWeight: 600 }}>{cvAnalysis.overallMatch}%</span> of the skills commonly requested for {cvAnalysis.profile.currentRole} roles.
                </p>
              </div>
              <div className="h-px w-full sm:h-16 sm:w-px" style={{ background: COLORS.border }} />
              <div className="grid flex-1 grid-cols-1 gap-5 sm:grid-cols-2">
                <div>
                  <p className="mb-2 text-xs font-medium" style={{ color: COLORS.textSecondary }}>Strong skills</p>
                  <div className="flex flex-wrap gap-2">
                    {cvAnalysis.foundSkills.map((s) => (
                      <span key={s} className="rounded-full px-3 py-1 text-xs font-medium" style={{ background: "rgba(22,163,74,0.1)", color: COLORS.success }}>{s}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="mb-2 text-xs font-medium" style={{ color: COLORS.textSecondary }}>Skills to improve</p>
                  <div className="flex flex-wrap gap-2">
                    {cvAnalysis.missingSkills.slice(0, 3).map((s) => (
                      <span key={s.name} className="rounded-full px-3 py-1 text-xs font-medium" style={{ background: "rgba(245,158,11,0.12)", color: "#B45309" }}>{s.name}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <button onClick={() => onNavigate("cv-analyzer")} className="mt-6 rounded-lg px-4 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90" style={{ background: COLORS.navy }}>
              View full skill gap analysis
            </button>
          </>
        ) : (
          <div className="mt-4 flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="max-w-md text-sm" style={{ color: COLORS.textSecondary }}>
              Upload your CV to see your personal market-readiness score, strong skills and skill gaps here instead of general market stats.
            </p>
            <button onClick={() => onNavigate("cv-analyzer")} className="whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-semibold text-white" style={{ background: COLORS.navy }}>
              Analyze my CV
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
