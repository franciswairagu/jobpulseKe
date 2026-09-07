// ---------------------------------------------------------------------------
// Mock API client.
//
// Every function here has the exact shape of the real endpoint described in
// the JobPulse spec (POST /api/cv/analyze, GET /api/jobs, etc). Today they
// resolve from in-memory mock data with a simulated network delay. Wiring
// the app to a real backend later means rewriting the *body* of these
// functions to `fetch(...)` - no page or component needs to change, since
// they only ever import from this file.
// ---------------------------------------------------------------------------

import { SKILLS, SKILL_MARKET_STATS, JOBS, SKILL_CATEGORIES, DATA_SOURCE_META } from "./mockData";
import { scoreSkillPriority, computeJobMatch, matchLabel } from "../lib/scoring";

const delay = (ms = 500) => new Promise((res) => setTimeout(res, ms));

function skillById(id) {
  return SKILLS.find((s) => s.id === id);
}

function statsFor(skillId) {
  return SKILL_MARKET_STATS.find((s) => s.skillId === skillId);
}

function statsForName(name) {
  const skill = SKILLS.find((s) => s.name === name);
  return skill ? statsFor(skill.id) : null;
}

function jobSkillNames(job) {
  return job.skills.map((id) => skillById(id)?.name).filter(Boolean);
}

// Single source of truth for "job + its match against a given CV analysis".
// Used by getJobs, getRecommendedJobs, matchJobToCV and the opportunity-
// unlock calculation below, so ranking and detail views can never disagree.
function jobWithMatch(job, cvAnalysis) {
  const names = jobSkillNames(job);
  const match = cvAnalysis ? computeJobMatch(job, names, cvAnalysis) : null;
  return { ...job, skillNames: names, match };
}

// GET /api/dashboard
export async function getDashboard({ region = "All Africa", period = "Last 6 months" } = {}) {
  await delay(400);
  const trending = [...SKILL_MARKET_STATS]
    .sort((a, b) => b.demand - a.demand)
    .slice(0, 8)
    .map((s) => ({ skill: skillById(s.skillId).name, value: s.demand }));

  const topSkill = SKILL_MARKET_STATS.reduce((a, b) => (b.demand > a.demand ? b : a));
  const fastestGrowing = SKILL_MARKET_STATS.reduce((a, b) => (b.growthRate > a.growthRate ? b : a));
  const avgSalary = Math.round(
    SKILL_MARKET_STATS.reduce((sum, s) => sum + s.avgSalary, 0) / SKILL_MARKET_STATS.length
  );
  const remotePct = Math.round((JOBS.filter((j) => j.remote).length / JOBS.length) * 100);

  return {
    filters: { region, period },
    snapshot: {
      mostDemandedSkill: { name: skillById(topSkill.skillId).name, detail: `Requested in ${topSkill.demand}% of postings` },
      fastestGrowingSkill: { name: skillById(fastestGrowing.skillId).name, growthRate: fastestGrowing.growthRate },
      avgSalary,
      remotePct,
    },
    trendingSkills: trending,
    highlightSkillTrend: {
      skill: skillById(topSkill.skillId).name,
      growthRate: topSkill.growthRate,
      points: topSkill.trend.map((value, i) => ({ month: ["Mar", "Apr", "May", "Jun", "Jul", "Aug"][i], value })),
    },
    dataSource: DATA_SOURCE_META,
  };
}

// GET /api/skills
export async function getMarketSkills({ query = "", sortKey = "demand", country, industry } = {}) {
  await delay(350);
  const q = query.trim().toLowerCase();
  let rows = SKILL_MARKET_STATS.map((s) => ({
    skill: skillById(s.skillId).name,
    skillId: s.skillId,
    demand: s.demand,
    growth: s.growthRate,
    jobs: s.jobCount,
    role: s.role,
    avgSalary: s.avgSalary,
    status: s.growthRate > 5 ? "Growing" : s.growthRate < -1 ? "Declining" : "Stable",
  }));
  if (q) rows = rows.filter((r) => r.skill.toLowerCase().includes(q));
  rows.sort((a, b) => b[sortKey] - a[sortKey]);
  return { skills: rows, total: rows.length, filters: { country, industry }, dataSource: DATA_SOURCE_META };
}

