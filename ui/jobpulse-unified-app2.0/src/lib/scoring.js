// Transparent, explainable scoring used by the mock API layer.
// A real backend should implement these exact functions server-side against
// live market data — the frontend never invents a number itself.

/**
 * Learning-priority score for a missing skill.
 * Every input is 0-100 (or a difficulty label converted to 0-100) so the
 * output is easy to explain to a user: "high demand + fast growth + easy to
 * learn + relevant to your target role = high priority".
 */
const DIFFICULTY_EASE = { Low: 90, Medium: 55, High: 25 };

export function scoreSkillPriority({ demand, growthRate = 0, difficulty = "Medium", roleRelevance = 70 }) {
  const ease = DIFFICULTY_EASE[difficulty] ?? 55;
  const growthComponent = Math.max(0, Math.min(100, 50 + growthRate * 2));

  const weighted =
    demand * 0.4 + growthComponent * 0.2 + ease * 0.2 + roleRelevance * 0.2;

  let priority = "LOW";
  if (weighted >= 65) priority = "HIGH";
  else if (weighted >= 45) priority = "MEDIUM";

  return { score: Math.round(weighted), priority };
}

/**
 * Overall CV <-> market match score, and the CV <-> single job match score
 * share the same shape: a weighted blend of sub-scores, each of which is
 * independently visible to the user so the total is never a black box.
 */
export function combineMatchScore(subScores, weights) {
  const total = Object.keys(weights).reduce((sum, key) => {
    const val = subScores[key] ?? 0;
    return sum + val * weights[key];
  }, 0);
  return Math.round(total);
}

export function matchLabel(score) {
  if (score >= 90) return "Excellent match";
  if (score >= 75) return "Strong match";
  if (score >= 55) return "Good match";
  if (score >= 35) return "Partial match";
  return "Weak match";
}

/**
 * Pure CV <-> job matching function. Deliberately takes plain data (skill
 * names, not ids/objects) so it can be reused both for scoring a single job
 * (job details modal) and for ranking every job in bulk (Recommended Jobs
 * tab, "opportunities unlocked" what-if calculations) without depending on
 * mockData/client internals.
 */
export function computeJobMatch(job, jobSkillNames, cvAnalysis) {
  if (!cvAnalysis) return null;

  const foundSet = new Set(cvAnalysis.foundSkills);
  const overlap = jobSkillNames.filter((s) => foundSet.has(s));
  const missing = jobSkillNames.filter((s) => !foundSet.has(s));

  let skillMatch;
  if (jobSkillNames.length === 0) {
    skillMatch = 0;
  } else {
    skillMatch = Math.round((overlap.length / jobSkillNames.length) * 100);
  }
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
