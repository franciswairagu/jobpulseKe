"""
Skill extraction for job postings and CV text.

IMPORTANT PROVENANCE NOTE
--------------------------------------------------------------------
The original `src/nlp/skill_extractor.py` referenced by
`nlp_analysis.ipynb` and by `src/recommender/job_loader.py`
(`from src.nlp.skill_extractor import get_extractor`) was never
uploaded to this project. This module is a reconstruction built to
match the *interface* the notebook and job_loader.py actually call:

    extractor = get_extractor()
    extracted = extractor.extract_skills(text)        # -> dict[str, set[str]]
    years = extractor.extract_years_experience(text)  # -> int

It is deliberately transparent, keyword/regex based extraction - not
a trained model - because that is also what the notebook's own
description of skill extraction describes ("keyword matching against
a skill list"). If the real `src/nlp/skill_extractor.py` becomes
available, drop it in at this path/interface and nothing else in the
backend needs to change.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, Set


# Skill taxonomy grouped by category. Extend freely - this is data, not logic.
SKILL_TAXONOMY: Dict[str, list[str]] = {
    "languages": [
        "python", "java", "javascript", "typescript", "go", "golang", "c#", "csharp",
        "c++", "php", "ruby", "kotlin", "swift", "rust", "scala", "r", "sql", "bash",
    ],
    "frameworks_libraries": [
        "django", "flask", "fastapi", "react", "next.js", "nextjs", "vue", "angular",
        "node.js", "nodejs", "express", "spring", "spring boot", ".net", "asp.net",
        "aspnet", "laravel", "rails", "tensorflow", "pytorch", "scikit-learn",
        "sklearn", "pandas", "numpy",
    ],
    "databases": [
        "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite",
        "elasticsearch", "dynamodb", "cassandra", "oracle", "mssql", "sql server",
    ],
    "cloud_devops": [
        "aws", "amazon web services", "azure", "microsoft azure", "gcp",
        "google cloud", "docker", "kubernetes", "k8s", "terraform", "ansible",
        "jenkins", "ci/cd", "cicd", "github actions", "gitlab ci",
    ],
    "data_ml": [
        "machine learning", "deep learning", "nlp", "computer vision", "power bi",
        "powerbi", "tableau", "excel", "data analysis", "data visualization",
        "etl", "airflow", "spark", "hadoop", "huggingface", "hugging face",
    ],
    "tools_other": [
        "git", "jira", "figma", "linux", "rest api", "graphql", "microservices",
        "agile", "scrum", "unit testing", "api design",
    ],
}


def _build_patterns(taxonomy: Dict[str, list[str]]) -> Dict[str, list[tuple[str, re.Pattern]]]:
    patterns: Dict[str, list[tuple[str, re.Pattern]]] = {}
    for category, skills in taxonomy.items():
        compiled = []
        for skill in skills:
            escaped = re.escape(skill.lower())
            lowered_skill = skill.lower()
            # Word-boundary match for alphanumeric skill names; falls back to
            # a whitespace boundary for tokens with punctuation at either
            # edge (e.g. "c++", "ci/cd", ".net") where an alnum boundary
            # would never match. Using re.search (not re.match) to check
            # the *last* character, since re.match always anchors at index 0.
            starts_alnum = bool(re.match(r"^[a-z0-9]", lowered_skill))
            ends_alnum = bool(re.search(r"[a-z0-9]$", lowered_skill))
            if starts_alnum and ends_alnum:
                pattern = re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")
            else:
                pattern = re.compile(rf"(?<!\S){escaped}(?!\S)" if not ends_alnum else rf"(?<!\S){escaped}(?![a-z0-9])")
            compiled.append((skill, pattern))
        patterns[category] = compiled
    return patterns


_YEARS_EXPERIENCE_PATTERNS = [
    re.compile(r"(\d{1,2})\s*\+?\s*years?\s+(?:of\s+)?experience", re.IGNORECASE),
    re.compile(r"experience\s*[:\-]?\s*(\d{1,2})\s*\+?\s*years?", re.IGNORECASE),
    re.compile(r"(\d{1,2})\s*\+?\s*yrs?\b", re.IGNORECASE),
]

EDUCATION_KEYWORDS = {
    "bachelor": "Bachelor's degree",
    "b.sc": "Bachelor's degree",
    "bsc": "Bachelor's degree",
    "master": "Master's degree",
    "msc": "Master's degree",
    "m.sc": "Master's degree",
    "phd": "PhD",
    "doctorate": "PhD",
    "diploma": "Diploma",
}

CERTIFICATION_KEYWORDS = [
    "aws certified", "azure certified", "google cloud certified", "pmp",
    "ccna", "comptia", "scrum master", "cissp", "ckad", "cka",
]

SENIORITY_KEYWORDS = {
    "intern": "Intern",
    "junior": "Junior",
    "entry level": "Entry Level",
    "entry-level": "Entry Level",
    "mid level": "Mid Level",
    "mid-level": "Mid Level",
    "senior": "Senior",
    "lead": "Lead",
    "principal": "Principal",
    "head of": "Head",
    "manager": "Manager",
    "director": "Director",
}


class SkillExtractor:
    """Keyword/regex based skill and metadata extraction."""

    def __init__(self, taxonomy: Dict[str, list[str]] | None = None):
        self.taxonomy = taxonomy or SKILL_TAXONOMY
        self._patterns = _build_patterns(self.taxonomy)

    def extract_skills(self, text: str) -> Dict[str, Set[str]]:
        """Return {category: {skills found}} for the given free text."""
        if not text or not isinstance(text, str):
            return {category: set() for category in self.taxonomy}
        lowered = text.lower()
        results: Dict[str, Set[str]] = {}
        for category, compiled in self._patterns.items():
            found = {skill for skill, pattern in compiled if pattern.search(lowered)}
            results[category] = found
        return results

    def extract_years_experience(self, text: str) -> int:
        if not text or not isinstance(text, str):
            return 0
        best = 0
        for pattern in _YEARS_EXPERIENCE_PATTERNS:
            for match in pattern.finditer(text):
                try:
                    value = int(match.group(1))
                except (ValueError, IndexError):
                    continue
                if 0 < value <= 40:
                    best = max(best, value)
        return best

    def extract_education(self, text: str) -> list[str]:
        if not text:
            return []
        lowered = text.lower()
        found = {label for keyword, label in EDUCATION_KEYWORDS.items() if keyword in lowered}
        return sorted(found)

    def extract_certifications(self, text: str) -> list[str]:
        if not text:
            return []
        lowered = text.lower()
        return sorted({kw for kw in CERTIFICATION_KEYWORDS if kw in lowered})

    def extract_seniority(self, text: str) -> tuple[str | None, bool]:
        """Return (seniority_level, keyword_found)."""
        if not text:
            return None, False
        lowered = text.lower()
        for keyword, label in SENIORITY_KEYWORDS.items():
            if keyword in lowered:
                return label, True
        return None, False


@lru_cache(maxsize=1)
def get_extractor() -> SkillExtractor:
    """Process-wide singleton, mirroring the notebook's `get_extractor()` usage."""
    return SkillExtractor()
