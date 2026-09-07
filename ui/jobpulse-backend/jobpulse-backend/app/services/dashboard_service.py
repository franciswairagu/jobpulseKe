from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from app.models.job import Job
from app.models.enums import JobStatus
from app.models.recommendation import Recommendation
from app.models.resume import Resume, ResumeAnalysis
from app.models.user import User
from app.services import job_service


def get_dashboard(db: Session, user: User) -> dict:
    latest_resume = (
        db.query(Resume)
        .filter(Resume.user_id == user.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    analysis: ResumeAnalysis | None = latest_resume.analysis if latest_resume else None

    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user.id)
        .order_by(Recommendation.score.desc().nullslast())
        .limit(10)
        .all()
    )

    available_jobs, _ = job_service.search_jobs(db, status=JobStatus.AVAILABLE, limit=10)

    return {
        "cv_score": analysis.cv_score if analysis else None,
        "skills": analysis.skills_found if analysis else [],
        "skills_to_improve": analysis.missing_skills if analysis else [],
        "recommendations": recommendations,
        "available_jobs": available_jobs,
        "market_insights": job_service.market_insights(db),
    }
