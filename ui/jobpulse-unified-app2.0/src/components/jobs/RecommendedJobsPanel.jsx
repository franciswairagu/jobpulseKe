import React, { useState, useCallback, useEffect } from "react";
import { X, Plus, Target } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";
import JobFilters from "./JobFilters";
import JobCard from "./JobCard";
import JobDetailsModal from "./JobDetailsModal";
import LoadingState from "../shared/LoadingState";
import EmptyState from "../shared/EmptyState";
import { getRecommendedJobs } from "../../api/client";
import { SUGGESTED_ROLES, withAddedRole } from "../../lib/roles";
import { useAsync } from "../../hooks/useAsync";
import { useSavedJobs } from "../../state/AppContext";

function SectionHeader({ title, subtitle, count }) {
  return (
    <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
      <div>
        <h3
          className="text-sm font-semibold uppercase tracking-wider"
          style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
        >
          {title}
        </h3>
        {subtitle && (
          <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>
            {subtitle}
          </p>
        )}
      </div>
      <span className="text-xs font-medium" style={{ color: COLORS.textMuted }}>
        {count} {count === 1 ? "role" : "roles"}
      </span>
    </div>
  );
}

function JobGrid({ jobs, savedJobIds, toggleSaveJob, onOpenDetails }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-children">
      {jobs.map((job) => (
        <JobCard
          key={job.id}
          job={job}
          saved={savedJobIds.includes(job.id)}
          onToggleSave={toggleSaveJob}
          onOpenDetails={onOpenDetails}
        />
      ))}
    </div>
  );
}

