from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.api.deps import get_current_user
from app.database import get_db
from app.models.job import Job, JobSkill
from app.models.skill import Skill
from app.models.enums import JobStatus
from app.models.user import User
from app.schemas.dashboard import DashboardOut, MarketInsights
from app.schemas.job import JobOut
from app.schemas.recommendation import RecommendationOut
from app.services.dashboard_service import get_dashboard

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.api.jobs import _to_job_out
    from app.api.recommendations import _to_out

    data = get_dashboard(db, current_user)
    return DashboardOut(
        cv_score=data["cv_score"],
        skills=data["skills"],
        skills_to_improve=data["skills_to_improve"],
        recommendations=[_to_out(r) for r in data["recommendations"]],
        available_jobs=[_to_job_out(j) for j in data["available_jobs"]],
        market_insights=MarketInsights(**data["market_insights"]),
    )


@router.get("/skill-trend")
def skill_trend(
    skill: str = Query(..., description="Skill name to track"),
    months: int = Query(12, ge=3, le=36, description="Number of months to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return monthly job posting counts for a specific skill over time."""
    from datetime import date, timedelta

    cutoff = date.today() - timedelta(days=months * 30)

    rows = (
        db.query(
            func.strftime("%Y-%m", Job.posted_at).label("month"),
            func.count(Job.id).label("count"),
        )
        .join(JobSkill, JobSkill.job_id == Job.id)
        .join(Skill, Skill.id == JobSkill.skill_id)
        .filter(
            Job.status == JobStatus.AVAILABLE,
            Job.posted_at.isnot(None),
            Job.posted_at >= cutoff,
            func.lower(Skill.name) == skill.lower(),
        )
        .group_by("month")
        .order_by("month")
        .all()
    )

    points = [{"month": r.month, "value": r.count} for r in rows]

    # Calculate growth rate
    growth_rate = 0
    if len(points) >= 2:
        recent = points[-1]["value"]
        previous = points[-2]["value"]
        if previous > 0:
            growth_rate = round(((recent - previous) / previous) * 100)

    return {
        "skill": skill,
        "growth_rate": growth_rate,
        "points": points,
    }
