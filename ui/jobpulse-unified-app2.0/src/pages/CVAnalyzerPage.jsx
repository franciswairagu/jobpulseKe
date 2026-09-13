import React, { useState, useCallback } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, X, ArrowRight, Loader2, Zap, GraduationCap, ExternalLink, Sparkles } from "lucide-react";
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend } from "recharts";
import { COLORS, FONTS, PRIORITY_STYLES } from "../lib/theme";
import { analyzeCV } from "../api/client";
import { useCVAnalysisActions, useAppState } from "../state/AppContext";
import EmptyState from "../components/shared/EmptyState";
import RecommendedJobsPanel from "../components/jobs/RecommendedJobsPanel";
import CareerPathsPanel from "../components/career/CareerPathsPanel";
import OpportunityUnlockCard from "../components/skills/OpportunityUnlockCard";
import CourseRecommendations from "../components/recommendations/CourseRecommendations";
import InterviewPrepPanel from "../components/recommendations/InterviewPrepPanel";

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
      className="relative flex flex-col items-center justify-center rounded-3xl border-2 border-dashed px-6 py-16 text-center transition-all duration-300 animate-fade-in"
      style={{
        borderColor: dragging ? COLORS.accent : COLORS.border,
        background: dragging ? "rgba(250,81,15,0.03)" : "#fff",
        boxShadow: dragging ? "0 0 0 4px rgba(250,81,15,0.1)" : "none",
      }}
    >
      <div
        className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl transition-transform duration-300"
        style={{
          background: dragging
            ? "linear-gradient(135deg, #FA510F, #E04500)"
            : COLORS.lightBlue,
          transform: dragging ? "scale(1.1)" : "scale(1)",
        }}
      >
        <UploadCloud
          size={28}
          className="transition-colors duration-300"
          style={{ color: dragging ? "#fff" : COLORS.accent }}
        />
      </div>

      {file ? (
        <div className="flex items-center gap-3 rounded-xl border px-4 py-3" style={{ borderColor: COLORS.border }}>
          <FileText size={18} style={{ color: COLORS.accent }} />
          <span className="text-sm font-semibold" style={{ color: COLORS.textDark }}>
            {file.name}
          </span>
          <span className="text-xs" style={{ color: COLORS.textMuted }}>
            {(file.size / 1024 / 1024).toFixed(1)} MB
          </span>
          <button
            onClick={() => setFile(null)}
            className="rounded-lg p-1 hover:bg-surface-tertiary transition-colors"
          >
            <X size={14} style={{ color: COLORS.textMuted }} />
          </button>
        </div>
      ) : (
        <>
          <p
            className="text-lg font-semibold"
            style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
          >
            Drag & drop your CV here
          </p>
          <p className="mt-1.5 text-sm" style={{ color: COLORS.textSecondary }}>
            or{" "}
            <label className="cursor-pointer font-semibold transition-colors hover:text-accent" style={{ color: COLORS.accent }}>
              browse files
              <input
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) acceptFile(f); }}
              />
            </label>
          </p>
          <p className="mt-4 text-xs" style={{ color: COLORS.textMuted }}>
            Supports PDF, DOCX · Maximum file size {MAX_SIZE_MB}MB
          </p>
        </>
      )}

      {validationError && (
        <p
          className="mt-4 flex items-center gap-1.5 text-xs font-medium animate-fade-in"
          style={{ color: COLORS.error }}
        >
          <AlertTriangle size={13} /> {validationError}
        </p>
      )}

      <button
        disabled={!file}
        onClick={() => file && onFile(file)}
        className="mt-6 flex items-center gap-2 rounded-xl px-8 py-3 text-sm font-semibold text-white transition-all duration-300 hover:shadow-glow-blue hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
        style={{
          background: file ? "linear-gradient(135deg, #FA510F, #E04500)" : COLORS.textMuted,
          boxShadow: file ? "0 4px 14px rgba(250,81,15,0.3)" : "none",
        }}
      >
        <Zap size={16} />
        Analyze CV
      </button>
    </div>
  );
}

