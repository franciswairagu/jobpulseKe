import React, { useState, useCallback } from "react";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertTriangle,
  X,
  ArrowRight,
  Loader2,
} from "lucide-react";
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  Legend,
} from "recharts";

const NAVY = "#0B1F3A";
const DEEP_BLUE = "#123B63";
const LIGHT_BLUE = "#EAF3FA";
const PAGE_BG = "#F7F9FC";
const TEXT_DARK = "#172033";
const TEXT_SECONDARY = "#667085";
const SUCCESS = "#16A34A";
const WARNING = "#F59E0B";
const ERROR = "#DC2626";

const foundSkills = ["Python", "SQL", "Excel", "Pandas", "Power BI"];

const missingSkills = [
  {
    name: "SQL Optimization",
    demand: 72,
    postings: 4820,
    difficulty: "Medium",
    priority: "HIGH",
  },
  {
    name: "AWS",
    demand: 49,
    postings: 2890,
    difficulty: "Medium",
    priority: "HIGH",
  },
  {
    name: "Docker",
    demand: 38,
    postings: 2110,
    difficulty: "Medium",
    priority: "MEDIUM",
  },
  {
    name: "Power BI",
    demand: 55,
    postings: 3210,
    difficulty: "Low",
    priority: "MEDIUM",
  },
  {
    name: "Machine Learning",
    demand: 35,
    postings: 1840,
    difficulty: "High",
    priority: "LOW",
  },
];

const radarData = [
  { category: "Programming", you: 80, market: 70 },
  { category: "Databases", you: 35, market: 78 },
  { category: "Cloud", you: 15, market: 60 },
  { category: "Data Analytics", you: 75, market: 72 },
  { category: "Machine Learning", you: 20, market: 45 },
  { category: "Visualization", you: 70, market: 65 },
  { category: "Soft Skills", you: 60, market: 55 },
];

const loadingSteps = [
  "Extracting skills...",
  "Comparing with job market data...",
  "Identifying skill gaps...",
  "Generating career insights...",
];

const priorityColor = {
  HIGH: { bg: "rgba(220,38,38,0.1)", fg: ERROR },
  MEDIUM: { bg: "rgba(245,158,11,0.12)", fg: "#B45309" },
  LOW: { bg: "rgba(22,163,74,0.1)", fg: SUCCESS },
};

function UploadArea({ onFile }) {
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState(null);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) setFileName(file.name);
    },
    []
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 text-center transition-colors"
      style={{
        borderColor: dragging ? DEEP_BLUE : "#CBD5E1",
        background: dragging ? LIGHT_BLUE : "#fff",
      }}
    >
      <div
        className="mb-4 flex h-14 w-14 items-center justify-center rounded-full"
        style={{ background: LIGHT_BLUE }}
      >
        <UploadCloud size={26} style={{ color: DEEP_BLUE }} />
      </div>

      {fileName ? (
        <div className="flex items-center gap-2 rounded-lg border px-4 py-2" style={{ borderColor: "#E4E9F2" }}>
          <FileText size={16} style={{ color: DEEP_BLUE }} />
          <span className="text-sm font-medium" style={{ color: TEXT_DARK }}>
            {fileName}
          </span>
          <button onClick={() => setFileName(null)}>
            <X size={14} style={{ color: TEXT_SECONDARY }} />
          </button>
        </div>
      ) : (
        <>
          <p
            className="text-base font-semibold"
            style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
          >
            Drag & drop your CV here
          </p>
          <p className="mt-1 text-sm" style={{ color: TEXT_SECONDARY }}>
            or{" "}
            <label className="cursor-pointer font-medium underline" style={{ color: DEEP_BLUE }}>
              browse files
              <input
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) setFileName(f.name);
                }}
              />
            </label>
          </p>
          <p className="mt-4 text-xs" style={{ color: TEXT_SECONDARY }}>
            Supports PDF, DOCX · Maximum file size 10MB
          </p>
        </>
      )}

      <button
        disabled={!fileName}
        onClick={() => fileName && onFile(fileName)}
        className="mt-6 rounded-lg px-6 py-2.5 text-sm font-semibold text-white transition-opacity"
        style={{
          background: fileName ? NAVY : "#CBD5E1",
          cursor: fileName ? "pointer" : "not-allowed",
        }}
      >
        Analyze CV
      </button>
    </div>
  );
}

