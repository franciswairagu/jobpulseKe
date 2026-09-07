import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, UniqueConstraint, func
from app.models.types import GUID, StringArray
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SkillSource


class Skill(Base):
    """Canonical skill entry. CV/job-extracted skill strings are mapped
    here so 'Structured Query Language' and 'SQL' resolve to one row."""

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aliases: Mapped[list[str]] = mapped_column(StringArray(), default=list)

    job_links: Mapped[list["JobSkill"]] = relationship(back_populates="skill")
    user_links: Mapped[list["UserSkill"]] = relationship(back_populates="skill")


class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"))
    skill_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("skills.id", ondelete="CASCADE"))
    source: Mapped[SkillSource] = mapped_column(Enum(SkillSource), default=SkillSource.CV)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="user_skills")
    skill: Mapped["Skill"] = relationship(back_populates="user_links")
