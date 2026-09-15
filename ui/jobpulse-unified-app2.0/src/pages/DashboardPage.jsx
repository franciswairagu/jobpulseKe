import React, { useCallback, useEffect, useState } from "react";
import {
  ArrowUpRight, TrendingUp, Wifi, BarChart3, ChevronRight, Sparkles,
  MapPin, ArrowUp, ArrowDown, Globe,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  LineChart, Line, CartesianGrid,
} from "recharts";
import { COLORS, FONTS, AFRICAN_COUNTRIES, PERIODS } from "../lib/theme";
import Dropdown from "../components/shared/Dropdown";
import LoadingState from "../components/shared/LoadingState";
import EmptyState from "../components/shared/EmptyState";
import { getDashboard, getSkillTrend } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAppState, useFilters } from "../state/AppContext";

function PulseLine({ color = COLORS.accent, opacity = 1, height = 20 }) {
  return (
    <svg viewBox="0 0 240 20" width="100%" height={height} preserveAspectRatio="none" style={{ opacity }}>
      <defs>
        <linearGradient id="pulseGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="50%" stopColor={color} stopOpacity={1} />
          <stop offset="100%" stopColor={color} stopOpacity="0.2" />
        </linearGradient>
      </defs>
      <polyline points="0,10 40,10 52,2 64,18 76,10 100,10 112,4 124,16 136,10 240,10" fill="none" stroke="url(#pulseGrad)" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div
      className="animate-scale-in"
      style={{
        background: "rgba(16,31,60,0.95)",
        backdropFilter: "blur(8px)",
        color: "#fff",
        padding: "10px 14px",
        borderRadius: "12px",
        fontSize: "13px",
        fontFamily: FONTS.body,
        boxShadow: "0 8px 24px rgba(0,0,0,0.2)",
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 2 }}>{label}</div>
      <div style={{ color: "#FF7A3D" }}>{payload[0].value}% of postings</div>
    </div>
  );
}

