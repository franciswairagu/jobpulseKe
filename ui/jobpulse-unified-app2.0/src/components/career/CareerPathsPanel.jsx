import React, { useCallback } from "react";
import { COLORS, FONTS } from "../../lib/theme";
import LoadingState from "../shared/LoadingState";
import EmptyState from "../shared/EmptyState";
import { getCareerPaths } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";

// Spec section 12: career paths the user is realistically qualified for,
// scored with the same skill-overlap math used for job matching.
export default function CareerPathsPanel({ cvAnalysis }) {
  const fetcher = useCallback(() => getCareerPaths(cvAnalysis), [cvAnalysis]);
  const { status, data, error, refetch } = useAsync(fetcher, [cvAnalysis]);

  if (!cvAnalysis) {
    return <EmptyState title="Analyze your CV first" description="Career path matches are calculated from your CV's skills - there's nothing to compare yet." />;
  }
  if (status === "loading") return <LoadingState label="Matching career paths..." />;
  if (status === "error") {
    return <EmptyState tone="error" title="Couldn't load career paths" description={error?.message} action={<button onClick={refetch} className="mt-2 rounded-lg px-4 py-2 text-xs font-semibold text-white" style={{ background: COLORS.navy }}>Retry</button>} />;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {data.paths.map((path) => (
        <div key={path.role} className="rounded-2xl border p-5" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>{path.role}</h3>
            <span className="whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold" style={{ background: path.matchScore >= 70 ? "rgba(22,163,74,0.1)" : path.matchScore >= 40 ? "rgba(245,158,11,0.12)" : "rgba(220,38,38,0.08)", color: path.matchScore >= 70 ? COLORS.success : path.matchScore >= 40 ? "#B45309" : COLORS.error }}>
              {path.matchScore}% match
            </span>
          </div>
          <p className="mt-1 text-xs" style={{ color: COLORS.textSecondary }}>
            {path.jobCount} open role{path.jobCount === 1 ? "" : "s"}
          </p>

          <div className="mt-3">
            <p className="mb-1.5 text-xs font-medium" style={{ color: COLORS.textSecondary }}>You already have</p>
            <div className="flex flex-wrap gap-1.5">
              {path.matchingSkills.length ? path.matchingSkills.map((s) => (
                <span key={s} className="rounded-full px-2.5 py-1 text-[11px] font-medium" style={{ background: "rgba(22,163,74,0.1)", color: COLORS.success }}>{s}</span>
              )) : <span className="text-xs" style={{ color: COLORS.textSecondary }}>None yet</span>}
            </div>
          </div>

          {path.missingSkills.length > 0 && (
            <div className="mt-3">
              <p className="mb-1.5 text-xs font-medium" style={{ color: COLORS.textSecondary }}>Skills to build</p>
              <div className="flex flex-wrap gap-1.5">
                {path.missingSkills.map((s) => (
                  <span key={s} className="rounded-full px-2.5 py-1 text-[11px] font-medium" style={{ background: "rgba(220,38,38,0.06)", color: COLORS.error }}>{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
