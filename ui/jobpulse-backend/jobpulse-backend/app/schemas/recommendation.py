from pydantic import BaseModel


class RecommendationOut(BaseModel):
    title: str
    type: str
    reason: str | None
    related_skill: str | None
    priority: str
    url: str | None
    provider: str | None
    score: float | None

    class Config:
        from_attributes = True


class RecommendationsResponse(BaseModel):
    interview_platforms: list[RecommendationOut]
    courses: list[RecommendationOut]
    learning_resources: list[RecommendationOut]


class RecommendedJobOut(BaseModel):
    job_id: str
    title: str
    company: str
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    reasons: list[str]
