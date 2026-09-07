import React, { useState, useCallback } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, X, ArrowRight, Loader2 } from "lucide-react";
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend } from "recharts";
import { COLORS, FONTS, PRIORITY_STYLES } from "../lib/theme";
import { analyzeCV } from "../api/client";
import { useCVAnalysisActions, useAppState } from "../state/AppContext";
import EmptyState from "../components/shared/EmptyState";
import RecommendedJobsPanel from "../components/jobs/RecommendedJobsPanel";
import CareerPathsPanel from "../components/career/CareerPathsPanel";
import OpportunityUnlockCard from "../components/skills/OpportunityUnlockCard";

const MAX_SIZE_MB = 10;
const ACCEPTED_EXT = [".pdf", ".docx"];

function validateFile(file) {
  const ext = "." + file.name.split(".").pop().toLowerCase();
  if (!ACCEPTED_EXT.includes(ext)) return "Only PDF and DOCX files are supported.";
  if (file.size === 0) return "This file looks empty. Try re-exporting your CV.";
  if (file.size > MAX_SIZE_MB * 1024 * 1024) return `File is larger than ${MAX_SIZE_MB}MB.`;
  return null;
}

function UploadArea({ onFile }) {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [validationError, setValidationError] = useState(null);

  const acceptFile = (f) => {
    const err = validateFile(f);
    setValidationError(err);
    setFile(err ? null : f);
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) acceptFile(f);
  }, []);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 text-center transition-colors"
      style={{ borderColor: dragging ? COLORS.deepBlue : "#CBD5E1", background: dragging ? COLORS.lightBlue : "#fff" }}
    >
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full" style={{ background: COLORS.lightBlue }}>
        <UploadCloud size={26} style={{ color: COLORS.deepBlue }} />
      </div>

      {file ? (
        <div className="flex items-center gap-2 rounded-lg border px-4 py-2" style={{ borderColor: COLORS.border }}>
          <FileText size={16} style={{ color: COLORS.deepBlue }} />
          <span className="text-sm font-medium" style={{ color: COLORS.textDark }}>{file.name}</span>
          <button onClick={() => setFile(null)}>
            <X size={14} style={{ color: COLORS.textSecondary }} />
          </button>
        </div>
      ) : (
        <>
          <p className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Drag & drop your CV here</p>
          <p className="mt-1 text-sm" style={{ color: COLORS.textSecondary }}>
            or{" "}
            <label className="cursor-pointer font-medium underline" style={{ color: COLORS.deepBlue }}>
              browse files
              <input type="file" accept=".pdf,.docx" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) acceptFile(f); }} />
            </label>
          </p>
          <p className="mt-4 text-xs" style={{ color: COLORS.textSecondary }}>Supports PDF, DOCX · Maximum file size {MAX_SIZE_MB}MB</p>
        </>
      )}

      {validationError && (
        <p className="mt-3 flex items-center gap-1.5 text-xs font-medium" style={{ color: COLORS.error }}>
          <AlertTriangle size={13} /> {validationError}
        </p>
      )}

      <button
        disabled={!file}
        onClick={() => file && onFile(file)}
        className="mt-6 rounded-lg px-6 py-2.5 text-sm font-semibold text-white transition-opacity"
        style={{ background: file ? COLORS.navy : "#CBD5E1", cursor: file ? "pointer" : "not-allowed" }}
      >
        Analyze CV
      </button>
    </div>
  );
}

