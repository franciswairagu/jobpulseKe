// ---------------------------------------------------------------------------
// API client — calls the real FastAPI backend.
//
// Auth tokens are read from localStorage (set by AuthContext). The Vite dev
// proxy forwards /api/* to http://localhost:8000 so no CORS issues in dev.
// ---------------------------------------------------------------------------

import { scoreSkillPriority, computeJobMatch, matchLabel } from "../lib/scoring";

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

function getAuthToken() {
  try {
    const raw = localStorage.getItem("jobpulse_auth");
    if (raw) {
      const { token } = JSON.parse(raw);
      return token;
    }
  } catch {}
  return null;
}

async function apiFetch(path, options = {}) {
  const token = getAuthToken();
  const headers = { ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body?.error?.message || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ---------------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------------

export async function registerUser({ name, email, password }) {
  const data = await apiFetch("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
  // Auto-login after register
  return loginUser({ email, password });
}

export async function loginUser({ email, password }) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message || "Login failed");
  }
  return res.json();
}

export async function fetchMe() {
  return apiFetch("/api/auth/me");
}

// ---------------------------------------------------------------------------
// Job adapters — transform backend shape to frontend shape
// ---------------------------------------------------------------------------

function adaptJob(job) {
  const skillNames = [...(job.required_skills || []), ...(job.preferred_skills || [])];
  return {
    id: job.id,
    title: job.title,
    company: job.company || "Unknown",
    country: job.country || "Remote",
    city: job.city,
    remote: job.remote,
    work_mode: job.work_mode,
    employment_type: job.employment_type,
    skills: skillNames,
    skillNames,
    experienceMin: 1,
    experienceMax: 5,
    postedAt: job.posted_at,
    source: job.source,
    sourceUrl: job.source_url,
    status: job.status,
  };
}

function jobSkillNames(job) {
  return job.skillNames || job.skills || [];
}

function jobWithMatch(job, cvAnalysis) {
  const names = jobSkillNames(job);
  const match = cvAnalysis ? computeJobMatch(job, names, cvAnalysis) : null;
  return { ...job, skillNames: names, match };
}

// ---------------------------------------------------------------------------
// Skill-market helpers — derived from DB aggregates
// ---------------------------------------------------------------------------

function buildSkillStatsFromJobs(jobs) {
  const skillMap = new Map();
  for (const job of jobs) {
    const names = jobSkillNames(job);
    for (const name of names) {
      if (!skillMap.has(name)) {
        skillMap.set(name, { name, demand: 0, jobCount: 0, countries: new Set() });
      }
      const s = skillMap.get(name);
      s.demand += 1;
      s.jobCount += 1;
      if (job.country) s.countries.add(job.country);
    }
  }

  const totalJobs = jobs.length || 1;
  return [...skillMap.values()]
    .map((s) => ({
      skill: s.name,
      demand: Math.round((s.demand / totalJobs) * 100),
      growth: 0,
      jobs: s.jobCount,
      role: s.name,
      status: "Stable",
    }))
    .sort((a, b) => b.demand - a.demand);
}

// ---------------------------------------------------------------------------
// GET /api/dashboard
// ---------------------------------------------------------------------------

export async function getDashboard({ region = "All Africa", period = "Last 6 months" } = {}) {
  const data = await apiFetch("/api/dashboard");

  const trending = (data.market_insights?.top_skills || []).slice(0, 8).map((s) => ({
    skill: s.skill,
    value: s.count,
  }));

  const totalJobs = data.market_insights?.total_available_jobs || 1;
  const topSkill = trending[0] || { skill: "N/A", value: 0 };
  const remotePct = data.market_insights?.remote_pct ?? (
    data.available_jobs?.length
      ? Math.round((data.available_jobs.filter((j) => j.remote).length / data.available_jobs.length) * 100)
      : 0
  );

  return {
    filters: { region, period },
    snapshot: {
      mostDemandedSkill: { name: topSkill.skill, detail: `Requested in ${topSkill.value} postings` },
      fastestGrowingSkill: { name: topSkill.skill, growthRate: 0 },
      remotePct,
    },
    trendingSkills: trending,
    highlightSkillTrend: {
      skill: topSkill.skill,
      growthRate: 0,
      points: [],
    },
    dataSource: {
      source: "JobPulseKE database",
      collectedAt: new Date().toISOString().split("T")[0],
      sampleSize: totalJobs,
    },
    // Pass through real data for personalization
    _cvScore: data.cv_score,
    _skills: data.skills,
    _skillsToImprove: data.skills_to_improve,
    _recommendations: data.recommendations,
    _availableJobs: (data.available_jobs || []).map(adaptJob),
  };
}

// ---------------------------------------------------------------------------
// GET /api/skills
// ---------------------------------------------------------------------------

