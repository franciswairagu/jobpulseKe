import React, { useState, useCallback } from "react";
import { Search, MapPin, Briefcase, Wifi, ChevronDown, Sparkles, Bookmark, X, CheckCircle2, XCircle } from "lucide-react";
import { COLORS, FONTS, AFRICAN_COUNTRIES } from "../lib/theme";
import Dropdown from "../components/shared/Dropdown";
import LoadingState from "../components/shared/LoadingState";
import EmptyState from "../components/shared/EmptyState";
import { getJobs, matchJobToCV } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAppState, useSavedJobs } from "../state/AppContext";

function MatchModal({ job, onClose, onNavigateToCVAnalyzer }) {
  const { cvAnalysis } = useAppState();
  const fetcher = useCallback(() => matchJobToCV(job, cvAnalysis), [job, cvAnalysis]);
  const { status, data } = useAsync(fetcher, [job.id, cvAnalysis]);

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 px-4" onClick={onClose}>
      <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Match with your CV</h3>
            <p className="text-xs" style={{ color: COLORS.textSecondary }}>{job.title} at {job.company}</p>
          </div>
          <button onClick={onClose}><X size={18} style={{ color: COLORS.textSecondary }} /></button>
        </div>

        {!cvAnalysis ? (
          <EmptyState
            title="Analyze your CV first"
            description="We need your CV profile before we can calculate a match score for this job."
            action={<button onClick={onNavigateToCVAnalyzer} className="mt-2 rounded-lg px-4 py-2 text-xs font-semibold text-white" style={{ background: COLORS.navy }}>Go to CV Analyzer</button>}
          />
        ) : status === "loading" ? (
          <LoadingState label="Calculating match..." />
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-4 rounded-xl p-4" style={{ background: COLORS.lightBlue }}>
              <p className="text-3xl font-semibold" style={{ color: COLORS.navy, fontFamily: FONTS.display }}>{data.matchScore}%</p>
              <div>
                <p className="text-sm font-semibold" style={{ color: COLORS.textDark }}>{data.recommendation}</p>
                <p className="text-xs" style={{ color: COLORS.textSecondary }}>Skill {data.skillMatch}% · Experience {data.experienceMatch}% · Education {data.educationMatch}% · Location {data.locationMatch}%</p>
              </div>
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold" style={{ color: COLORS.textSecondary }}>Your strengths for this role</p>
              <div className="flex flex-wrap gap-2">
                {data.strengths.length ? data.strengths.map((s) => (
                  <span key={s} className="flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium" style={{ background: "rgba(22,163,74,0.1)", color: COLORS.success }}><CheckCircle2 size={12} /> {s}</span>
                )) : <p className="text-xs" style={{ color: COLORS.textSecondary }}>No direct skill overlap detected.</p>}
              </div>
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold" style={{ color: COLORS.textSecondary }}>Skills to close the gap</p>
              <div className="flex flex-wrap gap-2">
                {data.missingSkills.length ? data.missingSkills.map((s) => (
                  <span key={s} className="flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium" style={{ background: "rgba(220,38,38,0.08)", color: COLORS.error }}><XCircle size={12} /> {s}</span>
                )) : <p className="text-xs" style={{ color: COLORS.textSecondary }}>You cover every required skill for this job.</p>}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function JobCard({ job, saved, onToggleSave, onMatch }) {
  return (
    <div className="flex flex-col justify-between rounded-2xl border p-5 transition-shadow hover:shadow-sm" style={{ borderColor: COLORS.border, background: "#fff" }}>
      <div>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>{job.title}</h3>
            <p className="mt-0.5 text-sm" style={{ color: COLORS.textSecondary }}>{job.company}</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {job.remote && (
              <span className="flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium" style={{ background: COLORS.lightBlue, color: COLORS.deepBlue }}>
                <Wifi size={11} /> Remote
              </span>
            )}
            <button onClick={() => onToggleSave(job.id)} aria-label="Save job">
              <Bookmark size={16} style={{ color: saved ? COLORS.deepBlue : "#CBD5E1", fill: saved ? COLORS.deepBlue : "none" }} />
            </button>
          </div>
        </div>

        <div className="mt-3 flex items-center gap-1.5 text-xs" style={{ color: COLORS.textSecondary }}>
          <MapPin size={13} /> {job.country}
          <span className="mx-1">·</span>
          <Briefcase size={13} /> {job.experienceMin}–{job.experienceMax} years
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {job.skillNames.map((s) => (
            <span key={s} className="rounded-full px-2.5 py-1 text-[11px] font-medium" style={{ background: "#F1F4F9", color: COLORS.textDark }}>{s}</span>
          ))}
        </div>

        <p className="mt-4 text-sm font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
          ${job.salaryMin.toLocaleString()} – ${job.salaryMax.toLocaleString()}
          <span className="text-xs font-normal" style={{ color: COLORS.textSecondary }}> /month</span>
        </p>
      </div>

      <div className="mt-5 flex gap-2">
        <button className="flex-1 rounded-lg px-4 py-2 text-sm font-semibold text-white" style={{ background: COLORS.navy }}>View job</button>
        <button onClick={() => onMatch(job)} className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border px-4 py-2 text-sm font-semibold" style={{ borderColor: COLORS.deepBlue, color: COLORS.deepBlue }}>
          <Sparkles size={13} /> Match with my CV
        </button>
      </div>
    </div>
  );
}

export default function JobMarketPage({ onNavigate }) {
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("All countries");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [matchingJob, setMatchingJob] = useState(null);
  const { savedJobIds, toggleSaveJob } = useSavedJobs();

  const fetcher = useCallback(() => getJobs({ query, country, remoteOnly }), [query, country, remoteOnly]);
  const { status, data, error, refetch } = useAsync(fetcher, [query, country, remoteOnly]);

  return (
    <div>
      <h1 className="text-2xl font-semibold sm:text-[28px]" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Job market</h1>
      <p className="mt-1.5 max-w-lg text-sm" style={{ color: COLORS.textSecondary }}>Discover open tech roles across African markets, matched to what you bring.</p>

      <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex flex-1 items-center gap-2 rounded-lg border px-3.5 py-2.5" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <Search size={16} style={{ color: COLORS.textSecondary }} />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search jobs by title, skill or company" className="w-full bg-transparent text-sm outline-none" style={{ color: COLORS.textDark }} />
        </div>
        <button onClick={() => setShowFilters((s) => !s)} className="flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium" style={{ borderColor: showFilters ? COLORS.deepBlue : COLORS.border, color: showFilters ? COLORS.deepBlue : COLORS.textDark, background: "#fff" }}>
          Filters <ChevronDown size={13} />
        </button>
      </div>

      {showFilters && (
        <div className="mt-3 flex flex-wrap gap-2">
          <Dropdown label="Country" value={country} options={["All countries", ...AFRICAN_COUNTRIES]} onChange={setCountry} />
          <Dropdown label="Remote" value={remoteOnly ? "Remote only" : "All types"} options={["All types", "Remote only"]} onChange={(v) => setRemoteOnly(v === "Remote only")} />
        </div>
      )}

      <p className="mt-5 text-xs" style={{ color: COLORS.textSecondary }}>
        {status === "success" ? `${data.total} open roles` : "\u00A0"}
        {savedJobIds.length > 0 && ` · ${savedJobIds.length} saved`}
      </p>

      <div className="mt-3">
        {status === "loading" && <LoadingState label="Loading open roles..." />}
        {status === "error" && (
          <EmptyState tone="error" title="Couldn't load jobs" description={error?.message} action={<button onClick={refetch} className="mt-2 rounded-lg px-4 py-2 text-xs font-semibold text-white" style={{ background: COLORS.navy }}>Retry</button>} />
        )}
        {status === "success" && data.jobs.length === 0 && (
          <EmptyState title={`No roles match "${query}"`} description="Try a different title, skill or company." />
        )}
        {status === "success" && data.jobs.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.jobs.map((job) => (
              <JobCard key={job.id} job={job} saved={savedJobIds.includes(job.id)} onToggleSave={toggleSaveJob} onMatch={setMatchingJob} />
            ))}
          </div>
        )}
      </div>

      {matchingJob && (
        <MatchModal job={matchingJob} onClose={() => setMatchingJob(null)} onNavigateToCVAnalyzer={() => { setMatchingJob(null); onNavigate("cv-analyzer"); }} />
      )}
    </div>
  );
}
