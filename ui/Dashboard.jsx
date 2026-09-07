import React, { useState } from "react";
import {
  LayoutDashboard,
  FileSearch,
  TrendingUp,
  Briefcase,
  Compass,
  DollarSign,
  Sparkles,
  Settings,
  LogOut,
  User,
  Search,
  Bell,
  ChevronDown,
  ArrowUpRight,
  Menu,
  X,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";

const NAVY = "#0B1F3A";
const DEEP_BLUE = "#123B63";
const LIGHT_BLUE = "#EAF3FA";
const PAGE_BG = "#F7F9FC";
const TEXT_DARK = "#172033";
const TEXT_SECONDARY = "#667085";
const SUCCESS = "#16A34A";
const WARNING = "#F59E0B";

// A small recurring "pulse" waveform — the brand's signature mark,
// used as a quiet divider/texture instead of generic hairlines.
function PulseLine({ color = DEEP_BLUE, opacity = 1, height = 20 }) {
  return (
    <svg
      viewBox="0 0 240 20"
      width="100%"
      height={height}
      preserveAspectRatio="none"
      style={{ opacity }}
    >
      <polyline
        points="0,10 40,10 52,2 64,18 76,10 100,10 112,4 124,16 136,10 240,10"
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

const navItems = [
  { label: "Dashboard", icon: LayoutDashboard, active: true },
  { label: "CV Analyzer", icon: FileSearch },
  { label: "Skill Demand", icon: TrendingUp },
  { label: "Job Market", icon: Briefcase },
  { label: "Career Insights", icon: Compass },
  { label: "Salary Insights", icon: DollarSign },
  { label: "AI Assistant", icon: Sparkles },
];

const trendingSkills = [
  { skill: "SQL", value: 72 },
  { skill: "Python", value: 68 },
  { skill: "Excel", value: 61 },
  { skill: "Power BI", value: 55 },
  { skill: "AWS", value: 49 },
  { skill: "JavaScript", value: 46 },
  { skill: "Tableau", value: 39 },
  { skill: "Machine Learning", value: 35 },
];

const sqlTrend = [
  { month: "Mar", value: 54 },
  { month: "Apr", value: 58 },
  { month: "May", value: 60 },
  { month: "Jun", value: 63 },
  { month: "Jul", value: 67 },
  { month: "Aug", value: 72 },
];

const strongSkills = ["Python", "Excel", "Pandas", "Data Visualization"];
const skillsToImprove = ["SQL", "Power BI", "Cloud Computing"];

const regions = [
  "All Africa",
  "Kenya",
  "Nigeria",
  "South Africa",
  "Ghana",
  "Uganda",
  "Rwanda",
  "Egypt",
];
const periods = ["Last 30 days", "Last 3 months", "Last 6 months", "Last year"];

function CustomBarTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div
      style={{
        background: NAVY,
        color: "#fff",
        padding: "8px 12px",
        borderRadius: 8,
        fontSize: 13,
        fontFamily: "Inter, sans-serif",
      }}
    >
      <div style={{ fontWeight: 600 }}>{label}</div>
      <div style={{ color: LIGHT_BLUE }}>{payload[0].value}% of postings</div>
    </div>
  );
}

function Dropdown({ value, options, onChange }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors"
        style={{
          borderColor: "#E4E9F2",
          color: TEXT_DARK,
          background: "#fff",
          fontFamily: "Inter, sans-serif",
        }}
      >
        {value}
        <ChevronDown size={14} style={{ color: TEXT_SECONDARY }} />
      </button>
      {open && (
        <div
          className="absolute right-0 z-20 mt-1 w-44 overflow-hidden rounded-lg border bg-white shadow-lg"
          style={{ borderColor: "#E4E9F2" }}
        >
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => {
                onChange(opt);
                setOpen(false);
              }}
              className="block w-full px-3 py-2 text-left text-sm hover:bg-[#F7F9FC]"
              style={{
                color: opt === value ? DEEP_BLUE : TEXT_DARK,
                fontWeight: opt === value ? 600 : 400,
                fontFamily: "Inter, sans-serif",
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

function CircularReadiness({ percent = 72, size = 128 }) {
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (percent / 100) * c;
  return (
    <svg width={size} height={size} className="shrink-0">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={LIGHT_BLUE}
        strokeWidth={stroke}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={NAVY}
        strokeWidth={stroke}
        strokeDasharray={c}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 0.6s ease" }}
      />
      <text
        x="50%"
        y="47%"
        textAnchor="middle"
        dominantBaseline="middle"
        style={{
          fontFamily: "Space Grotesk, sans-serif",
          fontSize: 30,
          fontWeight: 700,
          fill: TEXT_DARK,
        }}
      >
        {percent}%
      </text>
      <text
        x="50%"
        y="66%"
        textAnchor="middle"
        dominantBaseline="middle"
        style={{
          fontFamily: "Inter, sans-serif",
          fontSize: 11,
          fill: TEXT_SECONDARY,
        }}
      >
        match
      </text>
    </svg>
  );
}

export default function Dashboard() {
  const [region, setRegion] = useState("All Africa");
  const [period, setPeriod] = useState("Last 6 months");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div
      className="flex min-h-screen w-full"
      style={{ background: PAGE_BG, fontFamily: "Inter, sans-serif" }}
    >
      {/* ---------- Sidebar (desktop) ---------- */}
      <aside
        className="hidden w-64 shrink-0 flex-col justify-between px-5 py-6 lg:flex"
        style={{ background: NAVY }}
      >
        <div>
          <div className="mb-9 flex items-center gap-2 px-1">
            <div
              className="flex h-8 w-8 items-center justify-center rounded-lg"
              style={{ background: "rgba(255,255,255,0.08)" }}
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <polyline
                  points="1,9 5,9 7,3 10,15 12,9 17,9"
                  stroke="#EAF3FA"
                  strokeWidth="1.8"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  fill="none"
                />
              </svg>
            </div>
            <span
              className="text-lg font-semibold tracking-tight text-white"
              style={{ fontFamily: "Space Grotesk, sans-serif" }}
            >
              JobPulse
            </span>
          </div>

          <nav className="flex flex-col gap-1">
            {navItems.map(({ label, icon: Icon, active }) => (
              <button
                key={label}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors"
                style={{
                  background: active ? "rgba(255,255,255,0.09)" : "transparent",
                  color: active ? "#fff" : "rgba(234,243,250,0.65)",
                  fontWeight: active ? 600 : 400,
                }}
              >
                <Icon size={17} strokeWidth={2} />
                {label}
              </button>
            ))}
          </nav>
        </div>

        <div
          className="flex flex-col gap-1 border-t pt-4"
          style={{ borderColor: "rgba(255,255,255,0.1)" }}
        >
          {[
            { label: "Profile", icon: User },
            { label: "Settings", icon: Settings },
            { label: "Logout", icon: LogOut },
          ].map(({ label, icon: Icon }) => (
            <button
              key={label}
              className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors"
              style={{ color: "rgba(234,243,250,0.65)" }}
            >
              <Icon size={17} strokeWidth={2} />
              {label}
            </button>
          ))}
        </div>
      </aside>

      {/* ---------- Mobile nav drawer ---------- */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-30 flex lg:hidden">
          <div className="w-64 px-5 py-6" style={{ background: NAVY }}>
            <div className="mb-8 flex items-center justify-between px-1">
              <span
                className="text-lg font-semibold text-white"
                style={{ fontFamily: "Space Grotesk, sans-serif" }}
              >
                JobPulse
              </span>
              <button onClick={() => setMobileNavOpen(false)}>
                <X size={20} color="#fff" />
              </button>
            </div>
            <nav className="flex flex-col gap-1">
              {navItems.map(({ label, icon: Icon, active }) => (
                <button
                  key={label}
                  className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm"
                  style={{
                    background: active ? "rgba(255,255,255,0.09)" : "transparent",
                    color: active ? "#fff" : "rgba(234,243,250,0.65)",
                    fontWeight: active ? 600 : 400,
                  }}
                >
                  <Icon size={17} />
                  {label}
                </button>
              ))}
            </nav>
          </div>
          <div
            className="flex-1"
            style={{ background: "rgba(11,31,58,0.4)" }}
            onClick={() => setMobileNavOpen(false)}
          />
        </div>
      )}

      {/* ---------- Main content ---------- */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top nav */}
        <header
          className="flex items-center justify-between gap-4 border-b px-5 py-4 lg:px-8"
          style={{ borderColor: "#E4E9F2", background: "#fff" }}
        >
          <div className="flex items-center gap-3">
            <button className="lg:hidden" onClick={() => setMobileNavOpen(true)}>
              <Menu size={22} color={TEXT_DARK} />
            </button>
            <div>
              <p
                className="text-base font-semibold sm:text-lg"
                style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
              >
                Good morning, Alvin
              </p>
              <p className="hidden text-xs sm:block" style={{ color: TEXT_SECONDARY }}>
                Wednesday, September 2
              </p>
            </div>
          </div>

          <div
            className="hidden flex-1 items-center gap-2 rounded-lg border px-3 py-2 md:flex md:max-w-sm"
            style={{ borderColor: "#E4E9F2", background: PAGE_BG }}
          >
            <Search size={16} style={{ color: TEXT_SECONDARY }} />
            <input
              placeholder="Search jobs, skills or companies..."
              className="w-full bg-transparent text-sm outline-none"
              style={{ color: TEXT_DARK }}
            />
          </div>

          <div className="flex items-center gap-4">
            <button className="relative">
              <Bell size={19} style={{ color: TEXT_SECONDARY }} />
              <span
                className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full"
                style={{ background: WARNING }}
              />
            </button>
            <div
              className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold text-white"
              style={{ background: DEEP_BLUE, fontFamily: "Space Grotesk, sans-serif" }}
            >
              A
            </div>
          </div>
        </header>

        <main className="flex-1 px-5 py-6 lg:px-8 lg:py-8">
          {/* Welcome card */}
          <div
            className="relative mb-7 overflow-hidden rounded-2xl px-6 py-7 sm:px-8"
            style={{ background: NAVY }}
          >
            <div className="relative z-10 max-w-lg">
              <h1
                className="text-2xl font-semibold text-white sm:text-[28px]"
                style={{ fontFamily: "Space Grotesk, sans-serif", lineHeight: 1.2 }}
              >
                Your career intelligence dashboard
              </h1>
              <p className="mt-2 text-sm" style={{ color: "rgba(234,243,250,0.75)" }}>
                See how your skills compare with what African tech employers are
                looking for.
              </p>
              <button
                className="mt-5 rounded-lg px-5 py-2.5 text-sm font-semibold transition-opacity hover:opacity-90"
                style={{ background: "#fff", color: NAVY }}
              >
                Analyze CV
              </button>
            </div>
            <div className="pointer-events-none absolute inset-y-0 right-0 hidden w-64 items-center opacity-40 sm:flex">
              <PulseLine color="#EAF3FA" height={90} />
            </div>
          </div>

          {/* Market snapshot — asymmetric bento, not 4 identical cards */}
          <div className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div
              className="rounded-2xl p-5 sm:col-span-2 lg:col-span-1"
              style={{ background: NAVY }}
            >
              <p className="text-xs font-medium" style={{ color: "rgba(234,243,250,0.6)" }}>
                Most demanded skill
              </p>
              <p
                className="mt-2 text-3xl font-semibold text-white"
                style={{ fontFamily: "Space Grotesk, sans-serif" }}
              >
                SQL
              </p>
              <p className="mt-1 text-xs" style={{ color: "rgba(234,243,250,0.6)" }}>
                Requested in 72% of postings
              </p>
            </div>

            <div className="rounded-2xl border p-5" style={{ borderColor: "#E4E9F2", background: "#fff" }}>
              <p className="text-xs font-medium" style={{ color: TEXT_SECONDARY }}>
                Fastest growing skill
              </p>
              <p
                className="mt-2 text-2xl font-semibold"
                style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
              >
                Cloud Computing
              </p>
              <div className="mt-1.5 flex items-center gap-1 text-xs font-medium" style={{ color: SUCCESS }}>
                <ArrowUpRight size={13} /> +25% this period
              </div>
            </div>

            <div className="rounded-2xl border p-5" style={{ borderColor: "#E4E9F2", background: "#fff" }}>
              <p className="text-xs font-medium" style={{ color: TEXT_SECONDARY }}>
                Average tech salary
              </p>
              <p
                className="mt-2 text-2xl font-semibold"
                style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
              >
                $1,850<span className="text-sm font-medium" style={{ color: TEXT_SECONDARY }}>/mo</span>
              </p>
              <div className="mt-1.5 flex items-center gap-1 text-xs font-medium" style={{ color: SUCCESS }}>
                <ArrowUpRight size={13} /> +6.2% vs last period
              </div>
            </div>

            <div className="rounded-2xl border p-5" style={{ borderColor: "#E4E9F2", background: LIGHT_BLUE }}>
              <p className="text-xs font-medium" style={{ color: DEEP_BLUE }}>
                Remote opportunities
              </p>
              <p
                className="mt-2 text-2xl font-semibold"
                style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
              >
                34%
              </p>
              <p className="mt-1.5 text-xs" style={{ color: DEEP_BLUE }}>
                of tracked listings
              </p>
            </div>
          </div>

          {/* Trending skills + skill trend */}
          <div className="mb-7 grid grid-cols-1 gap-4 lg:grid-cols-5">
            {/* What employers want */}
            <div
              className="rounded-2xl border p-5 sm:p-6 lg:col-span-3"
              style={{ borderColor: "#E4E9F2", background: "#fff" }}
            >
              <div className="mb-1 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2
                    className="text-base font-semibold"
                    style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
                  >
                    What employers want
                  </h2>
                  <p className="mt-0.5 text-xs" style={{ color: TEXT_SECONDARY }}>
                    Most frequently requested skills across African tech postings
                  </p>
                </div>
                <div className="flex gap-2">
                  <Dropdown value={region} options={regions} onChange={setRegion} />
                  <Dropdown value={period} options={periods} onChange={setPeriod} />
                </div>
              </div>

              <div className="mt-4 h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={trendingSkills}
                    layout="vertical"
                    margin={{ top: 4, right: 24, left: 4, bottom: 4 }}
                    barCategoryGap={14}
                  >
                    <XAxis type="number" domain={[0, 80]} hide />
                    <YAxis
                      type="category"
                      dataKey="skill"
                      width={110}
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 12.5, fill: TEXT_DARK, fontFamily: "Inter, sans-serif" }}
                    />
                    <Tooltip
                      cursor={{ fill: "rgba(11,31,58,0.04)" }}
                      content={<CustomBarTooltip />}
                    />
                    <Bar
                      dataKey="value"
                      radius={[0, 6, 6, 0]}
                      barSize={16}
                      fill={DEEP_BLUE}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* SQL demand trend */}
            <div
              className="rounded-2xl border p-5 sm:p-6 lg:col-span-2"
              style={{ borderColor: "#E4E9F2", background: "#fff" }}
            >
              <div className="mb-1 flex items-start justify-between">
                <div>
                  <h2
                    className="text-base font-semibold"
                    style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
                  >
                    SQL demand
                  </h2>
                  <p className="mt-0.5 text-xs" style={{ color: TEXT_SECONDARY }}>
                    Demand over the selected period
                  </p>
                </div>
                <button className="flex items-center gap-1 text-xs font-medium" style={{ color: DEEP_BLUE }}>
                  Change skill <ChevronDown size={12} />
                </button>
              </div>

              <div
                className="mt-3 inline-flex items-baseline gap-2 rounded-lg px-3 py-1.5"
                style={{ background: LIGHT_BLUE }}
              >
                <span
                  className="text-xl font-semibold"
                  style={{ color: SUCCESS, fontFamily: "Space Grotesk, sans-serif" }}
                >
                  +18.4%
                </span>
                <span className="text-xs" style={{ color: DEEP_BLUE }}>
                  demand increased
                </span>
              </div>

              <div className="mt-4 h-44 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sqlTrend} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid vertical={false} stroke="#EEF2F7" />
                    <XAxis
                      dataKey="month"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 11.5, fill: TEXT_SECONDARY, fontFamily: "Inter, sans-serif" }}
                    />
                    <YAxis hide domain={[45, 80]} />
                    <Tooltip content={<CustomBarTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={NAVY}
                      strokeWidth={2.5}
                      dot={{ r: 3, fill: NAVY }}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Your market readiness */}
          <div
            className="rounded-2xl border p-5 sm:p-6"
            style={{ borderColor: "#E4E9F2", background: "#fff" }}
          >
            <h2
              className="text-base font-semibold"
              style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
            >
              Your market readiness
            </h2>

            <div className="mt-4 flex flex-col gap-6 sm:flex-row sm:items-center">
              <div className="flex items-center gap-5">
                <CircularReadiness percent={72} />
                <p className="max-w-xs text-sm" style={{ color: TEXT_SECONDARY }}>
                  Your current skill profile matches approximately{" "}
                  <span style={{ color: TEXT_DARK, fontWeight: 600 }}>72%</span> of the
                  skills commonly requested for your target roles.
                </p>
              </div>

              <div className="h-px w-full sm:h-16 sm:w-px" style={{ background: "#E4E9F2" }} />

              <div className="grid flex-1 grid-cols-1 gap-5 sm:grid-cols-2">
                <div>
                  <p className="mb-2 text-xs font-medium" style={{ color: TEXT_SECONDARY }}>
                    Strong skills
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {strongSkills.map((s) => (
                      <span
                        key={s}
                        className="rounded-full px-3 py-1 text-xs font-medium"
                        style={{ background: "rgba(22,163,74,0.1)", color: SUCCESS }}
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="mb-2 text-xs font-medium" style={{ color: TEXT_SECONDARY }}>
                    Skills to improve
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {skillsToImprove.map((s) => (
                      <span
                        key={s}
                        className="rounded-full px-3 py-1 text-xs font-medium"
                        style={{ background: "rgba(245,158,11,0.12)", color: "#B45309" }}
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <button
              className="mt-6 rounded-lg px-4 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
              style={{ background: NAVY }}
            >
              View full skill gap analysis
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}
