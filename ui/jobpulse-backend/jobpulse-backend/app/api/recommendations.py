from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.enums import RecommendationType
from app.models.recommendation import Recommendation
from app.models.resume import Resume
from app.models.user import User
from app.schemas.recommendation import RecommendationOut, RecommendationsResponse, RecommendedJobOut
from app.services.recommendation_service import generate_recommendations

router = APIRouter(prefix="/api", tags=["recommendations"])


def _to_out(rec: Recommendation) -> RecommendationOut:
    return RecommendationOut(
        title=rec.title,
        type=rec.type.value,
        reason=rec.reason,
        related_skill=rec.related_skill,
        priority=rec.priority.value,
        url=rec.url,
        provider=rec.provider,
        score=rec.score,
        duration=rec.duration,
        difficulty=rec.difficulty,
    )


@router.get("/recommendations", response_model=RecommendationsResponse)
def get_recommendations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest_resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    analysis = latest_resume.analysis if latest_resume else None

    result = generate_recommendations(db, current_user, analysis)
    courses = [_to_out(r) for r in result["courses"]]
    interview_platforms = [_to_out(r) for r in result["interview_platforms"]]

    return RecommendationsResponse(
        interview_platforms=interview_platforms,
        courses=courses,
        learning_resources=courses,
    )


@router.get("/jobs/recommended", response_model=list[RecommendedJobOut])
def get_recommended_jobs(top_k: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest_resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    analysis = latest_resume.analysis if latest_resume else None

    result = generate_recommendations(db, current_user, analysis, top_k=top_k)
    return [
        RecommendedJobOut(
            job_id=r.job.job_id,
            title=r.job.title,
            company=r.job.company,
            match_score=r.match_percentage,
            matched_skills=sorted(r.matched_skills),
            missing_skills=sorted(r.missing_skills),
            reasons=r.reasons,
        )
        for r in result["job_recommendations"]
    ]
