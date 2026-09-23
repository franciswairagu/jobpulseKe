// ATS (Applicant Tracking System) scoring — how well an analyzed CV would
// pass an automated screen for one specific job posting (Jobscan-style).
//
// Raw CV text is never stored (backend privacy policy), so this scores the
// structured signals already available on both sides:
//   • keywords  = skills extracted server-side from the REAL job description
//                 at ingest time (required_skills + preferred_skills)
//   • seniority = CV seniority_level vs seniority words in the job title
//   • education = credentials found on the CV
//   • profile   = breadth of skills, years of experience, certifications
// Same philosophy as scoring.js: pure function, every sub-score visible.

import { combineMatchScore } from "./scoring";

const WEIGHTS = { keywords: 0.55, seniority: 0.15, education: 0.1, profile: 0.2 };

// Ladder shared by CV seniority labels and job-title detection.
// 0 junior/entry · 1 mid · 2 senior · 3 lead/principal · 4 management
const CV_RANK = {
  intern: 0,
  junior: 0,
  "entry level": 0,
  "mid-level": 1,
  mid: 1,
  professional: 1,
  senior: 2,
  lead: 3,
  principal: 3,
  head: 3,
  manager: 4,
  director: 4,
};

const RANK_LABELS = ["Junior/Entry", "Mid-level", "Senior", "Lead/Principal", "Management"];

function jobTitleRank(title) {
  const t = String(title || "").toLowerCase();
  if (/\b(intern|trainee|graduate)\b/.test(t)) return 0;
  if (/\b(junior|jr|entry)\b/.test(t)) return 0;
  if (/\b(mid|intermediate)\b/.test(t)) return 1;
  if (/\b(senior|sr)\b/.test(t)) return 2;
  if (/\b(lead|principal|staff|head|chief)\b/.test(t)) return 3;
  if (/\b(manager|director|vp)\b/.test(t)) return 4;
  return null;
}

function keywordScore(job, cvAnalysis) {
  const keywords = job.skillNames || [];
  const found = new Set((cvAnalysis.foundSkills || []).map((s) => String(s).toLowerCase()));
  const matched = keywords.filter((k) => found.has(String(k).toLowerCase()));
  const missing = keywords.filter((k) => !found.has(String(k).toLowerCase()));
  const score = keywords.length ? Math.round((matched.length / keywords.length) * 100) : 70;
  return { score, keywords, matched, missing };
}

function seniorityScore(cvAnalysis, jobTitle) {
  const cvLabel = cvAnalysis.profile?.currentRole || "Professional";
  const cvRank = CV_RANK[String(cvLabel).toLowerCase()] ?? 1;
  const jobRank = jobTitleRank(jobTitle);
  if (jobRank === null) {
    return { score: 75, cvLabel, jobLabel: null, gap: null };
  }
  const gap = Math.abs(cvRank - jobRank);
  const score = gap === 0 ? 100 : gap === 1 ? 60 : 20;
  return { score, cvLabel, jobLabel: RANK_LABELS[jobRank], gap };
}

function educationScore(cvAnalysis) {
  const education = cvAnalysis._raw?.education || [];
  return { score: education.length ? 100 : 0, count: education.length };
}

function profileScore(cvAnalysis) {
  const skills = (cvAnalysis.foundSkills || []).length;
  const years = cvAnalysis.profile?.yearsExperience || 0;
  const certs = (cvAnalysis._raw?.certifications || []).length;
  const score =
    Math.min(50, skills * 6.25) + Math.min(30, years * 10) + (certs > 0 ? 20 : 0);
  return { score: Math.round(score), skills, years, certs };
}

export function atsLabel(score) {
  if (score >= 80) return "ATS ready";
  if (score >= 60) return "Good coverage";
  if (score >= 40) return "Needs tailoring";
  return "Likely filtered out";
}

/**
 * Compute the ATS report for one job + the current CV analysis.
 * Returns the overall score, the four sub-scores, a Jobscan-style checklist,
 * matched/missing keyword lists and concrete fix tips.
 */
export function computeATSScore(job, cvAnalysis) {
  if (!cvAnalysis || !job) return null;

  const kw = keywordScore(job, cvAnalysis);
  const sen = seniorityScore(cvAnalysis, job.title);
  const edu = educationScore(cvAnalysis);
  const prof = profileScore(cvAnalysis);

  const score = combineMatchScore(
    { keywords: kw.score, seniority: sen.score, education: edu.score, profile: prof.score },
    WEIGHTS
  );

  const keywordStatus =
    kw.keywords.length === 0 ? "warn" : kw.score >= 70 ? "pass" : kw.score >= 40 ? "warn" : "fail";
  const seniorityStatus =
    sen.gap === null ? "warn" : sen.gap === 0 ? "pass" : sen.gap === 1 ? "warn" : "fail";
  const educationStatus = edu.score ? "pass" : "fail";
  const profileStatus = prof.score >= 80 ? "pass" : prof.score >= 50 ? "warn" : "fail";

  const checks = [
    {
      id: "keywords",
      label: "JD keywords on your CV",
      status: keywordStatus,
      detail:
        kw.keywords.length === 0
          ? "No keywords could be extracted from this posting"
          : `${kw.matched.length} of ${kw.keywords.length} keywords found`,
      value: kw.score,
    },
    {
      id: "seniority",
      label: "Seniority alignment",
      status: seniorityStatus,
      detail:
        sen.gap === null
          ? "Job title doesn't state a seniority level"
          : sen.gap === 0
          ? `${sen.cvLabel} CV fits this ${sen.jobLabel} role`
          : sen.gap === 1
          ? `One level apart — ${sen.cvLabel} CV vs ${sen.jobLabel} role`
          : `Large gap — ${sen.cvLabel} CV vs ${sen.jobLabel} role`,
      value: sen.score,
    },
    {
      id: "education",
      label: "Education listed",
      status: educationStatus,
      detail: edu.count ? `${edu.count} credential${edu.count > 1 ? "s" : ""} on your CV` : "No education found on your CV",
      value: edu.score,
    },
    {
      id: "profile",
      label: "Profile completeness",
      status: profileStatus,
      detail: `${prof.skills} skills · ${prof.years} yrs experience · ${prof.certs} cert${prof.certs === 1 ? "" : "s"}`,
      value: prof.score,
    },
  ];

  const tips = [];
  for (const m of kw.missing.slice(0, 5)) {
    tips.push(`Add “${m}” to your skills or experience section`);
  }
  if (educationStatus === "fail") {
    tips.push("List your education (degree, institution, year)");
  }
  if (profileStatus !== "pass") {
    tips.push("Add quantified achievements and your years of experience");
  }
  if (seniorityStatus === "fail" && sen.jobLabel) {
    tips.push(`Reframe your CV headline toward the ${sen.jobLabel} level of this role`);
  }

  return {
    score,
    label: atsLabel(score),
    keywordMatch: kw.score,
    seniorityMatch: sen.score,
    educationMatch: edu.score,
    profileMatch: prof.score,
    checks,
    matchedKeywords: kw.matched,
    missingKeywords: kw.missing,
    tips,
  };
}
