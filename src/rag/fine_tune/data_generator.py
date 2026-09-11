"""Auto-generate Q&A training pairs from job postings.

Parses rag_document fields and generates question-answer pairs using
templates for each question type (skill_inquiry, job_search, career_advice,
market_intelligence, salary_compensation, company_industry, location_geography).
"""
import json
import logging
import random
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Question templates per type
# ---------------------------------------------------------------------------

_SKILL_TEMPLATES = [
    "What skills are required for a {job_title}?",
    "What technical skills does a {job_title} need?",
    "Which programming languages are needed for {job_title} roles?",
    "What frameworks and tools should a {job_title} know?",
    "What are the must-have skills for {job_title}?",
    "Is {skill} important for {job_title} positions?",
    "What tech stack do {job_title}s use?",
]

_JOB_SEARCH_TEMPLATES = [
    "Are there any {job_title} openings at {company}?",
    "Find {job_title} jobs in {location}",
    "What {job_title} roles are available in {country}?",
    "Show me remote {job_title} positions",
    "Which companies are hiring {job_title}s?",
    "What {work_mode} {job_title} jobs exist?",
    "Are there {seniority_level} {job_title} positions in {location}?",
]

_CAREER_TEMPLATES = [
    "How do I become a {job_title}?",
    "What career path leads to {job_title}?",
    "What is the career progression for {job_title}?",
    "What seniority levels exist for {job_title}?",
    "How do I transition into {job_title}?",
    "What does a {seniority_level} {job_title} do?",
    "What skills do I need to advance from junior to senior {job_title}?",
]

_MARKET_TEMPLATES = [
    "What are the most in-demand skills in {country}?",
    "Which skills are trending in {location}?",
    "What is the job market like for {job_title} in {country}?",
    "How many {job_title} jobs are there in {location}?",
    "What companies are hiring the most in {country}?",
    "What are the top roles in {location}?",
    "What is the demand for {skill} in {country}?",
]

_SALARY_TEMPLATES = [
    "What is the salary range for {job_title}?",
    "How much do {job_title}s earn in {country}?",
    "What is the average pay for {seniority_level} {job_title}?",
    "What compensation can I expect as a {job_title}?",
]

_COMPANY_TEMPLATES = [
    "What does {company} hire for?",
    "What roles are available at {company}?",
    "Is {company} hiring in {location}?",
    "What tech stack does {company} use?",
]

_LOCATION_TEMPLATES = [
    "What tech jobs are available in {location}?",
    "Which companies are hiring in {country}?",
    "What is the tech scene like in {location}?",
    "Are there remote jobs available in {country}?",
]

TEMPLATES = {
    "skill_inquiry": _SKILL_TEMPLATES,
    "job_search": _JOB_SEARCH_TEMPLATES,
    "career_advice": _CAREER_TEMPLATES,
    "market_intelligence": _MARKET_TEMPLATES,
    "salary_compensation": _SALARY_TEMPLATES,
    "company_industry": _COMPANY_TEMPLATES,
    "location_geography": _LOCATION_TEMPLATES,
}

# Template weights (higher = more likely to be sampled)
TYPE_WEIGHTS = {
    "skill_inquiry": 3,
    "job_search": 3,
    "career_advice": 2,
    "market_intelligence": 2,
    "salary_compensation": 1,
    "company_industry": 2,
    "location_geography": 1,
}

SYSTEM_PROMPT = """You are JobPulse Assistant, an AI helper for the African tech job market.
Answer questions about tech jobs, skills, careers, and market trends across Africa.
Use ONLY the provided context. Be concise, cite sources, and end with a practical recommendation."""


