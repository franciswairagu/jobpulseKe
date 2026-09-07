import React, { useState, useMemo } from "react";
import {
  Search,
  MapPin,
  Briefcase,
  Wifi,
  ChevronDown,
  Sparkles,
} from "lucide-react";

const NAVY = "#0B1F3A";
const DEEP_BLUE = "#123B63";
const LIGHT_BLUE = "#EAF3FA";
const PAGE_BG = "#F7F9FC";
const TEXT_DARK = "#172033";
const TEXT_SECONDARY = "#667085";
const SUCCESS = "#16A34A";

const jobs = [
  {
    title: "Data Analyst",
    company: "Zola Fintech",
    country: "Kenya",
    remote: true,
    skills: ["SQL", "Python", "Power BI", "Excel"],
    experience: "2–4 years",
    salaryMin: 1200,
    salaryMax: 2000,
  },
  {
    title: "Cloud Engineer",
    company: "NimbusWorks",
    country: "Nigeria",
    remote: true,
    skills: ["AWS", "Docker", "Terraform", "Python"],
    experience: "3–5 years",
    salaryMin: 2200,
    salaryMax: 3400,
  },
  {
    title: "BI Analyst",
    company: "Kaya Retail Group",
    country: "South Africa",
    remote: false,
    skills: ["Power BI", "SQL", "DAX", "Excel"],
    experience: "1–3 years",
    salaryMin: 900,
    salaryMax: 1600,
  },
  {
    title: "Machine Learning Engineer",
    company: "Sahel AI Labs",
    country: "Ghana",
    remote: true,
    skills: ["Python", "TensorFlow", "SQL", "AWS"],
    experience: "3–6 years",
    salaryMin: 2500,
    salaryMax: 4000,
  },
  {
    title: "Data Scientist",
    company: "Amana Health",
    country: "Kenya",
    remote: false,
    skills: ["Python", "Machine Learning", "SQL", "Pandas"],
    experience: "2–5 years",
    salaryMin: 1800,
    salaryMax: 2900,
  },
  {
    title: "Frontend Developer",
    company: "Duka Commerce",
    country: "Rwanda",
    remote: true,
    skills: ["JavaScript", "React", "TypeScript"],
    experience: "1–3 years",
    salaryMin: 1000,
    salaryMax: 1700,
  },
];

const filterGroups = [
  { label: "Country", options: ["All countries", "Kenya", "Nigeria", "South Africa", "Ghana", "Rwanda"] },
  { label: "Job type", options: ["All types", "Full-time", "Contract", "Internship"] },
  { label: "Experience", options: ["Any level", "Entry", "Mid", "Senior"] },
  { label: "Salary", options: ["Any range", "$500–1,500", "$1,500–3,000", "$3,000+"] },
];