function LoadingState() {
  const [stepIndex, setStepIndex] = useState(0);

  React.useEffect(() => {
    if (stepIndex >= loadingSteps.length - 1) return;
    const t = setTimeout(() => setStepIndex((i) => i + 1), 900);
    return () => clearTimeout(t);
  }, [stepIndex]);

  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border px-6 py-16" style={{ borderColor: "#E4E9F2", background: "#fff" }}>
      <Loader2 size={30} className="mb-5 animate-spin" style={{ color: DEEP_BLUE }} />
      <div className="flex flex-col gap-2.5">
        {loadingSteps.map((step, i) => (
          <div key={step} className="flex items-center gap-2 text-sm">
            {i < stepIndex ? (
              <CheckCircle2 size={15} style={{ color: SUCCESS }} />
            ) : i === stepIndex ? (
              <Loader2 size={15} className="animate-spin" style={{ color: DEEP_BLUE }} />
            ) : (
              <div className="h-[15px] w-[15px] rounded-full border" style={{ borderColor: "#CBD5E1" }} />
            )}
            <span
              style={{
                color: i <= stepIndex ? TEXT_DARK : TEXT_SECONDARY,
                fontWeight: i === stepIndex ? 600 : 400,
              }}
            >
              {step}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ResultsView() {
  return (
    <div className="flex flex-col gap-6">
      {/* Overall match */}
      <div
        className="flex flex-col items-start gap-5 rounded-2xl p-6 sm:flex-row sm:items-center sm:justify-between"
        style={{ background: NAVY }}
      >
        <div>
          <p className="text-xs font-medium" style={{ color: "rgba(234,243,250,0.65)" }}>
            Overall market match
          </p>
          <p
            className="mt-1 text-4xl font-semibold text-white"
            style={{ fontFamily: "Space Grotesk, sans-serif" }}
          >
            78%
          </p>
          <p className="mt-1 max-w-sm text-sm" style={{ color: "rgba(234,243,250,0.75)" }}>
            Your CV matches the current market requirements for your selected
            career path.
          </p>
        </div>
        <button
          className="flex items-center gap-1.5 whitespace-nowrap rounded-lg bg-white px-5 py-2.5 text-sm font-semibold"
          style={{ color: NAVY }}
        >
          View career path <ArrowRight size={14} />
        </button>
      </div>

      {/* Found + missing */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-2" style={{ borderColor: "#E4E9F2", background: "#fff" }}>
          <h3
            className="mb-1 text-base font-semibold"
            style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
          >
            Skills found in your CV
          </h3>
          <p className="mb-4 text-xs" style={{ color: TEXT_SECONDARY }}>
            {foundSkills.length} skills detected
          </p>
          <div className="flex flex-wrap gap-2">
            {foundSkills.map((s) => (
              <span
                key={s}
                className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium"
                style={{ background: "rgba(22,163,74,0.1)", color: SUCCESS }}
              >
                <CheckCircle2 size={12} />
                {s}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-3" style={{ borderColor: "#E4E9F2", background: "#fff" }}>
          <h3
            className="mb-1 text-base font-semibold"
            style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
          >
            Skills employers want that you're missing
          </h3>
          <p className="mb-4 text-xs" style={{ color: TEXT_SECONDARY }}>
            Ranked by recommended learning priority
          </p>

          <div className="flex flex-col divide-y" style={{ borderColor: "#EEF2F7" }}>
            {missingSkills.map((skill) => (
              <div key={skill.name} className="flex flex-wrap items-center justify-between gap-3 py-3.5">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold" style={{ color: TEXT_DARK }}>
                      {skill.name}
                    </span>
                    <span
                      className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                      style={{
                        background: priorityColor[skill.priority].bg,
                        color: priorityColor[skill.priority].fg,
                      }}
                    >
                      {skill.priority}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs" style={{ color: TEXT_SECONDARY }}>
                    Demand {skill.demand}% · {skill.postings.toLocaleString()} postings ·{" "}
                    {skill.difficulty} difficulty
                  </p>
                </div>
                <button
                  className="rounded-lg border px-3.5 py-1.5 text-xs font-semibold"
                  style={{ borderColor: DEEP_BLUE, color: DEEP_BLUE }}
                >
                  Learn more
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Radar chart */}
      <div className="rounded-2xl border p-5 sm:p-6" style={{ borderColor: "#E4E9F2", background: "#fff" }}>
        <h3
          className="mb-1 text-base font-semibold"
          style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
        >
          Skill gap visualization
        </h3>
        <p className="mb-2 text-xs" style={{ color: TEXT_SECONDARY }}>
          Your skills against market demand, by category
        </p>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData} outerRadius="70%">
              <PolarGrid stroke="#E4E9F2" />
              <PolarAngleAxis
                dataKey="category"
                tick={{ fontSize: 12, fill: TEXT_DARK, fontFamily: "Inter, sans-serif" }}
              />
              <Radar
                name="Market demand"
                dataKey="market"
                stroke={LIGHT_BLUE}
                fill={DEEP_BLUE}
                fillOpacity={0.15}
                strokeWidth={2}
              />
              <Radar
                name="Your skills"
                dataKey="you"
                stroke={NAVY}
                fill={NAVY}
                fillOpacity={0.35}
                strokeWidth={2}
              />
              <Legend
                wrapperStyle={{ fontSize: 12, fontFamily: "Inter, sans-serif", paddingTop: 12 }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Biggest opportunity */}
      <div
        className="flex flex-col gap-4 rounded-2xl border p-6 sm:flex-row sm:items-center sm:justify-between"
        style={{ borderColor: "#E4E9F2", background: LIGHT_BLUE }}
      >
        <div className="flex items-start gap-3">
          <AlertTriangle size={20} style={{ color: DEEP_BLUE, marginTop: 2 }} />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: DEEP_BLUE }}>
              Your biggest opportunity
            </p>
            <p
              className="mt-1 text-xl font-semibold"
              style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
            >
              SQL
            </p>
            <p className="mt-1 max-w-md text-sm" style={{ color: TEXT_SECONDARY }}>
              SQL appears in 72% of relevant job postings, but it wasn't
              detected in your CV. Recommended path: fundamentals → joins →
              aggregations → window functions → projects.
            </p>
          </div>
        </div>
        <button
          className="whitespace-nowrap rounded-lg px-5 py-2.5 text-sm font-semibold text-white"
          style={{ background: NAVY }}
        >
          Add SQL to my learning goals
        </button>
      </div>
    </div>
  );
}

export default function CVAnalyzer() {
  const [stage, setStage] = useState("upload"); // upload | loading | results

  const handleFile = () => {
    setStage("loading");
    setTimeout(() => setStage("results"), 3600);
  };

  return (
    <div className="min-h-screen w-full" style={{ background: PAGE_BG, fontFamily: "Inter, sans-serif" }}>
      <div className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
        <h1
          className="text-2xl font-semibold sm:text-[28px]"
          style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
        >
          Analyze your CV
        </h1>
        <p className="mt-1.5 max-w-lg text-sm" style={{ color: TEXT_SECONDARY }}>
          Upload your CV to compare your skills with current employer demand
          across the African tech market.
        </p>

        <div className="mt-8">
          {stage === "upload" && <UploadArea onFile={handleFile} />}
          {stage === "loading" && <LoadingState />}
          {stage === "results" && <ResultsView />}
        </div>

        {stage === "results" && (
          <button
            className="mt-6 text-xs font-medium underline"
            style={{ color: TEXT_SECONDARY }}
            onClick={() => setStage("upload")}
          >
            Analyze a different CV
          </button>
        )}
      </div>
    </div>
  );
}
