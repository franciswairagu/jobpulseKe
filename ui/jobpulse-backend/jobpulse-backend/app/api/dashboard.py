from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
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
