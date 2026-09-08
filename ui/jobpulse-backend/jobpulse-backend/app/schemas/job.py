import uuid
from datetime import date, datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: uuid.UUID
    title: str
    company: str | None
    country: str | None
    city: str | None
    remote: bool
    work_mode: str | None
    employment_type: str | None
    source: str
    source_url: str | None
    posted_at: date | None
    expires_at: date | None
    status: str
    required_skills: list[str] = []
    preferred_skills: list[str] = []

    class Config:
        from_attributes = True


class JobListOut(BaseModel):
    jobs: list[JobOut]
    total: int
    page: int
    limit: int


class JobStatusHistoryOut(BaseModel):
    status: str
    timestamp: datetime
    source: str | None
    confidence: float | None
    note: str | None

    class Config:
        from_attributes = True


class JobStatusUpdate(BaseModel):
    status: str
    source: str | None = None
    confidence: float | None = None
    note: str | None = None


class SkillDemandOut(BaseModel):
    skill: str
    demand: int
    jobs: int
    role: str = ""
    growth: int = 0
    status: str = "Stable"


class SkillDemandResponse(BaseModel):
    skills: list[SkillDemandOut]
    total: int
    dataSource: dict
