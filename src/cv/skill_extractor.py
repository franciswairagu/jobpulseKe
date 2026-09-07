"""Extract a normalised candidate profile from CV text."""

import re

from src.nlp.skill_extractor import get_extractor
from src.recommender.models import CandidateProfile
from src.recommender.skills_matcher import SkillMatcher


def profile_from_text(text: str, name: str = "") -> CandidateProfile:
    """Build a candidate profile using the same taxonomy used for job ads."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("CV text is empty or unreadable.")
    extractor = get_extractor()
    extracted = extractor.extract_skills(text)
    skills = SkillMatcher().normalize_skills({skill for group in extracted.values() for skill in group})
    inferred_name = name.strip() or _infer_name(text)
    return CandidateProfile(
        name=inferred_name,
        skills=skills,
        years_experience=_estimate_years_experience(text),
        education=extractor.extract_education(text),
        certifications=extractor.extract_certifications(text),
    )


def _infer_name(text: str) -> str:
    """Use a plausible first header line without treating an email as a name."""
    for line in text.splitlines()[:8]:
        candidate = " ".join(line.strip().split())
        if candidate and "@" not in candidate and 1 < len(candidate) <= 70 and len(candidate.split()) <= 5:
            return candidate.title() if candidate.isupper() else candidate
    return "Candidate"


def _estimate_years_experience(text: str) -> int:
    explicit = get_extractor().extract_years_experience(text)
    # CVs often write "2021–Present" rather than an explicit count.
    years = [int(year) for year in re.findall(r"\b(19\d{2}|20\d{2})\b", text)]
    current_year = __import__("datetime").date.today().year
    past_years = [year for year in years if year <= current_year]
    dated_estimate = max(0, current_year - min(past_years)) if past_years else 0
    return min(max(explicit, dated_estimate), 50)