def _safe_str(value: Any) -> str:
    """Convert value to string, handling NaN/None."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in ("nan", "none", "") else text


def _extract_fields(row: dict) -> dict:
    """Extract structured fields from a job record."""
    skills = row.get("skills", [])
    # Handle numpy arrays
    if hasattr(skills, 'tolist'):
        skills = skills.tolist()
    if isinstance(skills, str):
        try:
            skills = json.loads(skills)
        except (json.JSONDecodeError, TypeError):
            skills = [s.strip() for s in skills.split(",") if s.strip()]

    return {
        "job_title": _safe_str(row.get("job_title")),
        "company": _safe_str(row.get("company")),
        "location": _safe_str(row.get("location")),
        "country": _safe_str(row.get("country")),
        "work_mode": _safe_str(row.get("work_mode")),
        "seniority_level": _safe_str(row.get("seniority_level")),
        "skills": skills,
        "rag_document": _safe_str(row.get("rag_document")),
    }


def _build_answer(fields: dict, q_type: str) -> str:
    """Build a grounded answer from the job fields."""
    parts = []

    if q_type == "skill_inquiry":
        skills = fields.get("skills", [])
        if skills:
            skills_str = ", ".join(skills[:10])
            parts.append(f"Based on the available job data, the skills required include: {skills_str}.")
            if fields["job_title"]:
                parts.append(f"These are for the {fields['job_title']} role")
                if fields["company"]:
                    parts.append(f"at {fields['company']}")
                parts.append(".")
        else:
            parts.append(f"The specific skills for {fields['job_title'] or 'this role'} are not fully listed in the dataset.")

    elif q_type == "job_search":
        if fields["job_title"]:
            parts.append(f"I found a {fields['job_title']} position")
            if fields["company"]:
                parts.append(f"at {fields['company']}")
            if fields["location"]:
                parts.append(f"in {fields['location']}")
            elif fields["country"]:
                parts.append(f"in {fields['country']}")
            parts.append(".")
            if fields["work_mode"]:
                parts.append(f"Work mode: {fields['work_mode']}.")
            skills = fields.get("skills", [])
            if skills:
                parts.append(f"Key skills: {', '.join(skills[:6])}.")

    elif q_type == "career_advice":
        parts.append(f"For a career as {fields['job_title'] or 'this role'}:")
        if fields["seniority_level"]:
            parts.append(f"Current level: {fields['seniority_level']}.")
        skills = fields.get("skills", [])
        if skills:
            parts.append(f"Focus on these skills: {', '.join(skills[:8])}.")

    elif q_type == "market_intelligence":
        if fields["country"]:
            parts.append(f"In {fields['country']}, there is demand for tech talent.")
        if fields["location"]:
            parts.append(f"Specifically in {fields['location']}.")
        skills = fields.get("skills", [])
        if skills:
            parts.append(f"Top skills: {', '.join(skills[:5])}.")

    elif q_type == "salary_compensation":
        parts.append("Salary data is limited in the current dataset.")
        if fields["seniority_level"]:
            parts.append(f"For {fields['seniority_level']} level roles, compensation varies by company and location.")

    elif q_type == "company_industry":
        if fields["company"]:
            parts.append(f"{fields['company']} is hiring for tech roles.")
            if fields["job_title"]:
                parts.append(f"Role: {fields['job_title']}.")

    elif q_type == "location_geography":
        location = fields["location"] or fields["country"]
        if location:
            parts.append(f"In {location}, there are tech job opportunities.")
            if fields["job_title"]:
                parts.append(f"Example: {fields['job_title']}.")

    else:
        if fields["job_title"]:
            parts.append(f"The {fields['job_title']} role")
            if fields["company"]:
                parts.append(f"at {fields['company']}")
            parts.append(" offers a good opportunity in the tech market.")
            skills = fields.get("skills", [])
            if skills:
                parts.append(f"Required skills include: {', '.join(skills[:6])}.")

    if not parts:
        parts.append("Based on the available data, this appears to be a relevant opportunity in the tech sector.")

    return " ".join(parts)


class TrainingDataGenerator:
    """Generate Q&A training pairs from job postings."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def generate_from_parquet(
        self,
        parquet_path: Path,
        max_pairs_per_job: int = 3,
        output_path: Path | None = None,
    ) -> list[dict]:
        """Generate training pairs from an enriched NLP parquet file."""
        df = pd.read_parquet(parquet_path)
        logger.info("Loaded %d records from %s", len(df), parquet_path)

        pairs = []
        records = df.to_dict(orient="records")

        for i, row in enumerate(records):
            fields = _extract_fields(row)
            if not fields["rag_document"]:
                continue

            num_pairs = random.randint(1, max_pairs_per_job)
            selected_types = random.choices(
                list(TEMPLATES.keys()),
                weights=[TYPE_WEIGHTS[t] for t in TEMPLATES.keys()],
                k=num_pairs,
            )

            for q_type in selected_types:
                templates = TEMPLATES[q_type]
                template = random.choice(templates)

                # Fill template with available fields
                question = self._fill_template(template, fields)
                if not question:
                    continue

                answer = _build_answer(fields, q_type)

                pairs.append({
                    "question": question,
                    "answer": answer,
                    "question_type": q_type,
                    "context": fields["rag_document"],
                    "job_id": row.get("job_id", ""),
                    "metadata": {
                        "job_title": fields["job_title"],
                        "company": fields["company"],
                        "location": fields["location"],
                        "country": fields["country"],
                        "skills": fields["skills"][:10],
                    },
                })

        logger.info("Generated %d training pairs from %d jobs", len(pairs), len(records))

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(pairs, f, indent=2)
            logger.info("Saved training pairs to %s", output_path)

        return pairs

    def _fill_template(self, template: str, fields: dict) -> str:
        """Fill a template string with field values."""
        skills = fields.get("skills", [])
        # Handle numpy arrays
        if hasattr(skills, 'tolist'):
            skills = skills.tolist()
        first_skill = skills[0] if skills and len(skills) > 0 else ""

        replacements = {
            "{job_title}": fields.get("job_title", ""),
            "{company}": fields.get("company", ""),
            "{location}": fields.get("location", "") or fields.get("country", ""),
            "{country}": fields.get("country", ""),
            "{work_mode}": fields.get("work_mode", ""),
            "{seniority_level}": fields.get("seniority_level", ""),
            "{skill}": str(first_skill) if first_skill else "",
        }

        for placeholder, value in replacements.items():
            if placeholder in template and not value:
                return ""
            template = template.replace(placeholder, value)

        return template.strip()

    def generate_chatml_format(
        self,
        pairs: list[dict],
    ) -> list[dict]:
        """Convert pairs to ChatML format for fine-tuning."""
        formatted = []
        for pair in pairs:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{pair['context']}\n\n{pair['question']}"},
                {"role": "assistant", "content": pair["answer"]},
            ]
            formatted.append({
                "messages": messages,
                "question_type": pair.get("question_type", "general"),
            })
        return formatted
