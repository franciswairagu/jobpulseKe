import React from "react";
import { MapPin, Briefcase, Wifi, Bookmark, Sparkles, ExternalLink } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";

export default function JobCard({ job, saved, onToggleSave, onOpenDetails }) {
  const match = job.match;

  return (
    <div
      onClick={() => onOpenDetails(job)}
      className="group flex cursor-pointer flex-col justify-between rounded-2xl border p-5 transition-all duration-300 hover-lift"
      style={{ borderColor: COLORS.border, background: "#fff" }}
    >
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h3
              className="text-base font-semibold leading-snug group-hover:text-accent transition-colors"
              style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
            >
              {job.title}
            </h3>
            <p className="mt-1 text-sm" style={{ color: COLORS.textSecondary }}>
              {job.company}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {job.remote && (
              <span
                className="flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium"
                style={{ background: COLORS.lightBlue, color: COLORS.accent }}
              >
                <Wifi size={11} /> Remote
              </span>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleSave(job.id);
              }}
              aria-label="Save job"
              className="rounded-lg p-1.5 transition-all hover:bg-surface-tertiary"
            >
              <Bookmark
                size={16}
                className="transition-all duration-200"
                style={{
                  color: saved ? COLORS.accent : COLORS.textMuted,
                  fill: saved ? COLORS.accent : "none",
                  transform: saved ? "scale(1.1)" : "scale(1)",
                }}
              />
            </button>
          </div>
        </div>

        {match && (
          <div
            className="mt-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
            style={{
              background:
                match.matchScore >= 75
                  ? "rgba(16,185,129,0.1)"
                  : match.matchScore >= 50
                  ? "rgba(245,158,11,0.1)"
                  : "rgba(239,68,68,0.08)",
              color:
                match.matchScore >= 75
                  ? "#059669"
                  : match.matchScore >= 50
                  ? "#D97706"
                  : COLORS.error,
            }}
          >
            <Sparkles size={11} /> {match.matchScore}% {match.recommendation.toLowerCase()}
          </div>
        )}

        <div className="mt-3 flex items-center gap-1.5 text-xs" style={{ color: COLORS.textMuted }}>
          <MapPin size={13} /> {job.country}
          <span className="mx-1 opacity-40">·</span>
          <Briefcase size={13} /> {job.experienceMin}–{job.experienceMax} years
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {job.skillNames.slice(0, 6).map((s) => {
            const isGap = match?.missingSkills.includes(s);
            return (
              <span
                key={s}
                className="rounded-full px-2.5 py-1 text-[11px] font-medium transition-all hover:scale-105"
                style={{
                  background: isGap ? "rgba(239,68,68,0.06)" : COLORS.surfaceTertiary,
                  color: isGap ? COLORS.error : COLORS.textDark,
                  border: isGap ? "1px solid rgba(239,68,68,0.1)" : "1px solid transparent",
                }}
              >
                {s}
              </span>
            );
          })}
          {job.skillNames.length > 6 && (
            <span className="rounded-full px-2 py-1 text-[10px] font-medium" style={{ color: COLORS.textMuted }}>
              +{job.skillNames.length - 6}
            </span>
          )}
        </div>
      </div>

      <div className="mt-5 flex gap-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onOpenDetails(job);
          }}
          className="flex-1 rounded-xl px-4 py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:shadow-glow-blue"
          style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
        >
          View job
        </button>
        {job.sourceUrl && (
          <a
            href={job.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1.5 rounded-xl border px-3.5 py-2.5 text-sm font-semibold transition-all duration-200 hover:border-accent/30 hover:bg-surface-tertiary"
            style={{ borderColor: COLORS.border, color: COLORS.textDark }}
          >
            <ExternalLink size={14} /> Apply
          </a>
        )}
      </div>
    </div>
  );
}
