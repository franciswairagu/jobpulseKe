import React, { useState, useCallback } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, X, ArrowRight, Loader2 } from "lucide-react";
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend } from "recharts";
import { COLORS, FONTS, PRIORITY_STYLES } from "../lib/theme";
import { analyzeCV } from "../api/client";
import { useCVAnalysisActions, useAppState } from "../state/AppContext";
import EmptyState from "../components/shared/EmptyState";

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

function LoadingState({ stage }) {
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

function ResultsView({ analysis, onAddLearningGoal, onViewJobs }) {
  const { foundSkills, missingSkills, radar, overallMatch, biggestOpportunity, profile } = analysis;
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-start gap-5 rounded-2xl p-6 sm:flex-row sm:items-center sm:justify-between" style={{ background: COLORS.navy }}>
        <div>
          <p className="text-xs font-medium" style={{ color: "rgba(234,243,250,0.65)" }}>Overall market match</p>
          <p className="mt-1 text-4xl font-semibold text-white" style={{ fontFamily: FONTS.display }}>{overallMatch}%</p>
          <p className="mt-1 max-w-sm text-sm" style={{ color: "rgba(234,243,250,0.75)" }}>
            Your CV matches the current market requirements for {profile.currentRole} roles.
          </p>
        </div>
        <button onClick={onViewJobs} className="flex items-center gap-1.5 whitespace-nowrap rounded-lg bg-white px-5 py-2.5 text-sm font-semibold" style={{ color: COLORS.navy }}>
          View matching jobs <ArrowRight size={14} />
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-2" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <h3 className="mb-1 text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Skills found in your CV</h3>
          <p className="mb-4 text-xs" style={{ color: COLORS.textSecondary }}>{foundSkills.length} skills detected</p>
          <div className="flex flex-wrap gap-2">
            {foundSkills.map((s) => (
              <span key={s} className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium" style={{ background: "rgba(22,163,74,0.1)", color: COLORS.success }}>
                <CheckCircle2 size={12} /> {s}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border p-5 sm:p-6 lg:col-span-3" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <h3 className="mb-1 text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Skills employers want that you're missing</h3>
          <p className="mb-4 text-xs" style={{ color: COLORS.textSecondary }}>Ranked by recommended learning priority</p>
          <div className="flex flex-col divide-y" style={{ borderColor: COLORS.rowBorder }}>
            {missingSkills.map((skill) => (
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
      </div>

      <div className="rounded-2xl border p-5 sm:p-6" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <h3 className="mb-1 text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Skill gap visualization</h3>
        <p className="mb-2 text-xs" style={{ color: COLORS.textSecondary }}>Your skills against market demand, by category</p>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radar} outerRadius="70%">
              <PolarGrid stroke={COLORS.border} />
              <PolarAngleAxis dataKey="category" tick={{ fontSize: 12, fill: COLORS.textDark, fontFamily: FONTS.body }} />
              <Radar name="Market demand" dataKey="market" stroke={COLORS.lightBlue} fill={COLORS.deepBlue} fillOpacity={0.15} strokeWidth={2} />
              <Radar name="Your skills" dataKey="you" stroke={COLORS.navy} fill={COLORS.navy} fillOpacity={0.35} strokeWidth={2} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: FONTS.body, paddingTop: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="flex flex-col gap-4 rounded-2xl border p-6 sm:flex-row sm:items-center sm:justify-between" style={{ borderColor: COLORS.border, background: COLORS.lightBlue }}>
        <div className="flex items-start gap-3">
          <AlertTriangle size={20} style={{ color: COLORS.deepBlue, marginTop: 2 }} />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: COLORS.deepBlue }}>Your biggest opportunity</p>
            <p className="mt-1 text-xl font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>{biggestOpportunity.name}</p>
            <p className="mt-1 max-w-md text-sm" style={{ color: COLORS.textSecondary }}>
              {biggestOpportunity.name} appears in {biggestOpportunity.demand}% of relevant job postings, but wasn't detected in your CV.
            </p>
          </div>
        </div>
        <button onClick={() => onAddLearningGoal(biggestOpportunity)} className="whitespace-nowrap rounded-lg px-5 py-2.5 text-sm font-semibold text-white" style={{ background: COLORS.navy }}>
          Add {biggestOpportunity.name} to my learning goals
        </button>
      </div>
    </div>
  );
}

export default function CVAnalyzerPage({ onNavigate }) {
  const [stage, setStage] = useState("upload"); // upload | loading | results | error
  const [analysisStage, setAnalysisStage] = useState(null);
  const [error, setError] = useState(null);
  const { cvAnalysis } = useAppState();
  const { setCVAnalysis } = useCVAnalysisActions();

  const handleFile = async (file) => {
    setStage("loading");
    setError(null);
    try {
      const result = await analyzeCV(file, setAnalysisStage);
      setCVAnalysis(result);
      setStage("results");
    } catch (e) {
      setError(e);
      setStage("error");
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold sm:text-[28px]" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Analyze your CV</h1>
      <p className="mt-1.5 max-w-lg text-sm" style={{ color: COLORS.textSecondary }}>
        Upload your CV to compare your skills with current employer demand across the African tech market.
      </p>

      <div className="mt-8">
        {stage === "upload" && <UploadArea onFile={handleFile} />}
        {stage === "loading" && <LoadingState stage={analysisStage} />}
        {stage === "error" && (
          <EmptyState
            tone="error"
            title="CV analysis failed"
            description={error?.message || "Something went wrong while analyzing your CV. Please try again."}
            action={<button onClick={() => setStage("upload")} className="mt-2 rounded-lg px-4 py-2 text-xs font-semibold text-white" style={{ background: COLORS.navy }}>Try again</button>}
          />
        )}
        {stage === "results" && cvAnalysis && (
          <ResultsView
            analysis={cvAnalysis}
            onAddLearningGoal={() => {}}
            onViewJobs={() => onNavigate("job-market")}
          />
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