export default function RecommendedJobsPanel({
  cvAnalysis,
  initialFocusSkill,
  initialDesiredRoles = [],
  onAddLearningGoal,
}) {
  const [query, setQuery] = useState(initialFocusSkill ?? "");
  const [country, setCountry] = useState("All countries");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [sortBy, setSortBy] = useState("match");
  const [showFilters, setShowFilters] = useState(false);
  const [openJob, setOpenJob] = useState(null);
  const [desiredRoles, setDesiredRoles] = useState(initialDesiredRoles);
  const [roleInput, setRoleInput] = useState("");
  const { savedJobIds, toggleSaveJob } = useSavedJobs();

  useEffect(() => {
    if (initialFocusSkill) setQuery(initialFocusSkill);
  }, [initialFocusSkill]);

  // Re-seed from CV inference whenever a new analysis arrives, but keep any
  // edits the candidate made for the lifetime of the current analysis.
  useEffect(() => {
    setDesiredRoles(initialDesiredRoles);
  }, [initialDesiredRoles]);

  const fetcher = useCallback(
    () => getRecommendedJobs({ query, country, remoteOnly, sortBy, cvAnalysis, desiredRoles }),
    [query, country, remoteOnly, sortBy, cvAnalysis, desiredRoles]
  );
  const { status, data, error, refetch } = useAsync(fetcher, [
    query,
    country,
    remoteOnly,
    sortBy,
    cvAnalysis,
    desiredRoles,
  ]);

  const addRole = (value) => {
    setDesiredRoles((prev) => withAddedRole(prev, value));
    setRoleInput("");
  };

  const removeRole = (role) => {
    setDesiredRoles((prev) => prev.filter((r) => r !== role));
  };

  const showSections = !!cvAnalysis && desiredRoles.length > 0;
  const targetJobs = showSections ? data?.jobs?.filter((j) => j.isTargetRole) ?? [] : [];
  const otherJobs = showSections ? data?.jobs?.filter((j) => !j.isTargetRole) ?? [] : [];

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2
            className="text-lg font-semibold"
            style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
          >
            {cvAnalysis ? "Jobs matched to your CV" : "Open roles"}
          </h2>
          <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>
            {cvAnalysis
              ? "Roles you're looking for come first with their match — then everything else."
              : "Analyze your CV to see personalized match scores here."}
          </p>
        </div>
      </div>

      {cvAnalysis && (
        <div
          className="mb-4 rounded-2xl border p-4"
          style={{ borderColor: COLORS.border, background: "#fff" }}
        >
          <div className="flex items-start gap-2.5">
            <span
              className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg"
              style={{ background: "rgba(250,81,15,0.08)", color: COLORS.accent }}
            >
              <Target size={15} />
            </span>
            <div className="min-w-0 flex-1">
              <p
                className="text-sm font-semibold"
                style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
              >
                Roles you're looking for
              </p>
              <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>
                These roles are shown first with their match score — other matches follow.
                {desiredRoles.length === 0 && " Add a role to get started."}
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                {desiredRoles.map((role) => (
                  <span
                    key={role}
                    className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium"
                    style={{ background: "rgba(250,81,15,0.08)", color: COLORS.accent }}
                  >
                    {role}
                    <button
                      onClick={() => removeRole(role)}
                      aria-label={`Remove ${role}`}
                      className="rounded-full p-0.5 transition-colors hover:bg-white/70"
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}

                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    addRole(roleInput);
                  }}
                  className="flex items-center gap-1.5"
                >
                  <input
                    list="desired-role-suggestions"
                    value={roleInput}
                    onChange={(e) => setRoleInput(e.target.value)}
                    placeholder="Add a role (e.g. Data Scientist)"
                    className="w-52 rounded-full border px-3 py-1.5 text-xs outline-none transition-all focus:border-accent"
                    style={{
                      borderColor: COLORS.border,
                      color: COLORS.textDark,
                      background: "#fff",
                    }}
                  />
                  <button
                    type="submit"
                    aria-label="Add role"
                    className="flex h-7 w-7 items-center justify-center rounded-full text-white transition-all hover:scale-105"
                    style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
                  >
                    <Plus size={14} />
                  </button>
                  <datalist id="desired-role-suggestions">
                    {SUGGESTED_ROLES.map((r) => (
                      <option key={r} value={r} />
                    ))}
                  </datalist>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}

      <JobFilters
        query={query}
        onQueryChange={setQuery}
        country={country}
        onCountryChange={setCountry}
        remoteOnly={remoteOnly}
        onRemoteChange={setRemoteOnly}
        sortBy={sortBy}
        onSortChange={setSortBy}
        showFilters={showFilters}
        onToggleFilters={() => setShowFilters((s) => !s)}
        personalized={!!cvAnalysis}
      />

      <p className="mt-4 text-xs" style={{ color: COLORS.textMuted }}>
        {status === "success"
          ? `${data.total} open roles${
              showSections ? ` · ${data.targetCount} in your target roles` : ""
            }`
          : "\u00A0"}
        {savedJobIds.length > 0 && ` · ${savedJobIds.length} saved`}
      </p>

      <div className="mt-4">
        {status === "loading" && <LoadingState label="Loading open roles..." />}
        {status === "error" && (
          <EmptyState
            tone="error"
            title="Couldn't load jobs"
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
        )}
        {status === "success" && data.jobs.length === 0 && (
          <EmptyState
            title={`No roles match "${query}"`}
            description="Try a different title, skill or company."
          />
        )}
        {status === "success" && data.jobs.length > 0 && showSections && (
          <div className="space-y-8">
            <section>
              <SectionHeader
                title="Roles you're looking for"
                subtitle={desiredRoles.join(" · ")}
                count={targetJobs.length}
              />
              {targetJobs.length > 0 ? (
                <JobGrid
                  jobs={targetJobs}
                  savedJobIds={savedJobIds}
                  toggleSaveJob={toggleSaveJob}
                  onOpenDetails={setOpenJob}
                />
              ) : (
                <p
                  className="rounded-xl border border-dashed px-4 py-5 text-center text-sm"
                  style={{ borderColor: COLORS.border, color: COLORS.textSecondary }}
                >
                  No open roles matched your target titles right now — the closest matches
                  are listed below.
                </p>
              )}
            </section>

            {otherJobs.length > 0 && (
              <section>
                <SectionHeader
                  title="Other matches"
                  subtitle="Open roles ranked by skill and profile match."
                  count={otherJobs.length}
                />
                <JobGrid
                  jobs={otherJobs}
                  savedJobIds={savedJobIds}
                  toggleSaveJob={toggleSaveJob}
                  onOpenDetails={setOpenJob}
                />
              </section>
            )}
          </div>
        )}
        {status === "success" && data.jobs.length > 0 && !showSections && (
          <JobGrid
            jobs={data.jobs}
            savedJobIds={savedJobIds}
            toggleSaveJob={toggleSaveJob}
            onOpenDetails={setOpenJob}
          />
        )}
      </div>

      {openJob && (
        <JobDetailsModal
          job={openJob}
          onClose={() => setOpenJob(null)}
          onAddLearningGoal={onAddLearningGoal}
        />
      )}
    </div>
  );
}
