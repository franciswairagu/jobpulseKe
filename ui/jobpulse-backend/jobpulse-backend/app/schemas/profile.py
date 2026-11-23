import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    career_interest: str | None = Field(default=None, max_length=255)
    years_experience: int | None = Field(default=None, ge=0, le=70)
    preferred_work_mode: str | None = Field(default=None, max_length=50)


class ResumeProfileOut(BaseModel):
    resume_id: uuid.UUID
    original_filename: str
    status: str
    uploaded_at: datetime
    available: bool


class ProfileOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str | None = None
    country: str | None = None
    city: str | None = None
    career_interest: str | None = None
    years_experience: int | None = None
    preferred_work_mode: str | None = None
    latest_resume: ResumeProfileOut | None = None
