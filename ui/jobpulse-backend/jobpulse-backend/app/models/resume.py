import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, func
from app.models.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ResumeStatus


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"))
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ResumeStatus] = mapped_column(Enum(ResumeStatus), default=ResumeStatus.UPLOADING)
    stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="resumes")
    analysis: Mapped["ResumeAnalysis"] = relationship(back_populates="resume", uselist=False, cascade="all, delete-orphan")


class ResumeAnalysis(Base):
    """
    Structured output of the CV analysis pipeline.

    Field provenance is tracked explicitly:
      - skills/years_experience/education/certifications/seniority_level:
        real output of the reconstructed skill_extractor (rule-based).
      - tech_category / tech_category_confidence: real output of the
        trained TF-IDF+LogisticRegression classifier IF its artifact is
        present at CV_CATEGORY_MODEL_PATH; null + classifier_available=False
        otherwise. Never fabricated.
      - cv_score: a deterministic, documented composite (see
        app/services/cv_service.py::compute_cv_score) - NOT an ML model
        output. score_type makes this explicit to API consumers.
    """

    __tablename__ = "resume_analyses"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("resumes.id", ondelete="CASCADE"), unique=True)

    cv_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_type: Mapped[str] = mapped_column(String(50), default="deterministic_composite")

    tech_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tech_category_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    classifier_available: Mapped[bool] = mapped_column(default=False)
    classifier_model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    skills_found: Mapped[list[str]] = mapped_column(JSON, default=list)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    education: Mapped[list[str]] = mapped_column(JSON, default=list)
    certifications: Mapped[list[str]] = mapped_column(JSON, default=list)
    seniority_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    strengths: Mapped[list[str]] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list)

    extractor_version: Mapped[str] = mapped_column(String(50), default="skill_extractor_v1_reconstructed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    resume: Mapped["Resume"] = relationship(back_populates="analysis")