function FilterDropdown({ label, options }) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(options[0]);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium"
        style={{ borderColor: "#E4E9F2", color: TEXT_DARK, background: "#fff" }}
      >
        <span style={{ color: TEXT_SECONDARY }}>{label}:</span>
        {value}
        <ChevronDown size={13} style={{ color: TEXT_SECONDARY }} />
      </button>
      {open && (
        <div
          className="absolute left-0 z-20 mt-1 w-44 overflow-hidden rounded-lg border bg-white shadow-lg"
          style={{ borderColor: "#E4E9F2" }}
        >
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => {
                setValue(opt);
                setOpen(false);
              }}
              className="block w-full px-3 py-2 text-left text-xs hover:bg-[#F7F9FC]"
              style={{
                color: opt === value ? DEEP_BLUE : TEXT_DARK,
                fontWeight: opt === value ? 600 : 400,
              }}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function JobCard({ job }) {
  return (
    <div
      className="flex flex-col justify-between rounded-2xl border p-5 transition-shadow hover:shadow-sm"
      style={{ borderColor: "#E4E9F2", background: "#fff" }}
    >
      <div>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3
              className="text-base font-semibold"
              style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
            >
              {job.title}
            </h3>
            <p className="mt-0.5 text-sm" style={{ color: TEXT_SECONDARY }}>
              {job.company}
            </p>
          </div>
          {job.remote && (
            <span
              className="flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium"
              style={{ background: LIGHT_BLUE, color: DEEP_BLUE }}
            >
              <Wifi size={11} /> Remote
            </span>
          )}
        </div>

        <div className="mt-3 flex items-center gap-1.5 text-xs" style={{ color: TEXT_SECONDARY }}>
          <MapPin size={13} />
          {job.country}
          <span className="mx-1">·</span>
          <Briefcase size={13} />
          {job.experience}
        </div>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {job.skills.map((s) => (
            <span
              key={s}
              className="rounded-full px-2.5 py-1 text-[11px] font-medium"
              style={{ background: "#F1F4F9", color: TEXT_DARK }}
            >
              {s}
            </span>
          ))}
        </div>

        <p
          className="mt-4 text-sm font-semibold"
          style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
        >
          ${job.salaryMin.toLocaleString()} – ${job.salaryMax.toLocaleString()}
          <span className="text-xs font-normal" style={{ color: TEXT_SECONDARY }}>
            {" "}
            /month
          </span>
        </p>
      </div>

      <div className="mt-5 flex gap-2">
        <button
          className="flex-1 rounded-lg px-4 py-2 text-sm font-semibold text-white"
          style={{ background: NAVY }}
        >
          View job
        </button>
        <button
          className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border px-4 py-2 text-sm font-semibold"
          style={{ borderColor: DEEP_BLUE, color: DEEP_BLUE }}
        >
          <Sparkles size={13} />
          Match with my CV
        </button>
      </div>
    </div>
  );
}

export default function JobMarket() {
  const [query, setQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return jobs;
    return jobs.filter(
      (j) =>
        j.title.toLowerCase().includes(q) ||
        j.company.toLowerCase().includes(q) ||
        j.skills.some((s) => s.toLowerCase().includes(q))
    );
  }, [query]);

  return (
    <div className="min-h-screen w-full" style={{ background: PAGE_BG, fontFamily: "Inter, sans-serif" }}>
      <div className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
        <h1
          className="text-2xl font-semibold sm:text-[28px]"
          style={{ color: TEXT_DARK, fontFamily: "Space Grotesk, sans-serif" }}
        >
          Job market
        </h1>
        <p className="mt-1.5 max-w-lg text-sm" style={{ color: TEXT_SECONDARY }}>
          Discover open tech roles across African markets, matched to what you
          bring.
        </p>

        {/* Search + filter toggle */}
        <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
          <div
            className="flex flex-1 items-center gap-2 rounded-lg border px-3.5 py-2.5"
            style={{ borderColor: "#E4E9F2", background: "#fff" }}
          >
            <Search size={16} style={{ color: TEXT_SECONDARY }} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search jobs by title, skill or company"
              className="w-full bg-transparent text-sm outline-none"
              style={{ color: TEXT_DARK }}
            />
          </div>
          <button
            onClick={() => setShowFilters((s) => !s)}
            className="flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium"
            style={{
              borderColor: showFilters ? DEEP_BLUE : "#E4E9F2",
              color: showFilters ? DEEP_BLUE : TEXT_DARK,
              background: "#fff",
            }}
          >
            Filters
            <ChevronDown size={13} />
          </button>
        </div>

        {showFilters && (
          <div className="mt-3 flex flex-wrap gap-2">
            {filterGroups.map((g) => (
              <FilterDropdown key={g.label} label={g.label} options={g.options} />
            ))}
          </div>
        )}

        <p className="mt-5 text-xs" style={{ color: TEXT_SECONDARY }}>
          {filtered.length} open roles
        </p>

        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((job) => (
            <JobCard key={job.title + job.company} job={job} />
          ))}
          {filtered.length === 0 && (
            <div
              className="col-span-full rounded-2xl border py-14 text-center text-sm"
              style={{ borderColor: "#E4E9F2", background: "#fff", color: TEXT_SECONDARY }}
            >
              No roles match "{query}". Try a different title, skill or company.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