function AnalysisLoadingState({ stage }) {
  const stages = [
    "Extracting document",
    "Parsing profile",
    "Comparing with market data",
    "Calculating skill gaps",
    "Generating recommendations",
  ];
  const stepIndex = Math.max(0, stages.indexOf(stage));

  return (
    <div
      className="flex flex-col items-center justify-center rounded-3xl border px-6 py-16 animate-fade-in"
      style={{ borderColor: COLORS.border, background: "#fff" }}
    >
      <div className="relative mb-6">
        <div
          className="h-14 w-14 rounded-full"
          style={{
            border: `3px solid ${COLORS.border}`,
            borderTopColor: COLORS.accent,
            animation: "spin 1s linear infinite",
          }}
        />
        <div
          className="absolute inset-0 flex items-center justify-center"
        >
          <div
            className="h-6 w-6 rounded-full"
            style={{
              border: `2px solid transparent`,
              borderTopColor: "rgba(250,81,15,0.3)",
              animation: "spin 1.5s linear infinite reverse",
            }}
          />
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {stages.map((step, i) => (
          <div key={step} className="flex items-center gap-3 text-sm">
            {i < stepIndex ? (
              <CheckCircle2 size={18} style={{ color: COLORS.success }} />
            ) : i === stepIndex ? (
              <Loader2 size={18} className="animate-spin" style={{ color: COLORS.accent }} />
            ) : (
              <div
                className="h-[18px] w-[18px] rounded-full border-2"
                style={{ borderColor: COLORS.border }}
              />
            )}
            <span
              className="transition-colors duration-300"
              style={{
                color: i <= stepIndex ? COLORS.textDark : COLORS.textMuted,
                fontWeight: i === stepIndex ? 600 : 400,
              }}
            >
              {step}
            </span>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

function NonTechCVMessage({ onReset }) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Main message */}
      <div
        className="relative overflow-hidden rounded-2xl p-6 sm:p-8"
        style={{ background: "linear-gradient(135deg, #101F3C, #1a2d4a)" }}
      >
        <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-accent/10 blur-3xl" />
        <div className="relative z-10">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl" style={{ background: "rgba(250,81,15,0.15)" }}>
            <Sparkles size={24} style={{ color: "#FF7A3D" }} />
          </div>
          <h2 className="text-xl font-bold text-white sm:text-2xl" style={{ fontFamily: FONTS.display }}>
            This doesn't look like a tech CV
          </h2>
          <p className="mt-3 max-w-lg text-sm text-white/70 leading-relaxed">
            We noticed your CV doesn't have much in the way of technical skills yet — and that's totally fine! Everyone starts somewhere, and a career in tech is absolutely within reach.
          </p>
        </div>
      </div>

      {/* Bootcamp recommendation */}
      <div
        className="rounded-2xl border p-6 sm:p-8"
        style={{ borderColor: COLORS.border, background: "#fff" }}
      >
        <div className="flex items-start gap-4">
          <div
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
            style={{ background: COLORS.lightBlue }}
          >
            <GraduationCap size={22} style={{ color: COLORS.accent }} />
          </div>
          <div className="flex-1">
            <h3 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
              Ready to break into tech?
            </h3>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: COLORS.textSecondary }}>
              Bootcamps are one of the fastest ways to gain in-demand tech skills and land your first role. Many graduates land jobs within months of completing their program.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <a
                href="https://moringaschool.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition-all hover:scale-105 hover:shadow-lg"
                style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
              >
                Moringa School <ExternalLink size={13} />
              </a>
              <a
                href="https://www.andela.com/learning/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 rounded-xl border px-5 py-2.5 text-sm font-semibold transition-all hover:bg-accent/5 hover:border-accent/30"
                style={{ borderColor: COLORS.accent, color: COLORS.accent }}
              >
                Andela Learning <ExternalLink size={13} />
              </a>
              <a
                href="https://www.pluralsight.com/browse"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 rounded-xl border px-5 py-2.5 text-sm font-semibold transition-all hover:bg-accent/5 hover:border-accent/30"
                style={{ borderColor: COLORS.accent, color: COLORS.accent }}
              >
                Pluralsight <ExternalLink size={13} />
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Coming soon */}
      <div
        className="rounded-2xl border p-6 sm:p-8"
        style={{ borderColor: COLORS.border, background: "#fff" }}
      >
        <h3 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
          More career paths are on the way
        </h3>
        <p className="mt-2 text-sm leading-relaxed" style={{ color: COLORS.textSecondary }}>
          We're currently focused on tech roles, but we're actively expanding to cover other industries like <strong>healthcare</strong>, <strong>finance</strong>, <strong>marketing</strong>, <strong>engineering</strong>, and more. Stay tuned — your career path will be here soon.
        </p>
        <p className="mt-3 text-xs font-medium" style={{ color: COLORS.textMuted }}>
          In the meantime, uploading a tech-focused CV will give you the best experience on JobPulse.
        </p>
      </div>

      <button
        onClick={onReset}
        className="flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition-all hover:scale-105"
        style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
      >
        <UploadCloud size={16} />
        Upload a different CV
      </button>
    </div>
  );
}


const TABS = [
  { key: "overview", label: "Overview" },
  { key: "jobs", label: "Recommended Jobs" },
  { key: "gaps", label: "Skill Gaps" },
  { key: "learn", label: "Courses & Prep" },
  { key: "careers", label: "Career Paths" },
];

