import React, { useState, useEffect } from "react";
import { TrendingUp, MapPin, Wifi, Compass, Loader2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { COLORS, FONTS } from "../lib/theme";
import { getCareerInsights } from "../api/client";
import { useAppState } from "../state/AppContext";

const SENIORITY_ORDER = ["Intern", "Entry Level", "Mid-Level", "Senior", "Lead", "Executive"];

const CATEGORY_LABELS = {
  programming_language: "Programming",
  web_framework: "Web Frameworks",
  cloud_platform: "Cloud",
  database: "Databases",
  ai_ml: "AI / ML",
  devops: "DevOps",
  data_platform: "Data Platforms",
  analytics: "Analytics",
  frontend: "Frontend",
  architecture: "Architecture",
  methodology: "Methodologies",
  testing: "Testing",
  mobile: "Mobile",
  security: "Security",
  infrastructure: "Infrastructure",
};

const CATEGORY_COLORS = {
  programming_language: "#FA510F",
  web_framework: "#8B5CF6",
  cloud_platform: "#F59E0B",
  database: "#10B981",
  ai_ml: "#EF4444",
  devops: "#6366F1",
  data_platform: "#14B8A6",
  analytics: "#F97316",
  frontend: "#EC4899",
  architecture: "#64748B",
  methodology: "#84CC16",
  testing: "#06B6D4",
  mobile: "#A855F7",
  security: "#DC2626",
  infrastructure: "#78716C",
};

function InsightCard({ icon: Icon, title, subtitle, iconBg, iconColor, children }) {
  return (
    <div
      className="rounded-2xl border p-5 sm:p-6 transition-all duration-300 hover-lift"
      style={{ borderColor: COLORS.border, background: "#fff" }}
    >
      <div className="mb-4 flex items-center gap-3">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-xl"
          style={{ background: iconBg }}
        >
          <Icon size={18} style={{ color: iconColor }} />
        </div>
        <div>
          <h3 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
            {title}
          </h3>
          <p className="text-xs" style={{ color: COLORS.textSecondary }}>
            {subtitle}
          </p>
        </div>
      </div>
      {children}
    </div>
  );
}

function CareerProgressionMap({ data }) {
  const { seniority_progression, user_seniority, experience_by_seniority } = data;
  const total = Object.values(seniority_progression).reduce((a, b) => a + b, 0);
  const userIdx = SENIORITY_ORDER.indexOf(user_seniority);

  return (
    <InsightCard icon={TrendingUp} title="Career Progression" subtitle="Where you sit on the seniority ladder" iconBg="rgba(250,81,15,0.1)" iconColor="#FA510F">
      <div className="space-y-3">
        {SENIORITY_ORDER.map((level, i) => {
          const count = seniority_progression[level] || 0;
          const pct = total > 0 ? (count / total) * 100 : 0;
          const isCurrent = level === user_seniority;
          const isPast = i < userIdx;
          const exp = experience_by_seniority?.[level];
          const expLabel = exp ? Object.entries(exp).filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1])[0]?.[0] : null;

          return (
            <div key={level} className="flex items-center gap-3">
              <div className="w-24 shrink-0 text-right">
                <span className="text-xs font-semibold" style={{ color: isCurrent ? COLORS.accent : isPast ? "#059669" : COLORS.textMuted }}>
                  {level}
                </span>
                {isCurrent && <span className="ml-1 text-[10px] font-bold text-accent">(you)</span>}
              </div>
              <div className="relative h-7 flex-1 overflow-hidden rounded-full" style={{ background: COLORS.surfaceTertiary }}>
                <div
                  className="absolute inset-y-0 left-0 rounded-full transition-all duration-700"
                  style={{
                    width: `${pct}%`,
                    background: isCurrent
                      ? "linear-gradient(90deg, #FA510F, #E04500)"
                      : isPast
                      ? "linear-gradient(90deg, #10B981, #059669)"
                      : "#CBD5E1",
                    minWidth: count > 0 ? "8px" : "0",
                  }}
                />
              </div>
              <div className="w-20 shrink-0">
                <span className="text-xs font-medium" style={{ color: COLORS.textSecondary }}>
                  {count.toLocaleString()} jobs
                </span>
              </div>
              <div className="w-24 shrink-0">
                {expLabel && (
                  <span className="text-[10px] font-medium" style={{ color: COLORS.textMuted }}>
                    {expLabel}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </InsightCard>
  );
}

function SkillsByLevelPanel({ data, hasCV }) {
  const { skills_by_seniority, user_seniority, next_level, skill_gaps_next_level } = data;
  const currentSkills = skills_by_seniority[user_seniority] || {};
  const nextSkills = next_level ? skills_by_seniority[next_level] || {} : {};

  const chartData = Object.entries(currentSkills)
    .map(([cat, count]) => ({
      name: CATEGORY_LABELS[cat] || cat,
      current: count,
      next: nextSkills[cat] || 0,
      color: CATEGORY_COLORS[cat] || "#94A3B8",
    }))
    .sort((a, b) => b.current - a.current)
    .slice(0, 8);

  return (
    <InsightCard icon={TrendingUp} title="Skills by Level" subtitle={`${user_seniority} skill distribution ${next_level ? `→ ${next_level}` : ""}`} iconBg="rgba(139,92,246,0.1)" iconColor="#8B5CF6">
      {chartData.length > 0 ? (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 20 }}>
              <XAxis type="number" tick={{ fontSize: 10, fill: COLORS.textMuted }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: COLORS.textDark }} width={90} />
              <Tooltip
                contentStyle={{ borderRadius: 12, border: `1px solid ${COLORS.border}`, fontSize: 12, boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }}
                formatter={(value, name) => [value, name === "current" ? user_seniority : next_level || "Next"]}
              />
              <Bar dataKey="current" radius={[0, 6, 6, 0]} barSize={14}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
              {next_level && <Bar dataKey="next" radius={[0, 6, 6, 0]} barSize={14} fill="#E2E8F0" />}
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="py-8 text-center text-sm" style={{ color: COLORS.textSecondary }}>
          {hasCV ? "No skill distribution data available" : "Upload your CV to see skill distribution"}
        </p>
      )}

      {next_level && Object.keys(skill_gaps_next_level).length > 0 && (
        <div className="mt-4 rounded-xl p-3" style={{ background: "rgba(139,92,246,0.05)" }}>
          <p className="text-xs font-semibold" style={{ color: "#7C3AED" }}>
            To reach {next_level}, build these areas:
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {Object.entries(skill_gaps_next_level).map(([cat, gap]) => (
              <span key={cat} className="rounded-full px-2.5 py-1 text-[10px] font-medium" style={{ background: "rgba(139,92,246,0.1)", color: "#7C3AED" }}>
                {CATEGORY_LABELS[cat] || cat} (+{gap})
              </span>
            ))}
          </div>
        </div>
      )}
    </InsightCard>
  );
}

function GeographicDemandPanel({ data, hasCV }) {
  const { skill_demand_by_country } = data;

  const countryTotals = {};
  for (const [, regions] of Object.entries(skill_demand_by_country)) {
    for (const [country, count] of Object.entries(regions)) {
      countryTotals[country] = (countryTotals[country] || 0) + count;
    }
  }

  const sorted = Object.entries(countryTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  return (
    <InsightCard icon={MapPin} title="Where Your Skills Are In Demand" subtitle="Countries with demand for your skill set" iconBg="rgba(16,185,129,0.1)" iconColor="#10B981">
      {sorted.length > 0 ? (
        <div className="space-y-2.5">
          {sorted.map(([country, count]) => (
            <div key={country} className="flex items-center gap-3">
              <span className="w-32 shrink-0 text-xs font-semibold" style={{ color: COLORS.textDark }}>
                {country}
              </span>
              <div className="relative h-5 flex-1 overflow-hidden rounded-full" style={{ background: COLORS.surfaceTertiary }}>
                <div
                  className="absolute inset-y-0 left-0 rounded-full"
                  style={{
                    width: `${(count / sorted[0][1]) * 100}%`,
                    background: country === "Global Remote"
                      ? "linear-gradient(90deg, #8B5CF6, #7C3AED)"
                      : "linear-gradient(90deg, #10B981, #059669)",
                    minWidth: "6px",
                  }}
                />
              </div>
              <span className="w-12 shrink-0 text-right text-[10px] font-medium" style={{ color: COLORS.textMuted }}>
                {count}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p className="py-8 text-center text-sm" style={{ color: COLORS.textSecondary }}>
          {hasCV ? "No geographic demand data available" : "Upload your CV to see geographic demand"}
        </p>
      )}
    </InsightCard>
  );
}

function RemoteOpportunityPanel({ data }) {
  const { remote_by_seniority, user_seniority, user_remote_stats, remote_by_category, overall_remote } = data;

  const seniorityData = SENIORITY_ORDER.map((level) => {
    const stats = remote_by_seniority[level] || {};
    return {
      name: level,
      remote: stats.remote_pct || 0,
      isCurrent: level === user_seniority,
    };
  });

  const topCategories = Object.entries(remote_by_category)
    .map(([cat, stats]) => ({
      name: CATEGORY_LABELS[cat] || cat,
      pct: stats.remote_pct || 0,
    }))
    .sort((a, b) => b.pct - a.pct)
    .slice(0, 6);

  return (
    <InsightCard icon={Wifi} title="Remote Opportunity Score" subtitle="Remote work availability by level" iconBg="rgba(249,115,22,0.1)" iconColor="#F97316">
      {user_remote_stats && (
        <div className="mb-4 rounded-xl p-3" style={{ background: "rgba(249,115,22,0.05)" }}>
          <p className="text-sm" style={{ color: COLORS.textDark }}>
            As a <span className="font-semibold">{user_seniority}</span> developer,{" "}
            <span className="font-bold" style={{ color: "#F97316" }}>{user_remote_stats.remote_pct || 0}%</span> of matching roles are remote.
          </p>
          <p className="mt-1 text-xs" style={{ color: COLORS.textMuted }}>
            Overall market remote rate: {overall_remote.remote_pct || 0}%
          </p>
        </div>
      )}

      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={seniorityData} margin={{ left: -10, right: 10 }}>
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: COLORS.textMuted }} />
            <YAxis tick={{ fontSize: 10, fill: COLORS.textMuted }} unit="%" />
            <Tooltip
              contentStyle={{ borderRadius: 12, border: `1px solid ${COLORS.border}`, fontSize: 12, boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }}
              formatter={(value) => [`${value.toFixed(1)}%`, "Remote"]}
            />
            <Bar dataKey="remote" radius={[6, 6, 0, 0]} barSize={28}>
              {seniorityData.map((entry, i) => (
                <Cell key={i} fill={entry.isCurrent ? "#F97316" : "#E2E8F0"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {topCategories.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-semibold" style={{ color: COLORS.textMuted }}>Highest remote by skill category</p>
          <div className="flex flex-wrap gap-1.5">
            {topCategories.map((cat) => (
              <span key={cat.name} className="rounded-full px-2.5 py-1 text-[10px] font-medium" style={{ background: "rgba(249,115,22,0.1)", color: "#F97316" }}>
                {cat.name}: {cat.pct.toFixed(0)}%
              </span>
            ))}
          </div>
        </div>
      )}
    </InsightCard>
  );
}

export default function CareerInsightsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { cvAnalysis } = useAppState();

  useEffect(() => {
    let cancelled = false;
    getCareerInsights()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load career insights");
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-2xl border p-16" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <Loader2 size={24} className="animate-spin" style={{ color: COLORS.accent }} />
        <span className="ml-3 text-sm" style={{ color: COLORS.textSecondary }}>Loading career insights...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border p-8 text-center" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <Compass size={32} style={{ color: COLORS.textMuted, margin: "0 auto 12px" }} />
        <p className="text-sm" style={{ color: COLORS.textSecondary }}>{error}</p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      <div className="mb-7">
        <h1 className="text-2xl font-bold sm:text-3xl" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
          Career Insights
        </h1>
        <p className="mt-2 max-w-lg text-sm" style={{ color: COLORS.textSecondary }}>
          Understand your career progression, skill distribution, and where opportunities exist across Africa.
        </p>
      </div>

      {!cvAnalysis && (
        <div className="mb-6 rounded-2xl border p-6 text-center" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <Compass size={28} style={{ color: COLORS.textMuted, margin: "0 auto 10px" }} />
          <p className="text-sm font-medium" style={{ color: COLORS.textDark }}>Upload your CV for personalized insights</p>
          <p className="mt-1 text-xs" style={{ color: COLORS.textSecondary }}>
            Go to <span className="font-semibold">CV Analyzer</span> to upload your CV and unlock tailored career recommendations.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 stagger-children">
        <CareerProgressionMap data={data} />
        <SkillsByLevelPanel data={data} hasCV={!!cvAnalysis} />
        <GeographicDemandPanel data={data} hasCV={!!cvAnalysis} />
        <RemoteOpportunityPanel data={data} />
      </div>
    </div>
  );
}