// GET /api/jobs
// Powers the "Recommended Jobs" tab inside CV Analyzer. When a cvAnalysis is
// passed in, every job is scored against it (via jobWithMatch/computeJobMatch)
// and results default to best-match-first - this is what makes job search
// "personalized" instead of a generic listing (spec sections 4, 14, 15).
export async function getRecommendedJobs({ query = "", country, remoteOnly = false, sortBy = "match", cvAnalysis = null } = {}) {
  await delay(350);
  const q = query.trim().toLowerCase();
  let rows = JOBS.map((j) => jobWithMatch(j, cvAnalysis));

  if (q) {
    rows = rows.filter(
      (j) =>
        j.title.toLowerCase().includes(q) ||
        j.company.toLowerCase().includes(q) ||
        j.skillNames.some((s) => s.toLowerCase().includes(q))
    );
  }
  if (country && country !== "All countries") rows = rows.filter((j) => j.country === country);
  if (remoteOnly) rows = rows.filter((j) => j.remote);

  const sorters = {
    match: (a, b) => (b.match?.matchScore ?? -1) - (a.match?.matchScore ?? -1),
    recent: (a, b) => new Date(b.postedAt) - new Date(a.postedAt),
    salary: (a, b) => b.salaryMax - a.salaryMax,
    fewestGaps: (a, b) => (a.match?.missingSkills.length ?? 99) - (b.match?.missingSkills.length ?? 99),
  };
  rows.sort(sorters[sortBy] ?? sorters.match);

  return { jobs: rows, total: rows.length, personalized: !!cvAnalysis };
}

// Kept for the generic (pre-CV) job listing case - same underlying data,
// no match scoring attached.
export async function getJobs(params = {}) {
  return getRecommendedJobs({ ...params, cvAnalysis: null });
}

// POST /api/cv/upload + POST /api/cv/analyze, combined for the mock.
// Returns the structured JSON shape specified in the product doc:
// { profile, skills, career_paths, strengths, weaknesses, missing_information }
export async function analyzeCV(file, onStageChange) {
  const stages = [
    "Extracting document",
    "Parsing profile",
    "Comparing with market data",
    "Calculating skill gaps",
    "Generating recommendations",
  ];
  for (const stage of stages) {
    onStageChange?.(stage);
    await delay(650);
  }

  // In a real pipeline this comes from the AI CV-parsing step (section 3).
  // The mock deterministically returns a fixed "found skills" set so the
  // rest of the app (dashboard personalization, job matching) has something
  // real to react to, regardless of which file was actually dropped.
  const foundSkillIds = ["python", "excel", "pandas", "power_bi"];
  const missingSkillIds = SKILLS.map((s) => s.id).filter((id) => !foundSkillIds.includes(id)).slice(0, 5);

  const missingSkills = missingSkillIds.map((id) => {
    const stats = statsFor(id);
    const difficulty = stats.demand > 60 ? "Medium" : stats.demand > 35 ? "Medium" : "High";
    const { score, priority } = scoreSkillPriority({
      demand: stats.demand,
      growthRate: stats.growthRate,
      difficulty,
      roleRelevance: 70,
    });
    return {
      name: skillById(id).name,
      demand: stats.demand,
      postings: stats.jobCount,
      difficulty,
      priority,
      priorityScore: score,
    };
  }).sort((a, b) => b.priorityScore - a.priorityScore);

  const overallMatch = Math.round(
    (foundSkillIds.length / (foundSkillIds.length + missingSkillIds.length)) * 100
  );

  const radar = SKILL_CATEGORIES.map((category, i) => ({
    category,
    you: [80, 35, 15, 75, 20, 70, 60][i],
    market: [70, 78, 60, 72, 45, 65, 55][i],
  }));

  return {
    profile: { name: file?.name?.split(".")[0] || "Candidate", currentRole: "Data Analyst", yearsExperience: 3, location: "Nairobi, Kenya" },
    foundSkills: foundSkillIds.map((id) => skillById(id).name),
    missingSkills,
    radar,
    overallMatch,
    biggestOpportunity: missingSkills[0],
    analyzedAt: new Date().toISOString(),
  };
}

