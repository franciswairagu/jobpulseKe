import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, func
from app.models.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import RecommendationPriority, RecommendationType


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"))
    resume_analysis_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("resume_analyses.id", ondelete="SET NULL"), nullable=True)

    type: Mapped[RecommendationType] = mapped_column(Enum(RecommendationType))
    title: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    related_skill: Mapped[str | None] = mapped_column(String(150), nullable=True)
    priority: Mapped[RecommendationPriority] = mapped_column(Enum(RecommendationPriority), default=RecommendationPriority.MEDIUM)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModelPrediction(Base):
    """Audit trail for every model/derived-score invocation - required so
    outputs remain traceable to the model_name/version that produced them."""

    __tablename__ = "model_predictions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    model_name: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[str] = mapped_column(String(50))
    prediction_type: Mapped[str] = mapped_column(String(100))
    input_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    output: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
