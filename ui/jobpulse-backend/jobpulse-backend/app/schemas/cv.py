import uuid
from datetime import datetime

from pydantic import BaseModel


class ResumeUploadOut(BaseModel):
    resume_id: uuid.UUID
    status: str
    uploaded_at: datetime


class ResumeStatusOut(BaseModel):
    status: str
    stage: str | None
    progress: int
    error_message: str | None = None


class SkillOut(BaseModel):
    name: str
    confidence: float | None = None


class CVAnalysisOut(BaseModel):
    resume_id: uuid.UUID
    cv_score: int | None
    score_type: str
    tech_category: str | None
    tech_category_confidence: float | None
    classifier_available: bool
    skills: list[SkillOut]
    years_experience: int
    education: list[str]
    certifications: list[str]
    seniority_level: str | None
    strengths: list[str]
    weaknesses: list[str]
    missing_skills: list[str]
    created_at: datetime

    class Config:
        from_attributes = True
