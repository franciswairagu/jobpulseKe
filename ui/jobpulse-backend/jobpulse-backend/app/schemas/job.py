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
    salary_min: float | None
    salary_max: float | None
    currency: str | None
    salary_reliable: bool
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
