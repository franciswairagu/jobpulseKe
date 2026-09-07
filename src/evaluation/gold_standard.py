"""Auto-sample gold standard test data from the enriched NLP dataset.

Strategy:
  - Sample N records from the latest NLP parquet (stratified by source)
  - Auto-annotate using keyword heuristics:
      * Seniority: title keyword matching (proven reliable)
      * Work mode: keyword detection in description
      * Employment type: keyword detection in description/title
      * Skills: run extractor, validate by literal text presence + taxonomy scan
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.nlp.skill_extractor import SKILL_TAXONOMY, get_extractor
from src.nlp.metadata_extractor import SeniorityLevel, get_metadata_extractor
from src.nlp.nlpv2 import latest_nlp_output

logger = logging.getLogger(__name__)

SENIORITY_GOLD_KEYWORDS = {
    "intern": SeniorityLevel.INTERN,
    "internship": SeniorityLevel.INTERN,
    "graduate": SeniorityLevel.ENTRY,
    "junior": SeniorityLevel.ENTRY,
    "entry level": SeniorityLevel.ENTRY,
    "mid-level": SeniorityLevel.MID,
    "mid level": SeniorityLevel.MID,
    "senior": SeniorityLevel.SENIOR,
    "principal": SeniorityLevel.SENIOR,
    "lead": SeniorityLevel.LEAD,
    "manager": SeniorityLevel.LEAD,
    "director": SeniorityLevel.EXECUTIVE,
    "vp": SeniorityLevel.EXECUTIVE,
    "cto": SeniorityLevel.EXECUTIVE,
    "ceo": SeniorityLevel.EXECUTIVE,
}

WORKMODE_GOLD_KEYWORDS = {
    "remote": "Remote",
    "fully remote": "Remote",
    "work from home": "Remote",
    "wfh": "Remote",
    "hybrid": "Hybrid",
    "on-site": "On-Site",
    "on site": "On-Site",
    "onsite": "On-Site",
    "in-office": "On-Site",
}

EMPLOYMENT_GOLD_KEYWORDS = {
    "full-time": "Full-Time",
    "full time": "Full-Time",
    "part-time": "Part-Time",
    "part time": "Part-Time",
    "contract": "Contract",
    "temporary": "Temporary",
    "freelance": "Freelance",
    "internship": "Internship",
}


def _infer_gold_seniority(title: str, description: str) -> SeniorityLevel:
    """Gold seniority from title/description keywords."""
    combined = f"{title} {description}".lower()
    for keyword, level in SENIORITY_GOLD_KEYWORDS.items():
        if keyword in title.lower():
            return level
    for keyword, level in SENIORITY_GOLD_KEYWORDS.items():
        if keyword in combined:
            return level
    return SeniorityLevel.MID


def _infer_gold_work_mode(description: str) -> Optional[str]:
    """Gold work mode from description keywords."""
    text = description.lower()
    for keyword in ["fully remote", "work from home", "wfh", "remote"]:
        if keyword in text:
            return "Remote"
    if "hybrid" in text:
        return "Hybrid"
    for keyword in ["on-site", "on site", "onsite", "in-office", "in office"]:
        if keyword in text:
            return "On-Site"
    return None


def _infer_gold_employment(title: str, description: str) -> Optional[str]:
    """Gold employment type from title + description keywords."""
    combined = f"{title} {description}".lower()
    for keyword, emp_type in EMPLOYMENT_GOLD_KEYWORDS.items():
        if keyword in combined:
            return emp_type
    return None


def _validate_skills(
    extracted_flat: set, text: str, taxonomy: dict
) -> tuple[set, set]:
    """Validate extracted skills against text.

    Returns (validated_skills, likely_false_positives).
    A skill is considered validated if it literally appears in the text
    (case-insensitive). Skills not found in text are flagged as potential FPs.
    """
    text_lower = text.lower()
    validated = set()
    likely_fp = set()
    for skill in extracted_flat:
        if skill in text_lower:
            validated.add(skill)
        else:
            likely_fp.add(skill)
    return validated, likely_fp


def _scan_for_misses(text: str, taxonomy: dict, found_skills: set) -> set:
    """Scan the taxonomy for skills that appear in text but weren't extracted."""
    text_lower = text.lower()
    misses = set()
    for skill in taxonomy:
        if skill not in found_skills:
            if skill in text_lower:
                misses.add(skill)
    return misses


