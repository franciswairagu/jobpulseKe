// Desired-role helpers for the CV Analyzer.
//
// The candidate tells us (or we infer from their CV) which roles they are
// looking for. Jobs matching those titles are shown FIRST with their match
// score; every other match follows. Pure functions only — no client/API deps.

const SENIORITY_WORDS = new Set([
  "senior", "sr", "junior", "jr", "entry", "mid", "lead", "principal",
  "staff", "associate", "intern", "chief", "head", "the", "of", "and", "a",
  "i", "ii", "iii", "iv", "1", "2", "3", "4",
]);

const WORD_EQUIVALENTS = {
  engineer: "developer",
  programmer: "developer",
  coder: "developer",
  dev: "developer",
  devs: "developer",
  analysts: "analyst",
  analytics: "analysis",
  "ml": "machine learning",
  "ai": "artificial intelligence",
};

/**
 * Role library used for two things:
 *  1. inferring likely desired roles from a CV's detected skills
 *  2. offering suggestions in the "roles you're looking for" input
 * Skill keywords follow the backend skill-extractor naming (lowercase).
 */
export const ROLE_LIBRARY = [
  { role: "Frontend Developer", skills: ["react", "javascript", "typescript", "css", "html", "vue", "angular", "next.js", "tailwind"] },
  { role: "Backend Developer", skills: ["python", "java", "node.js", "api", "django", "spring", "golang", "go", "php", "ruby", "express"] },
  { role: "Full Stack Developer", skills: ["react", "node.js", "javascript", "python", "api", "mongodb", "sql", "html", "css"] },
  { role: "Data Scientist", skills: ["machine learning", "python", "statistics", "pandas", "numpy", "tensorflow", "pytorch", "deep learning", "scikit-learn"] },
  { role: "Data Analyst", skills: ["sql", "excel", "power bi", "tableau", "python", "statistics", "data visualization", "reporting"] },
  { role: "Data Engineer", skills: ["sql", "spark", "airflow", "etl", "kafka", "hadoop", "python", "data pipelines", "aws"] },
  { role: "Machine Learning Engineer", skills: ["machine learning", "python", "tensorflow", "pytorch", "nlp", "deep learning", "artificial intelligence"] },
  { role: "DevOps Engineer", skills: ["docker", "kubernetes", "terraform", "aws", "ci/cd", "jenkins", "linux", "ansible", "git"] },
  { role: "Cloud Engineer", skills: ["aws", "azure", "gcp", "cloud", "docker", "kubernetes", "terraform", "linux"] },
  { role: "Mobile Developer", skills: ["android", "ios", "flutter", "react native", "swift", "kotlin", "mobile"] },
  { role: "Cybersecurity Analyst", skills: ["security", "cybersecurity", "siem", "firewall", "penetration testing", "network security", "information security"] },
  { role: "QA Engineer", skills: ["selenium", "testing", "cypress", "qa", "automation testing", "manual testing", "jira"] },
  { role: "Product Manager", skills: ["product management", "roadmap", "agile", "stakeholder", "jira", "scrum", "product"] },
  { role: "Business Analyst", skills: ["requirements", "sql", "excel", "stakeholder", "agile", "tableau", "process improvement", "documentation"] },
  { role: "UI/UX Designer", skills: ["figma", "sketch", "ui design", "ux", "prototyping", "adobe xd", "wireframing"] },
  { role: "Network Engineer", skills: ["cisco", "routing", "switching", "network", "ccna", "tcp/ip", "dns"] },
  { role: "Systems Administrator", skills: ["linux", "windows server", "active directory", "vmware", "system administration", "powershell"] },
  { role: "Database Administrator", skills: ["sql", "oracle", "mysql", "postgresql", "database", "backup", "db2"] },
  { role: "Technical Support", skills: ["troubleshooting", "helpdesk", "customer service", "ticketing", "it support", "hardware"] },
];

export const SUGGESTED_ROLES = ROLE_LIBRARY.map((r) => r.role);

const MAX_DESIRED_ROLES = 6;

function normalizeSkill(value) {
  return String(value || "")
    .toLowerCase()
    .trim()
    .replace(/[-_]+/g, " ")
    .replace(/\s+/g, " ");
}

function canonToken(token) {
  const mapped = WORD_EQUIVALENTS[token];
  if (!mapped) return [token];
  return mapped.includes(" ") ? mapped.split(" ") : [mapped];
}

/** Lowercased, seniority-stripped, synonym-canonicalised tokens for a title. */
export function titleTokens(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9+#./ ]/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .filter((t) => !SENIORITY_WORDS.has(t))
    .flatMap(canonToken);
}

/**
 * Does a desired role match a job title?
 * Seniority words are ignored ("Senior Frontend Engineer" ~ "Frontend Developer")
 * and developer/engineer/programmer are treated as equivalent. Tokens of the
 * shorter phrase must be fully contained in the other, so "Data Scientist"
 * never matches "Data Analyst".
 */
export function roleMatchesTitle(role, title) {
  const r = titleTokens(role);
  const t = titleTokens(title);
  if (!r.length || !t.length) return false;
  const rSet = new Set(r);
  const tSet = new Set(t);
  const allRoleInTitle = r.every((x) => tSet.has(x));
  const allTitleInRole = t.every((x) => rSet.has(x));
  return allRoleInTitle || allTitleInRole;
}

/** True when the job's title matches any of the candidate's desired roles. */
export function jobMatchesAnyRole(job, desiredRoles) {
  if (!job?.title || !desiredRoles?.length) return false;
  return desiredRoles.some((role) => roleMatchesTitle(role, job.title));
}

/**
 * Infer the roles a candidate is likely looking for from their CV analysis.
 * Scores each library role by overlap with the CV's detected skills and
 * returns the top `limit` role titles (empty when nothing overlaps).
 */
export function inferDesiredRoles(cvAnalysis, limit = 3) {
  const found = (cvAnalysis?.foundSkills || []).map(normalizeSkill).filter(Boolean);
  if (!found.length) return [];

  const strong = found.filter((s) => s.length >= 3);
  const foundSet = new Set(found);

  const scored = ROLE_LIBRARY.map(({ role, skills }) => {
    let score = 0;
    for (const raw of skills) {
      const kw = normalizeSkill(raw);
      if (foundSet.has(kw)) {
        score += 1;
        continue;
      }
      // Substring overlap only for meaningful tokens ("power bi" in
      // "power bi dashboards"); single-letter skills like "r" are exact-only.
      if (kw.length >= 3 && strong.some((f) => f.includes(kw) || kw.includes(f))) {
        score += 1;
      }
    }
    return { role, score };
  })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score);

  return scored.slice(0, limit).map((x) => x.role);
}

/** Add a role to the desired list (case-insensitive dedupe, capped). */
export function withAddedRole(desiredRoles, value) {
  const v = String(value || "").trim();
  if (!v) return desiredRoles;
  if (desiredRoles.length >= MAX_DESIRED_ROLES) return desiredRoles;
  if (desiredRoles.some((r) => r.toLowerCase() === v.toLowerCase())) return desiredRoles;
  return [...desiredRoles, v];
}

export { MAX_DESIRED_ROLES };
