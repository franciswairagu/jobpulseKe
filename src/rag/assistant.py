"""JobPulse RAG Assistant.

Orchestrates retrieval and generation for job-market questions.
Uses ChromaDB for retrieval and Ollama for LLM generation.
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from .retriever import JobPulseRAG
from .llm import OllamaLLM, LLMConfig
from .prompts import (
    SYSTEM_PROMPT,
    FINETUNED_SYSTEM_PROMPT,
    build_rag_prompt,
    QUESTION_TYPE_HINTS,
)

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
        r"\b(?:most|top|best|highest|popular)\s+(?:in\s+demand|demanded|common|frequent)",
        r"\b(?:in\s+demand|trending|growing|fastest\s+growing|emerging)",
        r"\b(?:what|which)\s+(?:skill|technology|role|job|position)\s+(?:is|are)\s+(?:the\s+)?(?:most|top|best|popular|common|needed|demanded)",
        r"\b(?:how\s+many|number\s+of)\s+(?:job|role|posting)",
        r"\b(?:market\s+(?:share|data|intelligence|trend|insight))",
    ],
    "skill_inquiry": [
        r"\b(?:what|which)\s+(?:skill|technology|tool|language|framework)",
        r"\b(?:do|should)\s+(?:i|we)\s+(?:need|learn|know|know about)",
        r"\b(?:is|are)\s+\w+\s+(?:in demand|popular|needed|required|important)",
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
    ],
    "salary_compensation": [
        r"\b(?:salary|compensation|pay|wage|earn|income|remuneration)",
        r"\b(?:how much|what)\s+(?:do|does|can|should)\s+\w+\s+(?:earn|make|get paid)",
        r"\b(?:budget|range|average|median|market rate)",
    ],
    "company_industry": [
        r"\b(?:which|what|any)\s+(?:company|companies|employer|startup)",
        r"\b(?:who)\s+(?:is|are)\s+(?:hiring|recruiting|looking)",
    ],
    "location_geography": [
        r"\b(?:where|location|country|city|region|cities)",
        r"\b(?:in|at|from)\s+(?:kenya|nigeria|south africa|ghana|egypt|rwanda|uganda|tanzania)",
        r"\b(?:african|africa)\s+(?:country|city|region|market)",
    ],
}


def _detect_question_type(question: str) -> str:
    """Detect the primary question type."""
    lowered = question.lower()
    scores: dict[str, int] = {}

    for qtype, patterns in _QUESTION_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, lowered))
        if score > 0:
            scores[qtype] = score

    return max(scores, key=scores.get) if scores else "general"


# ---------------------------------------------------------------------------
# Skill extraction
# ---------------------------------------------------------------------------

_SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#",
    "php", "ruby", "kotlin", "swift", "sql", "bash", "react", "vue", "angular",
    "next.js", "django", "flask", "fastapi", "spring", "node.js", "express",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "postgresql",
    "mysql", "mongodb", "redis", "elasticsearch", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "numpy", "machine learning", "deep learning",
    "data science", "nlp", "tableau", "power bi", "spark", "hadoop", "airflow",
    "git", "ci/cd", "jenkins", "linux", "agile", "scrum",
]


def _extract_mentioned_skills(question: str) -> list[str]:
    """Extract skill names mentioned in the question."""
    lowered = question.lower()
    return [s for s in _SKILL_KEYWORDS if s in lowered]


def _aggregate_skills(results: pd.DataFrame) -> dict[str, int]:
    """Count skill frequency across results."""
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
    """Count location frequency."""
    counter: Counter = Counter()
    for _, row in results.iterrows():
        loc = row.get("location") or row.get("country") or ""
        if loc and str(loc).strip() and str(loc).lower() != "nan":
            counter[str(loc).strip()] += 1
    return dict(counter.most_common(10))


def _aggregate_companies(results: pd.DataFrame) -> dict[str, int]:
    """Count company frequency."""
    counter: Counter = Counter()
    for _, row in results.iterrows():
        company = row.get("company")
        if company and str(company).strip() and str(company).lower() != "nan":
            counter[str(company).strip()] += 1
    return dict(counter.most_common(10))


# ---------------------------------------------------------------------------
# Answer composers
# ---------------------------------------------------------------------------

def _val(value: Any, fallback: str) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback
    text = str(value).strip()
    return text if text and text.lower() != "nan" else fallback


def _fmt_skills(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in list(value)[:6])
    if isinstance(value, str) and value.strip():
        return value[:200]
    return ""


def _compose_skill_answer(question: str, results: pd.DataFrame, mentioned_skills: list[str]) -> str:
    skill_counts = _aggregate_skills(results)
    locations = _aggregate_locations(results)

    lines = []
    if mentioned_skills:
        lines.append(f"Great question! Here's what I found about **{', '.join(mentioned_skills)}** in the African tech market:\n")
    else:
        lines.append(f"Here's what the data tells us:\n")

    if skill_counts:
        lines.append("**Top skills showing up across job postings:**")
        for skill, count in list(skill_counts.items())[:6]:
            lines.append(f"- **{skill}** — mentioned in {count} posting{'s' if count != 1 else ''}")
        lines.append("")

    if not results.empty:
        lines.append("**Some roles that match:**")
        for i, (_, row) in enumerate(results.head(3).iterrows(), start=1):
            title = _val(row.get("job_title"), "Untitled role")
            company = _val(row.get("company"), "")
            location = _val(row.get("location"), _val(row.get("country"), ""))
            parts = [f"**{title}**"]
            if company and company != "":
                parts.append(f"at {company}")
            if location:
                parts.append(f"— {location}")
            lines.append(f"  {i}. {' '.join(parts)}")
        lines.append("")

    if locations:
        top_locs = list(locations.items())[:4]
        loc_str = ", ".join(loc for loc, _ in top_locs)
        lines.append(f"📍 These roles are mostly in: **{loc_str}**")

    return "\n".join(lines)


def _compose_job_answer(question: str, results: pd.DataFrame) -> str:
    lines = [f"I found **{len(results)} role{'s' if len(results) != 1 else ''}** that might interest you:\n"]

    for i, (_, row) in enumerate(results.iterrows(), start=1):
        title = _val(row.get("job_title"), "Untitled role")
        company = _val(row.get("company"), "")
        location = _val(row.get("location"), _val(row.get("country"), ""))
        skills = _fmt_skills(row.get("skills"))
        parts = [f"**{title}**"]
        if company:
            parts.append(f"at {company}")
        if location:
            parts.append(f"— {location}")
        lines.append(f"{i}. {' '.join(parts)}")
        if skills:
            lines.append(f"   Skills: {skills}")
        lines.append("")

    return "\n".join(lines)


def _compose_general_answer(question: str, results: pd.DataFrame) -> str:
    skill_counts = _aggregate_skills(results)
    companies = _aggregate_companies(results)

    lines = [f"I found **{len(results)} result{'s' if len(results) != 1 else ''}** related to your question:\n"]

    for i, (_, row) in enumerate(results.iterrows(), start=1):
        title = _val(row.get("job_title"), "Untitled role")
        company = _val(row.get("company"), "")
        location = _val(row.get("location"), _val(row.get("country"), ""))
        parts = [f"**{title}**"]
        if company:
            parts.append(f"at {company}")
        if location:
            parts.append(f"— {location}")
        lines.append(f"{i}. {' '.join(parts)}")

    lines.append("")
    if skill_counts:
        top = list(skill_counts.keys())[:5]
        lines.append(f"**Key skills to note:** {', '.join(top)}")
    if companies:
        top_companies = list(companies.keys())[:5]
        lines.append(f"**Companies hiring:** {', '.join(top_companies)}")

    return "\n".join(lines)


def _compose_no_match_answer(question: str) -> str:
    return (
        f"I couldn't find strong matches for **\"{question}\"** in our dataset.\n\n"
        f"**Tips:**\n"
        f"- Try broadening your search terms\n"
        f"- Use synonyms (e.g., \"backend\" instead of \"server-side\")\n"
        f"- Check the **Skill Demand** tab for an overview of what's trending"
    )


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class JobPulseAssistant:
    """Answer job-market questions using retrieved JobPulse records."""

    def __init__(
        self,
        rag: JobPulseRAG | None = None,
        llm: OllamaLLM | None = None,
        use_finetuned: bool = False,
    ):
        self.rag = rag or JobPulseRAG()
        self.llm = llm or OllamaLLM()
        self.use_finetuned = use_finetuned
        self._system_prompt = FINETUNED_SYSTEM_PROMPT if use_finetuned else SYSTEM_PROMPT

    def ask(
        self,
        question: str,
        top_k: int = 5,
        market_data: dict | None = None,
    ) -> AssistantAnswer:
        """Answer a question about the job market."""
        self.rag.ensure_ready()

        question_type = _detect_question_type(question)
        mentioned_skills = _extract_mentioned_skills(question)

        # Market intelligence uses special handling
        if question_type == "market_intelligence":
            results = self.rag.query(question, top_k=top_k)
            sources = [_source(row) for _, row in results.iterrows()]
            answer = self._compose_market_answer(question, results, market_data)
            return AssistantAnswer(answer, "grounded", sources)

        results = self.rag.query(question, top_k=top_k)
        sources = [_source(row) for _, row in results.iterrows()]

        if results.empty or not self.rag.has_strong_matches(results):
            return AssistantAnswer(_compose_no_match_answer(question), "low", sources)

        # Try LLM generation first
        llm_answer = self._try_llm_generate(question, question_type, results)
        if llm_answer is not None:
            return AssistantAnswer(llm_answer, "grounded", sources)

        # Template fallback
        if question_type == "skill_inquiry":
            answer = _compose_skill_answer(question, results, mentioned_skills)
        elif question_type == "job_search":
            answer = _compose_job_answer(question, results)
        else:
            answer = _compose_general_answer(question, results)

        return AssistantAnswer(answer, "grounded", sources)

    def _try_llm_generate(
        self, question: str, question_type: str, results: pd.DataFrame,
    ) -> str | None:
        """Attempt LLM generation."""
        if not self.llm.available:
            return None

        # Try fine-tuned model first if available
        model = None
        if self.use_finetuned and self.llm.has_model("jobpulse-finetuned"):
            model = "jobpulse-finetuned"

        context = self.rag.format_context(results)
        prompt = build_rag_prompt(question, question_type)
        return self.llm.generate(
            prompt=prompt,
            context=context,
            system=self._system_prompt,
            model=model,
        )

    def _compose_market_answer(
        self, question: str, results: pd.DataFrame, market_data: dict | None,
    ) -> str:
        """Compose market intelligence answer."""
        lines = []
        if market_data and market_data.get("skills"):
            lines.append("Here's what's trending in the market right now:\n")
            for i, skill in enumerate(market_data["skills"][:8], 1):
                if isinstance(skill, dict):
                    name = skill.get("name", str(skill))
                    count = skill.get("count", "")
                    pct = skill.get("percentage", "")
                    lines.append(f"{i}. **{name}** — {count} jobs ({pct}%)")
                else:
                    lines.append(f"{i}. **{skill}**")
            lines.append("")
            lines.append("These skills keep coming up across the most recent job postings.")
        elif not results.empty:
            skill_counts = _aggregate_skills(results)
            if skill_counts:
                lines.append("Based on recent postings, here are the most sought-after skills:\n")
                for skill, count in list(skill_counts.items())[:8]:
                    lines.append(f"- **{skill}** — {count} job{'s' if count != 1 else ''}")
                lines.append("")
                lines.append("If you're looking to upskill, these are solid bets.")
        else:
            lines.append("I don't have specific market data for this query yet.")

        return "\n".join(lines)


def _source(row: pd.Series) -> dict[str, Any]:
    return {
        "job_id": _val(row.get("job_id"), ""),
        "title": _val(row.get("job_title"), "Untitled role"),
        "company": _val(row.get("company"), "Unknown company"),
        "url": _val(row.get("vacancy_url"), ""),
        "score": round(float(row.get("score", 0.0)), 4),
    }
