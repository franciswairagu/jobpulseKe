"""
CV analysis orchestration.

compute_cv_score() is the ONE deterministic-scoring function in this
codebase. It is documented here in full so nobody mistakes it for an
ML output:

    up to 40 pts  -> breadth of skills found (10+ distinct skills = full marks)
    up to 25 pts  -> years of experience stated (8+ years = full marks)
    20 pts        -> any education credential detected
    up to 15 pts  -> certifications found (3+ = full marks)

This mirrors the *shape* the spec wants (a 0-100 score under "cv_score")
without pretending the underlying rule-based extractor is a scoring
model - it never claimed to produce one.
"""

from __future__ import annotations

import uuid
from collections import Counter

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.storage import get_storage_backend
from app.ml.adapters.cv_analyzer import CVAnalyzer, CVExtraction
from app.ml.preprocessing import cv_parser
from app.models.enums import ResumeStatus, SkillSource
from app.models.job import Job, JobSkill
from app.models.recommendation import ModelPrediction
from app.models.resume import Resume, ResumeAnalysis
from app.models.skill import Skill, UserSkill

MAX_SKILL_SCORE_COUNT = 10
MAX_EXPERIENCE_SCORE_YEARS = 8
MAX_CERT_SCORE_COUNT = 3


def compute_cv_score(extraction: CVExtraction) -> int:
    skill_component = 40 * min(len(extraction.skills_found), MAX_SKILL_SCORE_COUNT) / MAX_SKILL_SCORE_COUNT
    experience_component = 25 * min(extraction.years_experience, MAX_EXPERIENCE_SCORE_YEARS) / MAX_EXPERIENCE_SCORE_YEARS
    education_component = 20 if extraction.education else 0
    cert_component = 15 * min(len(extraction.certifications), MAX_CERT_SCORE_COUNT) / MAX_CERT_SCORE_COUNT
    return round(skill_component + experience_component + education_component + cert_component)


def derive_strengths_weaknesses(extraction: CVExtraction) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    weaknesses: list[str] = []

    if len(extraction.skills_found) >= 8:
        strengths.append(f"Broad technical skill set ({len(extraction.skills_found)} skills detected).")
    elif len(extraction.skills_found) <= 2:
        weaknesses.append("Very few technical skills detected in the CV text.")

    if extraction.years_experience >= 4:
        strengths.append(f"{extraction.years_experience}+ years of stated experience.")
    elif extraction.years_experience == 0:
        weaknesses.append("No years of experience explicitly stated.")

    if extraction.certifications:
        strengths.append(f"Holds {len(extraction.certifications)} relevant certification(s).")
    else:
        weaknesses.append("No certifications detected.")

    if extraction.education:
        strengths.append(f"Education credential detected: {', '.join(extraction.education)}.")
    else:
        weaknesses.append("No formal education credential detected in the CV text.")

    if not extraction.classifier_available:
        weaknesses.append(
            "Tech-category classification unavailable (no trained classifier artifact loaded) - "
            "career-path matching relies on skill overlap only."
        )

    return strengths, weaknesses


def top_market_skills(db: Session, limit: int = 25) -> list[str]:
    """Real DB aggregate: most frequently required skills across ingested jobs."""
    rows = (
        db.query(Skill.name, func.count(JobSkill.id).label("cnt"))
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .group_by(Skill.name)
        .order_by(func.count(JobSkill.id).desc())
        .limit(limit)
        .all()
    )
    return [name for name, _ in rows]


def derive_missing_skills(db: Session, extraction: CVExtraction, limit: int = 5) -> list[str]:
    have = {s.lower() for s in extraction.skills_found}
    market_skills = top_market_skills(db, limit=50)
    missing = [s for s in market_skills if s.lower() not in have]
    return missing[:limit]


def _get_or_create_skill(db: Session, name: str) -> Skill:
    existing = db.query(Skill).filter(func.lower(Skill.name) == name.lower()).first()
    if existing:
        return existing
    skill = Skill(name=name)
    db.add(skill)
    db.flush()
    return skill


def sync_user_skills(db: Session, user_id: uuid.UUID, skill_names: list[str]) -> None:
    for name in skill_names:
        skill = _get_or_create_skill(db, name)
        existing_link = (
            db.query(UserSkill)
            .filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill.id)
            .first()
        )
        if not existing_link:
            db.add(UserSkill(user_id=user_id, skill_id=skill.id, source=SkillSource.CV))


def process_resume(db: Session, resume: Resume) -> ResumeAnalysis:
    """Runs the full pipeline synchronously. Called directly or from a
    Celery task (see app/workers/tasks.py) depending on deployment size."""

    storage = get_storage_backend()
    try:
        resume.status = ResumeStatus.EXTRACTING_TEXT
        resume.stage = "EXTRACTING_TEXT"
        resume.progress = 20
        db.add(resume)
        db.commit()

        local_path = storage.read_path(resume.storage_key)
        cv_parser.validate_file(local_path)
        text = cv_parser.extract_text(local_path)

        resume.status = ResumeStatus.NLP_ANALYSIS
        resume.stage = "NLP_ANALYSIS"
        resume.progress = 55
        db.add(resume)
        db.commit()

        analyzer = CVAnalyzer()
        extraction = analyzer.analyze(text)

        resume.status = ResumeStatus.SKILL_ANALYSIS
        resume.stage = "SKILL_ANALYSIS"
        resume.progress = 75
        db.add(resume)
        db.commit()

        cv_score = compute_cv_score(extraction)
        strengths, weaknesses = derive_strengths_weaknesses(extraction)
        missing_skills = derive_missing_skills(db, extraction)

        analysis = ResumeAnalysis(
            resume_id=resume.id,
            cv_score=cv_score,
            score_type="deterministic_composite",
            tech_category=extraction.tech_category,
            tech_category_confidence=extraction.tech_category_confidence,
            classifier_available=extraction.classifier_available,
            classifier_model_version=extraction.classifier_model_version,
            skills_found=extraction.skills_found,
            years_experience=extraction.years_experience,
            education=extraction.education,
            certifications=extraction.certifications,
            seniority_level=extraction.seniority_level,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_skills=missing_skills,
        )
        db.add(analysis)

        sync_user_skills(db, resume.user_id, extraction.skills_found)

        db.add(ModelPrediction(
            user_id=resume.user_id,
            model_name="CV_NLP_MODEL",
            model_version=extraction.classifier_model_version or "extractor_only",
            prediction_type="cv_analysis",
            input_reference=str(resume.id),
            output={
                "tech_category": extraction.tech_category,
                "tech_category_confidence": extraction.tech_category_confidence,
                "classifier_available": extraction.classifier_available,
                "skills_found": extraction.skills_found,
            },
        ))

        resume.status = ResumeStatus.COMPLETED
        resume.stage = "COMPLETED"
        resume.progress = 100
        db.add(resume)

        # Per the "never persist the raw CV" policy - delete the stored
        # file now that structured analysis has been extracted.
        try:
            storage.delete(resume.storage_key)
            resume.storage_key = None
        except Exception:
            pass

        db.commit()
        db.refresh(analysis)
        return analysis

    except Exception as exc:
        db.rollback()
        resume.status = ResumeStatus.FAILED
        resume.stage = "FAILED"
        resume.error_message = str(exc)[:1000]
        db.add(resume)
        db.commit()
        raise
