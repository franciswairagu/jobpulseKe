"""Adapters from JobPulse CSV/Parquet records to recommender models."""

import re
from pathlib import Path
from typing import Iterable

from app.ml.preprocessing.skill_extractor import get_extractor
from .models import Job


def jobs_from_records(records: Iterable[dict]) -> list[Job]:
    extractor = get_extractor()
    jobs = []
    for index, record in enumerate(records):
        description = _text(record.get("job_description") or record.get("description"))
        extracted = extractor.extract_skills(description)
        skills = {skill for group in extracted.values() for skill in group}
        preferred_skills = _extract_preferred_skills(description, extractor)
        explicit_skills = record.get("skills")
        if isinstance(explicit_skills, (list, set, tuple)):
            skills.update(str(item) for item in explicit_skills)
        jobs.append(Job(
            job_id=_text(record.get("job_id")) or str(index),
            title=_text(record.get("job_title") or record.get("title")),
            company=_text(record.get("company")), description=description, skills=skills - preferred_skills,
            years_experience=extractor.extract_years_experience(description),
            country=_text(record.get("country")), work_mode=_text(record.get("work_mode")),
            employment_type=_text(record.get("employment_type")),
            application_deadline=_text(record.get("application_deadline")),
            vacancy_url=_text(record.get("vacancy_url") or record.get("url")),
            preferred_skills=preferred_skills,
        ))
    return jobs


def load_jobs(path: str | Path) -> list[Job]:
    """Load a CSV or Parquet file from a JobPulse pipeline export."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Job dataset does not exist: {source}")
    import pandas as pd
    if source.suffix.lower() == ".csv":
        frame = pd.read_csv(source)
    elif source.suffix.lower() in {".parquet", ".pq"}:
        frame = pd.read_parquet(source)
    else:
        raise ValueError("Job dataset must be a CSV or Parquet file.")
    return jobs_from_records(frame.fillna("").to_dict(orient="records"))


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _extract_preferred_skills(description: str, extractor) -> set[str]:
    """Extract skills only from common optional-requirement clauses."""
    optional_clauses = re.findall(
        r"[^.\n]*(?:preferred|nice to have|bonus|advantageous|plus)[^.\n]*",
        description,
        flags=re.IGNORECASE,
    )
    extracted = set()
    for clause in optional_clauses:
        for group in extractor.extract_skills(clause).values():
            extracted.update(group)
    return extracted