// POST /api/jobs/:id/match
export async function matchJobToCV(job, cvAnalysis) {
  await delay(400);
  if (!cvAnalysis) return null;
  return computeJobMatch(job, jobSkillNames(job), cvAnalysis);
}

// Not a literal spec endpoint, but the calculation behind spec section 10/11
// ("Learning SQL could improve your eligibility for 37 additional jobs").
// For each of the user's missing skills, re-scores every job as if that one
// skill were added to the CV, and counts how many jobs cross from "not a
// real candidate" (<70% match) to a genuine match (>=70%). This is
// calculated from the same job data used everywhere else in the app, never
// invented, per the spec's explicit "only show this number if it can
// actually be calculated" rule.
const QUALIFYING_THRESHOLD = 70;

export async function getOpportunityUnlocks(cvAnalysis) {
  await delay(300);
  if (!cvAnalysis) return { unlocks: [] };

  const unlocks = cvAnalysis.missingSkills.map((missing) => {
    const hypotheticalCV = { ...cvAnalysis, foundSkills: [...cvAnalysis.foundSkills, missing.name] };
    let unlockedCount = 0;
    const unlockedJobIds = [];
    for (const job of JOBS) {
      const names = jobSkillNames(job);
      if (!names.includes(missing.name)) continue;
      const before = computeJobMatch(job, names, cvAnalysis).matchScore;
      const after = computeJobMatch(job, names, hypotheticalCV).matchScore;
      if (before < QUALIFYING_THRESHOLD && after >= QUALIFYING_THRESHOLD) {
        unlockedCount += 1;
        unlockedJobIds.push(job.id);
      }
    }
    return { skill: missing.name, priority: missing.priority, unlockedCount, unlockedJobIds };
  }).filter((u) => u.unlockedCount > 0)
    .sort((a, b) => b.unlockedCount - a.unlockedCount);

  return { unlocks };
}

// Not a literal spec endpoint either, but backs the "Career Paths" tab
// (section 12). Derives candidate career paths from the roles actually
// present in the market-stats/jobs mock data, then scores each one against
// the CV's found skills using the same transparent skill-overlap math as
// job matching - so "82% match for Data Analyst" is explainable the same
// way "84% match for this job" is.
export async function getCareerPaths(cvAnalysis) {
  await delay(400);
  if (!cvAnalysis) return { paths: [] };

  const roleToJobs = new Map();
  for (const job of JOBS) {
    if (!roleToJobs.has(job.title)) roleToJobs.set(job.title, []);
    roleToJobs.get(job.title).push(job);
  }

  const foundSet = new Set(cvAnalysis.foundSkills);
  const paths = [...roleToJobs.entries()].map(([role, jobsForRole]) => {
    const requiredSkillSet = new Set(jobsForRole.flatMap((j) => jobSkillNames(j)));
    const required = [...requiredSkillSet];
    const have = required.filter((s) => foundSet.has(s));
    const missing = required.filter((s) => !foundSet.has(s));
    const matchScore = required.length ? Math.round((have.length / required.length) * 100) : 0;
    const salaryMin = Math.min(...jobsForRole.map((j) => j.salaryMin));
    const salaryMax = Math.max(...jobsForRole.map((j) => j.salaryMax));

    return {
      role,
      matchScore,
      requiredSkills: required,
      matchingSkills: have,
      missingSkills: missing,
      salaryMin,
      salaryMax,
      jobCount: jobsForRole.length,
    };
  }).sort((a, b) => b.matchScore - a.matchScore);

  return { paths };
}

// Sync lookup (no network delay - it's cheap, and job-details UI needs it
// without another loading spinner): demand/priority context for a single
// skill by display name, used in the "skills you're missing" breakdown.
export function getSkillInsight(skillName) {
  const stats = statsForName(skillName);
  if (!stats) return null;
  const difficulty = stats.demand > 60 ? "Medium" : stats.demand > 35 ? "Medium" : "High";
  const { priority } = scoreSkillPriority({ demand: stats.demand, growthRate: stats.growthRate, difficulty, roleRelevance: 70 });
  return { demand: stats.demand, postings: stats.jobCount, growthRate: stats.growthRate, difficulty, priority };
}