function CircularReadiness({ percent = 0, size = 140 }) {
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (percent / 100) * c;
  const color = percent >= 70 ? "#10B981" : percent >= 40 ? "#F59E0B" : "#EF4444";

  return (
    <div className="relative">
      <svg width={size} height={size} className="shrink-0">
        <defs>
          <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FA510F" />
            <stop offset="100%" stopColor={color} />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={COLORS.border} strokeWidth={stroke} opacity={0.3} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="url(#gaugeGrad)" strokeWidth={stroke} strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round" transform={`rotate(-90 ${size / 2} ${size / 2})`} style={{ transition: "stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1)" }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>{percent}%</span>
        <span className="text-xs font-medium" style={{ color: COLORS.textMuted }}>match</span>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, detail, accent = false }) {
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl p-5 transition-all duration-300 hover-lift ${accent ? "" : "border"}`}
      style={{
        background: accent ? "linear-gradient(135deg, #101F3C 0%, #1a2d4a 100%)" : "#fff",
        borderColor: accent ? "transparent" : COLORS.border,
      }}
    >
      {accent && (
        <div className="absolute inset-0 opacity-20">
          <PulseLine color="rgba(96,165,250,0.5)" height={60} />
        </div>
      )}
      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ background: accent ? "rgba(255,255,255,0.1)" : "rgba(250,81,15,0.08)" }}>
            <Icon size={16} style={{ color: accent ? "#FF7A3D" : COLORS.accent }} />
          </div>
          <p className="text-xs font-medium" style={{ color: accent ? "rgba(234,243,250,0.6)" : COLORS.textSecondary }}>{label}</p>
        </div>
        <p className="text-2xl font-bold mt-1" style={{ color: accent ? "#fff" : COLORS.textDark, fontFamily: FONTS.display }}>{value}</p>
        {detail && <p className="text-xs mt-1" style={{ color: accent ? "rgba(234,243,250,0.5)" : COLORS.textMuted }}>{detail}</p>}
      </div>
    </div>
  );
}

function JobCard({ job }) {
  return (
    <a
      href={job.sourceUrl || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="flex-shrink-0 w-64 rounded-xl border p-4 transition-all hover:shadow-md hover:-translate-y-0.5"
      style={{ borderColor: COLORS.border, background: "#fff" }}
    >
      <p className="text-sm font-semibold truncate" style={{ color: COLORS.textDark }}>{job.title}</p>
      <p className="text-xs mt-1 truncate" style={{ color: COLORS.textSecondary }}>{job.company}</p>
      <div className="mt-3 flex items-center gap-2">
        <MapPin size={11} style={{ color: COLORS.textMuted }} />
        <span className="text-[11px]" style={{ color: COLORS.textMuted }}>{job.country}{job.city ? `, ${job.city}` : ""}</span>
        {job.remote && (
          <span className="ml-auto rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ background: COLORS.successLight, color: "#059669" }}>Remote</span>
        )}
      </div>
      {job.skillNames?.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1">
          {job.skillNames.slice(0, 3).map((s) => (
            <span key={s} className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ background: COLORS.lightBlue, color: COLORS.accent }}>{s}</span>
          ))}
        </div>
      )}
    </a>
  );
}

export default function DashboardPage({ onNavigate }) {
  const { cvAnalysis } = useAppState();
  const { filters, setFilters } = useFilters();
  const [skillTrend, setSkillTrend] = useState({ skill: "", growthRate: 0, points: [] });
  const [selectedSkill, setSelectedSkill] = useState(null);

  const fetcher = useCallback(() => getDashboard({ region: filters.region, period: filters.period }), [filters.region, filters.period]);
  const { status, data, error, refetch } = useAsync(fetcher, [filters.region, filters.period]);

  // Fetch skill trend when top skill is known or selected skill changes
  useEffect(() => {
    const skill = selectedSkill || data?.trendingSkills?.[0]?.skill;
    if (skill && skill !== "N/A") {
      getSkillTrend(skill, 12).then(setSkillTrend).catch(() => {});
    }
  }, [selectedSkill, data?.trendingSkills?.[0]?.skill]);

  if (status === "loading") return <LoadingState label="Loading your market snapshot..." />;
  if (status === "error") {
    return (
      <EmptyState
        tone="error"
        title="Couldn't load dashboard data"
        description={error?.message || "The market data service didn't respond. Try again."}
        action={
          <button onClick={refetch} className="mt-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition-all hover:scale-105" style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}>
            Retry
          </button>
        }
      />
    );
  }

  const { snapshot, trendingSkills, dataSource, weeklyActivity, topCountries, recentJobs } = data;
  const highlightSkillTrend = skillTrend.points.length > 0 ? skillTrend : { skill: trendingSkills[0]?.skill || "N/A", growthRate: 0, points: [] };

  return (
    <div className="space-y-6">
      {/* Welcome hero */}
      <div className="relative overflow-hidden rounded-3xl px-8 py-8 sm:px-10 sm:py-10" style={{ background: "linear-gradient(135deg, #101F3C 0%, #1a2d4a 50%, #101F3C 100%)" }}>
        <div className="absolute inset-0 opacity-20"><PulseLine color="rgba(96,165,250,0.6)" height={120} /></div>
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-accent/10 blur-3xl" />
        <div className="absolute -bottom-20 -left-20 h-48 w-48 rounded-full bg-emerald-500/10 blur-3xl" />
        <div className="relative z-10 max-w-lg">
          <h1 className="text-2xl font-bold text-white sm:text-3xl" style={{ fontFamily: FONTS.display, lineHeight: 1.2 }}>
            Your career intelligence dashboard
          </h1>
          <p className="mt-3 text-sm leading-relaxed" style={{ color: "rgba(234,243,250,0.7)" }}>
            See how your skills compare with what African tech employers are looking for.
          </p>
          <button
            onClick={() => onNavigate("cv-analyzer")}
            className="group mt-6 flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold transition-all duration-300 hover:shadow-glow-blue hover:scale-[1.02]"
            style={{ background: "linear-gradient(135deg, #FA510F, #E04500)", color: "#fff", boxShadow: "0 4px 14px rgba(250,81,15,0.3)" }}
          >
            <Sparkles size={16} />
            {cvAnalysis ? "Re-analyze CV" : "Upload your CV"}
            <ChevronRight size={16} className="transition-transform group-hover:translate-x-1" />
          </button>
        </div>
      </div>

      {/* Data source + filters */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-1">
        <div className="flex items-center gap-2">
          <div className="pulse-dot" style={{ background: COLORS.success }} />
          <p className="text-xs" style={{ color: COLORS.textMuted }}>
            {dataSource.sampleSize.toLocaleString()} postings tracked · {dataSource.collectedAt}
          </p>
        </div>
        <div className="flex gap-2">
          <Dropdown value={filters.region} options={["All Africa", ...AFRICAN_COUNTRIES]} onChange={(region) => setFilters({ region })} />
          <Dropdown value={filters.period} options={PERIODS} onChange={(period) => setFilters({ period })} />
        </div>
      </div>

      {/* Stats grid — 6 cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6 stagger-children">
        <StatCard icon={TrendingUp} label="Top skill" value={snapshot.mostDemandedSkill.name} detail={snapshot.mostDemandedSkill.detail} accent />
        <StatCard icon={Wifi} label="Remote" value={`${snapshot.remotePct}%`} detail="of listings" />
        <StatCard icon={BarChart3} label="Total jobs" value={dataSource.sampleSize.toLocaleString()} detail="across Africa" />
        <StatCard icon={ArrowUp} label="Added this week" value={weeklyActivity.added} detail="new postings" />
        <StatCard icon={ArrowDown} label="Removed" value={weeklyActivity.removed} detail="expired" />
        <StatCard icon={Globe} label="Top country" value={topCountries[0]?.country || "N/A"} detail={`${topCountries[0]?.count || 0} jobs`} />
      </div>

      {/* Top countries bar */}
      {topCountries.length > 0 && (
        <div className="rounded-2xl border p-4" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <h3 className="text-sm font-semibold mb-3" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
            Where the jobs are
          </h3>
          <div className="flex flex-wrap gap-2">
            {topCountries.map((c) => (
              <div key={c.country} className="flex items-center gap-2 rounded-full border px-3 py-1.5" style={{ borderColor: COLORS.border }}>
                <span className="text-xs font-medium" style={{ color: COLORS.textDark }}>{c.country}</span>
                <span className="text-[11px] font-bold px-1.5 py-0.5 rounded-full" style={{ background: COLORS.lightBlue, color: COLORS.accent }}>{c.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Trending skills bar chart */}
        <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-3" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <div className="mb-1 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>What employers want</h2>
              <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>Most requested skills across African tech postings</p>
            </div>
          </div>
          <div className="mt-4 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendingSkills} layout="vertical" margin={{ top: 4, right: 24, left: 4, bottom: 4 }} barCategoryGap={14}>
                <defs>
                  <linearGradient id="barGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#FA510F" />
                    <stop offset="100%" stopColor="#E04500" />
                  </linearGradient>
                </defs>
                <XAxis type="number" domain={[0, 80]} hide />
                <YAxis type="category" dataKey="skill" width={110} tickLine={false} axisLine={false} tick={{ fontSize: 12.5, fill: COLORS.textDark, fontFamily: FONTS.body }} />
                <Tooltip cursor={{ fill: "rgba(250,81,15,0.04)" }} content={<CustomTooltip />} />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={18} fill="url(#barGrad)" onClick={(data) => setSelectedSkill(data.skill)} style={{ cursor: "pointer" }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Skill trend line chart */}
        <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-2" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <div className="mb-1 flex items-start justify-between">
            <div>
              <h2 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>{highlightSkillTrend.skill} demand</h2>
              <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>Demand over the selected period</p>
            </div>
            <button onClick={() => onNavigate("skill-demand")} className="flex items-center gap-1 text-xs font-semibold transition-colors hover:text-accent" style={{ color: COLORS.accent }}>
              View all <ChevronRight size={12} />
            </button>
          </div>
          <div className="mt-3 inline-flex items-baseline gap-2 rounded-xl px-3 py-1.5" style={{ background: COLORS.lightBlue }}>
            <span className="text-xl font-bold" style={{ color: highlightSkillTrend.growthRate >= 0 ? COLORS.success : COLORS.error, fontFamily: FONTS.display }}>
              {highlightSkillTrend.growthRate >= 0 ? "+" : ""}{highlightSkillTrend.growthRate}%
            </span>
            <span className="text-xs" style={{ color: COLORS.accent }}>demand change</span>
          </div>
          <div className="mt-4 h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={highlightSkillTrend.points} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="lineGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#FA510F" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#FA510F" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke={COLORS.borderLight} strokeDasharray="3 3" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fontSize: 11.5, fill: COLORS.textMuted, fontFamily: FONTS.body }} />
                <YAxis hide domain={["dataMin - 10", "dataMax + 10"]} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="value" stroke="#FA510F" strokeWidth={2.5} dot={{ r: 4, fill: "#FA510F", strokeWidth: 2, stroke: "#fff" }} activeDot={{ r: 6, strokeWidth: 2, stroke: "#fff" }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent jobs */}
      {recentJobs.length > 0 && (
        <div className="rounded-2xl border p-5 sm:p-6" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Recent job openings</h2>
            <button onClick={() => onNavigate("skill-demand")} className="flex items-center gap-1 text-xs font-semibold" style={{ color: COLORS.accent }}>
              View all <ChevronRight size={12} />
            </button>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1" style={{ scrollbarWidth: "thin" }}>
            {recentJobs.slice(0, 6).map((job) => <JobCard key={job.id} job={job} />)}
          </div>
        </div>
      )}

      {/* Market readiness */}
      <div className="rounded-2xl border p-5 sm:p-6" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <h2 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Your market readiness</h2>
        {cvAnalysis ? (
          <>
            <div className="mt-5 flex flex-col gap-6 sm:flex-row sm:items-center">
              <div className="flex items-center gap-6">
                <CircularReadiness percent={cvAnalysis.overallMatch} />
                <p className="max-w-xs text-sm leading-relaxed" style={{ color: COLORS.textSecondary }}>
                  Your skill profile matches <span style={{ color: COLORS.textDark, fontWeight: 700 }}>{cvAnalysis.overallMatch}%</span> of skills for {cvAnalysis.profile.currentRole} roles.
                </p>
              </div>
              <div className="h-px w-full sm:h-20 sm:w-px" style={{ background: COLORS.border }} />
              <div className="grid flex-1 grid-cols-1 gap-5 sm:grid-cols-2">
                <div>
                  <p className="mb-2.5 text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>Strong skills</p>
                  <div className="flex flex-wrap gap-2">
                    {cvAnalysis.foundSkills.map((s) => (
                      <span key={s} className="rounded-full px-3 py-1.5 text-xs font-medium" style={{ background: COLORS.successLight, color: "#059669" }}>{s}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="mb-2.5 text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>Skills to improve</p>
                  <div className="flex flex-wrap gap-2">
                    {cvAnalysis.missingSkills.slice(0, 3).map((s) => (
                      <span key={s.name} className="rounded-full px-3 py-1.5 text-xs font-medium" style={{ background: COLORS.warningLight, color: "#D97706" }}>{s.name}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <button onClick={() => onNavigate("cv-analyzer")} className="mt-6 rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition-all hover:scale-105" style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}>
              View full skill gap analysis
            </button>
          </>
        ) : (
          <div className="mt-4 flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="max-w-md text-sm leading-relaxed" style={{ color: COLORS.textSecondary }}>
              Upload your CV to see your personal market-readiness score and skill gaps.
            </p>
            <button onClick={() => onNavigate("cv-analyzer")} className="whitespace-nowrap rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition-all hover:scale-105" style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}>
              Analyze my CV
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
