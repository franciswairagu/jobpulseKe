import React from "react";
import { X, MapPin, Briefcase, Wifi, CheckCircle2, ExternalLink, Target, TrendingUp, FileText, ClipboardCheck, AlertTriangle, XCircle } from "lucide-react";
import { COLORS, FONTS, PRIORITY_STYLES } from "../../lib/theme";
import { getSkillInsight } from "../../api/client";

function MatchBar({ label, value }) {
  const barColor =
    value >= 75 ? "#10B981" : value >= 50 ? "#F59E0B" : "#EF4444";
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 shrink-0 text-xs font-medium" style={{ color: COLORS.textSecondary }}>
        {label}
      </span>
      <div className="h-2 flex-1 overflow-hidden rounded-full" style={{ background: COLORS.surfaceTertiary }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${value}%`,
            background: `linear-gradient(90deg, ${barColor}cc, ${barColor})`,
          }}
        />
      </div>
      <span className="w-10 shrink-0 text-right text-xs font-bold" style={{ color: COLORS.textDark }}>
        {value}%
      </span>
    </div>
  );
}

const ATS_STATUS = {
  pass: { icon: CheckCircle2, color: COLORS.success },
  warn: { icon: AlertTriangle, color: COLORS.warning },
  fail: { icon: XCircle, color: COLORS.error },
};

function ATSScoreBar({ value }) {
  const barColor = value >= 80 ? "#10B981" : value >= 60 ? "#F59E0B" : "#EF4444";
  return (
    <div className="h-2 w-full overflow-hidden rounded-full" style={{ background: COLORS.surfaceTertiary }}>
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{ width: `${value}%`, background: `linear-gradient(90deg, ${barColor}cc, ${barColor})` }}
      />
    </div>
  );
}

function ATSSection({ ats }) {
  return (
    <div className="mb-5 rounded-xl border p-4" style={{ borderColor: COLORS.borderLight, background: "#fff" }}>
      <div className="flex items-center gap-2 mb-3">
        <ClipboardCheck size={16} style={{ color: COLORS.accent }} />
        <p className="text-sm font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
          ATS score
        </p>
        <span
          className="ml-auto rounded-full px-2.5 py-1 text-xs font-bold"
          style={{
            background: ats.score >= 80 ? "rgba(16,185,129,0.1)" : ats.score >= 60 ? "rgba(245,158,11,0.1)" : "rgba(239,68,68,0.08)",
            color: ats.score >= 80 ? "#059669" : ats.score >= 60 ? "#D97706" : COLORS.error,
          }}
        >
          {ats.score}% · {ats.label}
        </span>
      </div>

      <div className="mb-4">
        <ATSScoreBar value={ats.score} />
        <p className="mt-1.5 text-[11px]" style={{ color: COLORS.textMuted }}>
          How well your CV passes this posting's automated keyword and profile screen.
        </p>
      </div>

      <div className="space-y-2">
        {ats.checks.map((c) => {
          const Icon = ATS_STATUS[c.status].icon;
          return (
            <div key={c.id} className="flex items-start gap-2.5 rounded-lg px-3 py-2" style={{ background: COLORS.pageBg }}>
              <Icon size={15} className="mt-0.5 shrink-0" style={{ color: ATS_STATUS[c.status].color }} />
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-xs font-semibold" style={{ color: COLORS.textDark }}>
                    {c.label}
                  </span>
                  <span className="text-xs font-bold" style={{ color: ATS_STATUS[c.status].color }}>
                    {c.value}%
                  </span>
                </div>
                <p className="mt-0.5 text-[11px]" style={{ color: COLORS.textSecondary }}>
                  {c.detail}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-3">
        <p className="text-xs font-semibold mb-1.5" style={{ color: COLORS.textDark }}>
          Keywords {ats.missingKeywords.length === 0 ? "matched" : "check"}
        </p>
        <div className="flex flex-wrap gap-1.5">
          {ats.matchedKeywords.map((k) => (
            <span
              key={`m-${k}`}
              className="rounded-full px-2 py-0.5 text-[11px] font-medium"
              style={{ background: "rgba(16,185,129,0.1)", color: "#059669" }}
            >
              {k}
            </span>
          ))}
          {ats.missingKeywords.map((k) => (
            <span
              key={`x-${k}`}
              className="rounded-full px-2 py-0.5 text-[11px] font-medium"
              style={{ background: "rgba(239,68,68,0.08)", color: COLORS.error }}
            >
              {k}
            </span>
          ))}
          {ats.matchedKeywords.length === 0 && ats.missingKeywords.length === 0 && (
            <span className="text-[11px]" style={{ color: COLORS.textMuted }}>
              No keywords extracted from this posting.
            </span>
          )}
        </div>
      </div>

      {ats.tips.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold mb-1.5" style={{ color: COLORS.textDark }}>
            How to improve
          </p>
          <ul className="space-y-1">
            {ats.tips.map((tip) => (
              <li key={tip} className="flex items-start gap-1.5 text-[11px]" style={{ color: COLORS.textSecondary }}>
                <span className="mt-1 h-1 w-1 shrink-0 rounded-full" style={{ background: COLORS.accent }} />
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function JobDetailsModal({ job, onClose, onAddLearningGoal }) {
  const match = job.match;
  const ats = job.ats;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center px-4 animate-fade-in"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0"
        style={{
          background: "rgba(16,31,60,0.5)",
          backdropFilter: "blur(8px)",
        }}
      />

      {/* Modal */}
      <div
        className="relative max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-3xl bg-white p-6 sm:p-8 animate-scale-in"
        style={{ boxShadow: "0 25px 60px rgba(16,31,60,0.3)" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-xl p-2 transition-colors hover:bg-surface-tertiary"
        >
          <X size={18} style={{ color: COLORS.textSecondary }} />
        </button>

        {/* Header */}
        <div className="mb-5">
          <div className="flex items-start gap-3">
            <div
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
              style={{ background: COLORS.lightBlue }}
            >
              <Target size={20} style={{ color: COLORS.accent }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3
                  className="text-lg font-bold"
                  style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
                >
                  {job.title}
                </h3>
                {job.sourceUrl && (
                  <a
                    href={job.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs font-semibold transition-colors hover:text-accent"
                    style={{ color: COLORS.accent }}
                  >
                    <ExternalLink size={13} /> View
                  </a>
                )}
              </div>
              <p className="text-sm" style={{ color: COLORS.textSecondary }}>
                {job.company}
              </p>
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs" style={{ color: COLORS.textMuted }}>
            <MapPin size={13} /> {job.country}
            {job.remote && (
              <span
                className="flex items-center gap-1 rounded-full px-2 py-0.5"
                style={{ background: COLORS.lightBlue, color: COLORS.accent }}
              >
                <Wifi size={11} /> Remote
              </span>
            )}
            <span className="mx-0.5 opacity-40">·</span>
            <Briefcase size={13} /> {job.experienceMin}–{job.experienceMax} years
          </div>
        </div>

        {/* Skills */}
        <div className="mb-5 flex flex-wrap gap-1.5">
          {job.skillNames.map((s) => (
            <span
              key={s}
              className="rounded-full px-2.5 py-1 text-[11px] font-medium"
              style={{ background: COLORS.surfaceTertiary, color: COLORS.textDark }}
            >
              {s}
            </span>
          ))}
        </div>

        {/* Job description */}
        {job.description && (
          <div className="mb-5">
            <div className="flex items-center gap-2 mb-2">
              <FileText size={15} style={{ color: COLORS.textSecondary }} />
              <p className="text-sm font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
                Job description
              </p>
            </div>
            <div
              className="max-h-40 overflow-y-auto whitespace-pre-line rounded-xl px-3.5 py-3 text-xs leading-relaxed"
              style={{ background: COLORS.pageBg, color: COLORS.textSecondary }}
            >
              {job.description}
            </div>
          </div>
        )}

        {/* ATS report */}
        {ats && <ATSSection ats={ats} />}

        {/* Match section */}
        {!match ? (
          <div
            className="rounded-xl p-4 text-center text-sm"
            style={{ background: COLORS.pageBg, color: COLORS.textSecondary }}
          >
            Analyze your CV to see your personal match score, strengths and skill gaps for this job.
          </div>
        ) : (
          <div className="space-y-5">
            {/* Score header */}
            <div
              className="rounded-xl p-4"
              style={{
                background: "linear-gradient(135deg, #101F3C, #1a2d4a)",
              }}
            >
              <div className="flex items-baseline gap-2">
                <span
                  className="text-3xl font-bold text-white"
                  style={{ fontFamily: FONTS.display }}
                >
                  {match.matchScore}%
                </span>
                <span className="text-sm font-semibold text-white/80">
                  {match.recommendation}
                </span>
              </div>
            </div>

            {/* Match bars */}
            <div className="space-y-2.5">
              <MatchBar label="Skills" value={match.skillMatch} />
              <MatchBar label="Experience" value={match.experienceMatch} />
              <MatchBar label="Education" value={match.educationMatch} />
              <MatchBar label="Location" value={match.locationMatch} />
            </div>

            {/* Strengths */}
            <div>
              <div className="flex items-center gap-2 mb-2.5">
                <CheckCircle2 size={16} style={{ color: COLORS.success }} />
                <p className="text-sm font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
                  Why you're a good match
                </p>
              </div>
              <div className="flex flex-col gap-2">
                {match.strengths.length === 0 && (
                  <p className="text-xs" style={{ color: COLORS.textSecondary }}>
                    No direct skill overlap detected for this role yet.
                  </p>
                )}
                {match.strengths.map((s) => (
                  <div
                    key={s}
                    className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm"
                    style={{ background: "rgba(16,185,129,0.05)" }}
                  >
                    <div className="h-1.5 w-1.5 rounded-full" style={{ background: COLORS.success }} />
                    <span style={{ color: COLORS.textDark }}>
                      <span className="font-semibold">{s}</span> matches this job's requirements
                    </span>
                  </div>
                ))}
                {match.experienceMatch >= 70 && (
                  <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm" style={{ background: "rgba(16,185,129,0.05)" }}>
                    <div className="h-1.5 w-1.5 rounded-full" style={{ background: COLORS.success }} />
                    <span style={{ color: COLORS.textDark }}>Your experience level fits this role</span>
                  </div>
                )}
                {match.locationMatch >= 90 && (
                  <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm" style={{ background: "rgba(16,185,129,0.05)" }}>
                    <div className="h-1.5 w-1.5 rounded-full" style={{ background: COLORS.success }} />
                    <span style={{ color: COLORS.textDark }}>Location/remote setup matches this job</span>
                  </div>
                )}
              </div>
            </div>

            {/* Missing skills */}
            <div>
              <div className="flex items-center gap-2 mb-2.5">
                <TrendingUp size={16} style={{ color: COLORS.warning }} />
                <p className="text-sm font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
                  Skills you're missing
                </p>
              </div>
              {match.missingSkills.length === 0 ? (
                <p className="text-xs" style={{ color: COLORS.textSecondary }}>
                  You cover every required skill for this job.
                </p>
              ) : (
                <div className="space-y-2">
                  {match.missingSkills.map((name) => {
                    const insight = getSkillInsight(name);
                    return (
                      <div
                        key={name}
                        className="flex items-center justify-between gap-3 rounded-xl border p-3"
                        style={{ borderColor: COLORS.borderLight }}
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold" style={{ color: COLORS.textDark }}>
                              {name}
                            </span>
                            {insight && (
                              <span
                                className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                                style={{
                                  background: PRIORITY_STYLES[insight.priority].bg,
                                  color: PRIORITY_STYLES[insight.priority].fg,
                                }}
                              >
                                {insight.priority}
                              </span>
                            )}
                          </div>
                          {insight && (
                            <p className="mt-0.5 text-xs" style={{ color: COLORS.textMuted }}>
                              Appears in {insight.demand}% of relevant postings · {insight.difficulty} to learn
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => onAddLearningGoal({ name })}
                          className="whitespace-nowrap rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all hover:bg-accent/5 hover:border-accent/30"
                          style={{ borderColor: COLORS.accent, color: COLORS.accent }}
                        >
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
