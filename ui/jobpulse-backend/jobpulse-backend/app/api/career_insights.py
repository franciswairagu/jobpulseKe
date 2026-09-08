from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.resume import Resume, ResumeAnalysis
from app.models.user import User

router = APIRouter(prefix="/api/career-insights", tags=["career-insights"])

ANALYTICS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent
    / "data" / "analytics"
)


def _load_latest_analytics() -> dict:
    """Load the most recent analytics JSON files."""
    if not ANALYTICS_DIR.exists():
        return {}

    refresh_dirs = sorted(
        [d for d in ANALYTICS_DIR.iterdir() if d.is_dir() and d.name.startswith("refresh_")],
        key=lambda d: d.name,
        reverse=True,
    )
    if not refresh_dirs:
        return {}

    base = refresh_dirs[0]
    result = {}
    for name in [
        "career_pathways.json",
        "skills_by_seniority.json",
        "remote_trends.json",
        "skill_region_matrix.json",
    ]:
        fpath = base / name
        if fpath.exists():
            try:
                result[name.replace(".json", "")] = json.loads(fpath.read_text())
            except Exception:
                pass
    return result


def _get_user_seniority(resume_analysis: ResumeAnalysis | None) -> str:
    """Infer seniority level from resume analysis."""
    if resume_analysis and resume_analysis.seniority_level:
        return resume_analysis.seniority_level
    return "Mid-Level"


def _get_user_skill_categories(resume_analysis: ResumeAnalysis | None) -> dict[str, int]:
    """Count user skills by category from resume analysis."""
    if not resume_analysis or not resume_analysis.skills_found:
        return {}
    from app.ml.preprocessing.skill_extractor import get_extractor
    extractor = get_extractor()
    categories: dict[str, int] = {}
    for skill in resume_analysis.skills_found:
        cat = extractor.taxonomy.get(skill.lower())
        if cat:
            categories[cat] = categories.get(cat, 0) + 1
    return categories


@router.get("")
def get_career_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analytics = _load_latest_analytics()

    resume_analysis = (
        db.query(ResumeAnalysis)
        .join(Resume, Resume.id == ResumeAnalysis.resume_id)
        .filter(Resume.user_id == current_user.id)
        .order_by(ResumeAnalysis.id.desc())
        .first()
    )

    user_seniority = _get_user_seniority(resume_analysis)
    user_skill_categories = _get_user_skill_categories(resume_analysis)
    user_skills = list(resume_analysis.skills_found) if resume_analysis and resume_analysis.skills_found else []

    career_pathways = analytics.get("career_pathways", {})
    seniority_progression = career_pathways.get("seniority_progression", {})
    skills_by_seniority = career_pathways.get("skills_by_seniority", {})
    experience_by_seniority = career_pathways.get("experience_by_seniority", {})
    remote_trends = analytics.get("remote_trends", {})
    skill_region = analytics.get("skill_region_matrix", {})

    SENIORITY_ORDER = ["Intern", "Entry Level", "Mid-Level", "Senior", "Lead", "Executive"]
    current_idx = SENIORITY_ORDER.index(user_seniority) if user_seniority in SENIORITY_ORDER else 2
    next_level = SENIORITY_ORDER[current_idx + 1] if current_idx + 1 < len(SENIORITY_ORDER) else None

    current_level_skills = skills_by_seniority.get(user_seniority, {})
    next_level_skills = skills_by_seniority.get(next_level, {}) if next_level else {}

    skill_gaps_next = {}
    for cat, count in next_level_skills.items():
        current_count = current_level_skills.get(cat, 0)
        if count > current_count:
            skill_gaps_next[cat] = count - current_count

    remote_by_seniority = remote_trends.get("by_seniority", {})
    user_remote = remote_by_seniority.get(user_seniority, {})

    skill_demand_by_country = {}
    for skill_name in user_skills:
        regions = skill_region.get(skill_name.lower(), {})
        if regions:
            skill_demand_by_country[skill_name] = regions

    countries_with_demand = set()
    for skill_regions in skill_demand_by_country.values():
        countries_with_demand.update(skill_regions.keys())
    countries_with_demand.discard("Global Remote")

    return {
        "user_seniority": user_seniority,
        "user_skills": user_skills,
        "user_skill_categories": user_skill_categories,
        "seniority_progression": seniority_progression,
        "skills_by_seniority": skills_by_seniority,
        "experience_by_seniority": experience_by_seniority,
        "next_level": next_level,
        "skill_gaps_next_level": skill_gaps_next,
        "remote_by_seniority": remote_by_seniority,
        "user_remote_stats": user_remote,
        "remote_by_category": remote_trends.get("by_skill_category", {}),
        "overall_remote": remote_trends.get("overall", {}),
        "skill_demand_by_country": skill_demand_by_country,
        "countries_with_demand": sorted(countries_with_demand),
        "cv_score": resume_analysis.cv_score if resume_analysis else None,
    }
