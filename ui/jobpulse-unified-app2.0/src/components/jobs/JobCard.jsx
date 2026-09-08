import React from "react";
import { MapPin, Briefcase, Wifi, Bookmark, Sparkles } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";

// Reused (not recreated) from the original standalone JobMarket.jsx, per the
// "one source of truth for job data and job components" rule - this is the
// only place a job card's markup lives now, whether rendered from a
// personalized recommendation list, a search result, or (previously) a
// generic job market page.
export default function JobCard({ job, saved, onToggleSave, onOpenDetails }) {
  const match = job.match;
  return (
    <div
      onClick={() => onOpenDetails(job)}
      className="flex cursor-pointer flex-col justify-between rounded-2xl border p-5 transition-shadow hover:shadow-sm"
      style={{ borderColor: COLORS.border, background: "#fff" }}
    >
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
            <button onClick={(e) => { e.stopPropagation(); onToggleSave(job.id); }} aria-label="Save job">
              <Bookmark size={16} style={{ color: saved ? COLORS.deepBlue : "#CBD5E1", fill: saved ? COLORS.deepBlue : "none" }} />
            </button>
          </div>
        </div>

        {match && (
          <div className="mt-3 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold" style={{ background: match.matchScore >= 75 ? "rgba(22,163,74,0.1)" : match.matchScore >= 50 ? "rgba(245,158,11,0.12)" : "rgba(220,38,38,0.08)", color: match.matchScore >= 75 ? COLORS.success : match.matchScore >= 50 ? "#B45309" : COLORS.error }}>
            <Sparkles size={11} /> {match.matchScore}% {match.recommendation.toLowerCase()}
          </div>
        )}

        <div className="mt-3 flex items-center gap-1.5 text-xs" style={{ color: COLORS.textSecondary }}>
          <MapPin size={13} /> {job.country}
          <span className="mx-1">·</span>
          <Briefcase size={13} /> {job.experienceMin}–{job.experienceMax} years
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {job.skillNames.map((s) => {
            const isGap = match?.missingSkills.includes(s);
            return (
              <span key={s} className="rounded-full px-2.5 py-1 text-[11px] font-medium" style={{ background: isGap ? "rgba(220,38,38,0.06)" : "#F1F4F9", color: isGap ? COLORS.error : COLORS.textDark }}>
                {s}
              </span>
            );
          })}
        </div>
      </div>

      <div className="mt-5 flex gap-2">
        <button onClick={(e) => { e.stopPropagation(); onOpenDetails(job); }} className="flex-1 rounded-lg px-4 py-2 text-sm font-semibold text-white" style={{ background: COLORS.navy }}>
          View job
        </button>
      </div>
    </div>
  );
}
