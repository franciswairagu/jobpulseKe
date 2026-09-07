import React, { useState, useCallback, useEffect } from "react";
import { COLORS, FONTS } from "../../lib/theme";
import JobFilters from "./JobFilters";
import JobCard from "./JobCard";
import JobDetailsModal from "./JobDetailsModal";
import LoadingState from "../shared/LoadingState";
import EmptyState from "../shared/EmptyState";
import { getRecommendedJobs } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";
import { useSavedJobs } from "../../state/AppContext";

// This is what used to be the standalone JobMarket.jsx page - refactored
// into a panel that lives inside CV Analyzer's "Recommended Jobs" tab
// (spec sections 3, 6, 14, 16). Same search/filter/card UI, now personalized
// whenever a cvAnalysis is available.
export default function RecommendedJobsPanel({ cvAnalysis, initialFocusSkill, onAddLearningGoal }) {
  const [query, setQuery] = useState(initialFocusSkill ?? "");
  const [country, setCountry] = useState("All countries");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [sortBy, setSortBy] = useState("match");
  const [showFilters, setShowFilters] = useState(false);
  const [openJob, setOpenJob] = useState(null);
  const { savedJobIds, toggleSaveJob } = useSavedJobs();

  useEffect(() => {
    if (initialFocusSkill) setQuery(initialFocusSkill);
  }, [initialFocusSkill]);

  const fetcher = useCallback(
    () => getRecommendedJobs({ query, country, remoteOnly, sortBy, cvAnalysis }),
    [query, country, remoteOnly, sortBy, cvAnalysis]
  );
  const { status, data, error, refetch } = useAsync(fetcher, [query, country, remoteOnly, sortBy, cvAnalysis]);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
            {cvAnalysis ? "Jobs matched to your CV" : "Open roles"}
          </h2>
          <p className="text-xs" style={{ color: COLORS.textSecondary }}>
            {cvAnalysis ? "Open roles that match your skills, experience, and career profile." : "Analyze your CV to see personalized match scores here."}
          </p>
        </div>
      </div>

      <JobFilters
        query={query} onQueryChange={setQuery}
        country={country} onCountryChange={setCountry}
        remoteOnly={remoteOnly} onRemoteChange={setRemoteOnly}
        sortBy={sortBy} onSortChange={setSortBy}
        showFilters={showFilters} onToggleFilters={() => setShowFilters((s) => !s)}
        personalized={!!cvAnalysis}
      />

      <p className="mt-4 text-xs" style={{ color: COLORS.textSecondary }}>
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
              <JobCard key={job.id} job={job} saved={savedJobIds.includes(job.id)} onToggleSave={toggleSaveJob} onOpenDetails={setOpenJob} />
            ))}
          </div>
        )}
      </div>

      {openJob && <JobDetailsModal job={openJob} onClose={() => setOpenJob(null)} onAddLearningGoal={onAddLearningGoal} />}
    </div>
  );
}