export async function getMarketSkills({ query = "", sortKey = "demand", country, industry } = {}) {
  const params = new URLSearchParams();
  if (country && country !== "All countries") params.set("country", country);
  params.set("limit", "100");

  const data = await apiFetch(`/api/jobs/skills/demand?${params}`);
  let rows = (data.skills || []).map((s) => ({
    skill: s.skill,
    demand: s.demand,
    growth: s.growth || 0,
    jobs: s.jobs,
    role: s.role || s.skill,
    status: s.status || "Stable",
  }));
  if (query.trim()) {
    const q = query.trim().toLowerCase();
    rows = rows.filter((r) => r.skill.toLowerCase().includes(q));
  }
  rows.sort((a, b) => b[sortKey] - a[sortKey]);

  return {
    skills: rows,
    total: rows.length,
    filters: { country, industry },
    dataSource: data.dataSource || { source: "JobPulseKE database", collectedAt: new Date().toISOString().split("T")[0] },
  };
}

// ---------------------------------------------------------------------------
// GET /api/jobs (with optional CV-based matching)
// ---------------------------------------------------------------------------

export async function getRecommendedJobs({ query = "", country, remoteOnly = false, sortBy = "match", cvAnalysis = null } = {}) {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  if (country && country !== "All countries") params.set("country", country);
  if (remoteOnly) params.set("remote", "true");
  params.set("limit", "100");

  const data = await apiFetch(`/api/jobs?${params}`);
  let rows = (data.jobs || []).map(adaptJob).map((j) => jobWithMatch(j, cvAnalysis));

  const sorters = {
    match: (a, b) => {
      const aHas = a.skillNames?.length > 0 ? 1 : 0;
      const bHas = b.skillNames?.length > 0 ? 1 : 0;
      if (aHas !== bHas) return bHas - aHas;
      return (b.match?.matchScore ?? -1) - (a.match?.matchScore ?? -1);
    },
    recent: (a, b) => new Date(b.postedAt || 0) - new Date(a.postedAt || 0),
    fewestGaps: (a, b) => (a.match?.missingSkills.length ?? 99) - (b.match?.missingSkills.length ?? 99),
  };
  rows.sort(sorters[sortBy] ?? sorters.match);

  return { jobs: rows, total: rows.length, personalized: !!cvAnalysis };
}

export async function getJobs(params = {}) {
  return getRecommendedJobs({ ...params, cvAnalysis: null });
}

// ---------------------------------------------------------------------------
// POST /api/cv/upload + POST /api/cv/{id}/analyze + GET /api/cv/{id}
// ---------------------------------------------------------------------------

export async function analyzeCV(file, onStageChange) {
  const stages = ["Uploading CV", "Analyzing skills", "Extracting metadata", "Computing match scores", "Generating recommendations"];

  onStageChange?.(stages[0]);
  const uploadRes = await apiFetch("/api/cv/upload", {
    method: "POST",
    body: (() => { const fd = new FormData(); fd.append("file", file); return fd; })(),
  });
  const resumeId = uploadRes.resume_id;

  onStageChange?.(stages[1]);
  await apiFetch(`/api/cv/${resumeId}/analyze`, { method: "POST" });

  // Poll for completion
  for (let i = 2; i < stages.length; i++) {
    onStageChange?.(stages[i]);
    await new Promise((r) => setTimeout(r, 800));
  }

  let analysis = null;
  for (let attempt = 0; attempt < 30; attempt++) {
    const status = await apiFetch(`/api/cv/${resumeId}/status`);
    const st = status.status?.toLowerCase();
    if (st === "completed") {
      analysis = await apiFetch(`/api/cv/${resumeId}`);
      break;
    }
    if (st === "failed") {
      throw new Error(status.error_message || "CV analysis failed");
    }
    await new Promise((r) => setTimeout(r, 1000));
  }

  if (!analysis) throw new Error("CV analysis timed out");

  // Transform backend CV analysis to frontend shape
  const foundSkills = (analysis.skills || []).map((s) => s.name);

  // Get all jobs to compute missing skill priorities
  const jobData = await apiFetch("/api/jobs?limit=200");
  const allJobs = (jobData.jobs || []).map(adaptJob);

  // Build skill stats from jobs
  const skillStats = buildSkillStatsFromJobs(allJobs);

  const missingSkills = (analysis.missing_skills || []).slice(0, 8).map((name) => {
    const stats = skillStats.find((s) => s.skill.toLowerCase() === name.toLowerCase());
    const difficulty = (stats?.demand || 0) > 60 ? "Medium" : (stats?.demand || 0) > 35 ? "Medium" : "High";
    const { score, priority } = scoreSkillPriority({
      demand: stats?.demand || 50,
      growthRate: stats?.growth || 0,
      difficulty,
      roleRelevance: 70,
    });
    return {
      name,
      demand: stats?.demand || 50,
      postings: stats?.jobs || 0,
      difficulty,
      priority,
      priorityScore: score,
    };
  }).sort((a, b) => b.priorityScore - a.priorityScore);

  const overallMatch = analysis.cv_score || Math.round(
    (foundSkills.length / (foundSkills.length + missingSkills.length)) * 100
  );

  const SKILL_CATEGORIES = ["Programming", "Databases", "Cloud", "Data Analytics", "Machine Learning", "Visualization", "Soft Skills"];
  const radar = SKILL_CATEGORIES.map((category, i) => ({
    category,
    you: Math.min(100, 30 + (foundSkills.length * 8) + i * 5),
    market: 50 + i * 7,
  }));

  return {
    profile: {
      name: file?.name?.split(".")[0] || "Candidate",
      currentRole: analysis.seniority_level || "Professional",
      yearsExperience: analysis.years_experience || 3,
      location: "Kenya",
    },
    foundSkills,
    missingSkills,
    radar,
    overallMatch,
    biggestOpportunity: missingSkills[0] || null,
    analyzedAt: analysis.created_at,
    // Pass through raw backend data for downstream use
    _raw: analysis,
    _resumeId: resumeId,
  };
}

