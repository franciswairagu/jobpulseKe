// Seed data shaped exactly like the normalized schema described in the
// product spec (skills / skill_market_stats / jobs). This is what a real
// Postgres-backed API would return - swapping client.js to call a real
// backend later requires no change to any page component.

export const SKILLS = [
  { id: "sql", name: "SQL", category: "Data" },
  { id: "python", name: "Python", category: "Programming" },
  { id: "excel", name: "Excel", category: "Data" },
  { id: "power_bi", name: "Power BI", category: "Visualization" },
  { id: "aws", name: "AWS", category: "Cloud" },
  { id: "javascript", name: "JavaScript", category: "Programming" },
  { id: "tableau", name: "Tableau", category: "Visualization" },
  { id: "machine_learning", name: "Machine Learning", category: "AI/ML" },
  { id: "docker", name: "Docker", category: "Cloud" },
  { id: "r", name: "R", category: "Data" },
  { id: "pandas", name: "Pandas", category: "Programming" },
];

export const SKILL_MARKET_STATS = [
  { skillId: "sql", demand: 72, growthRate: 18.4, jobCount: 4820, avgSalary: 1450, role: "Data Analyst", trend: [54, 58, 60, 63, 67, 72] },
  { skillId: "python", demand: 68, growthRate: 12.1, jobCount: 4350, avgSalary: 1980, role: "Data Scientist", trend: [58, 60, 61, 64, 66, 68] },
  { skillId: "excel", demand: 61, growthRate: 2.0, jobCount: 3960, avgSalary: 1100, role: "Business Analyst", trend: [59, 59, 60, 60, 61, 61] },
  { skillId: "power_bi", demand: 55, growthRate: 21.3, jobCount: 3210, avgSalary: 1350, role: "BI Analyst", trend: [40, 43, 46, 49, 52, 55] },
  { skillId: "aws", demand: 49, growthRate: 25.0, jobCount: 2890, avgSalary: 2600, role: "Cloud Engineer", trend: [33, 37, 40, 43, 46, 49] },
  { skillId: "javascript", demand: 46, growthRate: 4.2, jobCount: 2640, avgSalary: 1500, role: "Frontend Developer", trend: [43, 44, 44, 45, 45, 46] },
  { skillId: "tableau", demand: 39, growthRate: -3.1, jobCount: 2015, avgSalary: 1300, role: "Data Analyst", trend: [45, 43, 42, 41, 40, 39] },
  { skillId: "machine_learning", demand: 35, growthRate: 15.4, jobCount: 1840, avgSalary: 2950, role: "ML Engineer", trend: [26, 28, 30, 32, 33, 35] },
  { skillId: "docker", demand: 33, growthRate: 19.2, jobCount: 1710, avgSalary: 2400, role: "DevOps Engineer", trend: [23, 26, 28, 30, 31, 33] },
  { skillId: "r", demand: 21, growthRate: -6.0, jobCount: 980, avgSalary: 1250, role: "Data Analyst", trend: [27, 25, 24, 23, 22, 21] },
];

export const JOBS = [
  { id: "job_1", title: "Data Analyst", company: "Zola Fintech", country: "Kenya", remote: true,
    skills: ["sql", "python", "power_bi", "excel"], experienceMin: 2, experienceMax: 4,
    salaryMin: 1200, salaryMax: 2000, currency: "USD", postedAt: "2026-08-21" },
  { id: "job_2", title: "Cloud Engineer", company: "NimbusWorks", country: "Nigeria", remote: true,
    skills: ["aws", "docker", "python"], experienceMin: 3, experienceMax: 5,
    salaryMin: 2200, salaryMax: 3400, currency: "USD", postedAt: "2026-08-18" },
  { id: "job_3", title: "BI Analyst", company: "Kaya Retail Group", country: "South Africa", remote: false,
    skills: ["power_bi", "sql", "excel"], experienceMin: 1, experienceMax: 3,
    salaryMin: 900, salaryMax: 1600, currency: "USD", postedAt: "2026-08-25" },
  { id: "job_4", title: "Machine Learning Engineer", company: "Sahel AI Labs", country: "Ghana", remote: true,
    skills: ["python", "machine_learning", "sql", "aws"], experienceMin: 3, experienceMax: 6,
    salaryMin: 2500, salaryMax: 4000, currency: "USD", postedAt: "2026-08-14" },
  { id: "job_5", title: "Data Scientist", company: "Amana Health", country: "Kenya", remote: false,
    skills: ["python", "machine_learning", "sql", "pandas"], experienceMin: 2, experienceMax: 5,
    salaryMin: 1800, salaryMax: 2900, currency: "USD", postedAt: "2026-08-27" },
  { id: "job_6", title: "Frontend Developer", company: "Duka Commerce", country: "Rwanda", remote: true,
    skills: ["javascript"], experienceMin: 1, experienceMax: 3,
    salaryMin: 1000, salaryMax: 1700, currency: "USD", postedAt: "2026-08-30" },
];

export const SKILL_CATEGORIES = ["Programming", "Databases", "Cloud", "Data Analytics", "Machine Learning", "Visualization", "Soft Skills"];

export const DATA_SOURCE_META = {
  source: "JobPulse ingestion pipeline (mock)",
  collectedAt: "2026-08-31",
  sampleSize: 10379,
  note: "Stands in for the real src/analytics output. Replace client.js internals with fetch() calls to /api/dashboard, /api/skills, /api/jobs once that backend exists.",
};
