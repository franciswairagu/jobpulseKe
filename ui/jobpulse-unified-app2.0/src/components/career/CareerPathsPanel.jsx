import React, { useCallback } from "react";
import { COLORS, FONTS } from "../../lib/theme";
import LoadingState from "../shared/LoadingState";
import EmptyState from "../shared/EmptyState";
import { getCareerPaths } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";

export default function CareerPathsPanel({ cvAnalysis }) {
  const fetcher = useCallback(() => getCareerPaths(cvAnalysis), [cvAnalysis]);
  const { status, data, error, refetch } = useAsync(fetcher, [cvAnalysis]);

  if (!cvAnalysis) {
    return (
      <EmptyState
        title="Analyze your CV first"
        description="Career path matches are calculated from your CV's skills — there's nothing to compare yet."
      />
    );
  }
  if (status === "loading") return <LoadingState label="Matching career paths..." />;
  if (status === "error") {
    return (
      <EmptyState
        tone="error"
        title="Couldn't load career paths"
        description={error?.message}
        action={
          <button
            onClick={refetch}
            className="mt-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white"
            style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
          >
            Retry
          </button>
        }
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 stagger-children">
      {data.paths.map((path) => (
        <div
          key={path.role}
          className="group rounded-2xl border p-5 transition-all duration-300 hover-lift"
          style={{ borderColor: COLORS.border, background: "#fff" }}
        >
          <div className="flex items-start justify-between gap-3">
            <h3
              className="text-base font-semibold group-hover:text-accent transition-colors"
              style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
            >
              {path.role}
            </h3>
            <span
              className="whitespace-nowrap rounded-full px-3 py-1 text-xs font-bold"
              style={{
                background:
                  path.matchScore >= 70
                    ? "rgba(16,185,129,0.1)"
                    : path.matchScore >= 40
                    ? "rgba(245,158,11,0.1)"
                    : "rgba(239,68,68,0.08)",
                color:
                  path.matchScore >= 70
                    ? "#059669"
                    : path.matchScore >= 40
                    ? "#D97706"
                    : COLORS.error,
              }}
            >
              {path.matchScore}% match
            </span>
          </div>
          <p className="mt-1 text-xs" style={{ color: COLORS.textMuted }}>
            {path.jobCount} open role{path.jobCount === 1 ? "" : "s"}
          </p>

          <div className="mt-3">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>
              You already have
            </p>
            <div className="flex flex-wrap gap-1.5">
              {path.matchingSkills.length
                ? path.matchingSkills.map((s) => (
                    <span
                      key={s}
                      className="rounded-full px-2.5 py-1 text-[11px] font-medium transition-all hover:scale-105"
                      style={{ background: "rgba(16,185,129,0.1)", color: "#059669" }}
                    >
                      {s}
                    </span>
                  ))
                : <span className="text-xs" style={{ color: COLORS.textMuted }}>None yet</span>}
            </div>
          </div>

          {path.missingSkills.length > 0 && (
            <div className="mt-3">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>
                Skills to build
              </p>
              <div className="flex flex-wrap gap-1.5">
                {path.missingSkills.map((s) => (
                  <span
                    key={s}
                    className="rounded-full px-2.5 py-1 text-[11px] font-medium transition-all hover:scale-105"
                    style={{ background: "rgba(239,68,68,0.06)", color: COLORS.error }}
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
