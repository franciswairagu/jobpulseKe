from pydantic import BaseModel

from app.schemas.job import JobOut
from app.schemas.recommendation import RecommendationOut


class MarketInsights(BaseModel):
    jobs_added_this_week: int
    jobs_removed_this_week: int
    total_available_jobs: int
    top_countries: list[dict]
    top_skills: list[dict]
    note: str = "Computed from real database aggregates. No forecasting/prediction is performed."


class DashboardOut(BaseModel):
    cv_score: int | None
    skills: list[str]
    skills_to_improve: list[str]
    recommendations: list[RecommendationOut]
    available_jobs: list[JobOut]
    market_insights: MarketInsights
