import React from "react";
import { X, MapPin, Briefcase, Wifi, CheckCircle2, AlertTriangle } from "lucide-react";
import { COLORS, FONTS, PRIORITY_STYLES } from "../../lib/theme";
import { getSkillInsight } from "../../api/client";

function MatchBar({ label, value }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 shrink-0 text-xs" style={{ color: COLORS.textSecondary }}>{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ background: COLORS.rowBorder }}>
        <div className="h-full rounded-full" style={{ width: `${value}%`, background: COLORS.navy }} />
      </div>
      <span className="w-9 shrink-0 text-right text-xs font-semibold" style={{ color: COLORS.textDark }}>{value}%</span>
    </div>
  );
}

// Section 7/8/9 of the spec: job info, match breakdown, "why you're a good
// match", and "skills you're missing" each with demand/priority context.
export default function JobDetailsModal({ job, onClose, onAddLearningGoal }) {
  const match = job.match;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 px-4" onClick={onClose}>
      <div className="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-6" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>{job.title}</h3>
            <p className="text-sm" style={{ color: COLORS.textSecondary }}>{job.company}</p>
            <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs" style={{ color: COLORS.textSecondary }}>
              <MapPin size={13} /> {job.country}
              {job.remote && <span className="flex items-center gap-1 rounded-full px-2 py-0.5" style={{ background: COLORS.lightBlue, color: COLORS.deepBlue }}><Wifi size={11} /> Remote</span>}
              <span className="mx-0.5">·</span>
              <Briefcase size={13} /> {job.experienceMin}–{job.experienceMax} years
            </div>
          </div>
          <button onClick={onClose}><X size={18} style={{ color: COLORS.textSecondary }} /></button>
        </div>

        <p className="mb-1 text-sm font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
          ${job.salaryMin.toLocaleString()} – ${job.salaryMax.toLocaleString()}
          <span className="text-xs font-normal" style={{ color: COLORS.textSecondary }}> /month</span>
        </p>

        <div className="mt-3 flex flex-wrap gap-1.5">
          {job.skillNames.map((s) => (
            <span key={s} className="rounded-full px-2.5 py-1 text-[11px] font-medium" style={{ background: "#F1F4F9", color: COLORS.textDark }}>{s}</span>
          ))}
        </div>

        {!match ? (
          <div className="mt-5 rounded-xl p-4 text-center text-sm" style={{ background: COLORS.pageBg, color: COLORS.textSecondary }}>
            Analyze your CV to see your personal match score, strengths and skill gaps for this job.
          </div>
        ) : (
          <div className="mt-5 flex flex-col gap-5">
            <div>
              <div className="mb-2 flex items-baseline gap-2">
                <span className="text-2xl font-semibold" style={{ color: COLORS.navy, fontFamily: FONTS.display }}>{match.matchScore}%</span>
                <span className="text-sm font-semibold" style={{ color: COLORS.textDark }}>{match.recommendation}</span>
              </div>
              <div className="flex flex-col gap-2">
                <MatchBar label="Skills" value={match.skillMatch} />
                <MatchBar label="Experience" value={match.experienceMatch} />
                <MatchBar label="Education" value={match.educationMatch} />
                <MatchBar label="Location" value={match.locationMatch} />
              </div>
            </div>

            <div>
              <p className="mb-2 text-sm font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Why you're a good match</p>
              <div className="flex flex-col gap-1.5">
                {match.strengths.length === 0 && <p className="text-xs" style={{ color: COLORS.textSecondary }}>No direct skill overlap detected for this role yet.</p>}
                {match.strengths.map((s) => (
                  <div key={s} className="flex items-center gap-2 text-sm" style={{ color: COLORS.textDark }}>
                    <CheckCircle2 size={14} style={{ color: COLORS.success }} /> {s} matches this job's requirements
                  </div>
                ))}
                {match.experienceMatch >= 70 && (
                  <div className="flex items-center gap-2 text-sm" style={{ color: COLORS.textDark }}>
                    <CheckCircle2 size={14} style={{ color: COLORS.success }} /> Your experience level fits this role
                  </div>
                )}
                {match.locationMatch >= 90 && (
                  <div className="flex items-center gap-2 text-sm" style={{ color: COLORS.textDark }}>
                    <CheckCircle2 size={14} style={{ color: COLORS.success }} /> Location/remote setup matches this job
                  </div>
                )}
              </div>
            </div>

            <div>
              <p className="mb-2 text-sm font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Skills you're missing</p>
              {match.missingSkills.length === 0 ? (
                <p className="text-xs" style={{ color: COLORS.textSecondary }}>You cover every required skill for this job.</p>
              ) : (
                <div className="flex flex-col divide-y" style={{ borderColor: COLORS.rowBorder }}>
                  {match.missingSkills.map((name) => {
                    const insight = getSkillInsight(name);
                    return (
                      <div key={name} className="flex items-center justify-between gap-3 py-2.5">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold" style={{ color: COLORS.textDark }}>{name}</span>
                            {insight && (
                              <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: PRIORITY_STYLES[insight.priority].bg, color: PRIORITY_STYLES[insight.priority].fg }}>{insight.priority}</span>
                            )}
                          </div>
                          {insight && (
                            <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>
                              Appears in {insight.demand}% of relevant postings · {insight.difficulty} to learn
                            </p>
                          )}
                        </div>
                        <button onClick={() => onAddLearningGoal({ name })} className="whitespace-nowrap rounded-lg border px-3 py-1.5 text-xs font-semibold" style={{ borderColor: COLORS.deepBlue, color: COLORS.deepBlue }}>
                          Add goal
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
