"""Conversational answer layer over JobPulse retrieval results.

Uses a local LLM (via Ollama) for natural-language generation when
available, falling back to template-based answers when the LLM is
unreachable or not installed.

Conversational-first design:
- Warm, natural language that sounds like a helpful friend
- Quick greeting detection (no LLM call needed)
- Compact context for faster LLM responses
- Conversation history for follow-ups
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Generator

import pandas as pd

from .retriever import JobPulseRAG
from .llm import OllamaLLM, LLMConfig, JOBPULSE_SYSTEM_PROMPT, build_rag_prompt, detect_greeting
from .cache import query_cache, cache_rag_response

logger = logging.getLogger(__name__)


@dataclass
class AssistantAnswer:
    answer: str
    confidence: str
    sources: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Question type detection (simplified)
# ---------------------------------------------------------------------------

_QUESTION_PATTERNS = {
    "market_intelligence": [
        r"\b(?:most|top|best|in\s+demand|trending|popular|common|needed)\s+(?:skill|technology|role|job|tool)",
        r"\b(?:skill|technology|role|job)\s+(?:demand|gap|shortage|trend)",
        r"\b(?:what|which)\s+(?:skill|technology|role|job|position)\s+(?:is|are)\s+(?:the\s+)?(?:most|top|best|popular|common|needed|demanded)",
        r"\b(?:how\s+many|number\s+of)\s+(?:job|role|posting)",
        r"\b(?:market\s+(?:data|trend|insight|intelligence))",
    ],
    "skill_inquiry": [
        r"\b(?:what|which)\s+(?:skill|technology|tool|language|framework)",
        r"\b(?:do|should)\s+(?:i|we)\s+(?:need|learn|know)",
        r"\b(?:is|are)\s+\w+\s+(?:in\s+demand|popular|needed|required|important)",
        r"\b(?:trending|growing|emerging)\s+(?:skill|technology|tool)",
    ],
    "job_search": [
        r"\b(?:find|search|show|look\s+for|available)\s+(?:job|role|position|opening)",
        r"\b(?:remote|onsite|hybrid)\s+(?:job|role|position|work)",
        r"\b(?:who|which)\s+(?:company|companies)\s+(?:is|are)\s+hiring",
        r"\b(?:hiring|vacancy|opening|recruitment)",
    ],
    "career_advice": [
        r"\b(?:how|what)\s+(?:do|can|should)\s+(?:i|we)\s+(?:become|get\s+into|start|transition)",
        r"\b(?:career|path|progression|growth|advance)",
        r"\b(?:switch|change|move|transition)\s+(?:to|into|from)",
    ],
    "salary_compensation": [
        r"\b(?:salary|compensation|pay|wage|earn|income|remuneration)",
        r"\b(?:how\s+much|what)\s+(?:do|does|can|should)\s+\w+\s+(?:earn|make|get\s+paid)",
    ],
}


def _detect_question_type(question: str) -> str:
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
    "python", "java", "javascript", "typescript", "go", "golang", "rust",
    "c++", "c#", "php", "ruby", "kotlin", "swift", "sql", "bash",
    "react", "vue", "angular", "next.js", "django", "flask", "fastapi",
    "spring", "node.js", "express",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "machine learning", "deep learning", "data science", "nlp",
    "tableau", "power bi", "excel", "spark", "hadoop", "airflow",
    "git", "ci/cd", "jenkins", "linux", "agile", "scrum",
]

_ROLE_SKILLS = {
    "data scientist": "Python, SQL, ML, TensorFlow/PyTorch, Statistics, Pandas",
    "data science": "Python, SQL, ML, TensorFlow/PyTorch, Statistics, Pandas",
    "machine learning": "Python, TensorFlow, PyTorch, Scikit-learn, SQL, Docker",
    "frontend": "JavaScript, React, HTML/CSS, TypeScript, Vue.js, Angular",
    "backend": "Python, Java, Node.js, SQL, REST APIs, Docker, PostgreSQL",
    "fullstack": "JavaScript, React, Node.js, SQL, Python, Docker",
    "devops": "Docker, Kubernetes, AWS/Azure/GCP, Terraform, CI/CD, Linux",
    "cloud": "AWS, Azure, GCP, Docker, Kubernetes, Terraform",
    "mobile": "React Native, Flutter, Swift, Kotlin, Dart, Firebase",
    "software engineer": "Python, Java, Git, SQL, REST APIs, Docker",
    "product manager": "Agile/Scrum, JIRA, SQL, Communication, Roadmapping",
    "ux/ui": "Figma, Adobe XD, User Research, Wireframing, HTML/CSS",
    "security": "Network Security, Python, Linux, SIEM, Compliance",
    "ai": "Python, TensorFlow, PyTorch, NLP, Computer Vision, LLMs",
    "analyst": "SQL, Python, Excel, Tableau/Power BI, Statistics",
}


def _extract_mentioned_skills(question: str) -> list[str]:
    lowered = question.lower()
    return [s for s in _SKILL_KEYWORDS if s in lowered]


def _infer_skills_from_question(question: str) -> str | None:
    lowered = question.lower()
    for role, skills in _ROLE_SKILLS.items():
        if role in lowered:
            return skills
    return None


# ---------------------------------------------------------------------------
# Compact aggregation helpers
# ---------------------------------------------------------------------------

def _top_skills(results: pd.DataFrame, n: int = 5) -> list[str]:
    counter: Counter = Counter()
    for _, row in results.iterrows():
        skills = row.get("skills")
        if isinstance(skills, (list, tuple, set)):
            for s in skills:
                counter[str(s).lower()] += 1
        elif isinstance(skills, str) and skills.strip():
            for s in skills.split(","):
                counter[s.strip().lower()] += 1
    return [s for s, _ in counter.most_common(n)]


def _top_companies(results: pd.DataFrame, n: int = 3) -> list[str]:
    counter: Counter = Counter()
    for _, row in results.iterrows():
        c = row.get("company")
        if c and str(c).strip() and str(c).lower() != "nan":
            counter[str(c).strip()] += 1
    return [c for c, _ in counter.most_common(n)]


def _top_locations(results: pd.DataFrame, n: int = 3) -> list[str]:
    counter: Counter = Counter()
    for _, row in results.iterrows():
        loc = row.get("location") or row.get("country") or ""
        if loc and str(loc).strip() and str(loc).lower() != "nan":
            counter[str(loc).strip()] += 1
    return [f"{l} ({c})" if c > 1 else l for l, c in counter.most_common(n)]


def _top_seniority(results: pd.DataFrame, n: int = 3) -> list[str]:
    counter: Counter = Counter()
    for _, row in results.iterrows():
        lev = row.get("seniority_level")
        if lev and str(lev).strip() and str(lev).lower() != "nan":
            counter[str(lev).strip()] += 1
    return [f"{l} ({c})" if c > 1 else l for l, c in counter.most_common(n)]


def _is_role_question(question: str) -> bool:
    return bool(re.search(r"\b(?:role|jobs|position|hiring)\b", question.lower()))


def _compact_results(results: pd.DataFrame, max_items: int = 3) -> str:
    """Build a compact text block from results for the LLM context."""
    lines = []
    for _, row in results.head(max_items).iterrows():
        title = _val(row.get("job_title"), "Role")
        company = _val(row.get("company"), "")
        loc = _val(row.get("location"), _val(row.get("country"), ""))
        skills = row.get("skills", "")
        if isinstance(skills, (list, tuple)):
            skills = ", ".join(str(s) for s in skills[:4])
        elif isinstance(skills, str):
            skills = skills[:120]
        else:
            skills = ""

        line = f"{title}"
        if company:
            line += f" at {company}"
        if loc:
            line += f" ({loc})"
        if skills:
            line += f" — Skills: {skills}"
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Conversational answer composers
# ---------------------------------------------------------------------------

def _compose_market_answer(question: str, market_data: dict | None) -> str:
    if market_data and market_data.get("is_role_question"):
        roles = market_data.get("roles", [])
        country = market_data.get("country", "Africa")
        if not roles:
            return f"I don't have enough role data for {country} right now. Try checking the Career Insights dashboard for more details."

        top_roles = roles[:8]
        lines = [f"Here's what's trending in {country} right now!"]
        lines.append("")
        for r in top_roles:
            title = r.get("title", "Unknown")
            count = r.get("count", 0)
            lines.append(f"- **{title}** — {count} open{'s' if count > 1 else ''}")
        lines.append("")
        total = market_data.get("total_jobs", "N/A")
        lines.append(f"I looked through {total} job postings to find this.")
        if roles:
            top_3 = [r.get("title") for r in roles[:3]]
            lines.append(f"The hottest roles are **{', '.join(top_3)}** — worth exploring if you're on the market!")
        return "\n".join(lines)

    elif market_data and market_data.get("skills"):
        skills = market_data["skills"]
        country = market_data.get("country", "Africa")
        top_skills = skills[:8]
        lines = [f"Great question! Here are the most sought-after skills in {country}:"]
        lines.append("")
        for s in top_skills:
            name = s.get("name", "Unknown")
            pct = s.get("percentage", 0)
            lines.append(f"- **{name}** — {pct:.0f}% of jobs mention it")
        lines.append("")
        total = market_data.get("total_jobs", "N/A")
        lines.append(f"That's from {total} job postings. ")
        if skills:
            top_3 = [s.get("name") for s in skills[:3]]
            lines.append(f"Focus on **{', '.join(top_3)}** and you'll be in a strong position!")
        return "\n".join(lines)

    return f"That's a market data question — I'd recommend checking the **Skill Demand** or **Career Insights** dashboards for the most accurate numbers. Is there a specific skill or role you're curious about?"


def _compose_skill_answer(question: str, results: pd.DataFrame, mentioned_skills: list[str]) -> str:
    skills = _top_skills(results, 5)
    companies = _top_companies(results, 3)
    locs = _top_locations(results, 3)

    if mentioned_skills:
        skill_str = ", ".join(mentioned_skills)
        lines = [f"Great choice! **{skill_str}** is definitely in demand."]
    else:
        lines = [f"Here's what I found!"]

    lines.append("")

    if results.empty:
        lines.append("I didn't find specific job postings matching this, but based on general market trends, this is a valuable area to invest in.")
    else:
        n = len(results)
        lines.append(f"I found {n} relevant role{'s' if n != 1 else ''}.")
        if skills:
            lines.append(f"The top skills showing up are **{', '.join(skills)}**.")
        if companies:
            lines.append(f"Companies hiring for this include **{', '.join(companies)}**.")
        if locs:
            lines.append(f"Most opportunities are in **{', '.join(locs)}**.")

    lines.append("")
    lines.append("Want me to dig deeper into any of these, or are you looking for something specific?")
    return "\n".join(lines)


def _compose_job_answer(question: str, results: pd.DataFrame) -> str:
    if results.empty:
        return "I couldn't find matching jobs right now. Could you try broadening your search — maybe a different skill or location?"

    n = len(results)
    lines = [f"Found {n} role{'s' if n != 1 else ''} for you!"]
    lines.append("")

    for _, row in results.head(4).iterrows():
        title = _val(row.get("job_title"), "Role")
        company = _val(row.get("company"), "")
        loc = _val(row.get("location"), _val(row.get("country"), ""))
        skills = row.get("skills", "")
        if isinstance(skills, (list, tuple)):
            skills = ", ".join(str(s) for s in skills[:3])
        elif isinstance(skills, str):
            skills = skills[:80]
        else:
            skills = ""

        line = f"- **{title}**"
        if company:
            line += f" at {company}"
        if loc:
            line += f" ({loc})"
        if skills:
            line += f" — {skills}"
        lines.append(line)

    lines.append("")
    locs = _top_locations(results, 3)
    if locs:
        lines.append(f"Most of these are in **{', '.join(locs)}**.")
    lines.append("Want more details on any of these roles?")
    return "\n".join(lines)


def _compose_career_answer(question: str, results: pd.DataFrame) -> str:
    skills = _top_skills(results, 6)
    seniority = _top_seniority(results, 3)

    lines = ["Here's what I'd suggest based on what's out there:"]
    lines.append("")

    if seniority:
        lines.append(f"Career levels I'm seeing: **{', '.join(seniority)}**.")
    if skills:
        lines.append(f"The key skills to focus on are **{', '.join(skills)}**.")

    lines.append("")
    lines.append("If you want, I can look at your CV to see how you stack up, or help you find specific roles to target. What sounds good?")
    return "\n".join(lines)


def _compose_general_answer(question: str, results: pd.DataFrame) -> str:
    if results.empty:
        return "Hmm, I didn't find much for that. Could you try rephrasing or asking about a specific skill or location?"

    skills = _top_skills(results, 4)
    companies = _top_companies(results, 3)
    locs = _top_locations(results, 3)

    lines = [f"I found {len(results)} relevant result{'s' if len(results) != 1 else ''}!"]
    lines.append("")

    for _, row in results.head(3).iterrows():
        title = _val(row.get("job_title"), "Role")
        company = _val(row.get("company"), "")
        loc = _val(row.get("location"), "")
        line = f"- **{title}**"
        if company:
            line += f" at {company}"
        if loc:
            line += f" ({loc})"
        lines.append(line)

    lines.append("")
    if skills:
        lines.append(f"Top skills: **{', '.join(skills)}**")
    if companies:
        lines.append(f"Hiring: **{', '.join(companies)}**")

    lines.append("")
    lines.append("Want me to focus on something specific — like a particular skill, company, or location?")
    return "\n".join(lines)


def _compose_no_match_answer(question: str) -> str:
    return (
        f"I couldn't find strong matches for \"{question}\" — "
        f"it might be a niche area or phrased differently in our dataset.\n\n"
        f"Try broadening your search or using different keywords. "
        f"You can also check the **Skill Demand** tab for what's actually in our data. "
        f"What else can I help with?"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _val(value: Any, fallback: str) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback
    text = str(value).strip()
    return text if text and text.lower() != "nan" else fallback


def _source(row: pd.Series) -> dict[str, Any]:
    return {
        "job_id": _val(row.get("job_id"), ""),
        "title": _val(row.get("job_title"), ""),
        "company": _val(row.get("company"), ""),
        "url": _val(row.get("vacancy_url"), ""),
        "score": round(float(row.get("score", 0.0)), 4),
    }


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class JobPulseAssistant:
    """Conversational assistant for African tech job market questions.

    Uses retrieval-augmented generation with a local LLM for natural,
    grounded answers. Falls back to conversational templates when the
    LLM is unavailable.
    """

    def __init__(
        self,
        rag: JobPulseRAG | None = None,
        llm: OllamaLLM | None = None,
    ):
        self.rag = rag or JobPulseRAG()
        if llm:
            self.llm = llm
        else:
            try:
                from .config import create_llm_config
                self.llm = OllamaLLM(config=create_llm_config())
            except Exception:
                self.llm = OllamaLLM()
        self._history: list[dict[str, str]] = []

    @cache_rag_response
    def ask(self, question: str, top_k: int = 3, market_data: dict | None = None) -> AssistantAnswer:
        self.rag.ensure_ready()

        greeting = detect_greeting(question)
        if greeting:
            self._history.append({"role": "user", "content": question})
            self._history.append({"role": "assistant", "content": greeting})
            return AssistantAnswer(greeting, "grounded", [])

        question_type = _detect_question_type(question)

        if question_type == "market_intelligence":
            if market_data:
                market_data["is_role_question"] = _is_role_question(question)
            results = self.rag.query(question, top_k=top_k)
            sources = [_source(row) for _, row in results.iterrows()]
            answer = _compose_market_answer(question, market_data)
            self._history.append({"role": "user", "content": question})
            self._history.append({"role": "assistant", "content": answer})
            return AssistantAnswer(answer, "grounded", sources)

        results = self.rag.query(question, top_k=top_k)
        sources = [_source(row) for _, row in results.iterrows()]

        if results.empty or not self.rag.has_strong_matches(results):
            answer = _compose_no_match_answer(question)
            self._history.append({"role": "user", "content": question})
            self._history.append({"role": "assistant", "content": answer})
            return AssistantAnswer(answer, "low", sources)

        llm_answer = self._try_llm_generate(question, question_type, results)
        if llm_answer is not None:
            self._history.append({"role": "user", "content": question})
            self._history.append({"role": "assistant", "content": llm_answer})
            return AssistantAnswer(llm_answer, "grounded", sources)

        if question_type == "skill_inquiry":
            answer = _compose_skill_answer(question, results, _extract_mentioned_skills(question))
        elif question_type == "job_search":
            answer = _compose_job_answer(question, results)
        elif question_type == "career_advice":
            answer = _compose_career_answer(question, results)
        elif question_type == "salary_compensation":
            answer = _compose_general_answer(question, results)
        else:
            answer = _compose_general_answer(question, results)

        self._history.append({"role": "user", "content": question})
        self._history.append({"role": "assistant", "content": answer})
        return AssistantAnswer(answer, "grounded", sources)

    def _try_llm_generate(
        self, question: str, question_type: str, results: pd.DataFrame,
    ) -> str | None:
        if not self.llm.available:
            return None

        context = _compact_results(results, max_items=3)
        prompt = build_rag_prompt(question, question_type)
        return self.llm.generate(
            prompt=prompt,
            context=context,
            system=JOBPULSE_SYSTEM_PROMPT,
            history=self._history,
        )

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._history.clear()

    # ------------------------------------------------------------------
    # Streaming generation (token-by-token)
    # ------------------------------------------------------------------

    def ask_stream(
        self, question: str, top_k: int = 3, market_data: dict | None = None,
    ) -> Generator[str | dict[str, Any], None, None]:
        """Yield token chunks, then yield a final dict with metadata.

        Usage:
            for event in assistant.ask_stream("python jobs in Kenya"):
                if isinstance(event, str):
                    display(event)        # partial token
                else:
                    render_sources(event)  # final metadata dict

        This method bypasses the response cache since streaming produces
        incremental output that can't be cached as a single object.
        """
        self.rag.ensure_ready()

        # --- Greetings (no LLM needed) ---
        greeting = detect_greeting(question)
        if greeting:
            self._history.append({"role": "user", "content": question})
            self._history.append({"role": "assistant", "content": greeting})
            yield greeting
            yield {"confidence": "grounded", "sources": [], "method": "template"}
            return

        question_type = _detect_question_type(question)

        # --- Market intelligence (DB aggregation, no LLM needed) ---
        if question_type == "market_intelligence":
            if market_data:
                market_data["is_role_question"] = _is_role_question(question)
            results = self.rag.query(question, top_k=top_k)
            sources = [_source(row) for _, row in results.iterrows()]
            answer = _compose_market_answer(question, market_data)
            self._history.append({"role": "user", "content": question})
            self._history.append({"role": "assistant", "content": answer})
            yield answer
            yield {"confidence": "grounded", "sources": sources, "method": "template"}
            return

        # --- RAG retrieval ---
        results = self.rag.query(question, top_k=top_k)
        sources = [_source(row) for _, row in results.iterrows()]

        if results.empty or not self.rag.has_strong_matches(results):
            answer = _compose_no_match_answer(question)
            self._history.append({"role": "user", "content": question})
            self._history.append({"role": "assistant", "content": answer})
            yield answer
            yield {"confidence": "low", "sources": sources, "method": "template"}
            return

        # --- Try streaming LLM generation ---
        if self.llm.available:
            context = _compact_results(results, max_items=3)
            prompt = build_rag_prompt(question, question_type)
            from .config import get_optimization_config
            max_ctx = get_optimization_config().max_context_chars

            full_answer: list[str] = []
            for chunk in self.llm.generate_stream(
                prompt=prompt,
                context=context,
                system=JOBPULSE_SYSTEM_PROMPT,
                history=self._history,
                max_context_chars=max_ctx,
            ):
                full_answer.append(chunk)
                yield chunk

            assembled = "".join(full_answer).strip()
            if assembled:
                self._history.append({"role": "user", "content": question})
                self._history.append({"role": "assistant", "content": assembled})
                yield {"confidence": "grounded", "sources": sources, "method": "llm"}
                return

        # --- Fallback to template answers ---
        if question_type == "skill_inquiry":
            answer = _compose_skill_answer(question, results, _extract_mentioned_skills(question))
        elif question_type == "job_search":
            answer = _compose_job_answer(question, results)
        elif question_type == "career_advice":
            answer = _compose_career_answer(question, results)
        elif question_type == "salary_compensation":
            answer = _compose_general_answer(question, results)
        else:
            answer = _compose_general_answer(question, results)

        self._history.append({"role": "user", "content": question})
        self._history.append({"role": "assistant", "content": answer})
        yield answer
        yield {"confidence": "grounded", "sources": sources, "method": "template"}