function OverviewTab({ analysis, onGoToJobs, onGoToTab }) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Match header */}
      <div
        className="relative overflow-hidden rounded-2xl p-6 sm:p-8"
        style={{ background: "linear-gradient(135deg, #101F3C, #1a2d4a)" }}
      >
        <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-accent/10 blur-3xl" />
        <div className="relative z-10 flex flex-col items-start gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider" style={{ color: "rgba(234,243,250,0.5)" }}>
              Overall market match
            </p>
            <p className="mt-2 text-4xl font-bold text-white" style={{ fontFamily: FONTS.display }}>
              {analysis.overallMatch}%
            </p>
            <p className="mt-2 max-w-sm text-sm text-white/70">
              You're a {analysis.overallMatch}% match for {analysis.profile.currentRole} roles in the current market.
            </p>
          </div>
          <button
            onClick={onGoToJobs}
            className="flex items-center gap-2 whitespace-nowrap rounded-xl bg-white px-6 py-3 text-sm font-semibold transition-all hover:scale-105 hover:shadow-lg"
            style={{ color: COLORS.accent }}
          >
            See matching jobs <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Skills grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div
          className="rounded-2xl border p-5 sm:p-6 lg:col-span-2"
          style={{ borderColor: COLORS.border, background: "#fff" }}
        >
          <h3
            className="mb-1 text-base font-semibold"
            style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
          >
            Skills found in your CV
          </h3>
          <p className="mb-4 text-xs" style={{ color: COLORS.textSecondary }}>
            {analysis.foundSkills.length} skills detected
          </p>
          <div className="flex flex-wrap gap-2">
            {analysis.foundSkills.map((s) => (
              <span
                key={s}
                className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all hover:scale-105"
                style={{ background: COLORS.successLight, color: "#059669" }}
              >
                <CheckCircle2 size={12} /> {s}
              </span>
            ))}
          </div>
        </div>

        <div
          className="rounded-2xl border p-5 sm:p-6 lg:col-span-3"
          style={{ borderColor: COLORS.border, background: "#fff" }}
        >
          <h3
            className="mb-1 text-base font-semibold"
            style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
          >
            Top skills employers want that you're missing
          </h3>
          <p className="mb-4 text-xs" style={{ color: COLORS.textSecondary }}>
            Ranked by recommended learning priority
          </p>
          <div className="space-y-3">
            {analysis.missingSkills.slice(0, 3).map((skill) => (
              <div
                key={skill.name}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border p-3"
                style={{ borderColor: COLORS.borderLight }}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold" style={{ color: COLORS.textDark }}>
                    {skill.name}
                  </span>
                  <span
                    className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                    style={{
                      background: PRIORITY_STYLES[skill.priority].bg,
                      color: PRIORITY_STYLES[skill.priority].fg,
                    }}
                  >
                    {skill.priority}
                  </span>
                </div>
                <button
                  onClick={() => onGoToTab("learn")}
                  className="text-xs font-semibold transition-colors hover:text-accent"
                  style={{ color: COLORS.accent }}
                >
                  Find courses
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <OpportunityUnlockCard cvAnalysis={analysis} onExplore={(skill) => onGoToTab("jobs", skill)} />
    </div>
  );
}

function SkillGapsTab({ analysis, onGoToTab }) {
  return (
    <div className="space-y-6 animate-fade-in">
      <div
        className="rounded-2xl border p-5 sm:p-6"
        style={{ borderColor: COLORS.border, background: "#fff" }}
      >
        <h3
          className="mb-1 text-base font-semibold"
          style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
        >
          Skills employers want that you're missing
        </h3>
        <p className="mb-4 text-xs" style={{ color: COLORS.textSecondary }}>
          Ranked by recommended learning priority
        </p>
        <div className="space-y-3">
          {analysis.missingSkills.map((skill) => (
            <div
              key={skill.name}
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl border p-3.5 transition-all hover:shadow-sm"
              style={{ borderColor: COLORS.borderLight }}
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold" style={{ color: COLORS.textDark }}>
                    {skill.name}
                  </span>
                  <span
                    className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                    style={{
                      background: PRIORITY_STYLES[skill.priority].bg,
                      color: PRIORITY_STYLES[skill.priority].fg,
                    }}
                  >
                    {skill.priority}
                  </span>
                </div>
                <p className="mt-0.5 text-xs" style={{ color: COLORS.textMuted }}>
                  Demand {skill.demand}% · {skill.postings.toLocaleString()} postings · {skill.difficulty} difficulty
                </p>
              </div>
              <button
                onClick={() => onGoToTab("learn")}
                className="rounded-xl border px-4 py-1.5 text-xs font-semibold transition-all hover:bg-accent/5 hover:border-accent/30"
                style={{ borderColor: COLORS.accent, color: COLORS.accent }}
              >
                Find courses
              </button>
            </div>
          ))}
        </div>
      </div>

      <div
        className="rounded-2xl border p-5 sm:p-6"
        style={{ borderColor: COLORS.border, background: "#fff" }}
      >
        <h3
          className="mb-1 text-base font-semibold"
          style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
        >
          Skill gap visualization
        </h3>
        <p className="mb-4 text-xs" style={{ color: COLORS.textSecondary }}>
          Your skills against market demand, by category
        </p>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={analysis.radar} outerRadius="70%">
              <defs>
                <linearGradient id="radarMarket" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#FA510F" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#FA510F" stopOpacity="0.1" />
                </linearGradient>
                <linearGradient id="radarYou" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#10B981" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#10B981" stopOpacity="0.15" />
                </linearGradient>
              </defs>
              <PolarGrid stroke={COLORS.borderLight} />
              <PolarAngleAxis dataKey="category" tick={{ fontSize: 12, fill: COLORS.textDark, fontFamily: FONTS.body }} />
              <Radar name="Market demand" dataKey="market" stroke="#FA510F" fill="url(#radarMarket)" strokeWidth={2} />
              <Radar name="Your skills" dataKey="you" stroke="#10B981" fill="url(#radarYou)" strokeWidth={2} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: FONTS.body, paddingTop: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default function CVAnalyzerPage() {
  const { cvAnalysis } = useAppState();
  const { setCVAnalysis } = useCVAnalysisActions();
  const [stage, setStage] = useState(() => (cvAnalysis ? "results" : "upload"));
  const [analysisStage, setAnalysisStage] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [jobSearchFocus, setJobSearchFocus] = useState(undefined);

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
      <div className="mb-8">
        <h1
          className="text-2xl font-bold sm:text-3xl"
          style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
        >
          CV Analyzer
        </h1>
        <p className="mt-2 max-w-lg text-sm" style={{ color: COLORS.textSecondary }}>
          Upload your CV to see your market match, skill gaps, and the jobs and career paths you're qualified for right now.
        </p>
      </div>

      <div>
        {stage === "upload" && <UploadArea onFile={handleFile} />}
        {stage === "loading" && <AnalysisLoadingState stage={analysisStage} />}
        {stage === "error" && (
          <EmptyState
            tone="error"
            title="CV analysis failed"
            description={error?.message || "Something went wrong while analyzing your CV. Please try again."}
            action={
              <button
                onClick={() => setStage("upload")}
                className="mt-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white"
                style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
              >
                Try again
              </button>
            }
          />
        )}

        {stage === "results" && cvAnalysis && (
          <div>
            {cvAnalysis.nonTechDetected ? (
              <NonTechCVMessage onReset={() => setStage("upload")} />
            ) : (
              <>
                <div className="mb-6 flex items-center justify-end">
                  <button
                    onClick={() => setStage("upload")}
                    className="flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-all hover:bg-accent/5 hover:border-accent/30"
                    style={{ borderColor: COLORS.border, color: COLORS.textDark }}
                  >
                    <UploadCloud size={15} />
                    Analyze a different CV
                  </button>
                </div>

                {/* Tab navigation */}
                <div className="mb-6 flex gap-1 overflow-x-auto border-b" style={{ borderColor: COLORS.border }}>
                  {TABS.map((t) => (
                    <button
                      key={t.key}
                      onClick={() => setActiveTab(t.key)}
                      className="relative whitespace-nowrap px-4 py-3 text-sm font-medium transition-colors duration-200"
                      style={{
                        color: activeTab === t.key ? COLORS.accent : COLORS.textSecondary,
                        fontWeight: activeTab === t.key ? 600 : 500,
                      }}
                    >
                      {t.label}
                      {activeTab === t.key && (
                        <div
                          className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
                          style={{ background: "linear-gradient(90deg, #FA510F, #E04500)" }}
                        />
                      )}
                    </button>
                  ))}
                </div>

                {activeTab === "overview" && (
                  <OverviewTab analysis={cvAnalysis} onGoToJobs={() => goToTab("jobs")} onGoToTab={goToTab} />
                )}
                {activeTab === "jobs" && (
                  <RecommendedJobsPanel
                    cvAnalysis={cvAnalysis}
                    initialFocusSkill={jobSearchFocus}
                    onAddLearningGoal={() => {}}
                  />
                )}
                {activeTab === "gaps" && (
                  <SkillGapsTab analysis={cvAnalysis} onGoToTab={goToTab} />
                )}
                {activeTab === "learn" && (
                  <div className="space-y-6 animate-fade-in">
                    <CourseRecommendations missingSkills={cvAnalysis.missingSkills} />
                    <InterviewPrepPanel foundSkills={cvAnalysis.foundSkills} />
                  </div>
                )}
                {activeTab === "careers" && <CareerPathsPanel cvAnalysis={cvAnalysis} />}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
