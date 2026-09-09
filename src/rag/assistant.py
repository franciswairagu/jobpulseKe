"""Grounded answer layer over JobPulse retrieval results.

Uses a local LLM (via Ollama) for natural-language generation when
available, falling back to template-based answers when the LLM is
unreachable or not installed.

Improved version with:
- Question type detection (skill inquiry, job search, career advice, etc.)
- LLM-powered generation with grounded context
- Natural language summaries tailored to each question type
- Skill and course recommendations based on retrieved results
- Market insights extracted from the result set
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from .retriever import JobPulseRAG
from .llm import OllamaLLM, LLMConfig, JOBPULSE_SYSTEM_PROMPT, build_rag_prompt

logger = logging.getLogger(__name__)


@dataclass
class AssistantAnswer:
    answer: str
    confidence: str
    sources: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Question type detection
# ---------------------------------------------------------------------------

_QUESTION_PATTERNS = {
    "market_intelligence": [
        r"\b(?:most|top|best|highest|popular)\s+(?:in\s+demand|demanded|common|frequent|popular|wanted|sought|needed|requested)",
        r"\b(?:in\s+demand|trending|growing|fastest\s+growing|emerging)",
        r"\b(?:what|which)\s+(?:skill|technology|role|job|position)\s+(?:is|are)\s+(?:the\s+)?(?:most|top|best|popular|common|needed|demanded)",
        r"\b(?:skill|skills|role|roles|job|jobs)\s+(?:in|across|for)\s+(?:kenya|nigeria|ghana|south\s+africa|egypt|africa)",
        r"\b(?:african|africa|kenya|nigeria|ghana|south\s+africa|egypt)\s+(?:market|tech\s+market|job\s+market)",
        r"\b(?:most|top|best)\s+(?:popular|common|frequent|needed)\s+(?:skill|technology|tool|role|job|position)",
        r"\b(?:skill|technology|tool|role|job)\s+(?:demand|gap|shortage|surplus)",
        r"\b(?:how\s+many|number\s+of)\s+(?:job|role|posting)",
        r"\b(?:market\s+(?:share|data|intelligence|trend|insight))",
        r"\b(?:which\s+skill|what\s+skill|which\s+role|what\s+role|what\s+job|which\s+job).*(?:kenya|nigeria|ghana|south\s+africa|egypt|africa)",
        r"\b(?:needed|available)\s+(?:role|job|position)",
        r"\b(?:most|top)\s+(?:hiring|recruited)",
    ],
    "skill_inquiry": [
        r"\b(?:what|which)\s+(?:skill|technology|tool|language|framework)",
        r"\b(?:do|should)\s+(?:i|we)\s+(?:need|learn|know|know about)",
        r"\b(?:is|are)\s+\w+\s+(?:in demand|popular|needed|required|important)",
        r"\b(?:how|what)\s+(?:important|valuable|useful)\s+is",
        r"\b(?:trending|growing|emerging)\s+(?:skill|technology|tool)",
    ],
    "job_search": [
        r"\b(?:find|search|show|look for|available)\s+(?:job|role|position|opening)",
        r"\b(?:remote|onsite|hybrid)\s+(?:job|role|position|work)",
        r"\b(?:job|role|position)\s+(?:in|at|for|near)",
        r"\b(?:who|which)\s+(?:company|companies)\s+(?:is|are)\s+hiring",
        r"\b(?:hiring|vacancy|opening|recruitment)",
    ],
    "career_advice": [
        r"\b(?:how|what)\s+(?:do|can|should)\s+(?:i|we)\s+(?:become|get into|start|transition)",
        r"\b(?:career|path|progression|growth|advance)",
        r"\b(?:senior|junior|lead|principal|entry|mid|intern)",
        r"\b(?:switch|change|move|transition)\s+(?:to|into|from)",
        r"\b(?:what)\s+(?:does|do)\s+(?:a|an)\s+\w+\s+(?:do|need|require)",
    ],
    "salary_compensation": [
        r"\b(?:salary|compensation|pay|wage|earn|income|remuneration)",
        r"\b(?:how much|what)\s+(?:do|does|can|should)\s+\w+\s+(?:earn|make|get paid)",
        r"\b(?:budget|range|average|median|market rate)",
    ],
    "company_industry": [
        r"\b(?:which|what|any)\s+(?:company|companies|employer|startup)",
        r"\b(?:who)\s+(?:is|are)\s+(?:hiring|recruiting|looking)",
        r"\b(?:work|job|role)\s+(?:at|in|for)\s+\w+",
    ],
    "location_geography": [
        r"\b(?:where|location|country|city|region|city|cities)",
        r"\b(?:in|at|from)\s+(?:kenya|nigeria|south africa|ghana|egypt|rwanda|uganda|tanzania)",
        r"\b(?:african|africa)\s+(?:country|city|region|market)",
    ],
}


def _detect_question_type(question: str) -> str:
    """Detect the primary question type from user input."""
    lowered = question.lower()
    scores: dict[str, int] = {}

    for qtype, patterns in _QUESTION_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, lowered):
                score += 1
        if score > 0:
            scores[qtype] = score

    if not scores:
        return "general"
    return max(scores, key=scores.get)


# ---------------------------------------------------------------------------
# Skill extraction helpers
# ---------------------------------------------------------------------------

def _extract_mentioned_skills(question: str) -> list[str]:
    """Extract skill names mentioned directly in the question."""
    SKILL_KEYWORDS = [
        "python", "java", "javascript", "typescript", "go", "golang", "rust",
        "c++", "c#", "php", "ruby", "kotlin", "swift", "sql", "bash",
        "react", "vue", "angular", "next.js", "django", "flask", "fastapi",
        "spring", "node.js", "express",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "machine learning", "deep learning", "data science", "nlp",
        "tableau", "power bi", "excel", "spark", "hadoop", "airflow",
        "git", "ci/cd", "jenkins", "linux",
        "agile", "scrum",
    ]
    lowered = question.lower()
    return [s for s in SKILL_KEYWORDS if s in lowered]


def _aggregate_skills(results: pd.DataFrame) -> dict[str, int]:
    """Count skill frequency across all retrieved results."""
    counter: Counter = Counter()
    for _, row in results.iterrows():
        skills = row.get("skills")
        if isinstance(skills, (list, tuple, set)):
            for s in skills:
                counter[str(s).lower()] += 1
        elif isinstance(skills, str) and skills.strip():
            for s in skills.split(","):
                counter[s.strip().lower()] += 1
    return dict(counter.most_common(15))


def _aggregate_locations(results: pd.DataFrame) -> dict[str, int]:
    """Count location frequency across results."""
    counter: Counter = Counter()
    for _, row in results.iterrows():
        loc = row.get("location") or row.get("country") or ""
        if loc and str(loc).strip() and str(loc).lower() != "nan":
            counter[str(loc).strip()] += 1
    return dict(counter.most_common(10))


def _aggregate_companies(results: pd.DataFrame) -> dict[str, int]:
    """Count company frequency across results."""
    counter: Counter = Counter()
    for _, row in results.iterrows():
        company = row.get("company")
        if company and str(company).strip() and str(company).lower() != "nan":
            counter[str(company).strip()] += 1
    return dict(counter.most_common(10))


def _aggregate_seniority(results: pd.DataFrame) -> dict[str, int]:
    """Count seniority level frequency."""
    counter: Counter = Counter()
    for _, row in results.iterrows():
        level = row.get("seniority_level")
        if level and str(level).strip() and str(level).lower() != "nan":
            counter[str(level).strip()] += 1
    return dict(counter.most_common(5))


def _aggregate_work_modes(results: pd.DataFrame) -> dict[str, int]:
    """Count work mode frequency."""
    counter: Counter = Counter()
    for _, row in results.iterrows():
        mode = row.get("work_mode")
        if mode and str(mode).strip() and str(mode).lower() != "nan":
            counter[str(mode).strip()] += 1
    return dict(counter.most_common(3))


# ---------------------------------------------------------------------------
# Answer composers per question type
# ---------------------------------------------------------------------------

def _is_role_question(question: str) -> bool:
    """Check if the question is about roles/jobs rather than skills."""
    role_keywords = r"\b(?:role|roles|job|jobs|position|positions|hiring)\b"
    return bool(re.search(role_keywords, question.lower()))


# ---------------------------------------------------------------------------
# Role-to-skills inference (fallback when retrieved results lack skill data)
# ---------------------------------------------------------------------------

_ROLE_SKILLS = {
    "data scientist": ["Python", "R", "SQL", "Machine Learning", "TensorFlow/PyTorch", "Statistics", "Pandas/NumPy", "Data Visualization"],
    "data science": ["Python", "R", "SQL", "Machine Learning", "TensorFlow/PyTorch", "Statistics", "Pandas/NumPy", "Data Visualization"],
    "machine learning": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "SQL", "Docker", "MLOps", "Statistics"],
    "frontend": ["JavaScript", "React", "HTML/CSS", "TypeScript", "Vue.js", "Angular", "Git", "Responsive Design"],
    "backend": ["Python", "Java", "Node.js", "SQL", "REST APIs", "Docker", "Git", "PostgreSQL"],
    "fullstack": ["JavaScript", "React", "Node.js", "SQL", "Python", "Docker", "Git", "REST APIs"],
    "devops": ["Docker", "Kubernetes", "AWS/Azure/GCP", "Terraform", "CI/CD", "Linux", "Bash", "Jenkins"],
    "cloud": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Linux", "Networking"],
    "mobile": ["React Native", "Flutter", "Swift", "Kotlin", "Dart", "Firebase", "Git", "REST APIs"],
    "software engineer": ["Python", "Java", "Git", "SQL", "REST APIs", "Docker", "Testing", "CI/CD"],
    "product manager": ["Agile/Scrum", "JIRA", "Data Analysis", "SQL", "Communication", "Roadmapping", "A/B Testing"],
    "ux/ui": ["Figma", "Adobe XD", "User Research", "Wireframing", "Prototyping", "HTML/CSS", "Design Systems"],
    "security": ["Network Security", "Penetration Testing", "SIEM", "Python", "Linux", "Compliance", "Cryptography"],
    "blockchain": ["Solidity", "Ethereum", "Web3.js", "Smart Contracts", "Cryptography", "JavaScript", "Rust"],
    "ai": ["Python", "TensorFlow", "PyTorch", "NLP", "Computer Vision", "LLMs", "MLOps", "Statistics"],
    "analyst": ["SQL", "Python", "Excel", "Tableau/Power BI", "Statistics", "Data Visualization", "Pandas"],
    "database": ["SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Backup/Recovery", "Performance Tuning"],
    "linux": ["Bash", "Shell Scripting", "Networking", "Docker", "System Administration", "Security", "Monitoring"],
}


def _infer_skills_from_question(question: str) -> list[str]:
    """Infer relevant skills from the question text using role keywords."""
    lowered = question.lower()
    for role, skills in _ROLE_SKILLS.items():
        if role in lowered:
            return skills
    return []


def _compose_market_intelligence_answer(question: str, results: pd.DataFrame, market_data: dict | None = None) -> str:
    """Answer market intelligence questions using actual skill or role demand data."""
    lines = []

    if market_data and market_data.get("is_role_question"):
        # Role-based market intelligence
        roles = market_data.get("roles", [])
        country = market_data.get("country", "Africa")

        if roles:
            lines.append(f"Based on the JobPulse dataset, here are the **most common roles** in {country}:")
            lines.append("")

            for i, role in enumerate(roles[:15], 1):
                title = role.get("title", "Unknown")
                count = role.get("count", 0)
                pct = role.get("percentage", 0)
                lines.append(f"  {i}. **{title}** — {count} posting{'s' if count > 1 else ''} ({pct:.1f}%)")

            lines.append("")
            lines.append(f"**Total jobs analyzed:** {market_data.get('total_jobs', 'N/A')}")
            lines.append("")
            lines.append("**What this means for you:**")
            if roles:
                top_3 = [r.get("title") for r in roles[:3]]
                lines.append(f"  - The most common roles are **{', '.join(top_3)}**")
                lines.append(f"  - These roles represent the highest hiring demand")
                lines.append("")
                lines.append("**Next steps:**")
                lines.append(f"  - Upload your CV in **CV Analyzer** to match against these roles")
                lines.append(f"  - Go to **Skill Demand** to see what skills these roles require")
                lines.append(f"  - Check **Career Insights** for progression paths")
        else:
            lines.append(f"No role data found for {country}. Try broadening your search.")

    elif market_data and market_data.get("skills"):
        # Skill-based market intelligence (existing logic)
        skills = market_data["skills"]
        country = market_data.get("country", "Africa")

        lines.append(f"Based on the JobPulse dataset, here are the **most in-demand skills** in {country}:")
        lines.append("")

        for i, skill in enumerate(skills[:15], 1):
            name = skill.get("name", "Unknown")
            count = skill.get("count", 0)
            pct = skill.get("percentage", 0)
            lines.append(f"  {i}. **{name}** — {count} jobs ({pct:.1f}% of all jobs)")

        lines.append("")
        lines.append(f"**Total jobs analyzed:** {market_data.get('total_jobs', 'N/A')}")
        lines.append("")

        lines.append("**What this means for you:**")
        if skills:
            top_3 = [s.get("name") for s in skills[:3]]
            lines.append(f"  - The top 3 skills are **{', '.join(top_3)}**")
            lines.append(f"  - These skills appear in the majority of job postings")
            lines.append(f"  - Focus on these to maximize your job opportunities")
            lines.append("")
            lines.append("**Next steps:**")
            lines.append(f"  - Go to **Skill Demand** to explore the full skills intelligence dashboard")
            lines.append(f"  - Upload your CV in **CV Analyzer** to see which of these skills you already have")
            lines.append(f"  - Check **Career Insights** for skill distribution by seniority level")
    else:
        lines.append(f'I found {len(results)} posting{"s" if len(results) != 1 else ""} related to "{question}",')
        lines.append("but this question is best answered using our **Skill Demand** or **Career Insights** dashboards.")
        lines.append("")
        lines.append("**For accurate market intelligence, visit:**")
        lines.append("  - **Skill Demand** tab — searchable table of all skills with demand %, growth rate, and job count")
        lines.append("  - **Career Insights** tab — skill distribution by seniority level and geographic demand")
        lines.append("  - **Dashboard** — market overview with top skills and trends")

    return "\n".join(lines)


def _compose_skill_answer(question: str, results: pd.DataFrame, mentioned_skills: list[str]) -> str:
    """Answer skill-related questions with demand insights."""
    lines = []
    skill_counts = _aggregate_skills(results)
    locations = _aggregate_locations(results)
    seniority = _aggregate_seniority(results)

    if mentioned_skills:
        skill_str = ", ".join(mentioned_skills)
        lines.append(f"Based on the JobPulse dataset, here's what I found about {skill_str}:")
    else:
        lines.append(f'Here\'s what the market data shows for "{question}":')

    lines.append("")

    # Show matching roles found
    if not results.empty:
        lines.append("**Matching roles found:**")
        for i, (_, row) in enumerate(results.head(5).iterrows(), start=1):
            title = _val(row.get("job_title"), "Untitled role")
            company = _val(row.get("company"), "Unknown company")
            location = _val(row.get("location"), _val(row.get("country"), ""))
            detail = f"  {i}. **{title}**"
            if company != "Unknown company":
                detail += f" at {company}"
            if location:
                detail += f" — {location}"
            lines.append(detail)
        lines.append("")

    if skill_counts:
        top_skills = list(skill_counts.items())[:8]
        lines.append("**Most relevant skills in these roles:**")
        for skill, count in top_skills:
            lines.append(f"  - {skill} (appears in {count} posting{'s' if count > 1 else ''})")
        lines.append("")
    else:
        # No skills extracted from results — provide role-specific guidance
        lines.append("**Key skills typically required for this type of role:**")
        role_skills = _infer_skills_from_question(question)
        if role_skills:
            for skill in role_skills[:8]:
                lines.append(f"  - {skill}")
        else:
            lines.append("  - Technical skills specific to the role (check individual job postings)")
            lines.append("  - Communication and teamwork")
            lines.append("  - Problem-solving and analytical thinking")
        lines.append("")

    if locations:
        top_locs = list(locations.items())[:5]
        loc_str = ", ".join(f"{loc} ({n})" for loc, n in top_locs)
        lines.append(f"**Where these roles are located:** {loc_str}")
        lines.append("")

    if seniority:
        levels = ", ".join(f"{lev} ({n})" for lev, n in list(seniority.items())[:3])
        lines.append(f"**Seniority levels found:** {levels}")
        lines.append("")

    lines.append("**Recommendation:**")
    if mentioned_skills:
        lines.append(f"If you're looking to strengthen your {skill_str} profile, consider:")
        lines.append(f"  - Building projects that showcase these skills")
        lines.append(f"  - Contributing to open-source projects using {skill_str}")
        lines.append(f"  - Earning relevant certifications if available")
    else:
        top = [s for s, _ in list(skill_counts.items())[:3]] if skill_counts else []
        if top:
            lines.append(f"The most in-demand skills in these results are **{', '.join(top)}**. "
                        f"Consider prioritizing these if you're planning your learning path.")
        else:
            lines.append("Upload your CV in the **CV Analyzer** tab to see how your current skills match these roles, "
                        "and check the **Skill Demand** dashboard for full market intelligence.")

    return "\n".join(lines)


def _compose_job_answer(question: str, results: pd.DataFrame) -> str:
    """Answer job search questions with structured results."""
    lines = [f'I found {len(results)} relevant posting{"s" if len(results) != 1 else ""} matching "{question}":']
    lines.append("")

    for i, (_, row) in enumerate(results.iterrows(), start=1):
        title = _val(row.get("job_title"), "Untitled role")
        company = _val(row.get("company"), "Unknown company")
        location = _val(row.get("location"), _val(row.get("country"), "Location not listed"))
        mode = _val(row.get("work_mode"), "")
        skills = _fmt_skills(row.get("skills"))

        detail = f"**{i}. {title}** at {company}"
        if location and location.lower() != "location not listed":
            detail += f" — {location}"
        if mode:
            detail += f" ({mode})"
        lines.append(detail)

        if skills:
            lines.append(f"   Skills: {skills}")
        lines.append("")

    locations = _aggregate_locations(results)
    work_modes = _aggregate_work_modes(results)

    if work_modes:
        mode_parts = [f"{m}: {c}" for m, c in work_modes.items()]
        lines.append(f"**Work modes available:** {', '.join(mode_parts)}")

    if locations:
        top_locs = list(locations.items())[:3]
        loc_str = ", ".join(f"{loc}" for loc, _ in top_locs)
        lines.append(f"**Top locations:** {loc_str}")

    lines.append("")
    lines.append("Browse the **CV Analyzer** tab to see personalized match scores for these roles.")

    return "\n".join(lines)


def _compose_career_answer(question: str, results: pd.DataFrame) -> str:
    """Answer career advice questions with progression insights."""
    lines = [f'Here\'s career guidance based on "{question}":']
    lines.append("")

    seniority = _aggregate_seniority(results)
    skill_counts = _aggregate_skills(results)

    if seniority:
        lines.append("**Career levels found in matching roles:**")
        for level, count in seniority.items():
            lines.append(f"  - {level}: {count} role{'s' if count > 1 else ''}")
        lines.append("")

    if skill_counts:
        top_skills = list(skill_counts.items())[:10]
        lines.append("**Key skills for this career path:**")
        for skill, count in top_skills:
            lines.append(f"  - {skill}")
        lines.append("")

    lines.append("**Suggested next steps:**")
    lines.append("  1. Upload your CV in the **CV Analyzer** tab to see your current match score")
    lines.append("  2. Review the **Skill Gaps** tab to identify what to learn next")
    lines.append("  3. Check **Career Insights** for progression paths and geographic demand")

    return "\n".join(lines)


def _compose_general_answer(question: str, results: pd.DataFrame) -> str:
    """Compose a general-purpose answer from retrieved results."""
    lines = [f'I found {len(results)} relevant posting{"s" if len(results) != 1 else ""} for "{question}":']
    lines.append("")

    skill_counts = _aggregate_skills(results)
    locations = _aggregate_locations(results)
    companies = _aggregate_companies(results)

    for i, (_, row) in enumerate(results.iterrows(), start=1):
        title = _val(row.get("job_title"), "Untitled role")
        company = _val(row.get("company"), "Unknown company")
        location = _val(row.get("location"), _val(row.get("country"), ""))
        skills = _fmt_skills(row.get("skills"))

        line = f"{i}. **{title}** at {company}"
        if location:
            line += f" — {location}"
        lines.append(line)
        if skills:
            lines.append(f"   Skills: {skills}")

    lines.append("")

    if skill_counts:
        top = [s for s, _ in list(skill_counts.items())[:5]]
        lines.append(f"**Common skills across these roles:** {', '.join(top)}")

    if companies:
        top_companies = list(companies.keys())[:5]
        lines.append(f"**Hiring companies:** {', '.join(top_companies)}")

    if locations:
        top_locs = list(locations.keys())[:5]
        lines.append(f"**Locations:** {', '.join(top_locs)}")

    lines.append("")
    lines.append("**Tip:** Use the **CV Analyzer** to see how your skills match these roles, "
                 "or **Skill Demand** to explore the full market intelligence dashboard.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class JobPulseAssistant:
    """Answer job-market questions using retrieved JobPulse records.

    When an Ollama LLM is available, generates natural-language answers
    grounded in the retrieved context. Falls back to template-based
    answers when the LLM is unreachable.
    """

    def __init__(
        self,
        rag: JobPulseRAG | None = None,
        llm: OllamaLLM | None = None,
    ):
        self.rag = rag or JobPulseRAG()
        self.llm = llm or OllamaLLM()

    def ask(self, question: str, top_k: int = 5, market_data: dict | None = None) -> AssistantAnswer:
        self.rag.ensure_ready()

        question_type = _detect_question_type(question)
        mentioned_skills = _extract_mentioned_skills(question)

        # For market intelligence questions, prioritize market data over RAG retrieval
        if question_type == "market_intelligence":
            if market_data:
                market_data["is_role_question"] = _is_role_question(question)
            results = self.rag.query(question, top_k=top_k)
            sources = [_source(row) for _, row in results.iterrows()]

            # Market intelligence uses template (needs structured SQL data)
            answer = _compose_market_intelligence_answer(question, results, market_data)
            return AssistantAnswer(answer, "grounded", sources)

        results = self.rag.query(question, top_k=top_k)
        sources = [_source(row) for _, row in results.iterrows()]

        if results.empty or not self.rag.has_strong_matches(results):
            return AssistantAnswer(
                _compose_no_match_answer(question), "low", sources,
            )

        # Try LLM generation first, fall back to templates
        llm_answer = self._try_llm_generate(question, question_type, results)
        if llm_answer is not None:
            return AssistantAnswer(llm_answer, "grounded", sources)

        # Template fallback when LLM is unavailable
        if question_type == "skill_inquiry":
            answer = _compose_skill_answer(question, results, mentioned_skills)
        elif question_type == "job_search":
            answer = _compose_job_answer(question, results)
        elif question_type == "career_advice":
            answer = _compose_career_answer(question, results)
        else:
            answer = _compose_general_answer(question, results)

        return AssistantAnswer(answer, "grounded", sources)

    def _try_llm_generate(
        self, question: str, question_type: str, results: pd.DataFrame,
    ) -> str | None:
        """Attempt LLM generation. Returns None if LLM is unavailable."""
        if not self.llm.available:
            return None

        context = JobPulseRAG.format_context(results)
        prompt = build_rag_prompt(question, question_type)
        return self.llm.generate(
            prompt=prompt,
            context=context,
            system=JOBPULSE_SYSTEM_PROMPT,
        )


def _compose_no_match_answer(question: str) -> str:
    """Compose a helpful response when no strong matches are found."""
    return (
        f'I couldn\'t find strong matches for "{question}" in the JobPulse dataset. '
        f"This could mean the role, skill, or location isn't well-represented in our current index.\n\n"
        f"**Suggestions:**\n"
        f"  - Try broadening your search (e.g., \"python developer\" instead of \"python ML engineer in Rwanda\")\n"
        f"  - Use synonyms (e.g., \"backend\" instead of \"server-side\")\n"
        f"  - Check the **Skill Demand** tab to see what skills and roles are most common in the dataset\n"
        f"  - The dataset is continuously updated — new postings are added regularly"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _source(row: pd.Series) -> dict[str, Any]:
    return {
        "job_id": _val(row.get("job_id"), ""),
        "title": _val(row.get("job_title"), "Untitled role"),
        "company": _val(row.get("company"), "Unknown company"),
        "url": _val(row.get("vacancy_url"), ""),
        "score": round(float(row.get("score", 0.0)), 4),
    }


def _val(value: Any, fallback: str) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback
    text = str(value).strip()
    return text if text and text.lower() != "nan" else fallback


def _fmt_skills(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        items = [str(item) for item in value[:6]]
        return ", ".join(items)
    if isinstance(value, str) and value.strip():
        return value[:200]
    return ""
