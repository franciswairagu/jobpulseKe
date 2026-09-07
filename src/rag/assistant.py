"""Grounded answer layer over JobPulse retrieval results.

This deliberately does not invent market facts. Every job named in an answer
is a retrieved record and appears again in `sources`, making it safe to expose
before an optional LLM generation provider is configured.
"""

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from .retriever import JobPulseRAG


@dataclass
class AssistantAnswer:
    answer: str
    confidence: str
    sources: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class JobPulseAssistant:
    """Answer job-market questions using only retrieved JobPulse records."""

    def __init__(self, rag: JobPulseRAG | None = None):
        self.rag = rag or JobPulseRAG()

    def ask(self, question: str, top_k: int = 5) -> AssistantAnswer:
        self.rag.ensure_ready()
        results = self.rag.query(question, top_k=top_k)
        sources = [_source(row) for _, row in results.iterrows()]
        if results.empty or not self.rag.has_strong_matches(results):
            return AssistantAnswer(
                "I could not find a strong match in the indexed JobPulse postings. "
                "Try adding a role, skill, country, or work mode.", "low", sources,
            )
        return AssistantAnswer(_compose_answer(question, results), "grounded", sources)


def _compose_answer(question: str, results: pd.DataFrame) -> str:
    lines = [f'I found {len(results)} relevant JobPulse posting(s) for "{question}".']
    for position, (_, row) in enumerate(results.iterrows(), start=1):
        title = _value(row.get("job_title"), "Untitled role")
        company = _value(row.get("company"), "Unknown company")
        location = _value(row.get("location"), _value(row.get("country"), "Unknown location"))
        mode = _value(row.get("work_mode"), "work mode not listed")
        skills = _skills(row.get("skills"))
        detail = f"{position}. {title} at {company} — {location}; {mode}."
        if skills:
            detail += f" Skills: {skills}."
        lines.append(detail)
    lines.append("These results are retrieved from the indexed JobPulse dataset; verify each listing before applying.")
    return "\n".join(lines)


def _source(row: pd.Series) -> dict[str, Any]:
    return {
        "job_id": _value(row.get("job_id"), ""),
        "title": _value(row.get("job_title"), "Untitled role"),
        "company": _value(row.get("company"), "Unknown company"),
        "url": _value(row.get("vacancy_url"), ""),
        "score": round(float(row.get("score", 0.0)), 4),
    }


def _value(value: Any, fallback: str) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback
    text = str(value).strip()
    return text if text and text.lower() != "nan" else fallback


def _skills(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in value[:8])
    return "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)
