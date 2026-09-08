import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint, func
from app.models.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import JobStatus


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "source_job_id", name="uq_job_source"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), index=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    work_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    source: Mapped[str] = mapped_column(String(50), index=True)
    source_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    posted_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.UNKNOWN, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    skill_links: Mapped[list["JobSkill"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    status_history: Mapped[list["JobStatusHistory"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"
    __table_args__ = (UniqueConstraint("job_id", "skill_id", name="uq_job_skill"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("jobs.id", ondelete="CASCADE"))
    skill_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("skills.id", ondelete="CASCADE"))
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False)

    job: Mapped["Job"] = relationship(back_populates="skill_links")
    skill: Mapped["Skill"] = relationship(back_populates="job_links")


class JobStatusHistory(Base):
    """Append-only status log. This IS the 'time series' data in this
    system - CRUD tracking of real observed status, not a forecast."""

    __tablename__ = "job_status_history"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("jobs.id", ondelete="CASCADE"))
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    job: Mapped["Job"] = relationship(back_populates="status_history")