def build_gold_set(
    n_samples: int = 30,
    nlp_parquet: Optional[Path] = None,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Build a gold standard test set by auto-sampling from enriched data.

    Returns list of dicts with keys:
        job_title, job_description, expected_skills, expected_seniority,
        expected_work_mode, expected_employment_type, source
    """
    if nlp_parquet is None:
        nlp_parquet = latest_nlp_output()

    if nlp_parquet is None or not Path(nlp_parquet).exists():
        logger.warning("No NLP output found — using synthetic fallback gold set")
        return _synthetic_fallback()

    df = pd.read_parquet(nlp_parquet)

    # Filter to records with meaningful descriptions
    df = df[df["job_description"].fillna("").str.strip().str.len() >= 50].copy()
    if len(df) == 0:
        logger.warning("No records with sufficient description length — using synthetic fallback")
        return _synthetic_fallback()

    # Stratified sample by source
    n_samples = min(n_samples, len(df))
    if "source" in df.columns:
        sampled = df.groupby("source", group_keys=False).apply(
            lambda g: g.sample(n=min(len(g), max(1, n_samples // max(1, df["source"].nunique()))), random_state=seed),
            include_groups=False,
        )
        # Trim or pad to exactly n_samples
        if len(sampled) > n_samples:
            sampled = sampled.sample(n=n_samples, random_state=seed)
        elif len(sampled) < n_samples:
            remaining = df.drop(sampled.index).sample(n=n_samples - len(sampled), random_state=seed)
            sampled = pd.concat([sampled, remaining])
    else:
        sampled = df.sample(n=n_samples, random_state=seed)

    skill_extractor = get_extractor()
    gold_set = []

    for _, row in sampled.iterrows():
        title = str(row.get("job_title") or "")
        desc = str(row.get("job_description") or "")
        text = f"{title} {desc}"

        # Auto-annotate gold labels
        gold_seniority = _infer_gold_seniority(title, desc)
        gold_work_mode = _infer_gold_work_mode(desc)
        gold_employment = _infer_gold_employment(title, desc)

        # Extract and validate skills
        extracted = skill_extractor.extract_skills(text)
        extracted_flat = {s for skills in extracted.values() for s in skills}
        validated, likely_fp = _validate_skills(extracted_flat, text, SKILL_TAXONOMY)
        misses = _scan_for_misses(text, SKILL_TAXONOMY, extracted_flat)

        # Gold skills = validated extraction + detected misses
        gold_skills = validated | misses

        gold_set.append({
            "job_title": title,
            "job_description": desc,
            "expected_skills": gold_skills,
            "expected_seniority": gold_seniority,
            "expected_work_mode": gold_work_mode,
            "expected_employment_type": gold_employment,
            "source": row.get("source", "unknown"),
        })

    logger.info("Built gold set: %d examples from %d candidates", len(gold_set), len(df))
    return gold_set


def _synthetic_fallback() -> List[Dict[str, Any]]:
    """Fallback synthetic gold set when no NLP data is available."""
    return [
        {
            "job_title": "Senior Python Backend Developer",
            "job_description": (
                "We're looking for a Senior Python Developer with 5+ years of experience "
                "building REST APIs with Django and FastAPI. Experience with PostgreSQL, "
                "Redis, and AWS is required. Docker and Kubernetes knowledge is a plus."
            ),
            "expected_skills": {"python", "django", "fastapi", "postgresql", "redis", "aws", "docker", "kubernetes"},
            "expected_seniority": SeniorityLevel.SENIOR,
            "expected_work_mode": None,
            "expected_employment_type": None,
            "source": "synthetic",
        },
        {
            "job_title": "Junior Frontend Developer",
            "job_description": (
                "Entry level React developer wanted. You'll work with JavaScript, "
                "TypeScript, and modern CSS. No prior experience required."
            ),
            "expected_skills": {"react", "javascript", "typescript", "css"},
            "expected_seniority": SeniorityLevel.ENTRY,
            "expected_work_mode": None,
            "expected_employment_type": None,
            "source": "synthetic",
        },
        {
            "job_title": "DevOps Engineer",
            "job_description": (
                "3+ years experience with Terraform, Kubernetes, and CI/CD pipelines. "
                "Strong knowledge of AWS and Azure required."
            ),
            "expected_skills": {"terraform", "kubernetes", "aws", "azure", "ci/cd"},
            "expected_seniority": SeniorityLevel.MID,
            "expected_work_mode": None,
            "expected_employment_type": None,
            "source": "synthetic",
        },
        {
            "job_title": "Data Scientist - Machine Learning",
            "job_description": (
                "Lead our ML team building models with TensorFlow and PyTorch. "
                "Strong Python and SQL skills required. Experience with Scikit-learn."
            ),
            "expected_skills": {"tensorflow", "pytorch", "python", "sql", "scikit-learn"},
            "expected_seniority": SeniorityLevel.LEAD,
            "expected_work_mode": None,
            "expected_employment_type": None,
            "source": "synthetic",
        },
        {
            "job_title": "Intern - Software Engineering",
            "job_description": (
                "Summer internship for students. Learn Java and Spring Boot from our "
                "engineering team. No prior professional experience required."
            ),
            "expected_skills": {"java", "spring boot"},
            "expected_seniority": SeniorityLevel.INTERN,
            "expected_work_mode": None,
            "expected_employment_type": None,
            "source": "synthetic",
        },
    ]