// ---------------------------------------------------------------------------
// POST /api/jobs/:id/match
// ---------------------------------------------------------------------------

export async function matchJobToCV(job, cvAnalysis) {
  if (!cvAnalysis) return null;
  const names = jobSkillNames(job);
  return computeJobMatch(job, names, cvAnalysis);
}

// ---------------------------------------------------------------------------
// Opportunity unlocks (derived from jobs + CV analysis)
// ---------------------------------------------------------------------------

const QUALIFYING_THRESHOLD = 70;

export async function getOpportunityUnlocks(cvAnalysis) {
  if (!cvAnalysis) return { unlocks: [] };

  const jobData = await apiFetch("/api/jobs?limit=200");
  const jobs = (jobData.jobs || []).map(adaptJob);

  const unlocks = (cvAnalysis.missingSkills || []).map((missing) => {
    const hypotheticalCV = { ...cvAnalysis, foundSkills: [...cvAnalysis.foundSkills, missing.name] };
    let unlockedCount = 0;
    const unlockedJobIds = [];
    for (const job of jobs) {
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
  })
    .filter((u) => u.unlockedCount > 0)
    .sort((a, b) => b.unlockedCount - a.unlockedCount);

  return { unlocks };
}

// ---------------------------------------------------------------------------
// Career paths (derived from job data)
// ---------------------------------------------------------------------------

export async function getCareerPaths(cvAnalysis) {
  if (!cvAnalysis) return { paths: [] };

  const jobData = await apiFetch("/api/jobs?limit=200");
  const jobs = (jobData.jobs || []).map(adaptJob);

  const roleToJobs = new Map();
  for (const job of jobs) {
    if (!roleToJobs.has(job.title)) roleToJobs.set(job.title, []);
    roleToJobs.get(job.title).push(job);
  }

  const foundSet = new Set(cvAnalysis.foundSkills);
  const paths = [...roleToJobs.entries()]
    .map(([role, jobsForRole]) => {
      const requiredSkillSet = new Set(jobsForRole.flatMap((j) => jobSkillNames(j)));
      const required = [...requiredSkillSet];
      const have = required.filter((s) => foundSet.has(s));
      const missing = required.filter((s) => !foundSet.has(s));
      const matchScore = required.length ? Math.round((have.length / required.length) * 100) : 0;
      return { role, matchScore, requiredSkills: required, matchingSkills: have, missingSkills: missing, jobCount: jobsForRole.length };
    })
    .sort((a, b) => b.matchScore - a.matchScore);

  return { paths };
}

// ---------------------------------------------------------------------------
// Career insights (analytics data + user profile)
// ---------------------------------------------------------------------------

export async function getCareerInsights() {
  return apiFetch("/api/career-insights");
}

// ---------------------------------------------------------------------------
// Sync skill insight lookup
// ---------------------------------------------------------------------------

export function getSkillInsight(skillName) {
  return { demand: 50, postings: 0, growthRate: 0, difficulty: "Medium", priority: "MEDIUM" };
}

// ---------------------------------------------------------------------------
// POST /api/rag/ask — AI assistant (RAG-powered)
// ---------------------------------------------------------------------------

export async function askRAG(question, topK = 5) {
  return apiFetch("/api/rag/ask", {
    method: "POST",
    body: JSON.stringify({ question, top_k: topK }),
  });
}

// ---------------------------------------------------------------------------
// GET /api/recommendations — courses + interview prep from backend
// ---------------------------------------------------------------------------

export async function getRecommendations() {
  try {
    const data = await apiFetch("/api/recommendations");
    return {
      courses: (data.courses || []).map((r) => ({
        title: r.title,
        skill: r.related_skill,
        provider: r.provider,
        url: r.url,
        reason: r.reason,
        priority: r.priority,
        duration: r.duration || "Self-paced",
        difficulty: r.difficulty || "All levels",
      })),
      interviewPrep: (data.interview_platforms || []).map((r) => ({
        title: r.title,
        skill: r.related_skill,
        provider: r.provider,
        url: r.url,
        reason: r.reason,
        duration: r.duration || "30 min",
        format: r.difficulty || "Mock interview",
      })),
    };
  } catch {
    return { courses: [], interviewPrep: [] };
  }
}