function AnalysisLoadingState({ stage }) {
  const stages = ["Extracting document", "Parsing profile", "Comparing with market data", "Calculating skill gaps", "Generating recommendations"];
  const stepIndex = Math.max(0, stages.indexOf(stage));
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border px-6 py-16" style={{ borderColor: COLORS.border, background: "#fff" }}>
      <Loader2 size={30} className="mb-5 animate-spin" style={{ color: COLORS.deepBlue }} />
      <div className="flex flex-col gap-2.5">
        {stages.map((step, i) => (
          <div key={step} className="flex items-center gap-2 text-sm">
            {i < stepIndex ? <CheckCircle2 size={15} style={{ color: COLORS.success }} /> : i === stepIndex ? <Loader2 size={15} className="animate-spin" style={{ color: COLORS.deepBlue }} /> : <div className="h-[15px] w-[15px] rounded-full border" style={{ borderColor: "#CBD5E1" }} />}
            <span style={{ color: i <= stepIndex ? COLORS.textDark : COLORS.textSecondary, fontWeight: i === stepIndex ? 600 : 400 }}>{step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "jobs", label: "Recommended Jobs" },
  { key: "gaps", label: "Skill Gaps" },
  { key: "careers", label: "Career Paths" },
];

function OverviewTab({ analysis, onGoToJobs, onGoToTab, onAddLearningGoal }) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-start gap-5 rounded-2xl p-6 sm:flex-row sm:items-center sm:justify-between" style={{ background: COLORS.navy }}>
        <div>
          <p className="text-xs font-medium" style={{ color: "rgba(234,243,250,0.65)" }}>Overall market match</p>
          <p className="mt-1 text-4xl font-semibold text-white" style={{ fontFamily: FONTS.display }}>{analysis.overallMatch}%</p>
          <p className="mt-1 max-w-sm text-sm" style={{ color: "rgba(234,243,250,0.75)" }}>
            You're a {analysis.overallMatch}% match for {analysis.profile.currentRole} roles in the current market.
          </p>
        </div>
        <button onClick={onGoToJobs} className="flex items-center gap-1.5 whitespace-nowrap rounded-lg bg-white px-5 py-2.5 text-sm font-semibold" style={{ color: COLORS.navy }}>
          See matching jobs <ArrowRight size={14} />
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-2" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <h3 className="mb-1 text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Skills found in your CV</h3>
          <p className="mb-4 text-xs" style={{ color: COLORS.textSecondary }}>{analysis.foundSkills.length} skills detected</p>
          <div className="flex flex-wrap gap-2">
            {analysis.foundSkills.map((s) => (
              <span key={s} className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium" style={{ background: "rgba(22,163,74,0.1)", color: COLORS.success }}>
                <CheckCircle2 size={12} /> {s}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-3" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <h3 className="mb-1 text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Top skills employers want that you're missing</h3>
          <p className="mb-4 text-xs" style={{ color: COLORS.textSecondary }}>Ranked by recommended learning priority - see the Skill Gaps tab for the full list</p>
          <div className="flex flex-col divide-y" style={{ borderColor: COLORS.rowBorder }}>
            {analysis.missingSkills.slice(0, 3).map((skill) => (
              <div key={skill.name} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold" style={{ color: COLORS.textDark }}>{skill.name}</span>
                  <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: PRIORITY_STYLES[skill.priority].bg, color: PRIORITY_STYLES[skill.priority].fg }}>{skill.priority}</span>
                </div>
                <button onClick={() => onGoToTab("gaps")} className="text-xs font-semibold" style={{ color: COLORS.deepBlue }}>Details</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <OpportunityUnlockCard cvAnalysis={analysis} onExplore={(skill) => onGoToTab("jobs", skill)} />
    </div>
  );
}

function SkillGapsTab({ analysis, onAddLearningGoal }) {
  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-3" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <h3 className="mb-1 text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Skills employers want that you're missing</h3>
        <p className="mb-4 text-xs" style={{ color: COLORS.textSecondary }}>Ranked by recommended learning priority</p>
        <div className="flex flex-col divide-y" style={{ borderColor: COLORS.rowBorder }}>
          {analysis.missingSkills.map((skill) => (
            <div key={skill.name} className="flex flex-wrap items-center justify-between gap-3 py-3.5">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold" style={{ color: COLORS.textDark }}>{skill.name}</span>
                  <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: PRIORITY_STYLES[skill.priority].bg, color: PRIORITY_STYLES[skill.priority].fg }}>{skill.priority}</span>
                </div>
                <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>
                  Demand {skill.demand}% · {skill.postings.toLocaleString()} postings · {skill.difficulty} difficulty
                </p>
              </div>
              <button onClick={() => onAddLearningGoal(skill)} className="rounded-lg border px-3.5 py-1.5 text-xs font-semibold" style={{ borderColor: COLORS.deepBlue, color: COLORS.deepBlue }}>
                Add to learning goals
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border p-5 sm:p-6" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <h3 className="mb-1 text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Skill gap visualization</h3>
        <p className="mb-2 text-xs" style={{ color: COLORS.textSecondary }}>Your skills against market demand, by category</p>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={analysis.radar} outerRadius="70%">
              <PolarGrid stroke={COLORS.border} />
              <PolarAngleAxis dataKey="category" tick={{ fontSize: 12, fill: COLORS.textDark, fontFamily: FONTS.body }} />
              <Radar name="Market demand" dataKey="market" stroke={COLORS.lightBlue} fill={COLORS.deepBlue} fillOpacity={0.15} strokeWidth={2} />
              <Radar name="Your skills" dataKey="you" stroke={COLORS.navy} fill={COLORS.navy} fillOpacity={0.35} strokeWidth={2} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: FONTS.body, paddingTop: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default function CVAnalyzerPage() {
  const [stage, setStage] = useState("upload"); // upload | loading | results | error
  const [analysisStage, setAnalysisStage] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [jobSearchFocus, setJobSearchFocus] = useState(undefined);
  const { cvAnalysis } = useAppState();
  const { setCVAnalysis } = useCVAnalysisActions();

  const handleFile = async (file) => {
    setStage("loading");
    setError(null);
    try {
      const result = await analyzeCV(file, setAnalysisStage);
      setCVAnalysis(result);
      setStage("results");
      setActiveTab("overview");
    } catch (e) {
      setError(e);
      setStage("error");
    }
  };

  const goToTab = (tab, focusSkill) => {
    setActiveTab(tab);
    setJobSearchFocus(focusSkill);
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold sm:text-[28px]" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>CV Analyzer</h1>
      <p className="mt-1.5 max-w-lg text-sm" style={{ color: COLORS.textSecondary }}>
        Upload your CV to see your market match, skill gaps, and the jobs and career paths you're qualified for right now.
      </p>

      <div className="mt-8">
        {stage === "upload" && <UploadArea onFile={handleFile} />}
        {stage === "loading" && <AnalysisLoadingState stage={analysisStage} />}
        {stage === "error" && (
          <EmptyState
            tone="error"
            title="CV analysis failed"
            description={error?.message || "Something went wrong while analyzing your CV. Please try again."}
            action={<button onClick={() => setStage("upload")} className="mt-2 rounded-lg px-4 py-2 text-xs font-semibold text-white" style={{ background: COLORS.navy }}>Try again</button>}
          />
        )}

        {stage === "results" && cvAnalysis && (
          <div>
            <div className="mb-6 flex gap-1 overflow-x-auto border-b" style={{ borderColor: COLORS.border }}>
              {TABS.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setActiveTab(t.key)}
                  className="whitespace-nowrap px-3 py-2.5 text-sm font-medium"
                  style={{
                    color: activeTab === t.key ? COLORS.navy : COLORS.textSecondary,
                    borderBottom: activeTab === t.key ? `2px solid ${COLORS.navy}` : "2px solid transparent",
                    fontWeight: activeTab === t.key ? 600 : 500,
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {activeTab === "overview" && (
              <OverviewTab analysis={cvAnalysis} onGoToJobs={() => goToTab("jobs")} onGoToTab={goToTab} />
            )}
            {activeTab === "jobs" && (
              <RecommendedJobsPanel cvAnalysis={cvAnalysis} initialFocusSkill={jobSearchFocus} onAddLearningGoal={() => {}} />
            )}
            {activeTab === "gaps" && <SkillGapsTab analysis={cvAnalysis} onAddLearningGoal={() => {}} />}
            {activeTab === "careers" && <CareerPathsPanel cvAnalysis={cvAnalysis} />}
          </div>
        )}
      </div>

      {stage === "results" && (
        <button className="mt-6 text-xs font-medium underline" style={{ color: COLORS.textSecondary }} onClick={() => setStage("upload")}>
          Analyze a different CV
        </button>
      )}
    </div>
  );
}
