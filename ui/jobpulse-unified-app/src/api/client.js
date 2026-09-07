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
import { scoreSkillPriority, combineMatchScore, matchLabel } from "../lib/scoring";

const delay = (ms = 500) => new Promise((res) => setTimeout(res, ms));

function skillById(id) {
  return SKILLS.find((s) => s.id === id);
}

function statsFor(skillId) {
  return SKILL_MARKET_STATS.find((s) => s.skillId === skillId);
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
export async function getJobs({ query = "", country, remoteOnly = false } = {}) {
  await delay(350);
  const q = query.trim().toLowerCase();
  let rows = JOBS.map((j) => ({ ...j, skillNames: j.skills.map((id) => skillById(id).name) }));
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
  return { jobs: rows, total: rows.length };
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
  await delay(500);
  if (!cvAnalysis) return null;

  const foundSet = new Set(cvAnalysis.foundSkills);
  const jobSkillNames = job.skills.map((id) => skillById(id)?.name).filter(Boolean);
  const overlap = jobSkillNames.filter((s) => foundSet.has(s));
  const missing = jobSkillNames.filter((s) => !foundSet.has(s));

  const skillMatch = jobSkillNames.length ? Math.round((overlap.length / jobSkillNames.length) * 100) : 0;
  // Deterministic stand-ins for experience/education/location match - a real
  // implementation compares the parsed CV profile against job requirements.
  const experienceMatch = Math.min(100, 60 + cvAnalysis.profile.yearsExperience * 6);
  const educationMatch = 85;
  const locationMatch = job.country === cvAnalysis.profile.location.split(", ").pop() ? 100 : job.remote ? 90 : 55;

  const matchScore = combineMatchScore(
    { skill: skillMatch, experience: experienceMatch, education: educationMatch, location: locationMatch },
    { skill: 0.5, experience: 0.25, education: 0.15, location: 0.1 }
  );

  return {
    matchScore,
    skillMatch,
    experienceMatch,
    educationMatch,
    locationMatch,
    strengths: overlap,
    missingSkills: missing,
    recommendation: matchLabel(matchScore),
  };
}
